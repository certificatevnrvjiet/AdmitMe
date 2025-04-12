import re
from GoogleAuthService import download_image_from_drive,process_image_with_gemini
import json

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


Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.'''

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
Mother Tongue: Mother tongue of the student(Give Only one)
Nationality: Nationality of the student
Religion: Religion of the student
College Name: Name of the college
Caste as per TC: Caste as per the Transfer Certificate (TC)


Please return the result in Dictionary format with exact field names as mentioned above (if any field not found return null)
just Dictionary no other stuff.'''

prompt_Inter_CBSE="""''Extract the following structured data from the image:
Board Name: Name of the educational board (e.g., CBSE, ICSE, State Board)
Hall Ticket Number: Hall ticket or roll number
Max Marks: 500
Percentage: Percentage scored(please Calculate as (total marks obtained/total maximum marks)*100)
Month_year: Month and year of passing (e.g., March 2020)
Subject Scores: Subject-wise scores (if available, please provide in a dictionary format with subject names as keys [keys are MATHS , PHYSICS , CHEMISTRY thats it no more needed] and scores as values)
Total Marks: Total marks obtained(Sum of all 5 subjects)

Please return the result in Dictionary format with exact field names as mentioned above (if any field not found return null)
just Dictionary no other stuff. """

prompt_SSC_Inter = '''Extract the following structured data from the image:
Board Name: Name of the educational board (e.g., CBSE, ICSE, State Board)
Hall Ticket Number: Hall ticket or registered number
Max Marks: 1000
Total Marks: Total marks obtained
Percentage: Percentage scored (please Calculate as (total marks obtained/total maximum marks)*100)
Subject Scores: Subject-wise scores (if available, please provide in a dictionary format with subject names as keys [the keys are (M1, M2, P1, C1 from 1st year) and (M3, M4, P2, C2, P_practicals, C_Practicals are from 2nd year) *Thats it no other marks needed needed] and scores as values)
Month_year: Month and year of passing (e.g., March 2020)

Please return the result in Dictionary format with exact field names as mentioned above  (if any field not found return null)
just Dictionary no other stuff.
'''
prompts=[prompt_SSC,prompt_uidai,prompt_jee_and_eamcet,prompt_TC,prompt_Inter_CBSE,prompt_SSC_Inter]

def extract(linkstr,prompt):
    file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', linkstr).group(1)
    image_bytes = download_image_from_drive(file_id_match)
    gemini_response = json.loads(process_image_with_gemini(image_bytes, prompt).split("```")[1][5:])
    # print(f"Gemini Response for {file_id_match}: {gemini_response}")
        # data_dict = json.loads(response.text.split("```")[1][5:])\
    # for i in gemini_response:
    #     print(f"{i}: {gemini_response[i]}")

    return gemini_response


#sample links

# extract("https://drive.google.com/open?id=1l52UOx3MHSZwO2VKhV1VtrDkLJ60ZIl1",prompt_SSC)

# extract("https://drive.google.com/open?id=1Fvt0dEOSyacvrsMcpyDBkw5vv5QeWRQi",prompt_uidai)

# extract("https://drive.google.com/open?id=1Fvt0dEOSyacvrsMcpyDBkw5vv5QeWRQi",prompt_jee_and_eamcet)

# extract("https://drive.google.com/open?id=1nQPgkyfYhiM8Xix9NfbY7d8TXzNTfDO1",prompt_TC)

# extract("https://drive.google.com/open?id=1A1HRUMNNYU0jj7NiY-hW38dOtt9pqYf3",prompt_Inter_CBSE)

# extract("https://drive.google.com/open?id=1Ow_5CWffrdOwvSQcmY5-n3GQYrDqbKmZ",prompt_SSC_Inter)
