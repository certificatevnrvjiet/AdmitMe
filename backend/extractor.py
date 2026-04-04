import re
from GoogleService import process_image_with_gemini
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import logging
import time
from io import BytesIO
from PIL import Image
import fitz
from services.document_service import parse_document_ref
from storage.gdrive import GoogleDriveStorageProvider


prompt_SSC = '''Extract the following structured data from the image:
Candidate Name: Name of the candidate
Father Name: Name of the father
Mother Name: Name of the mother
Date of Birth: Date of birth in the format DD/MM/YYYY
tenth_board_name: Name of the educational board (e.g., CBSE, ICSE, State Board)
tenth_school_name: Name of the school
tenth_hall_ticket_no: Hall ticket or roll number
tenth_max_marks/CGPA: Total maximum marks possible (if telanagana state "10")
tenth_total_marks/CGPA: Total marks obtained
tenth_percentage: Percentage scored(please Calculate as (total marks obtained/total maximum marks)*100)
tenth_month_year: Month and year of passing (e.g., March 2020)
identification_marks1: Identification marks (if any)
identification_marks2: Identification marks (if any)
district_code: 


Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.'''

prompt_IGCSE_Inter = '''Extract the following structured data from the image:
Board Name: AS Level or IGCSE
Hall Ticket Number: Centre/Candidate number
Max Marks: 400
Subject Scores: Subject-wise scores (if available, please provide in a dictionary format with subject names as keys [the keys are maths as M4, physics as P2, chemistry as C2, do not read anything else] and scores as values)
Total Marks: sum of all subject scores
Percentage: Percentage scored (please Calculate as (total marks obtained/total maximum marks)*100)
Month_Passing: Month and year of passing (e.g., March 2020)
district_code: 


Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.
'''

prompt_ISC_Inter = '''Extract the following structured data from the image:
Board Name: ISC 
Hall Ticket Number: Candidate ID
Max Marks: 500
Subject Scores: Subject-wise scores (if available, please provide in a dictionary format with subject names as keys [the keys are maths as M4, physics as P2, chemistry as C2, do not read anything else] and scores as values)
Total Marks: sum of all subject scores
Percentage: Percentage scored (please Calculate as (total marks obtained/total maximum marks)*100)
Month_Passing: Month and year of passing (e.g., March 2020)
district_code: 

Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.
'''

prompt_CBSE_Inter=''' Extract the following structured data from the image:
Board Name: CBSE
Hall Ticket Number: Hall ticket or roll number
Max Marks: 500
Percentage: Percentage scored(please Calculate as (total marks obtained/total maximum marks)*100)
Month_year: Month and year of passing (e.g., March 2020)
Subject Scores: Subject-wise scores (if available, please provide in a dictionary format with subject names as keys [keys are 'M4' , 'P2' , 'C2' thats it no more needed only 3] and scores as values)
'Total Marks': Total marks obtained(Sum of all 5 subjects)
district_code: 

Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff. '''

prompt_uidai = '''Extract the following structured data from the image:
Number: Number of the Aadhar card
Gender: Male/Female /Others


Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.
'''

prompt_jee_and_eamcet = '''Extract the following structured data from the image:
HT Number: Hall ticket number 
Rank : Rank obtained

Please return the result in Dictionary format with exact field names as mentioned above (if any field not found return null)
just Dictionary no other stuff.'''

prompt_TC = '''Extract the following structured data from the image:
Nationality: Nationality of the student
Religion: Religion of the student
College Name: Name of the college

Please return the result in Dictionary format with exact field names as mentioned above (if any field not found return null)
just Dictionary no other stuff.'''

prompt_SSC_Inter = '''Extract the following structured data from the image:
Board Name: Name of the educational board (e.g., CBSE, ICSE, State Board)
Hall Ticket Number: Hall ticket or registered number
Max Marks: 1000
Total Marks: Total marks obtained
Percentage: Percentage scored (please Calculate as (total marks obtained/total maximum marks)*100)
Subject Scores: Subject-wise scores (if available, please provide in a dictionary format with subject names as keys [the keys are ('M1', 'M2', 'P1', 'C1' from 1st year) and ('M3', 'M4', 'P2', 'C2', 'P_Practicals', 'C_Practicals' are from 2nd year) *Thats it no other marks needed needed] and scores as values)
Month_year: Month and year of passing (e.g., March 2020)
district_code: 

Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.
'''

prompt_Diploma= '''Extract the following structured data from the image:
Board Name: Name of the educational board (e.g., CBSE, ICSE, State Board)
Hall Ticket Number: Hall ticket or registered number
Max Marks: 10
Total Marks: CGPA Scored
Percentage: Percentage scored (please Calculate as (total marks obtained/total maximum marks)*100 )
Subject Scores: Subject-wise scores (if available, please provide in a dictionary format with subject names as keys [the keys are ('M1', 'M2', 'P1', 'C1' from 1st year) and ('M3', 'M4', 'P2', 'C2', 'P_Practicals', 'C_Practicals' are from 2nd year) *Thats it no other marks needed needed] and scores as values)
Month_year: Month and year of passing (e.g., March 2020)

Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.
'''

prompts=[prompt_SSC,prompt_uidai,prompt_jee_and_eamcet,prompt_TC, prompt_SSC_Inter, prompt_IGCSE_Inter, prompt_ISC_Inter, prompt_CBSE_Inter,prompt_Diploma]

def _parse_gemini_json(response_text: str) -> dict:
    text = (response_text or "").strip()
    if not text:
        return {}

    # 1) Direct JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # 2) Fenced JSON block
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fence_match:
        try:
            parsed = json.loads(fence_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 3) Largest object-looking block
    object_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if object_match:
        try:
            parsed = json.loads(object_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    raise ValueError("Unable to parse JSON object from Gemini response")





@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
async def extract(linkstr: str, prompt: str, drive_service) -> dict:
    """Process single image with retry logic"""
    providers = {
        "gdrive": GoogleDriveStorageProvider(drive_service)
    }
    return await extract_from_document_ref(linkstr, prompt, providers)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
async def extract_from_document_ref(document_ref: str, prompt: str, storage_providers: dict) -> dict:
    """Process a document using provider:key ref or legacy URL."""
    try:
        parsed_ref = parse_document_ref(document_ref)
        if not parsed_ref:
            raise ValueError(f"Invalid document ref: {document_ref}")

        provider = storage_providers.get(parsed_ref.provider)
        if not provider:
            raise ValueError(f"No storage provider configured for: {parsed_ref.provider}")

        image_bytes = await asyncio.to_thread(provider.get_bytes, parsed_ref.key)
        if not image_bytes:
            raise ValueError("Empty image data from storage")
        
        # Convert PDF bytes to image bytes when required
        if image_bytes[:4] == b"%PDF":
            pdf_doc = fitz.open(stream=image_bytes, filetype="pdf")
            if len(pdf_doc) == 0:
                raise ValueError("PDF has no pages")
            page = pdf_doc[-1]
            pix = page.get_pixmap()
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            image_out = BytesIO()
            image.save(image_out, format="PNG")
            image_bytes = image_out.getvalue()

        # Process with Gemini
        response_text = await asyncio.to_thread(
            process_image_with_gemini, 
            image_bytes, 
            prompt
        )
        
        # Parse response
        return _parse_gemini_json(response_text)
    
    except Exception as e:
        logging.error(f"Extract failed: {document_ref} - {str(e)}")
        return {"error": str(e), "link": document_ref}

#sample links

# responses = sheet.get_all_records()

# for response in responses:
#     board = response['12th Board']
#     if board == 'State':
#         extract(response['12th Marksheet'],prompt_SSC_Inter)
#     elif board == 'AS and A Level':
#         extract(response['12th Marksheet'],prompt_IGCSE_Inter)
#     elif board == 'ISC':
#         extract(response['12th Marksheet'],prompt_ISC_Inter)
#     elif board == 'CBSE':
#         extract(response['12th Marksheet'],prompt_CBSE_Inter)

# extract("https://drive.google.com/open?id=1l52UOx3MHSZwO2VKhV1VtrDkLJ60ZIl1",prompt_SSC)

# extract("https://drive.google.com/open?id=1Fvt0dEOSyacvrsMcpyDBkw5vv5QeWRQi",prompt_uidai)

# extract("https://drive.google.com/open?id=1Fvt0dEOSyacvrsMcpyDBkw5vv5QeWRQi",prompt_jee_and_eamcet)

# extract("https://drive.google.com/open?id=1nQPgkyfYhiM8Xix9NfbY7d8TXzNTfDO1",prompt_TC)

# extract("https://drive.google.com/open?id=1A1HRUMNNYU0jj7NiY-hW38dOtt9pqYf3",prompt_Inter_CBSE)

# extract("https://drive.google.com/open?id=1Ow_5CWffrdOwvSQcmY5-n3GQYrDqbKmZ",prompt_SSC_Inter)
