#!/bin/bash

# Script de démarrage du backend Python

echo "🚀 Démarrage du backend Quantis..."

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔌 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -r requirements.txt

# Vérifier que le token Gemini est configuré
if [ -z "$GEMINI_TOKEN" ]; then
    echo "⚠️  Attention: GEMINI_TOKEN n'est pas défini dans les variables d'environnement"
    echo "   Assurez-vous d'avoir un fichier .env avec GEMINI_TOKEN=votre_token"
fi

# Démarrer le serveur
echo "🌟 Démarrage du serveur FastAPI sur http://localhost:8000"
cd api
python main.py




