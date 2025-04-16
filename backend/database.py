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
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise

# Get Firestore database instance
db = initialize_firebase()

# Initialize FastAPI app
# app = FastAPI()

# Pydantic model for data validation
# class Item(BaseModel):
#     name: str
#     description: Optional[str] = None  # Description is optional

# # Firestore client
# # db = firestore.client()
# collection_name = "items" 

# @app.post("/items")
# async def create_item(item: Item):
#     """
#     Creates a new item in the Firestore collection.
#     Uses the add() method to let Firestore generate a unique ID.
#     """
#     try:
#         items_ref = db.collection(collection_name)
#         _, doc_ref = items_ref.add(item.dict())
#         #  Use doc_ref.id to get the ID of the newly created document
#         new_item = {"id": doc_ref.id, **item.dict()}
#         return new_item
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error creating item: {e}")
