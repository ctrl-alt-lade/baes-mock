import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

# Locate serviceAccountKey.json in the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_KEY_PATH = BASE_DIR / "serviceAccountKey.json"
KEY_PATH_ENV = os.getenv("FIREBASE_CREDENTIALS_PATH")
KEY_PATH = Path(KEY_PATH_ENV) if KEY_PATH_ENV else DEFAULT_KEY_PATH


def init_firebase():
    """Initialize Firebase Admin SDK using the local service account key."""
    if not firebase_admin._apps:
        if not KEY_PATH.exists():
            print(
                f"[WARNING] Firebase service account key not found at '{KEY_PATH}'.\n"
                "Please place your 'serviceAccountKey.json' file in the project root\n"
                "or set the FIREBASE_CREDENTIALS_PATH environment variable."
            )
            return None
        cred = credentials.Certificate(str(KEY_PATH))
        firebase_admin.initialize_app(cred)
    return firestore.client()


# Export the Firestore client instance
try:
    db = init_firebase()
except Exception as e:
    print(f"[ERROR] Failed to initialize Firebase Firestore client: {e}")
    db = None
