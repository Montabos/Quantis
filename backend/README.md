# Quantis Backend API

Backend Python FastAPI pour le traitement des fichiers et l'analyse de décisions financières.

## Installation

1. Créer un environnement virtuel Python :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement :
Créer un fichier `.env` à la racine du projet avec :
```
GEMINI_TOKEN=votre_cle_api_gemini
```

## Démarrage

```bash
cd backend/api
python main.py
```

Ou avec uvicorn directement :
```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera disponible sur `http://localhost:8000`

## Endpoints

### Files
- `POST /api/files/process` - Traiter un fichier uploadé (extraction métadonnées, conversion CSV)
- `DELETE /api/files/{file_id}` - Supprimer un fichier
- `GET /api/files/list` - Lister tous les fichiers

### Decisions
- `POST /api/decisions/analyze` - Analyser une décision financière

### Dashboard
- `GET /api/dashboard/data` - Obtenir les données pour le dashboard

## Structure

```
backend/
├── api/
│   ├── main.py              # Application FastAPI principale
│   └── routes/
│       ├── files.py         # Routes pour les fichiers
│       ├── decisions.py     # Routes pour les analyses de décision
│       └── dashboard.py     # Routes pour le dashboard
└── requirements.txt         # Dépendances Python
```

## Notes

- Les fichiers sont stockés dans le dossier `uploads/` à la racine du projet
- Les fichiers Excel sont automatiquement convertis en CSV
- Le backend utilise les services de `code_interpreter/` pour l'analyse




