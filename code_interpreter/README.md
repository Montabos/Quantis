# Gemini Code Interpreter - Outil de Test

Outil d'exploration et de test pour la fonctionnalité **Code Execution** de Gemini API. Cet outil permet d'uploader des fichiers Excel financiers et d'observer en détail comment Gemini génère et exécute du code Python pour analyser les données.

## 🎯 Objectif

Cet outil est conçu pour **tester et explorer** la fonctionnalité Code Execution de Gemini. Il offre une visibilité maximale sur :
- Les prompts envoyés à Gemini
- Le code Python généré automatiquement
- Les résultats d'exécution du code
- Les graphiques créés
- Tous les détails techniques de l'interaction

**Note** : Cet outil n'est pas optimisé pour la production. Il est conçu pour le développement, le test et la compréhension du fonctionnement de Gemini Code Execution.

## 📋 Prérequis

- Python 3.8 ou supérieur
- Une clé API Gemini (gratuite sur [Google AI Studio](https://aistudio.google.com/app/apikey))

## 🚀 Installation

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer la clé API**
   - Copier le fichier `.env.example` vers `.env`
   - Éditer `.env` et ajouter votre clé API :
     ```
     gemini_token=votre_cle_api_ici
     ```

## 💻 Utilisation

1. **Lancer l'application Streamlit**
   ```bash
   python -m streamlit run app.py
   ```

2. **Ouvrir votre navigateur**
   - L'application s'ouvrira automatiquement sur `http://localhost:8501`

3. **Uploader un fichier Excel**
   - Cliquez sur "Browse files" et sélectionnez un fichier `.xlsx`, `.xls` ou `.csv`
   - Les métadonnées du fichier seront affichées automatiquement

4. **Lancer l'analyse**
   - Cliquez sur "🚀 Analyser avec Gemini Code Execution"
   - Observez les différentes sections qui se remplissent :
     - Analyse textuelle
     - Code généré
     - Résultats d'exécution
     - Graphiques créés

5. **Explorer les détails**
   - Utilisez les onglets dans la section "Détails techniques" pour voir :
     - Le code Python généré
     - Les sorties d'exécution
     - La réponse complète de l'API
     - Les métadonnées de l'analyse

## 📁 Structure du projet

```
code_interpreter/
├── app.py                    # Application Streamlit principale
├── services/
│   ├── __init__.py
│   ├── gemini_service.py     # Service Gemini avec Code Execution
│   └── file_utils.py         # Utilitaires pour fichiers Excel
├── documentation/            # Documentation Gemini API
├── financial_rules.json      # Règles financières et KPIs par type de document
├── .env                      # Configuration (non versionné)
├── env.example.txt          # Template de configuration
├── requirements.txt          # Dépendances Python
└── README.md                # Ce fichier
```

## 🔧 Fonctionnalités

### Système de règles financières
- **Détection automatique** : Identification du type de document (Bilan, Compte de résultat, Grand Livre, etc.)
- **KPIs guidés** : Calcul automatique des KPIs pertinents selon le type de document détecté
- **Graphiques suggérés** : Génération de graphiques adaptés au type de données
- **Règles configurables** : Fichier JSON modifiable pour ajouter de nouveaux types de documents

### Visibilité maximale
- **Métadonnées du fichier** : Colonnes, types, aperçu des données
- **Prompt envoyé** : Voir exactement ce qui est envoyé à Gemini
- **Code généré** : Tous les blocs de code Python créés par Gemini
- **Résultats d'exécution** : Sorties complètes du code exécuté
- **Graphiques** : Affichage des images PNG générées
- **Règles appliquées** : Affichage des règles financières utilisées pour l'analyse
- **Logs détaillés** : Tous les événements de l'application

### Export
- Télécharger le code généré en fichier `.py`
- Télécharger les résultats complets en JSON

### Debug
- Section logs avec historique des événements
- Affichage des erreurs avec stack trace complète
- Métadonnées techniques de l'analyse

## 📊 Exemples de fichiers à tester

Vous pouvez tester avec différents types de fichiers Excel financiers :
- **Bilan comptable** : Actifs, Passifs
- **Compte de résultat** : Revenus, Dépenses
- **Grand Livre** : Transactions avec dates et montants
- **Cash Flow** : Flux de trésorerie
- **Portefeuille** : Actions, prix, quantités
- **Factures** : Liste de factures avec montants

Gemini détectera automatiquement le type de document et générera les KPIs et graphiques appropriés.

## 🐛 Dépannage

### Erreur "gemini_token non trouvée"
- Vérifiez que le fichier `.env` existe et contient `gemini_token=votre_cle`
- Assurez-vous que `python-dotenv` est installé

### Erreur lors de l'upload
- Vérifiez que le fichier est bien un `.xlsx`, `.xls` ou `.csv`
- Vérifiez que le fichier n'est pas corrompu

### Timeout lors de l'analyse
- Les fichiers très volumineux peuvent prendre du temps
- Gemini Code Execution a une limite de 30 secondes par exécution
- Essayez avec un fichier plus petit ou un échantillon

### Pas de code généré
- Vérifiez que vous utilisez un modèle Gemini qui supporte Code Execution
- Le modèle `gemini-2.0-flash-exp` est utilisé par défaut

## 📚 Documentation

- **Documentation technique** : [Fonctionnement du projet](documentation/FONCTIONNEMENT_PROJET.md) - Explication détaillée de l'architecture, du workflow et des technologies utilisées
- **Documentation Gemini API** : Documentation officielle de Gemini Code Execution disponible dans le dossier `documentation/`

## 🔒 Sécurité

- Ne partagez jamais votre fichier `.env` (il contient votre clé API)
- Les fichiers uploadés sont traités temporairement et supprimés après analyse
- Cet outil est conçu pour le développement local uniquement

## 📝 Notes

- Cet outil utilise le modèle `gemini-2.0-flash-exp` qui supporte Code Execution
- Les graphiques générés sont sauvegardés en PNG par Gemini
- Le code généré utilise principalement `pandas`, `matplotlib` et `seaborn`
- Les fichiers temporaires sont automatiquement nettoyés après analyse

## 🤝 Contribution

Cet outil est un projet de test/exploration. N'hésitez pas à le modifier pour vos besoins !

## 📄 Licence

Ce projet est fourni à des fins éducatives et de test.

