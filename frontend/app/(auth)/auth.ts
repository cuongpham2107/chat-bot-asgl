
import NextAuth, { User } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { authConfig } from './auth.config';

// Augment the existing types rather than creating new interfaces
declare module 'next-auth' {
  interface User {
    username: string;
    accessToken: string;
    user: string;
    tokenType: string;
  }
}

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut,
} = NextAuth({
  ...authConfig,
  debug: process.env.NODE_ENV === 'development',
  providers: [
    CredentialsProvider({
      credentials: {
        username: { label: 'Username', type: 'text' },
        accessToken: { label: 'Access Token', type: 'text' },
        user: { label: 'User', type: 'text' },
      },
      async authorize(credentials) : Promise<User | null> {
        try {
          const { username, accessToken, user } = credentials || {};

          if(!username || !accessToken) {
            return null;
          }
          
          return {
            id: username as string,
            username: username as string,
            accessToken: accessToken as string, 
            user: user as string,
            tokenType: 'Bearer'
          };
        } catch (error) {
          console.error('Error in authorize callback:', error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.username = user.username;
        token.accessToken = user.accessToken;
        token.user = user.user;
        token.tokenType = 'Bearer';
      }

      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.username = token.username as string;
        session.user.accessToken = token.accessToken as string;
        session.user.user = token.user as string;
        session.user.tokenType = token.tokenType as string;
      }

      return session;
    },
  },
});
