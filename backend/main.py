import os
from dotenv import load_dotenv
from openai import OpenAI 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY was not found.")

client = OpenAI(api_key=api_key)

app = FastAPI(title="AI Film Studio API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "AI Film Studio API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/video-plan")
def create_video_plan(data: dict):
    topic = data.get("topic", "")

    return {
        "topic": topic,
        "title": f"Educational Video: {topic}",
        "steps": [
            "Generate a short script",
            "Create storyboard scenes",
            "Add voice-over narration",
            "Create captions",
            "Export final video",
        ],
    }

@app.post("/generate-script")
def generate_script(data: dict):
    topic = data.get("topic", "").strip()

    if not topic:
        return {"error": "Please provide a topic."}

    prompt = f"""
Create a short educational video script about: {topic}

The audience is high school students.
The video should be approximately 60 to 90 seconds long.

Structure the script with:

1. Title
2. Introduction
3. Scene 1
4. Scene 2
5. Scene 3
6. Conclusion

For each scene, include:
- Narration: what the narrator says
- Visual: what should appear on screen

Keep the language clear, engaging, and educational.
Do not make the script unnecessarily long.
"""

    response = client.responses.create(
        model="gpt-6-luna",
        input=prompt
    )

    return {
        "topic": topic,
        "script": response.output_text
    }