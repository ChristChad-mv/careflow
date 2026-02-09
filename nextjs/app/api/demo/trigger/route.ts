import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { GoogleAuth } from 'google-auth-library';
// Using built-in crypto for UUID generation
const uuidv4 = () => crypto.randomUUID();

export async function POST(req: NextRequest) {
    try {
        // 1. Check Authentication
        const session = await auth();
        if (!session?.user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { patientId, scheduleHour = 8 } = await req.json();

        if (!patientId) {
            return NextResponse.json({ error: 'patientId is required' }, { status: 400 });
        }

        // 2. Get Agent URL from Environment
        // Priority: CAREFLOW_AGENT_URL > NEXT_PUBLIC_API_URL > Default
        const agentUrl = process.env.CAREFLOW_AGENT_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        console.log(`🚀 Triggering Demo Call for patient ${patientId} via ${agentUrl}`);

        // 3. Prepare A2A JSON-RPC Request
        // This follows the exact pattern from trigger_rounds_prod.py
        const requestId = Math.floor(Math.random() * 1000000);
        const messageText = `start daily rounds for ${scheduleHour}:00`;

        const rpcRequest = {
            jsonrpc: "2.0",
            method: "message/stream",
            id: requestId,
            params: {
                message: {
                    messageId: uuidv4(),
                    kind: "message",
                    role: "user",
                    parts: [{ kind: "text", text: messageText }]
                }
            }
        };

        // 4. Get OIDC Token (if in production)
        let headers: Record<string, string> = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        };

        // Only attempt to get OIDC token if it's not a local URL
        if (!agentUrl.includes('localhost') && !agentUrl.includes('127.0.0.1')) {
            try {
                const auth = new GoogleAuth();
                const client = await auth.getIdTokenClient(agentUrl);
                const token = await client.idTokenProvider.fetchIdToken(agentUrl);
                headers['Authorization'] = `Bearer ${token}`;
            } catch (authError) {
                console.warn("⚠️ Failed to get OIDC token, proceeding without it:", authError);
            }
        }

        // 5. Send Request to Agent
        // We use a short timeout for the trigger itself since the agent runs rounds in background
        const response = await fetch(agentUrl, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(rpcRequest),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ Agent Error (${response.status}):`, errorText);
            return NextResponse.json({
                error: `Agent returned error ${response.status}`,
                details: errorText
            }, { status: 502 });
        }

        return NextResponse.json({
            success: true,
            message: `Rounds triggered for ${scheduleHour}:00. Patient ${patientId} should be called shortly.`,
            agentResponseStatus: response.status
        });

    } catch (error: any) {
        console.error("❌ Demo Trigger API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
