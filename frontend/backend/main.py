from fastapi import FastAPI

app = FastAPI(title="AI Film Studio API")

@app.get("/")
def root():
    return {"message": "AI Film Studio API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}Get