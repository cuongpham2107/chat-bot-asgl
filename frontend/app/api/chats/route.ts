import { auth } from "@/app/(auth)/auth";
import { NextResponse } from 'next/server';

const baseUrl = process.env.BACKEND_API_URL!;

export async function GET() {
  try {
    const session = await auth();
    // If no session or no access token, return empty array
    if (!session?.user?.accessToken) {
      console.log("No access token found");
      return NextResponse.json([]);
    }

    const token = session.user.accessToken;
    
    const res = await fetch(`${baseUrl}/api/chats`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      // If the backend API returned an error, return that error
      return new NextResponse(await res.text(), {
        status: res.status,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }

    // Return the data from the backend API
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in /api/chats:", error);
    return NextResponse.json([], { status: 500 });
  }
}
