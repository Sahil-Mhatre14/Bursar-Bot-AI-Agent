import os
import pandas as pd
from datetime import datetime
from app.state import State
from app.tools.sqlite_tools import get_students_due_next_30_days

REPORTS_DIR = os.getenv("BURSARBOT_REPORTS_DIR", "reports")

def summarize_node(state: State) -> State:
    rows = get_students_due_next_30_days.invoke({"limit": 2000, "term": None})

    os.makedirs(REPORTS_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"students_due_next_30_days_{ts}.csv"
    path = os.path.join(REPORTS_DIR, filename)

    if not rows:
        df = pd.DataFrame(columns=[
            "student_id","first_name","last_name","email","term","due_date",
            "total_fees_usd","paid_to_date_usd","balance_usd"
        ])
        df.to_csv(path, index=False)
        return {"result": f"No rows found. Exported empty report to: {path}"}

    df = pd.DataFrame(rows)

    df = df[[
        "student_id","first_name","last_name","email","term","due_date",
        "total_fees_usd","paid_to_date_usd","balance_usd"
    ]]

    df.to_csv(path, index=False)

    return {
        "result": f"Exported {len(df)} students due in the next 30 days to: {path}"
    }