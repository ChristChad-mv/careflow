import "server-only";
import * as admin from "firebase-admin";
import { getFirestore } from "firebase-admin/firestore";

interface FirebaseAdminConfig {
    projectId: string;
    clientEmail?: string;
    privateKey?: string;
}

function formatPrivateKey(key: string) {
    return key.replace(/\\n/g, "\n");
}

export function createFirebaseAdminApp(params: FirebaseAdminConfig) {
    const privateKey = params.privateKey ? formatPrivateKey(params.privateKey) : undefined;

    if (admin.apps.length > 0) {
        return admin.app();
    }

    if (params.clientEmail && privateKey) {
        return admin.initializeApp({
            credential: admin.credential.cert({
                projectId: params.projectId,
                clientEmail: params.clientEmail,
                privateKey: privateKey,
            }),
            projectId: params.projectId,
        });
    } else {
        return admin.initializeApp({
            credential: admin.credential.applicationDefault(),
            projectId: params.projectId,
        });
    }
}

export async function initAdmin() {
    const params = {
        projectId: process.env.FIREBASE_PROJECT_ID || process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "careflow-478811",
        clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
        privateKey: process.env.FIREBASE_PRIVATE_KEY,
    };

    return createFirebaseAdminApp(params);
}

export async function getAdminDb() {
    const app = await initAdmin();
    // Connect to the specific named database 'careflow-db'
    return getFirestore(app, 'careflow-db');
}
