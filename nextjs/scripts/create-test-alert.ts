/**
 * Script pour créer une alerte test en temps réel
 */

import { initializeApp, getApps, applicationDefault } from 'firebase-admin/app';
import { getFirestore, Timestamp } from 'firebase-admin/firestore';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Load .env
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const envPath = path.resolve(__dirname, '../.env');

if (fs.existsSync(envPath)) {
    const envConfig = fs.readFileSync(envPath, 'utf8');
    envConfig.split('\n').forEach((line) => {
        const match = line.match(/^([^=]+)=(.*)$/);
        if (match) {
            const key = match[1].trim();
            let value = match[2].trim();
            if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            process.env[key] = value;
        }
    });
}

const projectId = process.env.FIREBASE_PROJECT_ID || process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

// Initialize Firebase
let app;
if (getApps().length === 0) {
    app = initializeApp({
        projectId,
        credential: applicationDefault()
    });
} else {
    app = getApps()[0];
}

const db = getFirestore(app, 'careflow-db');

const main = async () => {
    const alertId = `alert_test_${Date.now()}`;

    const alert = {
        id: alertId,
        patientId: "p_h1_001",
        patientName: "Christ Chadrak MVOUNGOU",
        hospitalId: "HOSP001",
        priority: "warning",
        status: "active",
        trigger: "🧪 TEST: Nouvelle alerte créée pour test temps réel !",
        aiBrief: "Ceci est une alerte de test pour vérifier le temps réel sur le dashboard.",
        createdAt: Timestamp.now(),
        updatedAt: Timestamp.now()
    };

    console.log('🚨 Création d\'une alerte test...');

    await db.collection('alerts').doc(alertId).set(alert);

    console.log(`✅ Alerte créée: ${alertId}`);
    console.log(`   👤 Patient: ${alert.patientName}`);
    console.log(`   ⚠️  Priority: ${alert.priority}`);
    console.log(`   📝 Trigger: ${alert.trigger}`);
    console.log('');
    console.log('👀 Regarde ton dashboard - l\'alerte devrait apparaître en temps réel !');

    process.exit(0);
};

main().catch(err => {
    console.error('❌ Erreur:', err);
    process.exit(1);
});
