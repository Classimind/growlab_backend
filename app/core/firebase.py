import os
import json
import firebase_admin
from firebase_admin import credentials
from app.core.config import settings


def init_firebase():
    # Prevent double init
    if firebase_admin._apps:
        # logger.info(" Firebase already initialized")
        return

    try:
        if settings.firebase_cred_json:
            cred_dict = json.loads(settings.firebase_cred_json)
            cred = credentials.Certificate(cred_dict)
            # logger.info(" Firebase initialized from env variable")
        else:
            if not os.path.exists(settings.firebase_cred_path):
                raise FileNotFoundError(
                    f"Credential file not found: {settings.firebase_cred_path}"
                )

            cred = credentials.Certificate(settings.firebase_cred_path)
            # logger.info(" Firebase initialized from file")

        firebase_admin.initialize_app(cred)

    except Exception as e:
        # logger.error("Firebase initialization failed", exc_info=True)
        raise