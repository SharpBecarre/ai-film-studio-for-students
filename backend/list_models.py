import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

models = client.models.list()

for model in sorted(models.data, key=lambda x: x.id):
    print(model.id)