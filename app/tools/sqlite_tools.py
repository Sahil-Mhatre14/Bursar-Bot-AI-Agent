import os
import sqlite3
from typing import Optional, List, Dict, Any

from langchain_core.tools import tool

DB_PATH = os.getenv("BURSARBOT_DB_PATH", "bursarbot.db")


def _connect():
    return sqlite3.connect(DB_PATH)


@tool
def get_students_with_dues(limit: int = 50, term: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return a list of students who have outstanding dues.
    Dues is computed as (total_fees_usd - paid_to_date_usd) > 0.

    Args:
      limit: max number of rows to return
      term: optional term filter (e.g., "Spring 2026")

    Returns:
      A list of dict rows including computed `balance_usd`.
    """
    limit = max(1, min(int(limit), 500))

    con = _connect()
    try:
        cur = con.cursor()

        if term:
            cur.execute(
                """
                SELECT
                    student_id, first_name, last_name, email, term,
                    total_fees_usd, paid_to_date_usd,
                    (total_fees_usd - paid_to_date_usd) AS balance_usd
                FROM students
                WHERE term = ?
                  AND (total_fees_usd - paid_to_date_usd) > 0
                ORDER BY balance_usd DESC
                LIMIT ?;
                """,
                (term, limit),
            )
        else:
            cur.execute(
                """
                SELECT
                    student_id, first_name, last_name, email, term,
                    total_fees_usd, paid_to_date_usd,
                    (total_fees_usd - paid_to_date_usd) AS balance_usd
                FROM students
                WHERE (total_fees_usd - paid_to_date_usd) > 0
                ORDER BY balance_usd DESC
                LIMIT ?;
                """,
                (limit,),
            )

        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


@tool
def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
    """
    Lookup a single student by ID and return row with computed `balance_usd`.
    Returns None if not found.
    """
    con = _connect()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT
                student_id, first_name, last_name, email, term,
                total_fees_usd, paid_to_date_usd,
                (total_fees_usd - paid_to_date_usd) AS balance_usd
            FROM students
            WHERE student_id = ?;
            """,
            (int(student_id),),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        con.close()


@tool
def get_students_due_next_30_days(limit: int = 500, term: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns students who have an outstanding balance AND due_date is within the next 30 days.
    Balance is computed as (total_fees_usd - paid_to_date_usd).
    """
    limit = max(1, min(int(limit), 2000))

    con = _connect()
    try:
        cur = con.cursor()

        if term:
            cur.execute(
                """
                SELECT
                  student_id, first_name, last_name, email, term, due_date,
                  total_fees_usd, paid_to_date_usd,
                  (total_fees_usd - paid_to_date_usd) AS balance_usd
                FROM students
                WHERE term = ?
                  AND (total_fees_usd - paid_to_date_usd) > 0
                  AND date(due_date) BETWEEN date('now') AND date('now', '+30 days')
                ORDER BY date(due_date) ASC, balance_usd DESC
                LIMIT ?;
                """,
                (term, limit),
            )
        else:
            cur.execute(
                """
                SELECT
                  student_id, first_name, last_name, email, term, due_date,
                  total_fees_usd, paid_to_date_usd,
                  (total_fees_usd - paid_to_date_usd) AS balance_usd
                FROM students
                WHERE (total_fees_usd - paid_to_date_usd) > 0
                  AND date(due_date) BETWEEN date('now') AND date('now', '+30 days')
                ORDER BY date(due_date) ASC, balance_usd DESC
                LIMIT ?;
                """,
                (limit,),
            )

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        con.close()