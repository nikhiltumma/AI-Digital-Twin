from fastapi import FastAPI

app = FastAPI(
    title="AI Digital Twin API",
    description="Backend API for the AI Digital Twin project",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "AI Digital Twin API is running"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-digital-twin-backend",
    }