import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from fastapi.responses import FileResponse
from video_renderer import render_storyboard
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
Keep each narrated segment short enough for approximately five seconds of video.
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
Create exactly five narrated segments: introduction, three main scenes, and conclusion. Each segment must contain approximately 8 to 10 spoken words, aiming for no more than five seconds of narration at normal speaking speed. Prioritize this five-second limit over the requested total video length.
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

@app.post("/generate-storyboard")
def generate_storyboard(data: dict):
    script = data.get("script")

    if not isinstance(script, dict):
        return {"error": "Please provide a valid script."}

    scenes = []

    # Introduction
    introduction = script.get("introduction", {})

    scenes.append({
        "scene_number": 0,
        "title": "Introduction",
        "narration": introduction.get("narration", ""),
        "visual": introduction.get("visual", "")
    })

    # Main scenes
    for scene in script.get("scenes", []):
        scenes.append({
            "scene_number": scene.get("scene_number"),
            "title": scene.get("title", ""),
            "narration": scene.get("narration", ""),
            "visual": scene.get("visual", "")
        })

    # Conclusion
    conclusion = script.get("conclusion", {})

    scenes.append({
        "scene_number": 4,
        "title": "Conclusion",
        "narration": conclusion.get("narration", ""),
        "visual": conclusion.get("visual", "")
    })

    return {
        "title": script.get("title", "Untitled Video"),
        "scenes": scenes
    }

@app.post("/generate-narration")
def generate_narration(data: dict):
    import uuid
    from pathlib import Path

    narration_text = data.get("text", "").strip()

    if not narration_text:
        return {"error": "Narration text is required."}

    output_folder = Path(__file__).parent / "generated_audio"
    output_folder.mkdir(exist_ok=True)

    output_file = output_folder / f"{uuid.uuid4().hex}.mp3"

    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=narration_text,
        response_format="mp3",
    ) as response:
        response.stream_to_file(output_file)

    return FileResponse(
        path=output_file,
        media_type="audio/mpeg",
        filename="narration.mp3",
    )

@app.post("/generate-video")
def generate_video(data: dict):
    import uuid
    from pathlib import Path
    from fastapi import HTTPException

    scenes = data.get("scenes")

    if not isinstance(scenes, list) or not scenes:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one storyboard scene."
        )

    if not all(isinstance(scene, dict) for scene in scenes):
        raise HTTPException(
            status_code=400,
            detail="Every storyboard scene must be an object."
        )

    output_folder = Path(__file__).parent / "generated_videos"
    output_folder.mkdir(exist_ok=True)

    output_path = output_folder / f"{uuid.uuid4().hex}.mp4"

    try:
        render_storyboard(scenes, client, output_path)
    except Exception:
        output_path.unlink(missing_ok=True)
        raise

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename="ai_film_studio_video.mp4",
    )
