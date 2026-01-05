const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, '../careflow-b7a79-firebase-adminsdk-fbsvc-41b20258bd.json');
const envPath = path.join(__dirname, '../.env');

try {
    const serviceAccount = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));

    const envContent = fs.readFileSync(envPath, 'utf8');

    // Check if keys already exist to avoid duplicates
    if (envContent.includes('FIREBASE_PRIVATE_KEY')) {
        console.log('Environment variables already configured.');
        process.exit(0);
    }

    const newEnvVars = `
# Admin SDK (Server-Side Only)
FIREBASE_PROJECT_ID=${serviceAccount.project_id}
FIREBASE_CLIENT_EMAIL=${serviceAccount.client_email}
FIREBASE_PRIVATE_KEY="${serviceAccount.private_key.replace(/\n/g, '\\n')}"
`;

    fs.appendFileSync(envPath, newEnvVars);
    console.log('✅ Successfully updated .env with Firebase credentials.');

} catch (error) {
    console.error('Error updating .env:', error);
    process.exit(1);
}
