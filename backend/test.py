# # backend.py
# from fastapi import FastAPI, Request
# from extractor import extract, prompt_SSC_Inter, prompt_IGCSE_Inter, prompt_ISC_Inter, prompt_CBSE_Inter

# app = FastAPI()

# @app.post("/process-form")
# async def process_form(data: Request):
#     body = await data.json()
#     board = body["12th Board"]
#     link = body["12th Marksheet"]

#     if board == "State":
#         result = extract(link, prompt_SSC_Inter)
#     elif board == "AS and A Level":
#         result = extract(link, prompt_IGCSE_Inter)
#     elif board == "ISC":
#         result = extract(link, prompt_ISC_Inter)
#     elif board == "CBSE":
#         result = extract(link, prompt_CBSE_Inter)
#     else:
#         return {"error": "Unknown board"}

#     return {"result": result}
from datetime import datetime


date_of_birth=datetime.strptime('16/08/2005', "%d-%m-%Y").date(),
print(date_of_birth)