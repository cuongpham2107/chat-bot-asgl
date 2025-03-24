import { auth } from "@/app/(auth)/auth";
import { NextResponse } from "next/server";

const baseUrl = process.env.BACKEND_API_URL!;

export async function POST(
    request: Request
) {
    try {
        const formData = await request.formData();
        const files = formData.getAll('files');

        if (!files || files.length === 0) {
            return NextResponse.json({ error: "No files provided" }, { status: 400 });
        }

        const session = await auth();
        if (!session?.user?.accessToken) {
            console.log("No access token found");
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const token = session.user.accessToken;

        // Create a new FormData object to send to the backend
        const backendFormData = new FormData();
        
        // Add each file to the FormData
        files.forEach((file) => {
            backendFormData.append('files', file);
        });

        // Send the request to the backend
        const response = await fetch(`${baseUrl}/api/files/upload`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
            },
            body: backendFormData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error("Backend API error:", response.status, errorData);
            return NextResponse.json(
                { error: "Error uploading files", details: errorData }, 
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error uploading files:", error);
        return NextResponse.json({ error: "Error uploading files" }, { status: 500 });
    }
}

// Handle OPTIONS request for CORS preflight
export async function OPTIONS() {
    return NextResponse.json({}, { 
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    });
}
