import argparse
import os
import sqlite3
import pandas as pd
from datetime import datetime


def load_input(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()

    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    if ext == ".csv":
        return pd.read_csv(path)

    raise ValueError(f"Unsupported input format: {ext}")


def validate_date_format(date_str: str) -> None:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid due_date format: {date_str}. Expected YYYY-MM-DD.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to CSV or Excel file")
    parser.add_argument("--db", default="bursarbot.db", help="SQLite DB file")
    parser.add_argument("--table", default="students", help="Table name")

    args = parser.parse_args()

    df = load_input(args.input)

    required_columns = [
        "student_id",
        "first_name",
        "last_name",
        "email",
        "term",
        "due_date",
        "total_fees_usd",
        "paid_to_date_usd",
    ]

    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[required_columns].copy()

    df["student_id"] = df["student_id"].astype(int)
    df["total_fees_usd"] = df["total_fees_usd"].astype(int)
    df["paid_to_date_usd"] = df["paid_to_date_usd"].astype(int)
    df["due_date"] = df["due_date"].astype(str)

    df["due_date"].apply(validate_date_format)

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {args.table};")
    conn.commit()

    cursor.execute(f"""
        CREATE TABLE {args.table} (
            student_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            term TEXT NOT NULL,
            due_date TEXT NOT NULL,   -- ISO YYYY-MM-DD
            total_fees_usd INTEGER NOT NULL,
            paid_to_date_usd INTEGER NOT NULL
        );
    """)

    conn.commit()

    df.to_sql(args.table, conn, if_exists="append", index=False)

    cursor.execute(f"CREATE INDEX idx_{args.table}_term ON {args.table}(term);")
    cursor.execute(f"CREATE INDEX idx_{args.table}_due_date ON {args.table}(due_date);")

    conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM {args.table};")
    total_rows = cursor.fetchone()[0]

    print(f"Loaded {total_rows} rows into {args.db}")
    print("Schema includes due_date. Balance will be computed dynamically in SQL.")

    conn.close()


if __name__ == "__main__":
    main()