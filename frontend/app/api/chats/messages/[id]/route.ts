import { auth } from "@/app/(auth)/auth";
import { NextResponse } from "next/server";

const baseUrl = process.env.BACKEND_API_URL!;
export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = await params;

  const { message, source_file_id } = await request.json();

    if (!message) {
        return NextResponse.json(
        { error: "Message content is required" },
        { status: 400 }
        );
    }
  const session = await auth();
  if (!session?.user?.accessToken) {
    console.log("No access token found");
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }


    const token = session.user.accessToken;

    try {
        const res = await fetch(`${baseUrl}/api/messages/chat/${id}/send`, {
            method: "POST",
            headers: {
                "accept": "application/json",
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                content: message,
                source_file_id: source_file_id,
                metadata: null // Changed from [] to null to match backend schema
            }),
        });

        if (!res.ok) {
            return NextResponse.json({ error: "Failed to send message" }, { status: 500 });
        }
        
        const data = await res.json();
        if (!data) {
            return NextResponse.json({ error: "No data returned from the API" }, { status: 500 });
        }
        
        return NextResponse.json(data, { status: 201 });
    } catch (error) {
        console.error(error);
        return NextResponse.json({ error: "An error occurred while sending the message" }, { status: 500 });
    }
}