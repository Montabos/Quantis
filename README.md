# Quantis v2

Application web de pilotage financier avec analyse de décisions assistée par IA (Google Gemini).

## 🎯 Fonctionnalités

- **📊 Dashboard financier** : Visualisation des KPIs et métriques clés
- **🤖 Analyse de décisions assistée par IA** : Posez une question financière et obtenez une analyse complète avec scénarios, recommandations et graphiques
- **📁 Gestion de fichiers** : Upload et analyse de fichiers Excel/CSV financiers
- **💬 Chat contextuel** : Assistant CFO pour discuter de vos analyses et ajuster les hypothèses
- **📈 Projections financières** : Scénarios optimiste, réaliste et pessimiste avec graphiques
- **🔐 Authentification sécurisée** : Système d'authentification avec Supabase

## 🚀 Démarrage Rapide

### Prérequis

- **Node.js** 18+ et npm
- **Python** 3.8+
- **Clé API Gemini** (gratuite sur [Google AI Studio](https://aistudio.google.com/app/apikey))
- **Compte Supabase** (gratuit sur [supabase.com](https://supabase.com))

### Installation

1. **Cloner le projet**
```bash
git clone <repo-url>
cd quantis-v2
```

2. **Installer les dépendances frontend**
```bash
npm install
```

3. **Installer les dépendances backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../code_interpreter
pip install -r requirements.txt
cd ..
```

4. **Configurer les variables d'environnement**

Créer un fichier `.env.local` à la racine avec :
```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=votre_url_supabase
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_cle_anon_supabase

# Gemini API
GEMINI_TOKEN=votre_cle_api_gemini

# Backend Python
PYTHON_BACKEND_URL=http://localhost:8000

# App URL (pour les callbacks)
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

5. **Configurer Supabase**

Exécuter les migrations SQL dans l'ordre :
- `supabase/migrations.sql`
- `supabase/add-profiles-migration.sql`
- `supabase/add-projects-migration.sql`
- `supabase/add-analysis-status-migration.sql`
- `supabase/storage-policies.sql`
- `supabase/update-projects-required.sql`

6. **Démarrer l'application**

```bash
npm run dev
```

Cette commande démarre automatiquement :
- Le frontend Next.js sur `http://localhost:3000`
- Le backend Python FastAPI sur `http://localhost:8000`

## 📁 Structure du Projet

```
quantis-v2/
├── app/                      # Next.js App Router
│   ├── api/                 # API Routes Next.js
│   │   ├── decisions/       # Endpoints d'analyse de décisions
│   │   ├── files/           # Endpoints de gestion de fichiers
│   │   └── auth/            # Authentification
│   ├── page.tsx             # Page principale
│   └── layout.tsx           # Layout global
├── components/              # Composants React
│   ├── decision/           # Composants pour les analyses
│   └── widgets/            # Widgets du dashboard
├── contexts/               # Contextes React (état global)
├── hooks/                  # Hooks personnalisés
├── lib/                    # Utilitaires et helpers
├── backend/                # Backend Python FastAPI
│   ├── api/
│   │   ├── main.py         # Application FastAPI principale
│   │   └── routes/         # Routes API
│   └── requirements.txt    # Dépendances Python backend
├── code_interpreter/       # Services d'analyse avec Gemini
│   ├── services/           # Services Python
│   │   ├── gemini_service.py      # Service Gemini Code Execution
│   │   ├── decision_analyzer.py    # Analyseur de décisions
│   │   └── data_checker.py         # Vérification de données
│   ├── templates/          # Prompts pour Gemini
│   └── requirements.txt    # Dépendances Python code_interpreter
├── scripts/                # Scripts utilitaires
│   └── start-backend.js    # Script de démarrage backend
├── supabase/               # Migrations SQL Supabase
└── public/                 # Fichiers statiques
```

## 🔧 Technologies Utilisées

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **React Context API**
- **Supabase Client**

### Backend
- **FastAPI** (Python)
- **Google Gemini API** (Code Execution)
- **Pandas** (Traitement de données)
- **Matplotlib/Seaborn** (Génération de graphiques)

### Base de données
- **Supabase** (PostgreSQL + Storage)

## 📖 Documentation

### Workflow d'Analyse

1. **Upload de fichiers** : L'utilisateur upload des fichiers Excel/CSV via la sidebar
2. **Question** : L'utilisateur pose une question dans la Decision Bar
3. **Analyse en temps réel** : Le système affiche les étapes de l'analyse dans un modal
4. **Rapport généré** : Un rapport complet est généré avec :
   - Métriques clés
   - Facteurs critiques
   - Scénarios (optimiste/réaliste/pessimiste)
   - Recommandations prioritaires
   - Alternatives stratégiques
   - Graphiques de projection
5. **Chat contextuel** : L'utilisateur peut discuter avec l'assistant CFO et ajuster les hypothèses

### Architecture

- **Frontend** : Next.js avec App Router, gestion d'état via Context API
- **Backend** : FastAPI avec endpoints RESTful
- **IA** : Google Gemini Code Execution pour l'analyse et la génération de code Python
- **Base de données** : Supabase (PostgreSQL) pour les données utilisateur et analyses
- **Storage** : Supabase Storage pour les fichiers uploadés

## 🛠️ Développement

### Scripts disponibles

```bash
npm run dev          # Démarre frontend + backend en parallèle
npm run dev:next     # Démarre uniquement le frontend
npm run dev:backend  # Démarre uniquement le backend
npm run build        # Build de production
npm run start        # Démarre en mode production
npm run lint         # Linter le code
```

### Structure des API

#### Frontend → Backend Python
- `POST /api/decisions/analyze/stream` : Lancer une analyse asynchrone
- `GET /api/decisions/analyze/[id]/status` : Polling du statut d'analyse
- `POST /api/decisions/analyze/[id]/update-status` : Mise à jour du statut (appelé par le backend)
- `POST /api/decisions/chat` : Chat contextuel sur une analyse
- `POST /api/decisions/generate-hypotheses` : Génération d'hypothèses

#### Backend Python → Gemini
- Utilise Gemini Code Execution pour générer et exécuter du code Python
- Analyse les fichiers CSV avec pandas
- Génère des graphiques avec matplotlib/seaborn

## 🔐 Sécurité

- Authentification via Supabase Auth
- Row Level Security (RLS) sur toutes les tables Supabase
- Variables d'environnement pour les secrets
- Validation des données côté serveur
- Sanitization des inputs utilisateur

## 📝 Variables d'Environnement

Voir `.env.example` pour la liste complète des variables nécessaires.

