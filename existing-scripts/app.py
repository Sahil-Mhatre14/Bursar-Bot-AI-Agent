# Import necessary libraries
import os
import json
from typing import Dict, Any
from flask import Flask, request, jsonify
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from google.oauth2 import service_account
from functools import wraps
from flask_cors import CORS
import hmac

# Use loaded configuration variables
LOCAL_JSON_FILE = "E:\student-info-api\config\\Local_student-info-api.json"
PROD_JSON_FILE = "E:\student-info-api\config\\Prod_student-info-api.json"

# --- Configuration Loader ---
def load_config(file_path: str = PROD_JSON_FILE) -> Dict[str, Any]:
    """Loads configuration from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {file_path}. Please create a config.json file.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in {file_path}. Please check your file.")

# Load configuration at startup
try:
    config = load_config()
except (FileNotFoundError, ValueError) as e:
    raise SystemExit(f"Configuration loading failed: {e}")

# Use loaded configuration variables
PROJECT_ID = config["gcp"]["project_id"]
DATASET_ID = config["gcp"]["dataset_id"]
SERVICE_ACCOUNT_JSON_PATH = config["gcp"]["bq_read_credential_file_path"]

#Tables & Queries
#INFO
INFO_TABLE_ID = config["gcp"]["info_table_id"]
INFO_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{INFO_TABLE_ID}"
INFO_TABLE_COLUMNS = config["gcp"]["info_table_columns"]
INFO_AND_ROLE_QUERY = config["gcp"]["info_and_role_query"]
QRY_STUDENT_DETAILS = f"""SELECT {INFO_TABLE_COLUMNS} FROM `{INFO_TABLE}` WHERE emplid = @student_id LIMIT 1;"""
QRY_STUDENT_DETAILS_AND_ROLE = f"""SELECT * FROM {INFO_AND_ROLE_QUERY} WHERE emplid = @student_id LIMIT 1"""

#ACAD
ACAD_TABLE_ID = config["gcp"]["acad_table_id"]
ACAD_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{ACAD_TABLE_ID}"
ACAD_TABLE_COLUMNS = config["gcp"]["acad_table_columns"]
QRY_STUDENT_ACAD_DETAILS = f"""SELECT {ACAD_TABLE_COLUMNS} FROM `{ACAD_TABLE}` WHERE emplid = @student_id;"""

#FINANCE
FINANCE_TABLE_ID = config["gcp"]["finance_table_id"]
FINANCE_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{FINANCE_TABLE_ID}"
FINANCE_TABLE_COLUMNS = config["gcp"]["finance_table_columns"]
QRY_STUDENT_FINANCE_DETAILS = f"""SELECT {FINANCE_TABLE_COLUMNS} FROM `{FINANCE_TABLE}` WHERE emplid = @student_id;"""

#FINANCE_COMPLETE_DETAILS
QRY_STUDENT_FINANCE_COMPLETE_DETAILS = f"""SELECT Item_DESCR,  ITEM_TERM,   FORMAT('$%.2f', SAFE_CAST(ITEM_AMT AS FLOAT64)) AS ITEM_AMT,   FORMAT_DATE('%m/%d/%Y', DATE(ITEM_EFFECTIVE_DT)) AS ITEM_EFFECTIVE_DT FROM `{FINANCE_TABLE}` WHERE emplid = @student_id;"""

#FINAID
#QRY_STUDENT_FINAID_DETAILS = f"""SELECT   emplid,   FORMAT('$%.2f', SAFE_CAST(highest_offer_AMT AS FLOAT64)) AS highest_offer_AMT,  FORMAT('$%.2f', SAFE_CAST(NET_AWARD_AMT AS FLOAT64)) AS NET_AWARD_AMT,  AWARD_POSTED,  AWARD_STATUS   FROM `sjsu-it-genai-poc.student_financials.FINAID_STDNT_AWARDS`  where emplid= @student_id;"""
QRY_STUDENT_FINAID_DETAILS = f""""SELECT  emplid,  FORMAT('$%.2f', SAFE_CAST(highest_offer_AMT AS FLOAT64)) AS highest_offer_AMT,   FORMAT('$%.2f', SAFE_CAST(NET_AWARD_AMT AS FLOAT64)) AS NET_AWARD_AMT,   AWARD_POSTED,   AWARD_STATUS, Category   FROM  `sjsu-it-genai-poc.student_financials.FINAID_STDNT_AWARDS`  where emplid= @student_id;"""


#COMMENTS
COMMENTS_TABLE_ID = config["gcp"]["comments_table_id"]
COMMENTS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{COMMENTS_TABLE_ID}"
COMMENTS_TABLE_COLUMNS = config["gcp"]["comments_table_columns"]
QRY_STUDENT_COMMENTS_DETAILS = f"""SELECT {COMMENTS_TABLE_COLUMNS} FROM `{COMMENTS_TABLE}` WHERE emplid = @student_id;"""

GRAVYTY_TABLE_ID = config["gcp"]["gravyty_table_id"]
GRAVYTY_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{GRAVYTY_TABLE_ID}"
QRY_GRAVYTY_USERS = f"""SELECT EMPLID, ROLE FROM  `{GRAVYTY_TABLE}`;"""

# API Security Configuration
API_KEY = config["api"]["api_key"]
ALLOWED_IPS = config.get("api", {}).get("allowed_ips", [])

#ADMIN_USERS = config["roles"]["admin_users"]
#STAFF_USERS = config["roles"]["staff_users"]

# --- Flask App Initialization ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# --- Enable CORS ---
CORS(app, resources={r"/*": {"origins": ["http://localhost", "https://app.ivy.ai/"]}})

# --- Security Decorator ---
def api_key_required(f):
    """
    A decorator to validate the API key from the Authorization header.
    Expects: Authorization: Bearer <api_key>
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not app.debug and not request.is_secure:
            return jsonify({"detail": "HTTPS is required"}), 403

        if ALLOWED_IPS:
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip not in ALLOWED_IPS:
                return jsonify({"detail": "Access denied from this IP address."}), 403

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"detail": "Authorization header is missing."}), 401

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"detail": "Invalid Authorization header format. Expected: 'Bearer <api_key>'"}), 401

        provided_key = parts[1]

        valid = False
        for apikey in API_KEY:
            if hmac.compare_digest(provided_key, apikey):
                valid = True
                break

        if not valid:
            return jsonify({"detail": "Invalid API key."}), 401

        return f(*args, **kwargs)

    return decorated_function

# Initialize the BigQuery client
try:
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON_PATH)
    client = bigquery.Client(credentials=credentials)
except GoogleAPIError as e:
    print(f"Failed to initialize BigQuery client: {e}")
    client = None

# --- API Endpoints ---
API_VERSION = "v1"

@app.route(f"/api/{API_VERSION}/studentinfo/<student_id>", methods=["GET"])
@api_key_required
def get_student_info(student_id: str) -> Dict[str, Any]:

    if not client:
        return jsonify({"detail": "BigQuery client is not configured correctly."}), 500

    authenticated_user_id = request.headers.get("X-Authenticated-User")

    if not authenticated_user_id:
        return jsonify({
            "detail": "X-Authenticated-User header is required. This should contain the user_id from Okta authentication."
        }), 400

    if '@' in authenticated_user_id:
        authenticated_user_id = authenticated_user_id.split('@')[0]

    if authenticated_user_id != student_id:
        print(f"Authenticated user (from 3rd party/Okta): {authenticated_user_id}")
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id}'")
    else:
        print(f"User '{authenticated_user_id}' is querying for self")

    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
            ]
        )
        # print(QRY_STUDENT_DETAILS_AND_ROLE)
        query_job = client.query(QRY_STUDENT_DETAILS_AND_ROLE, job_config=job_config)
        rows = list(query_job.result())

        if not rows:
            return jsonify({"detail": f"Student with ID '{student_id}' not found."}), 404

        student_data = rows[0]
        result_dict = dict(student_data.items())

        return jsonify(result_dict)

    except GoogleAPIError as e:
        print(f"BigQuery API error: {e}")
        return jsonify({"detail": "An error occurred while querying BigQuery."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"detail": "An unexpected error occurred."}), 500


@app.route(f"/api/{API_VERSION}/studentfinance/<student_id>", methods=["GET"])
@api_key_required
def get_student_finance(student_id: str) -> Dict[str, Any]:

    if not client:
        return jsonify({"detail": "BigQuery client is not configured correctly."}), 500

    authenticated_user_id = request.headers.get("X-Authenticated-User")

    if not authenticated_user_id:
        return jsonify({
            "detail": "X-Authenticated-User header is required. This should contain the user_id from Okta authentication."
        }), 400

    if '@' in authenticated_user_id:
        authenticated_user_id = authenticated_user_id.split('@')[0]

    if authenticated_user_id != student_id:
        print(f"Authenticated user (from 3rd party/Okta): {authenticated_user_id}")
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id}'")
    else:
        print(f"User '{authenticated_user_id}' is querying for self")

    
    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
            ]
        )
        query_job = client.query(QRY_STUDENT_FINANCE_DETAILS, job_config=job_config)
        rows = [dict(row.items()) for row in query_job.result()]

        if not rows:
            return jsonify({"detail": f"Student with ID '{student_id}' not found."}), 404

        return jsonify(rows)

    except GoogleAPIError as e:
        print(f"BigQuery API error: {e}")
        return jsonify({"detail": "An error occurred while querying BigQuery."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"detail": "An unexpected error occurred."}), 500

@app.route(f"/api/{API_VERSION}/studentfinancecompleteDetails/<student_id>", methods=["GET"])
@api_key_required
def get_student_financecompleteDetails(student_id: str) -> Dict[str, Any]:

    if not client:
        return jsonify({"detail": "BigQuery client is not configured correctly."}), 500

    authenticated_user_id = request.headers.get("X-Authenticated-User")

    if not authenticated_user_id:
        return jsonify({
            "detail": "X-Authenticated-User header is required. This should contain the user_id from Okta authentication."
        }), 400

    if '@' in authenticated_user_id:
        authenticated_user_id = authenticated_user_id.split('@')[0]

    if authenticated_user_id != student_id:
        print(f"Authenticated user (from 3rd party/Okta): {authenticated_user_id}")
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id}'")
    else:
        print(f"User '{authenticated_user_id}' is querying for self")

    
    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
            ]
        )
        query_job = client.query(QRY_STUDENT_FINANCE_COMPLETE_DETAILS, job_config=job_config)
        rows = [dict(row.items()) for row in query_job.result()]

        if not rows:
            return jsonify({"detail": f"Student with ID '{student_id}' not found."}), 404

        return jsonify(rows)

    except GoogleAPIError as e:
        print(f"BigQuery API error: {e}")
        return jsonify({"detail": "An error occurred while querying BigQuery."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"detail": "An unexpected error occurred."}), 500

@app.route(f"/api/{API_VERSION}/studentfinaid/<student_id>", methods=["GET"])
@api_key_required
def get_student_finaid(student_id: str) -> Dict[str, Any]:

    if not client:
        return jsonify({"detail": "BigQuery client is not configured correctly."}), 500

    authenticated_user_id = request.headers.get("X-Authenticated-User")

    if not authenticated_user_id:
        return jsonify({
            "detail": "X-Authenticated-User header is required. This should contain the user_id from Okta authentication."
        }), 400

    if '@' in authenticated_user_id:
        authenticated_user_id = authenticated_user_id.split('@')[0]

    if authenticated_user_id != student_id:
        print(f"Authenticated user (from 3rd party/Okta): {authenticated_user_id}")
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id}'")
    else:
        print(f"User '{authenticated_user_id}' is querying for self")

    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
            ]
        )
        query_job = client.query(QRY_STUDENT_FINAID_DETAILS, job_config=job_config)
        rows = [dict(row.items()) for row in query_job.result()]

        if not rows:
            return jsonify({"detail": f"Student with ID '{student_id}' not found."}), 404

        return jsonify(rows)

    except GoogleAPIError as e:
        print(f"BigQuery API error: {e}")
        return jsonify({"detail": "An error occurred while querying BigQuery."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"detail": "An unexpected error occurred."}), 500


@app.route(f"/api/{API_VERSION}/studentacad/<student_id>", methods=["GET"])
@api_key_required
def get_student_acad(student_id: str) -> Dict[str, Any]:

    if not client:
        return jsonify({"detail": "BigQuery client is not configured correctly."}), 500

    authenticated_user_id = request.headers.get("X-Authenticated-User")

    if not authenticated_user_id:
        return jsonify({
            "detail": "X-Authenticated-User header is required. This should contain the user_id from Okta authentication."
        }), 400

    if '@' in authenticated_user_id:
        authenticated_user_id = authenticated_user_id.split('@')[0]

    if authenticated_user_id != student_id:
        print(f"Authenticated user (from 3rd party/Okta): {authenticated_user_id}")
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id}'")
    else:
        print(f"User '{authenticated_user_id}' is querying for self")

    '''
    if authenticated_user_id in ADMIN_USERS:
        authenticated_user_role = "admin"
    elif authenticated_user_id in STAFF_USERS:
        authenticated_user_role = "staff"
    else:
        authenticated_user_role = "student"

    if authenticated_user_role == "admin":
        student_id_for_query = student_id
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id_for_query}'")
    elif authenticated_user_role == "staff":
        if student_id not in STAFF_USERS:
            return jsonify({
                "detail": "You are not authorized to view this student's information."
            }), 403
        student_id_for_query = student_id
        print(f"Staff user '{authenticated_user_id}' is querying for student '{student_id_for_query}'")
    else:
        if authenticated_user_id != student_id:
            return jsonify({
                "detail": "You are not authorized to view this student's information. You can only view your own."
            }), 403
        student_id_for_query = authenticated_user_id
        print(f"Student user '{authenticated_user_id}' is querying for their own record.")
    '''
    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
            ]
        )
        query_job = client.query(QRY_STUDENT_ACAD_DETAILS, job_config=job_config)
        rows = [dict(row.items()) for row in query_job.result()]

        if not rows:
            return jsonify({"detail": f"Student with ID '{student_id}' not found."}), 404

        return jsonify(rows)

    except GoogleAPIError as e:
        print(f"BigQuery API error: {e}")
        return jsonify({"detail": "An error occurred while querying BigQuery."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"detail": "An unexpected error occurred."}), 500


@app.route(f"/api/{API_VERSION}/studentcomments/<student_id>", methods=["GET"])
@api_key_required
def get_student_comments(student_id: str) -> Dict[str, Any]:

    if not client:
        return jsonify({"detail": "BigQuery client is not configured correctly."}), 500

    authenticated_user_id = request.headers.get("X-Authenticated-User")

    if not authenticated_user_id:
        return jsonify({
            "detail": "X-Authenticated-User header is required. This should contain the user_id from Okta authentication."
        }), 400

    if '@' in authenticated_user_id:
        authenticated_user_id = authenticated_user_id.split('@')[0]

    if authenticated_user_id != student_id:
        print(f"Authenticated user (from 3rd party/Okta): {authenticated_user_id}")
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id}'")
    else:
        print(f"User '{authenticated_user_id}' is querying for self")
    
    '''
    if authenticated_user_id in ADMIN_USERS:
        authenticated_user_role = "admin"
    elif authenticated_user_id in STAFF_USERS:
        authenticated_user_role = "staff"
    else:
        authenticated_user_role = "student"


    if authenticated_user_role == "admin":
        student_id_for_query = student_id
        print(f"Admin user '{authenticated_user_id}' is querying for student '{student_id_for_query}'")
    elif authenticated_user_role == "staff":
        if student_id not in STAFF_USERS:
            return jsonify({
                "detail": "You are not authorized to view this student's information."
            }), 403
        student_id_for_query = student_id
        print(f"Staff user '{authenticated_user_id}' is querying for student '{student_id_for_query}'")
    else:
        if authenticated_user_id != student_id:
            return jsonify({
                "detail": "You are not authorized to view this student's information. You can only view your own."
            }), 403
        student_id_for_query = authenticated_user_id
        print(f"Student user '{authenticated_user_id}' is querying for their own record.")
    '''
    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("student_id", "STRING", student_id),
            ]
        )
        query_job = client.query(QRY_STUDENT_COMMENTS_DETAILS, job_config=job_config)
        rows = [dict(row.items()) for row in query_job.result()]
    
        if not rows:
            return jsonify({"detail": f"Student with ID '{student_id}' not found."}), 404

        return jsonify(rows)

    except GoogleAPIError as e:
        print(f"BigQuery API error: {e}")
        return jsonify({"detail": "An error occurred while querying BigQuery."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"detail": "An unexpected error occurred."}), 500


@app.route(f"/api/{API_VERSION}/health", methods=["GET"])
def health_check():
    """Health check endpoint - no authentication required."""
    return jsonify({"status": "healthy", "service": "Student Info API", "version": API_VERSION}), 200


@app.route("/", methods=["GET"])
def index():
    """API information endpoint."""
    return jsonify({
        "service": "Student Info API",
        "version": API_VERSION,
        "authentication": "API Key required in Authorization header",
        "base_url": f"/api/{API_VERSION}",
        "endpoints": {
            f"/api/{API_VERSION}/studentinfo/{{id}}": "GET - Retrieve student information (requires API key and authenticated user header)",
            f"/api/{API_VERSION}/studentfinance/{{id}}": "GET - Retrieve student finance balance information (requires API key and authenticated user header)",
            f"/api/{API_VERSION}/studentfinancecompleteDetails/{{id}}": "GET - Retrieve student finance balance detailed information (requires API key and authenticated user header)",
            f"/api/{API_VERSION}/studentfinaid/{{id}}": "GET - Retrieve student financial aid information (requires API key and authenticated user header)",
            f"/api/{API_VERSION}/studentacadinfo/{{id}}": "GET - Retrieve student academic information (requires API key and authenticated user header)",
            f"/api/{API_VERSION}/studentcomments/{{id}}": "GET - Retrieve student comments (requires API key and authenticated user header)",
            f"/api/{API_VERSION}/health": "GET - Health check"
        },
        "usage": {
            "headers": {
                "Authorization": "Bearer <api_key>",
                "X-Authenticated-User": "Authenticated user in the request header"
            },
            "Info ": f"GET /api/{API_VERSION}/studentinfo/12345",
            "Finance Balance ": f"GET /api/{API_VERSION}/studentfinance/12345",
            "Finance Balance Details ": f"GET /api/{API_VERSION}/studentfinancecompleteDetails/12345",
            "Finance Aid ": f"GET /api/{API_VERSION}/studentfinaid/12345",
            "Acad ": f"GET /api/{API_VERSION}/studentacadinfo/12345",
            "Comments ": f"GET /api/{API_VERSION}/studentcomments/12345",
            "Health  ": f"GET /api/{API_VERSION}/health",
        }
    }), 200


# --- Run the application ---
if __name__ == "__main__":
    app.run(host="10.1.5.54", port=5012, debug=True)
