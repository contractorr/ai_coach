// TODO: next-auth pinned at 5.0.0-beta.30 — beta semver is unreliable.
// Auth.js was acquired by Better Auth; evaluate migrating to better-auth
// or waiting for a stable next-auth v5 release before upgrading.
import NextAuth from "next-auth";
import type { Provider } from "next-auth/providers";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
import { SignJWT } from "jose";

const jwtSecret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET);

const TEST_ACCOUNTS: Record<string, { name: string; email: string }> = {
  junior_dev: { name: "Junior Dev", email: "junior_dev@test.local" },
  founder: { name: "Founder", email: "founder@test.local" },
  switcher: { name: "Switcher", email: "switcher@test.local" },
};

const providers: Provider[] = [
  GitHub({
    clientId: process.env.GITHUB_CLIENT_ID!,
    clientSecret: process.env.GITHUB_CLIENT_SECRET!,
  }),
  Google({
    clientId: process.env.GOOGLE_CLIENT_ID!,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
  }),
];

if (process.env.ENABLE_TEST_AUTH === "true") {
  providers.push(
    Credentials({
      name: "Test Account",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const username = credentials?.username as string;
        const password = credentials?.password as string;
        if (password !== "test") return null;
        const account = TEST_ACCOUNTS[username];
        if (!account) return null;
        return { id: username, name: account.name, email: account.email };
      },
    }),
  );
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  providers,
  session: { strategy: "jwt" },
  callbacks: {
    authorized({ auth }) {
      return !!auth?.user;
    },
    async jwt({ token, account }) {
      // Pin sub to the OAuth provider's stable ID so it survives logout/login.
      // NextAuth v5 beta sets sub to a random UUID without a DB adapter.
      if (account) {
        token.sub = `${account.provider}:${account.providerAccountId}`;
      }
      if ((account || !token.backendToken) && token.sub) {
        token.backendToken = await new SignJWT({
          sub: token.sub,
          email: token.email,
          name: token.name,
        })
          .setProtectedHeader({ alg: "HS256" })
          .setExpirationTime("30d")
          .sign(jwtSecret);
      }
      return token;
    },
    async session({ session, token }) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (session as any).accessToken = token.backendToken;
      if (token.sub) session.user.id = token.sub;
      return session;
    },
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
});
