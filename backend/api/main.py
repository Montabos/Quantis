"""
FastAPI backend for Quantis file processing and decision analysis
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env.local ou .env à la racine du projet
project_root = Path(__file__).parent.parent.parent
env_paths = [
    project_root / '.env.local',  # Priorité à .env.local (standard Next.js)
    project_root / '.env',
    Path(__file__).parent.parent / '.env',  # Essayer aussi dans le dossier backend
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=False)  # override=False pour garder les valeurs déjà chargées
        break

# Add code_interpreter to path
code_interpreter_path = Path(__file__).parent.parent.parent / "code_interpreter"
sys.path.insert(0, str(code_interpreter_path))

# Add backend directory to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import routes - try relative import first, then absolute
try:
    from .routes import files, decisions, dashboard
except ImportError:
    # Fallback for when running as module (python -m uvicorn api.main:app)
    from api.routes import files, decisions, dashboard

app = FastAPI(title="Quantis Backend API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/")
async def root():
    return {"message": "Quantis Backend API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




