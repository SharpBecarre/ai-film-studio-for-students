import os
from dotenv import load_dotenv 
import openai

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY was not found.")

client = openai.OpenAI(api_key=api_key)

response = client.responses.create(
    model="gpt-6-luna",
    input="Explain gravity to a 12-year-old in two sentences.")

print(response.output_text)
