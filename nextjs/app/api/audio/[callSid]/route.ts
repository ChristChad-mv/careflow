
import { NextRequest, NextResponse } from "next/server";

export async function GET(
    request: NextRequest,
    context: { params: Promise<{ callSid: string }> }
) {
    const { callSid } = await context.params;
    const accountSid = process.env.TWILIO_ACCOUNT_SID;
    const authToken = process.env.TWILIO_AUTH_TOKEN;

    if (!accountSid || !authToken) {
        return NextResponse.json(
            { error: "Twilio credentials not configured" },
            { status: 500 }
        );
    }

    try {
        // 1. Get Recording SID for the Call
        const recordingsUrl = `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Calls/${callSid}/Recordings.json`;

        // Create Basic Auth header
        const authHeader = "Basic " + Buffer.from(accountSid + ":" + authToken).toString("base64");

        const metadataResp = await fetch(recordingsUrl, {
            headers: { Authorization: authHeader },
        });

        if (!metadataResp.ok) {
            return NextResponse.json(
                { error: "Failed to fetch recording metadata" },
                { status: metadataResp.status }
            );
        }

        const data = await metadataResp.json();
        const recordings = data.recordings;

        if (!recordings || recordings.length === 0) {
            return NextResponse.json(
                { error: "No recordings found for this call" },
                { status: 404 }
            );
        }

        // Capture the first recording
        const recordingSid = recordings[0].sid;

        // 2. Fetch the Audio Media
        const mediaUrl = `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Recordings/${recordingSid}.mp3`;

        const mediaResp = await fetch(mediaUrl, {
            headers: { Authorization: authHeader },
        });

        if (!mediaResp.ok) {
            return NextResponse.json(
                { error: "Failed to fetch audio file" },
                { status: mediaResp.status }
            )
        }

        // 3. Stream back to client
        // We pass the Content-Type from Twilio (audio/mpeg)
        const contentType = mediaResp.headers.get("content-type") || "audio/mpeg";

        return new NextResponse(mediaResp.body, {
            headers: {
                "Content-Type": contentType,
                "Cache-Control": "public, max-age=3600", // Cache for 1 hour
            },
        });

    } catch (error: any) {
        console.error("Audio Proxy Error:", error);
        return NextResponse.json(
            { error: "Internal Server Error" },
            { status: 500 }
        );
    }
}
