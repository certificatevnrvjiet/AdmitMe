import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase and return Firestore client."""
    try:
        # Provide the correct path to your service account key
        cred = credentials.Certificate("./serviceAccountKey.json")
        
        # Check if already initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully.")
        
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise

# Test connection function
def test_firebase_connection(db):
    try:
        # Try to access the collection
        docs = db.collection('studentsdemo').limit(1).stream()
        # Try to get first document (just to test)
        next(docs, None)
        return True, "Connection successful"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

# Get Firestore database instance
db = initialize_firebase()

# Test the connection immediately
success, message = test_firebase_connection(db)
print(f"Firebase Connection Test: {message}")
