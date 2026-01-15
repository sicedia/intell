#!/usr/bin/env node

/**
 * Script to verify all translation keys are present in both en.json and es.json
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// Load translation files
const enPath = path.join(__dirname, '../messages/en.json');
const esPath = path.join(__dirname, '../messages/es.json');

const enTranslations = JSON.parse(fs.readFileSync(enPath, 'utf8'));
const esTranslations = JSON.parse(fs.readFileSync(esPath, 'utf8'));

// Function to get all keys from a nested object
function getAllKeys(obj, prefix = '') {
  const keys = [];
  for (const key in obj) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
      keys.push(...getAllKeys(obj[key], fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

// Get all keys from both translation files
const enKeys = new Set(getAllKeys(enTranslations));
const esKeys = new Set(getAllKeys(esTranslations));

// Find keys in English that are missing in Spanish
const missingInSpanish = [...enKeys].filter(key => !esKeys.has(key));

// Find keys in Spanish that are missing in English
const missingInEnglish = [...esKeys].filter(key => !enKeys.has(key));

// Extract translation keys from source code
function extractTranslationKeysFromCode() {
  const srcPath = path.join(__dirname, '../src');
  
  // Find all .tsx and .ts files
  const files = execSync(`find "${srcPath}" -type f \\( -name "*.tsx" -o -name "*.ts" \\)`, {
    encoding: 'utf8',
    shell: true
  }).trim().split('\n').filter(Boolean);

  const usedKeys = new Set();
  
  for (const file of files) {
    try {
      const content = fs.readFileSync(file, 'utf8');
      
      // Match useTranslations('namespace') patterns
      const namespaceMatches = content.matchAll(/useTranslations\(['"]([^'"]+)['"]\)/g);
      for (const match of namespaceMatches) {
        const namespace = match[1];
        
        // Find all t('key') or t("key") calls after this namespace
        // This is a simplified approach - in reality, we'd need to track the scope
        const tMatches = content.matchAll(/t\(['"]([^'"]+)['"]\)/g);
        for (const tMatch of tMatches) {
          const key = tMatch[1];
          const fullKey = `${namespace}.${key}`;
          usedKeys.add(fullKey);
        }
      }
    } catch (error) {
      // Skip files that can't be read
    }
  }
  
  return usedKeys;
}

// Recursively find all TypeScript files
function findFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      findFiles(filePath, fileList);
    } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
      fileList.push(filePath);
    }
  });
  return fileList;
}

// More sophisticated extraction that tracks multiple translation variables
function extractTranslationKeys() {
  const srcPath = path.join(__dirname, '../src');
  const files = findFiles(srcPath);

  const usedKeys = new Map(); // Map of file -> Set of keys
  
  for (const file of files) {
    try {
      const content = fs.readFileSync(file, 'utf8');
      const fileKeys = new Set();
      
      // Map of variable names to their namespaces
      // e.g., { 't': 'generate.results', 'tCommon': 'common', 'tAI': 'aiDescription' }
      const translationVars = new Map();
      
      // Find all useTranslations declarations
      const lines = content.split('\n');
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Match: const t = useTranslations('namespace');
        // Match: const tCommon = useTranslations('common');
        // Match: const tAI = useTranslations('aiDescription');
        const translationMatch = line.match(/(?:const|let|var)\s+(\w+)\s*=\s*useTranslations\(['"]([^'"]+)['"]\)/);
        if (translationMatch) {
          const varName = translationMatch[1];
          const namespace = translationMatch[2];
          translationVars.set(varName, namespace);
          continue;
        }
        
        // Now find all usages of these translation variables
        // Match: t('key'), tCommon('key'), tAI('key'), etc.
        for (const [varName, namespace] of translationVars.entries()) {
          // Match the variable name followed by ('key' or "key")
          // Use word boundary to avoid matching partial names
          const regex = new RegExp(`\\b${varName}\\s*\\(['"]([^'"]+)['"]`, 'g');
          const matches = line.matchAll(regex);
          for (const match of matches) {
            const key = match[1];
            // Skip empty keys and keys that look like template literals or variables
            if (key && !key.includes('${') && !key.startsWith('{')) {
              const fullKey = `${namespace}.${key}`;
              fileKeys.add(fullKey);
            }
          }
        }
      }
      
      if (fileKeys.size > 0) {
        usedKeys.set(file, fileKeys);
      }
    } catch (error) {
      // Skip files that can't be read
      console.warn(`Warning: Could not process ${file}: ${error.message}`);
    }
  }
  
  return usedKeys;
}

log('\n🔍 Checking translation files...\n', 'blue');

// Check for missing keys between languages
if (missingInSpanish.length > 0) {
  log(`❌ Found ${missingInSpanish.length} keys in English missing in Spanish:`, 'red');
  missingInSpanish.forEach(key => log(`   - ${key}`, 'yellow'));
  log('');
}

if (missingInEnglish.length > 0) {
  log(`❌ Found ${missingInEnglish.length} keys in Spanish missing in English:`, 'red');
  missingInEnglish.forEach(key => log(`   - ${key}`, 'yellow'));
  log('');
}

// Extract and check used keys
log('📝 Extracting translation keys from source code...\n', 'blue');
const usedKeysMap = extractTranslationKeys();
const allUsedKeys = new Set();
usedKeysMap.forEach(keys => keys.forEach(key => allUsedKeys.add(key)));

log(`Found ${allUsedKeys.size} unique translation keys used in code\n`, 'blue');

// Check which used keys are missing
const missingUsedKeys = {
  en: [],
  es: []
};

for (const key of allUsedKeys) {
  if (!enKeys.has(key)) {
    missingUsedKeys.en.push(key);
  }
  if (!esKeys.has(key)) {
    missingUsedKeys.es.push(key);
  }
}

// Report results
if (missingUsedKeys.en.length > 0) {
  log(`❌ Found ${missingUsedKeys.en.length} used keys missing in English:`, 'red');
  missingUsedKeys.en.forEach(key => log(`   - ${key}`, 'yellow'));
  log('');
} else {
  log('✅ All used keys exist in English translations', 'green');
}

if (missingUsedKeys.es.length > 0) {
  log(`❌ Found ${missingUsedKeys.es.length} used keys missing in Spanish:`, 'red');
  missingUsedKeys.es.forEach(key => log(`   - ${key}`, 'yellow'));
  log('');
} else {
  log('✅ All used keys exist in Spanish translations', 'green');
}

// Summary
log('\n📊 Summary:', 'blue');
log(`   Total keys in English: ${enKeys.size}`, 'reset');
log(`   Total keys in Spanish: ${esKeys.size}`, 'reset');
log(`   Total keys used in code: ${allUsedKeys.size}`, 'reset');
log(`   Keys missing between languages: ${missingInSpanish.length + missingInEnglish.length}`, 
  (missingInSpanish.length + missingInEnglish.length > 0 ? 'yellow' : 'green'));
log(`   Used keys missing in translations: ${missingUsedKeys.en.length + missingUsedKeys.es.length}`, 
  (missingUsedKeys.en.length + missingUsedKeys.es.length > 0 ? 'red' : 'green'));

// Exit with error code if there are missing keys
if (missingUsedKeys.en.length > 0 || missingUsedKeys.es.length > 0 || 
    missingInSpanish.length > 0 || missingInEnglish.length > 0) {
  process.exit(1);
}

log('\n✅ All translations are complete!', 'green');
