import os
import pandas as pd
from datetime import datetime
from app.state import State
from app.tools.bigquery_tools import get_students_past_due_by_bucket

REPORTS_DIR = os.getenv("BURSARBOT_REPORTS_DIR", "reports")

def summarize_node(state: State) -> State:
    rows = get_students_past_due_by_bucket.invoke({"bucket": None, "limit": 500})

    os.makedirs(REPORTS_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"past_due_students_{ts}.csv"
    path = os.path.join(REPORTS_DIR, filename)

    if not rows or (len(rows) == 1 and "error" in rows[0]):
        error = rows[0].get("error", "Unknown error") if rows else "No data returned"
        return {"result": f"Could not generate report: {error}"}

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)

    bucket_summary = df.groupby("aging_bucket").size().to_dict()
    summary_lines = "\n".join(
        f"  {bucket}: {count} student(s)"
        for bucket, count in sorted(bucket_summary.items())
    )

    return {
        "result": (
            f"Exported {len(df)} past-due students to: {path}\n\n"
            f"Breakdown by aging bucket:\n{summary_lines}"
        )
    }