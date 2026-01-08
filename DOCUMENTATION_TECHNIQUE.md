# 📋 Documentation Technique - Quantis v2

## Vue d'ensemble

**Quantis v2** est une application web de pilotage financier qui utilise l'intelligence artificielle (Google Gemini) pour analyser automatiquement des décisions financières complexes à partir de fichiers Excel/CSV.

---

## 🔄 Mécanique d'Analyse - Workflow Complet

### 1. **Upload de Fichiers**
```
Utilisateur authentifié upload Excel/CSV
        │
        ▼
┌─────────────────────────────────────┐
│  Supabase Auth                      │
│  • Vérification token JWT            │
│  • Extraction user_id + company_id  │
│  • Vérification RLS policies         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Traitement Backend                 │
│  • Extraction métadonnées            │
│  • Détection type document          │
│  • Conversion Excel → CSV            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Supabase Storage                   │
│  • Upload vers bucket               │
│  • Chiffrement automatique          │
└──────────────┬──────────────────────┘

- Détection automatique du type de document financier (Bilan, Compte de résultat, Cash Flow, etc.)
- Conversion automatique Excel → CSV (requis par Gemini Code Execution)

---

### 2. **Analyse de Décision**

Lorsqu'un utilisateur pose une question (ex: "Puis-je recruter un commercial à 60k€ ?"), le système suit un processus intelligent en 2 étapes :

#### **Étape 1 : Analyse & Planification (Gemini 3)**

```
Question utilisateur + Fichiers disponibles
        │
        ▼
┌─────────────────────────────────────┐
│  Analyse Question + Connaissances   │
│  Financières                        │
│  • Type de décision identifié        │
│  • KPIs pertinents déterminés       │
│    (ex: Trésorerie, Ratio de solvabilité)│
│  • Structure rapport optimale       │
│  • Méthodes de calcul identifiées par rapport a notre fichier de connaissance sur les kpi financiers  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Mapping Données Disponibles dans les fichiers excels de l'utilisateur       │
│  • Métadonnées fichiers analysées   │
│  • Correspondance entre KPIs necessaires pour l'analyse ↔ et les Données dispo dans les csv   │
│  • Données manquantes identifiées   │
│  • Adaptation structure rapport     │
└──────────────┬──────────────────────┘
               │
               ▼
Plan d'analyse JSON généré
• KPIs à calculer avec formules
• Graphiques à générer
• Scénarios à projeter
```

**Logique :**
- **Base de connaissances financières** : Le système utilise des règles métier pour identifier les KPIs pertinents selon le type de décision (recrutement → impact trésorerie, capacité d'endettement, etc.)
- **Adaptation intelligente** : Si certaines données manquent, le système adapte le rapport (estimation, scénarios simplifiés, ou demande de données complémentaires)

**Durée :** ~15-20 secondes

#### **Étape 2 : Génération du rapport & Exécution (Gemini Code Execution)**

```
Plan d'analyse (generé à l'étape précédente + Fichiers CSV)
        │
        ▼
┌─────────────────────────────────────┐
│  Génération Code Python pour calculer les kpis et creer les graphiques             │
│  • Code adapté aux fichiers csv       │
│  • Formules KPIs intégrées          │
│  • Gestion formats variés           │
│  • Génération graphiques            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Exécution (Sandbox)                │
│  • Calcul KPIs financiers           │
│    (Trésorerie, Ratios, Projections)│
│  • Graphiques professionnels        │
│  • Extraction métriques clés        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Analyse Contextuelle              │
│  • Interprétation résultats         │
│  • Scénarios (optimiste/réaliste/   │
│    pessimiste) avec jalons          │
│  • Recommandations prioritaires     │
│  • Alternatives stratégiques        │
└─────────────────────────────────────┘
```

**Logique :**
- **Calculs financiers spécialisés** : Le code généré applique les formules financières appropriées (ex: `days_cash_on_hand = trésorerie / (dépenses_mensuelles / 30)`)
- **Validation** : Vérification de la cohérence des résultats et détection d'anomalies
- **Recommandations contextuelles** : Basées sur les seuils financiers standards et la situation spécifique de l'entreprise

**Durée :** ~40-50 secondes

**Résultat final :**
- ✅ KPIs financiers calculés avec formules explicitées
- ✅ Facteurs critiques identifiés et quantifiés
- ✅ 3 scénarios projetés avec jalons temporels
- ✅ Recommandations prioritaires avec impacts estimés
- ✅ Graphiques professionnels (PNG)
- ✅ Analyse narrative complète et actionnable

**Améliorations futures :**
- 📊 **Base de connaissances enrichie** : Règles sectorielles, benchmarks, seuils d'alerte personnalisés
- 🤖 **Apprentissage** : Historique des décisions pour améliorer les recommandations
- 🔄 **Validation croisée** : Vérification multi-sources et détection d'incohérences
- 📈 **Prédictions ML** : Modèles prédictifs pour projections plus précises
- Connexion aux api ERP des outils financiers des entreprises pour avoir directement acces à toutes les info financieres

---

## 🧠 Intelligence Artificielle - Gemini Code Execution

### Fonctionnement

**Gemini Code Execution** permet à l'IA de :
1. **Générer du code Python** adapté à chaque fichier csv qui peuvent avoir des formats differents pour chaque utilisateur
2. **Exécuter le code** dans un environnement sandbox sécurisé
3. **Analyser les résultats** et générer des insights

### Avantages

- ✅ **Adaptabilité** : Le code généré s'adapte automatiquement à la structure de chaque fichier
- ✅ **Robustesse** : Gestion automatique des formats variés (dates françaises/anglaises, encodages, etc.)
- ✅ **Transparence** : Le code généré est visible et traçable
- ✅ **Pas de préparation** : Fonctionne avec n'importe quel fichier Excel/CSV financier


### Fonctionnalités

**À venir :**
- 📊 **Dashboard avancé** : Visualisations interactives, alertes automatiques
- 🔗 **Intégrations** : Connexion directe aux ERP (SAP, Sage, etc.)
- 📄 **Support formats** : PDF, API REST, webhooks
- 🤖 **Apprentissage** : Modèles ML pour prédictions financières
- 👥 **Collaboration** : Partage d'analyses, commentaires, annotations
- 📈 **Benchmarking** : Comparaisons sectorielles automatiques

### Sécurité & Conformité

**À implémenter :**
- 🔐 Authentification multi-facteurs
- 🔒 Chiffrement des données au repos
- 📋 Audit logs complets
- ✅ Conformité RGPD (suppression données, droit à l'oubli)
- 🛡️ Rate limiting sur API

### Scalabilité

**Architecture cible :**
- 🐳 Containerisation (Docker)
- ☸️ Orchestration (Kubernetes)
- 🔄 Load balancing
- 💾 Base de données distribuée
- 📊 Monitoring (Prometheus, Grafana)

---

