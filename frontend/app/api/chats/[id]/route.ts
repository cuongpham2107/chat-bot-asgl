import { auth } from "@/app/(auth)/auth";
import { NextResponse } from 'next/server';

const baseUrl = process.env.BACKEND_API_URL!;
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = await params;
  console.log("ID", id);
  const session = await auth();

  if (!session?.user?.accessToken) {
    console.log("No access token found");
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const token = session.user.accessToken;


  try {
    const res = await fetch(`${baseUrl}/api/messages/chat/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      }
    });
    
    if (!res.ok) {
      return NextResponse.json({error:"Failed to get chat"});
    }
    
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error }, { status: 500 });
  }
}


export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = await params;

  const session = await auth();

  if (!session?.user?.accessToken) {
    console.log("No access token found");
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  
  const token = session.user.accessToken;
  
  try {
    const res = await fetch(`${baseUrl}/api/chats/${id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      }
    });
    
    if (!res.ok) {
      return NextResponse.json({error:"Failed to delete chat"});
    }
    
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: error }, { status: 500 });
  }
}
