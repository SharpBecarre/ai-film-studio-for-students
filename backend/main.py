import os
import json
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
    audience = data.get("audience", "High School")
    video_length = data.get("video_length", "60")
    style = data.get("style", "Educational")

    if not topic:
        return {"error": "Please provide a topic."}

    prompt = f"""
Create a short educational video script about: {topic}

Target audience: {audience}
Target video length: approximately {video_length} seconds
Style: {style}

Adjust the vocabulary, explanations, and level of detail for the target audience.
Adjust the amount of narration so the complete video is appropriate for the requested video length.
Write the narration in the requested style.

Return ONLY valid JSON.
Do not use Markdown.
Do not use ``` code fences.
Do not include any text before or after the JSON.

Use exactly this structure:

{{
  "title": "Video title",
  "introduction": {{
    "narration": "Narration for the introduction",
    "visual": "Description of what should appear on screen"
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "title": "Scene title",
      "narration": "Narration for this scene",
      "visual": "Description of what should appear on screen"
    }},
    {{
      "scene_number": 2,
      "title": "Scene title",
      "narration": "Narration for this scene",
      "visual": "Description of what should appear on screen"
    }},
    {{
      "scene_number": 3,
      "title": "Scene title",
      "narration": "Narration for this scene",
      "visual": "Description of what should appear on screen"
    }}
  ],
  "conclusion": {{
    "narration": "Narration for the conclusion",
    "visual": "Description of what should appear on screen"
  }}
}}

Create exactly 3 scenes.

Keep the narration clear, engaging, and accurate.
Make the complete narration appropriate for approximately {video_length} seconds.
Make the vocabulary and explanation level appropriate for: {audience}.
Use this presentation style: {style}.
"""

    response = client.responses.create(
        model="gpt-6-luna",
        input=prompt
    )

    script_data = json.loads(response.output_text)

    return {
        "topic": topic,
        "audience": audience,
        "video_length": video_length,
        "style": style,
        "script": script_data
    }
