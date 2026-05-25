from fastapi import Request
from config.settings import GOOGLE_API_KEY, GOOGLE_CREDENTIALS, GEMINI_MODEL
from googleapiclient.discovery import build
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import fitz  # PyMuPDF
import mimetypes
from google.auth.transport.requests import Request
import os
import json


DRIVE_SEMAPHORE = asyncio.Semaphore(1)

def _load_creds_dict():
    raw = GOOGLE_CREDENTIALS
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]




def authenticate_service_account():
    """Authenticates with Google APIs using a service account."""
    try:
        creds_dict = _load_creds_dict()
        if not creds_dict:
            raise ValueError("GOOGLE_CREDENTIALS is missing or invalid JSON")

        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES

        )
        print("Authentication successful using service account.")
        return credentials
    except FileNotFoundError:
        print(f"Error: The service account file '{GOOGLE_CREDENTIALS}' was not found.")
        print("Please ensure it's in the same directory as the script or provide the full path.")
        return None
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        return None


def get_sheets_service():
    """Returns an authorized Sheets API service instance."""
    creds = authenticate_service_account()
    if not creds:
        raise Exception("Failed to authenticate with Google Sheets API")
    return build('sheets', 'v4', credentials=creds)

def get_drive_service():
    """Returns an authorized Drive API service instance."""
    creds = authenticate_service_account()
    if not creds:
        raise Exception("Failed to authenticate with Google Drive API")
    return build('drive', 'v3', credentials=creds)

def read_google_sheet(service, spreadsheet_id, range_name):
    """Reads data from a Google Sheet."""
    print(f"\n--- Reading Google Sheet: {spreadsheet_id} (Range: {range_name}) ---")
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print('No data found in the specified range.')
        else:
            return values
    except HttpError as error:
        print(f"An error occurred while reading the Google Sheet: {error}")
        print("Ensure the service account has appropriate Sheets roles and the spreadsheet is shared with its email.")
        if error.resp.status == 403:
            print("Check permissions. Make sure the service account email has access to the spreadsheet.")
        elif error.resp.status == 404:
            print("Spreadsheet not found. Verify the SPREADSHEET_ID is correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
def download_drive_image_as_bytes(file_id, drive_service):
    """Downloads an image or the first page of a PDF from Google Drive and returns it as PNG bytes."""
    try:
        # Get file metadata
        file_metadata = drive_service.files().get(fileId=file_id, fields="mimeType, name").execute()
        mime_type = file_metadata['mimeType']
        file_name = file_metadata['name']
        print(f"Downloading '{file_name}' with MIME type: {mime_type}")

        # Download file content
        request = drive_service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        
        # Handle PDF files
        if mime_type == "application/pdf":
            pdf_doc = fitz.open(stream=fh.read(), filetype="pdf")
            if len(pdf_doc) == 0:
                raise Exception(f"PDF file {file_name} has no pages")
            page = pdf_doc[-1]  # Get the last page
            pix = page.get_pixmap()
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        # Handle image files
        elif mime_type.startswith("image/"):
            image = Image.open(fh).convert("RGB")
        else:
            raise Exception(f"Unsupported MIME type: {mime_type}")

        # Convert image to PNG bytes
        image_byte_io = BytesIO()
        image.save(image_byte_io, format="PNG")
        return image_byte_io.getvalue()

    except Exception as e:
        print(f"Error downloading file from Drive: {e}")
        return None

async def download_image_from_drive(file_id: str, cred) -> bytes | None:
    """Async wrapper for Drive download with credentials refresh"""
    async with DRIVE_SEMAPHORE:
        
        creds = cred
        if creds and getattr(creds, "expired", False):
            creds.refresh(Request())
        
        # Run synchronous download in thread
        return await asyncio.to_thread(
            download_drive_image_as_bytes,
            file_id,
            creds
        )



def process_image_with_gemini(image_bytes, prompt):
    """
    Configure the Google Generative AI client and process the given image bytes with a text prompt.
    Returns the generated raw text from the model.
    """
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    try:
        image = Image.open(BytesIO(image_bytes))
        contents = [image, prompt]
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        return f"Error processing image with Gemini: {e}"
