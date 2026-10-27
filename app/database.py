import os
import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

BASE_DIR = Path(__file__).resolve().parent.parent

db = None

if not firebase_admin._apps:
    cred_env = os.environ.get("FIREBASE_CREDENTIALS")
    
    if cred_env:
        # Running on Vercel: load from environment variable
        try:
            cred_dict = json.loads(cred_env)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        except Exception as e:
            print(f"Failed to initialize Firebase from environment variable: {e}")
    else:
        # Running locally: load from serviceAccountKey.json
        key_path = BASE_DIR / "serviceAccountKey.json"
        if key_path.exists():
            try:
                cred = credentials.Certificate(str(key_path))
                firebase_admin.initialize_app(cred)
                db = firestore.client()
            except Exception as e:
                print(f"Failed to initialize Firebase from file: {e}")
        else:
            print(f"Warning: Neither FIREBASE_CREDENTIALS env var nor {key_path} found.")
else:
    db = firestore.client()