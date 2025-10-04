from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    courses, materials, topics, quizzes, questions,
    attempts, answers, progress, rag_routes, notes,
    exercises, exams, mindmap
)
from app.routes import llm_routes
from app.core.database import Base, engine
from app.models import models
import logging
import os

app = FastAPI(title="AI Learning Backend")


os.makedirs('/app/logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/app.log')
    ]
)

logger = logging.getLogger(__name__)

origins = [
    "http://localhost:5173",  # if using Vite
    "http://localhost:3000",  # if using CRA
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Allow frontend requests (React dev server, later desktop app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # in prod, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(llm_routes.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(topics.router)
app.include_router(quizzes.router)
app.include_router(questions.router)
app.include_router(attempts.router)
app.include_router(answers.router)
app.include_router(progress.router)
app.include_router(rag_routes.router)
app.include_router(notes.router)
app.include_router(exercises.router)
app.include_router(mindmap.router)


Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Learning Backend running 🚀"}
