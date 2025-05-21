import google.generativeai as genai
import re
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
if not GOOGLE_GEMINI_API_KEY:
    raise ValueError("API key not found. Please set the GOOGLE_GEMINI_API_KEY environment variable.")

genai.configure(api_key=GOOGLE_GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def interpret_question(question):
    prompt = f"""You are an assistant that translates natural language questions into Python dictionaries for querying an Oracle table FULLSTOCK
with these columns: PN, DESCRIPTION, QTY_OH, QTY_RESERVED, WAREHOUSE_CODE, LOCATION_CODE, CONDITION_CODE, STOCK_LINE, CTRL_NUMBER, CTRL_ID.

Convert the following question into one of these Python-style dictionaries:

If the question is a greeting like "hi", "hello", "hey", "thank you",then respond with:
{{
  "action": "greeting",
  "raw_input": "hi"
}}

If the question is not related to inventory (e.g. asking about deleting data, general help, or anything unrelated), respond with:
{{
  "action": "off_topic",
  "raw_input": "can you remove this?"
}}

# Get quantity fields for a specific part number:
{{
  "action": "query",
  "fields": ["QTY_OH"],
  "pn": "P210P01"
}}

# Filter by numeric conditions (e.g. QTY_OH > 400):
{{
  "action": "filter",
  "field": "QTY_OH",
  "condition": ">",
  "value": 400
}}

# Get top N parts by quantity:
{{
  "action": "top",
  "field": "QTY_OH",
  "limit": 5
}}

# Query all parts matching a description (even partially):
{{
  "action": "search_description",
  "keyword": "HPC STATOR VARIABLE VANE"
}}

# Query all parts available in a specific location:
{{
  "action": "search_by_location",
  "location": "A01-02"
}}

Question: {question}
Reply only with the dictionary."""




    response = model.generate_content(prompt)
    text = response.text

    match = re.search(r'\{[\s\S]*?\}', text)
    if match:
        return match.group(0)
    else:
        raise ValueError("Could not extract valid dictionary from Gemini response.")
