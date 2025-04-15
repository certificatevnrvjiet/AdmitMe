import firebase_admin
from firebase_admin import credentials, firestore


# Initialize Firebase
cred = credentials.Certificate("./serviceAccountKey.json")  # 🔥 Provide correct path
firebase_admin.initialize_app(cred)

# Get Firestore database instance
db = firestore.client()


