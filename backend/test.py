from googleapiclient.discovery import build
from config.settings import FRONTEND_URL,SPREADSHEET_ID
from GoogleService import read_google_sheet
from GoogleService import authenticate_service_account
credentials = authenticate_service_account()
sheets_service = build('sheets', 'v4', credentials=credentials)
RANGE='cse!A12:B12'
print(read_google_sheet(sheets_service,SPREADSHEET_ID,RANGE))
