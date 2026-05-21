import os
from datetime import datetime
from functools import lru_cache
from typing import Annotated, Any, Dict, List, Optional

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports")

VALID_BUCKETS = {"61-90", "91-120", "121-150", ">150"}


def get_user_role(user_id: str) -> str:
    """
    Look up the user's role from AIGravyty_USERS.
    If found, returns that role (e.g. 'admin', 'staff').
    If not found, the user is a student — returns 'student'.
    """
    from google.cloud import bigquery

    project = os.getenv("BQ_PROJECT_ID", "sjsu-it-genai-poc")
    dataset = os.getenv("BQ_DATASET_ID", "student_financials")
    gravyty = f"{project}.{dataset}.AIGravyty_USERS"

    query = f"SELECT ROLE FROM `{gravyty}` WHERE EMPLID = @user_id LIMIT 1"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
    )

    try:
        rows = list(_bq_client().query(query, job_config=job_config).result())
        if rows and rows[0].get("ROLE"):
            return str(rows[0].get("ROLE")).lower()
        return "student"
    except Exception:
        return "student"


@lru_cache(maxsize=1)
def _bq_client():
    """
    Create a BigQuery client.

    Auth is resolved via standard Google auth (recommended):
    - GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
    """
    from google.cloud import bigquery  # lazy import so repo works without dep until installed

    # Explicit project if provided; otherwise let google-auth infer it.
    project = os.getenv("BQ_PROJECT_ID") or None
    return bigquery.Client(project=project)


def _finance_table_fqn() -> str:
    project_id = os.getenv("BQ_PROJECT_ID", "sjsu-it-genai-poc")
    dataset_id = os.getenv("BQ_DATASET_ID", "student_financials")
    table_id = os.getenv("BQ_FINANCE_TABLE_ID", "Student_FinancialRecords")
    return f"{project_id}.{dataset_id}.{table_id}"


@tool
def get_student_balance_bigquery(
    student_id: str,
    state: Annotated[dict, InjectedState],
) -> List[Dict[str, Any]]:
    """
    Fetch all individual balance records for a student from BigQuery by EMPLID.
    Each row in Student_FinancialRecords is returned as a separate balance entry.

    Args:
      student_id: EMPLID (string). Example: "000775672"

    Returns:
      List of dicts, one per record, with keys:
        student_id, item_descr, item_amt, applied_amt, balance,
        account_term, item_term, item_effective_dt, item_type_cd
    """
    from google.cloud import bigquery

    # For students, enforce that they can only query their own records
    if state.get("user_role") == "student":
        authenticated_id = state.get("user_id")
        if authenticated_id and str(student_id).strip() != str(authenticated_id).strip():
            return [{
                "error": (
                    f"Access denied. You are authenticated as student {authenticated_id} "
                    f"but requested data for student {student_id}. "
                    f"You can only access your own records."
                )
            }]
        student_id = authenticated_id or student_id

    student_id = str(student_id).strip()
    if not student_id:
        raise ValueError("student_id is required")

    table = _finance_table_fqn()
    query = f"""
    SELECT
      @student_id                                                  AS student_id,
      ACCOUNT_TERM,
      Item_DESCR                                                   AS item_descr,
      SAFE_CAST(ITEM_AMT AS FLOAT64)                               AS item_amt,
      SAFE_CAST(APPLIED_AMT AS FLOAT64)                            AS applied_amt,
      ITEM_TERM                                                    AS item_term,
      FORMAT_DATE('%m/%d/%Y', DATE(ITEM_EFFECTIVE_DT))             AS item_effective_dt,
      ITEM_TYPE_CD                                                 AS item_type_cd,
      SAFE_CAST(Balance AS FLOAT64)                                AS balance
    FROM `{table}`
    WHERE emplid = @student_id
    ORDER BY ITEM_EFFECTIVE_DT
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
        ]
    )

    try:
        rows = list(_bq_client().query(query, job_config=job_config).result())
        if not rows:
            return [{"student_id": student_id, "error": "No finance records found for that student_id.", "source": "bigquery"}]

        return [dict(r) for r in rows]
    except Exception as e:
        return [{"student_id": student_id, "error": f"{type(e).__name__}: {str(e)}", "source": "bigquery"}]


@tool
def get_students_past_due_by_bucket(
    bucket: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch past-due students from BigQuery grouped by aging bucket.

    Args:
        bucket: Filter by a specific aging bucket. One of: "61-90", "91-120",
                "121-150", ">150". Pass None to return all past-due students
                across every bucket.
        limit:  Max students to return (1-500, default 100).

    Returns:
        List of dicts, one per overdue entry, with keys:
            student_id, first_name, last_name, email, phone,
            address, city, state, postal,
            due_date, days_past_due, aging_bucket,
            payment_status, reason_codes, financial_aid_status
    """
    from google.cloud import bigquery

    if bucket is not None and bucket not in VALID_BUCKETS:
        return [{"error": f"Invalid bucket '{bucket}'. Must be one of {sorted(VALID_BUCKETS)} or None."}]

    limit = max(1, min(limit, 500))

    project   = os.getenv("BQ_PROJECT_ID", "sjsu-it-genai-poc")
    dataset   = os.getenv("BQ_DATASET_ID", "student_financials")
    personal  = f"{project}.{dataset}.Student_Personal"
    finance   = f"{project}.{dataset}.Student_FinancialRecords"
    late_pay  = f"{project}.{dataset}.late_pay"

    bucket_filter = "TRUE" if bucket is None else "d.aging_bucket = @bucket"

    query = f"""
    WITH dues AS (
      SELECT
        lp.student_id,
        PARSE_DATE('%m/%d/%Y', lp.due_date)                               AS due_date,
        DATE_DIFF(CURRENT_DATE(),
                  PARSE_DATE('%m/%d/%Y', lp.due_date), DAY)               AS days_past_due,
        CASE
          WHEN DATE_DIFF(CURRENT_DATE(),
                         PARSE_DATE('%m/%d/%Y', lp.due_date), DAY) BETWEEN 61  AND 90  THEN '61-90'
          WHEN DATE_DIFF(CURRENT_DATE(),
                         PARSE_DATE('%m/%d/%Y', lp.due_date), DAY) BETWEEN 91  AND 120 THEN '91-120'
          WHEN DATE_DIFF(CURRENT_DATE(),
                         PARSE_DATE('%m/%d/%Y', lp.due_date), DAY) BETWEEN 121 AND 150 THEN '121-150'
          WHEN DATE_DIFF(CURRENT_DATE(),
                         PARSE_DATE('%m/%d/%Y', lp.due_date), DAY) > 150              THEN '>150'
          ELSE '0-60'
        END                                                                AS aging_bucket,
        lp.payment_status,
        lp.reason_code                                                     AS reason_codes,
        lp.financial_aid_status
      FROM `{late_pay}` lp
      WHERE lp.due_date IS NOT NULL
    )
    SELECT
      d.student_id,
      sp.FIRST_NAME                                                        AS first_name,
      sp.LAST_NAME                                                         AS last_name,
      sp.EMAIL_ADDR                                                        AS email,
      sp.PHONE                                                             AS phone,
      sp.ADDRESS1                                                          AS address,
      sp.CITY                                                              AS city,
      sp.STATE                                                             AS state,
      sp.POSTAL                                                            AS postal,
      d.due_date,
      d.days_past_due,
      d.aging_bucket,
      d.payment_status,
      d.reason_codes,
      d.financial_aid_status,
      ROUND(COALESCE(bal.total_balance, 0), 2)                            AS balance
    FROM dues d
    LEFT JOIN `{personal}` sp ON sp.EMPLID = d.student_id
    LEFT JOIN (
      SELECT emplid, SUM(SAFE_CAST(Balance AS FLOAT64)) AS total_balance
      FROM `{finance}`
      GROUP BY emplid
    ) bal ON bal.emplid = d.student_id
    WHERE d.days_past_due > 0 AND {bucket_filter}
    ORDER BY d.days_past_due DESC
    LIMIT @limit
    """

    params = [bigquery.ScalarQueryParameter("limit", "INT64", limit)]
    if bucket is not None:
        params.append(bigquery.ScalarQueryParameter("bucket", "STRING", bucket))

    job_config = bigquery.QueryJobConfig(query_parameters=params)

    try:
        rows = list(_bq_client().query(query, job_config=job_config).result())
        data = [dict(row) for row in rows]

        report_path = _save_excel_report(data, bucket)
        for record in data:
            record["report_path"] = report_path

        return data
    except Exception as e:
        return [{"error": f"{type(e).__name__}: {str(e)}"}]


def _save_excel_report(data: List[Dict], bucket: Optional[str]) -> str:
    import pandas as pd

    bucket_label = bucket.replace(">", "gt") if bucket else "all"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"students_past_due_{bucket_label}_{timestamp}.xlsx"

    os.makedirs(REPORTS_DIR, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, filename)

    df = pd.DataFrame(data)
    display_cols = [
        "student_id", "first_name", "last_name", "email", "phone",
        "address", "city", "state", "postal",
        "due_date", "days_past_due", "aging_bucket",
        "payment_status", "reason_codes", "financial_aid_status",
    ]
    df = df[[c for c in display_cols if c in df.columns]]

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Past Due Students")
        ws = writer.sheets["Past Due Students"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    # Return a direct backend URL — frontend calls the backend directly (no proxy)
    backend = os.getenv("BURSARBOT_BACKEND_URL", "http://localhost:8001")
    return f"{backend}/reports/{filename}"


@tool
def get_student_financial_aid(
    student_id: str,
    state: Annotated[dict, InjectedState],
) -> List[Dict[str, Any]]:
    """
    Fetch financial aid records for a student from the FINAID_STDNT_AWARDS table.

    Args:
        student_id: EMPLID (string). Example: "000775672"

    Returns:
        List of dicts with keys: student_id, highest_offer_amt, net_award_amt,
        award_posted, award_status, category
    """
    from google.cloud import bigquery

    if state.get("user_role") == "student":
        authenticated_id = state.get("user_id")
        if authenticated_id and str(student_id).strip() != str(authenticated_id).strip():
            return [{
                "error": (
                    f"Access denied. You are authenticated as student {authenticated_id} "
                    f"but requested financial aid for student {student_id}. "
                    f"You can only access your own records."
                )
            }]
        student_id = authenticated_id or student_id

    student_id = str(student_id).strip()

    project = os.getenv("BQ_PROJECT_ID", "sjsu-it-genai-poc")
    dataset = os.getenv("BQ_DATASET_ID", "student_financials")
    table = f"{project}.{dataset}.FINAID_STDNT_AWARDS"

    query = f"""
    SELECT
      @student_id                                                      AS student_id,
      FORMAT('$%.2f', SAFE_CAST(highest_offer_AMT AS FLOAT64))        AS highest_offer_amt,
      FORMAT('$%.2f', SAFE_CAST(NET_AWARD_AMT AS FLOAT64))            AS net_award_amt,
      AWARD_POSTED                                                     AS award_posted,
      AWARD_STATUS                                                     AS award_status,
      Category                                                         AS category
    FROM `{table}`
    WHERE emplid = @student_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("student_id", "STRING", student_id)]
    )

    try:
        rows = list(_bq_client().query(query, job_config=job_config).result())
        if not rows:
            return [{"student_id": student_id, "error": "No financial aid records found for this student."}]
        return [dict(row) for row in rows]
    except Exception as e:
        return [{"student_id": student_id, "error": f"{type(e).__name__}: {str(e)}"}]


@tool
def get_student_comments(
    student_id: str,
    state: Annotated[dict, InjectedState],
) -> List[Dict[str, Any]]:
    """
    Fetch all comments/notes for a student from the Student_Comment table.

    Args:
        student_id: EMPLID (string). Example: "000775672"

    Returns:
        List of dicts with keys: student_id, comment_dt, comment
    """
    from google.cloud import bigquery

    if state.get("user_role") == "student":
        authenticated_id = state.get("user_id")
        if authenticated_id and str(student_id).strip() != str(authenticated_id).strip():
            return [{
                "error": (
                    f"Access denied. You are authenticated as student {authenticated_id} "
                    f"but requested comments for student {student_id}. "
                    f"You can only access your own records."
                )
            }]
        student_id = authenticated_id or student_id

    student_id = str(student_id).strip()

    project = os.getenv("BQ_PROJECT_ID", "sjsu-it-genai-poc")
    dataset = os.getenv("BQ_DATASET_ID", "student_financials")
    table = f"{project}.{dataset}.Student_Comment"

    query = f"""
    SELECT
      @student_id                                        AS student_id,
      comment_dt,
      COMMENTS                                           AS comment
    FROM `{table}`
    WHERE emplid = @student_id
    ORDER BY comment_dt DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("student_id", "STRING", student_id)]
    )

    try:
        rows = list(_bq_client().query(query, job_config=job_config).result())
        if not rows:
            return [{"student_id": student_id, "error": "No comments found for this student."}]
        return [dict(row) for row in rows]
    except Exception as e:
        return [{"student_id": student_id, "error": f"{type(e).__name__}: {str(e)}"}]
