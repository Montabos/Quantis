#!/usr/bin/env node

/**
 * Script pour démarrer le backend Python avec gestion des variables d'environnement
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Charger les variables d'environnement depuis .env ou .env.local à la racine
function loadEnvFile() {
  const rootDir = path.join(__dirname, '..');
  const envPaths = [
    path.join(rootDir, '.env.local'), // Priorité à .env.local (standard Next.js)
    path.join(rootDir, '.env'),
    path.join(rootDir, 'backend', '.env'),
  ];
  
  const env = {};
  
  // Charger tous les fichiers .env (le dernier écrase les précédents)
  for (const envPath of envPaths) {
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf-8');
      envContent.split('\n').forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine && !trimmedLine.startsWith('#')) {
          const [key, ...valueParts] = trimmedLine.split('=');
          if (key && valueParts.length > 0) {
            const value = valueParts.join('=').trim();
            // Supprimer les guillemets si présents
            const cleanValue = value.replace(/^["']|["']$/g, '');
            const cleanKey = key.trim();
            
            // Ajouter la clé telle quelle
            env[cleanKey] = cleanValue;
            
            // Ajouter aussi en minuscules pour compatibilité avec le backend Python
            // qui cherche "gemini_token" en minuscules
            if (cleanKey.toUpperCase() === 'GEMINI_TOKEN') {
              env['gemini_token'] = cleanValue;
            }
          }
        }
      });
    }
  }
  
  return env;
}

// Détecter si on est sur Windows
const isWindows = process.platform === 'win32';

// Chemin vers le backend
const backendPath = path.join(__dirname, '..', 'backend');
const venvPath = path.join(backendPath, 'venv');

// Variables d'environnement
const env = {
  ...process.env,
  ...loadEnvFile(),
};

// Trouver le Python à utiliser (venv en priorité, sinon système)
function findPython() {
  return new Promise((resolve, reject) => {
    // Vérifier si venv existe
    if (fs.existsSync(venvPath)) {
      const pythonInVenv = isWindows 
        ? path.join(venvPath, 'Scripts', 'python.exe')
        : path.join(venvPath, 'bin', 'python');
      
      if (fs.existsSync(pythonInVenv)) {
        resolve(pythonInVenv);
        return;
      }
    }
    
    // Sinon utiliser Python système
    const pythonCmd = isWindows ? 'python' : 'python3';
    const check = spawn(pythonCmd, ['--version'], { stdio: 'pipe' });
    
    check.on('close', (code) => {
      if (code === 0) {
        resolve(pythonCmd);
      } else {
        reject(new Error(`Python n'est pas installé ou n'est pas dans le PATH`));
      }
    });
    
    check.on('error', () => {
      reject(new Error(`Python n'est pas installé ou n'est pas dans le PATH`));
    });
  });
}

// Démarrer le backend
async function startBackend() {
  try {
    const pythonCmd = await findPython();
    
    console.log('🚀 Démarrage du backend Python...');
    console.log(`📁 Répertoire: ${backendPath}`);
    
    // Vérifier que GEMINI_TOKEN est défini
    if (!env.GEMINI_TOKEN) {
      console.warn('⚠️  Attention: GEMINI_TOKEN n\'est pas défini dans les variables d\'environnement');
      console.warn('   Assurez-vous d\'avoir un fichier .env avec GEMINI_TOKEN=votre_token');
    }
    
    // Lancer uvicorn
    const args = [
      '-m',
      'uvicorn',
      'api.main:app',
      '--reload',
      '--host',
      '0.0.0.0',
      '--port',
      '8000'
    ];
    
    const backendProcess = spawn(pythonCmd, args, {
      cwd: backendPath,
      env: env,
      stdio: 'inherit',
      shell: isWindows,
    });
    
    backendProcess.on('error', (error) => {
      console.error('❌ Erreur lors du démarrage du backend:', error.message);
      process.exit(1);
    });
    
    backendProcess.on('exit', (code) => {
      if (code !== 0 && code !== null) {
        console.error(`❌ Le backend s'est arrêté avec le code ${code}`);
        process.exit(code);
      }
    });
    
    // Gérer l'arrêt propre
    process.on('SIGINT', () => {
      console.log('\n🛑 Arrêt du backend...');
      backendProcess.kill('SIGINT');
      process.exit(0);
    });
    
    process.on('SIGTERM', () => {
      backendProcess.kill('SIGTERM');
      process.exit(0);
    });
    
  } catch (error) {
    console.error('❌ Erreur:', error.message);
    process.exit(1);
  }
}

startBackend();

