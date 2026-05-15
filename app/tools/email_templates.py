import os
from datetime import date

COLLECTOR_NAME = os.getenv("BURSARBOT_COLLECTOR_NAME", "Bursar Collections")
COLLECTOR_PHONE = os.getenv("BURSARBOT_COLLECTOR_PHONE", "(408) 924-1601")

_FOOTER = """\
Any questions you may have concerning this matter may be directed to {collector_name} at {collector_phone}. \
Once you have paid the balance, please contact your Account Specialist to have the hold removed.

SJSU Bursar's Office
One Washington Square,
San José, CA 95192-0138"""

_CL1_BODY = (
    "This is a notice for the outstanding balance as noted above. "
    "You may view your student account detail through your MySJSU portal.\n\n"
    "Please pay your past due debt within 30 days from the date of this letter. "
    "We encourage you to pay electronically to ensure your payment is posted within the 30-day time period. "
    "You may make payment by ACH using your bank's routing number and your checking or savings account number. "
    "There is no fee to make payment using ACH. You may also pay by credit card (online only). "
    "Note: There is a 2.65% convenience fee that will be charged in addition to the payment amount. "
    "You may also mail a check in the payment envelope enclosed for your convenience. "
    "Please be sure that your name and student ID number appear on the face of the check so you will receive proper credit. "
    "A hold has been placed on your academic records that will prevent you from receiving services from the University. "
    "If you fail to remit payment or to contact our office within the next 30 days, your account will be reviewed "
    "for referral to the Franchise Tax Board for offsetting of any refunds owed to you by the State of California "
    "and under review to be prepared for referral to an outside collection agency for further action."
)

_CL2_BODY = (
    "This is your second notice for the outstanding balance as noted above. "
    "You may view your student account detail through your MySJSU portal.\n\n"
    "Please pay your past due debt within 30 days from the date of this letter. "
    "We encourage you to pay electronically to ensure your payment is posted within the 30-day time period. "
    "You may make payment by ACH using your bank's routing number and your checking or savings account number. "
    "There is no fee to make payment using ACH. You may also pay by credit card (online only). "
    "Note: There is a 2.65% convenience fee that will be charged in addition to the payment amount. "
    "You may also mail a check in the payment envelope enclosed for your convenience. "
    "Please be sure that your name and student ID number appear on the face of the check so you will receive proper credit. "
    "A hold has been placed on your academic records that will prevent you from receiving services from the University. "
    "If you fail to remit payment or to contact our office within the next 30 days, your account will be reviewed "
    "for referral to the Franchise Tax Board for offsetting of any refunds owed to you by the State of California "
    "and under further review to be prepared for referral to an outside collection agency for further action."
)

_FINAL_DEMAND_BODY = (
    "This is a final demand notice for the outstanding balance as noted above. "
    "You may view your student account detail through your MySJSU portal.\n\n"
    "Please pay your past due debt within 30 days from the date of this letter. "
    "We encourage you to pay electronically to ensure your payment is posted within the 30-day time period. "
    "You may make payment by ACH using your bank's routing number and your checking or savings account number. "
    "There is no fee to make payment using ACH. You may also pay by credit card (online only). "
    "Note: There is a 2.65% convenience fee that will be charged in addition to the payment amount. "
    "You may also mail a check in the payment envelope enclosed for your convenience. "
    "Please be sure that your name and student ID number appear on the face of the check so you will receive proper credit.\n\n"
    "A hold has been placed on your academic records that will prevent you from receiving services from the University. "
    "If you fail to remit payment or to contact our office within the next 30 days, your account will be referred "
    "to the Franchise Tax Board for offsetting of any refunds owed to you by the State of California and your account "
    "will be referred to an outside collection agency for further action."
)

# bucket → (subject, body)
BUCKET_TEMPLATES = {
    "61-90":   ("Outstanding Balance Notice – Action Required",                  _CL1_BODY),
    "91-120":  ("Second Notice: Outstanding Balance – Action Required",           _CL2_BODY),
    "121-150": ("FINAL DEMAND: Outstanding Balance – Immediate Action Required",  _FINAL_DEMAND_BODY),
    ">150":    ("FINAL DEMAND: Outstanding Balance – Immediate Action Required",  _FINAL_DEMAND_BODY),
}


def build_email(
    bucket: str,
    student_name: str,
    student_id: str,
    address: str,
    city: str,
    state: str,
    postal: str,
    balance: str,
) -> tuple[str, str]:
    """
    Returns (subject, body) for the given bucket using the official template.
    Raises ValueError for unsupported buckets.
    """
    if bucket not in BUCKET_TEMPLATES:
        raise ValueError(
            f"No email template for bucket '{bucket}'. "
            f"Supported: {list(BUCKET_TEMPLATES.keys())}"
        )

    subject, body_text = BUCKET_TEMPLATES[bucket]
    today = date.today().strftime("%B %d, %Y")

    body = (
        f"Date: {today}\n\n"
        f"{student_name}\n"
        f"{address}\n"
        f"{city}, {state} {postal}\n"
        f"                    ID# {student_id}\n"
        f"                    Balance: ${balance}\n\n"
        f"** THIS REQUIRES YOUR IMMEDIATE ATTENTION **\n\n"
        f"Dear {student_name}:\n\n"
        f"{body_text}\n\n"
        + _FOOTER.format(
            collector_name=COLLECTOR_NAME,
            collector_phone=COLLECTOR_PHONE,
        )
    )

    return subject, body
