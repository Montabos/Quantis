@echo off
REM Script de démarrage du backend Python (Windows)

echo 🚀 Démarrage du backend Quantis...

REM Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo 📦 Création de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
echo 🔌 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances
echo 📥 Installation des dépendances...
pip install -r requirements.txt

REM Vérifier que le token Gemini est configuré
if "%GEMINI_TOKEN%"=="" (
    echo ⚠️  Attention: GEMINI_TOKEN n'est pas défini dans les variables d'environnement
    echo    Assurez-vous d'avoir un fichier .env avec GEMINI_TOKEN=votre_token
)

REM Démarrer le serveur
echo 🌟 Démarrage du serveur FastAPI sur http://localhost:8000
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000




