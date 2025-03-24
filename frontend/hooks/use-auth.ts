import { useEffect, useState } from "react";

export function useAuth() {
    const [token, setToken] = useState<string | null>(null);
    const baseUrl = "http://localhost:8000"; // Replace with your actual base URL
    useEffect(() => {
        const fetchSession = async () => {
          try {
            const sessionRes = await fetch("/api/auth/session");
            
            if (!sessionRes.ok) throw new Error("Failed to fetch session");
            const session = await sessionRes.json();
            setToken(session?.user?.accessToken || null);
          } catch (error) {
            console.error("Error fetching session:", error);
          }
        };
    
        fetchSession();
    }, []);
    return {
        baseUrl,
        token
    };
}