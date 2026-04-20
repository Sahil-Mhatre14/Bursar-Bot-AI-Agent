import os
from functools import lru_cache
from typing import Any, Dict, Optional

from langchain_core.tools import tool


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
def get_student_balance_bigquery(student_id: str) -> Dict[str, Any]:
    """
    Fetch a student's current balance from BigQuery by EMPLID.

    Args:
      student_id: EMPLID (string). Example: "01234567"

    Returns:
      Dict with keys: student_id, balance_usd (float), balance_formatted (string)
    """
    from google.cloud import bigquery

    student_id = str(student_id).strip()
    if not student_id:
        raise ValueError("student_id is required")

    table = _finance_table_fqn()
    query = f"""
    SELECT
      @student_id AS student_id,
      MAX(SAFE_CAST(balance AS FLOAT64)) AS balance_usd
    FROM `{table}`
    WHERE emplid = @student_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
        ]
    )

    try:
        rows = list(_bq_client().query(query, job_config=job_config).result())
        if not rows:
            return {
                "student_id": student_id,
                "error": "No finance records found for that student_id.",
                "source": "bigquery",
            }

        balance_usd: Optional[float] = rows[0].get("balance_usd")
        if balance_usd is None:
            return {
                "student_id": student_id,
                "error": "Balance field was null for that student_id.",
                "source": "bigquery",
            }

        return {
            "student_id": student_id,
            "balance_usd": float(balance_usd),
            "balance_formatted": f"${float(balance_usd):.2f}",
            "source": "bigquery",
        }
    except Exception as e:
        # Return a compact error payload so the LLM can surface root cause.
        return {
            "student_id": student_id,
            "error": f"{type(e).__name__}: {str(e)}",
            "source": "bigquery",
        }

