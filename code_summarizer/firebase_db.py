import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
from typing import List, Dict

log = logging.getLogger(__name__)

FIRESTORE_INITIALIZED = False
db = None

firebase_secret_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')

if firebase_secret_json:
    try:
        import json
        # Convert the JSON string from the env var into a dictionary
        credentials_dict = json.loads(firebase_secret_json)
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_dict)
            firebase_admin.initialize_app(cred)
            log.info("Firebase Admin SDK initialized from Secret.")
        else:
            log.info("Firebase Admin SDK already initialized.")
        db = firestore.client()
        FIRESTORE_INITIALIZED = True
    except Exception as e:
        log.error(f"Failed to initialize Firebase from Secret: {e}", exc_info=True)
else:
    log.warning("Firebase Secret (FIREBASE_SERVICE_ACCOUNT_JSON) not found in environment. Firebase disabled.")

def is_firestore_available() -> bool:
    return FIRESTORE_INITIALIZED and db is not None

def upload_summary_to_firebase(summary: Dict):
    if not is_firestore_available():
        log.debug("Firestore unavailable, skipping upload.")
        return

    required_keys = ['repo_url', 'file_path', 'language', 'function_code', 'summary']
    if not all(key in summary for key in required_keys):
        log.warning(f"Skipped upload: Missing required keys. Has: {list(summary.keys())}")
        return

    try:
        if "embedding" in summary and not isinstance(summary["embedding"], list):
            log.warning(f"Removing invalid non-list embedding before upload for {summary.get('file_path')}")
            del summary["embedding"]

        doc_ref = db.collection("functions").document()
        doc_ref.set(summary)
        log.debug(f"Uploaded summary for: {summary.get('file_path')}")
    except Exception as e:
        log.error(f"Error uploading summary for {summary.get('file_path')} to Firebase: {e}", exc_info=True)

def get_summaries_by_repo(repo_url: str) -> List[Dict]:
    if not is_firestore_available():
        log.warning("Firestore unavailable, cannot fetch summaries.")
        return []
    summaries = []
    try:
        log.info(f"Querying Firestore for repo_url: {repo_url}")
        docs_stream = db.collection("functions").where("repo_url", "==", repo_url).stream()
        summaries = [doc.to_dict() for doc in docs_stream]
        log.info(f"Found {len(summaries)} existing summaries in Firestore for {repo_url}.")
    except Exception as e:
        log.error(f"Error fetching summaries for {repo_url} from Firebase: {e}", exc_info=True)
        return []
    return summaries