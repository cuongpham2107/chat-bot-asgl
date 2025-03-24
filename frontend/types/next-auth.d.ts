// eslint-disable-next-line @typescript-eslint/no-unused-vars
import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      username: string;
      accessToken: string;
      tokenType: string;
    } & DefaultSession['user'];
  }

  interface User {
    id: string;
    username: string;
    accessToken: string;
    tokenType: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    username: string;
    accessToken: string;
    tokenType: string;
  }
}
