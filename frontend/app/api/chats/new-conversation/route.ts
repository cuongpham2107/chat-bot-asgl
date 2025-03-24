import { auth } from "@/app/(auth)/auth";
import { NextResponse } from 'next/server';


 // Get base URL from environment variable
 const baseUrl = process.env.BACKEND_API_URL;

export async function POST(
    request: Request
){
    try {
        const body = await request.json();
        const { message } = body;
        
        if (!message) {
            return NextResponse.json(
                { error: "Message content is required" },
                { status: 400 }
            )
        }
        
        // Get token from session
        // Note: You'll need to implement a way to get the session
        // This could be using next-auth or your custom auth solution
        const session = await auth(); // Implement this function to get your session
        const token = session?.user?.accessToken;
        
        if (!token) {
            throw new Error("Authentication token not found");
        }
        // Append message as a URL parameter
        const url = new URL(`${baseUrl}/api/chats/new-conversation`);
        url.searchParams.append("message", message);
        
        const response = await fetch(url.toString(), { 
            method: 'POST',
            headers: {
            'Authorization': `Bearer ${token}`
            },
        });
        
        if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
        }
        
        const data = await response.json();
        if(!data) {
            return NextResponse.json(
                { error: "No data returned from the API" },
                { status: 500 }
            );
        }
        return NextResponse.json(data, { status: 201 });

    } catch (error) {
      console.error("Error creating conversation:", error);
      return NextResponse.json(
        { error: "Failed to create conversation" },
        { status: 500 }
      );
    }
}



