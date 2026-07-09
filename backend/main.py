from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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