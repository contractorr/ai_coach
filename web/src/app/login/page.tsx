"use client";

import { useState } from "react";
import Link from "next/link";
import { signIn } from "next-auth/react";
import {
  Brain,
  Github,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { FEATURES } from "@/lib/features";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const ENABLE_TEST_AUTH =
  process.env.NEXT_PUBLIC_ENABLE_TEST_AUTH === "true";
const TEST_USERS = ["junior_dev", "founder", "switcher"] as const;


export default function LoginPage() {
  const [testUser, setTestUser] = useState<string>("junior_dev");
  const [testPass, setTestPass] = useState("");

  return (
    <div className="flex min-h-screen flex-col items-center bg-muted/40 px-4 pt-[12vh] pb-12">
      <Card className="w-full max-w-[400px]">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <Brain className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-2xl text-primary">StewardMe</CardTitle>
          <CardDescription className="text-balance">
            AI steward that scans the world, learns from your journal, and
            tells you what matters next. Open-source and self-hosted.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Button
            variant="outline"
            className="w-full"
            onClick={() => signIn("github", { callbackUrl: "/home" })}
          >
            <Github className="mr-2 h-4 w-4" />
            Continue with GitHub
          </Button>
          <Button
            className="w-full"
            onClick={() => signIn("google", { callbackUrl: "/home" })}
          >
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </Button>
          {ENABLE_TEST_AUTH && (
            <>
              <div className="relative my-1">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs text-muted-foreground">
                  <span className="bg-card px-2">dev only</span>
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="test-username">Test account</Label>
                <select
                  id="test-username"
                  value={testUser}
                  onChange={(e) => setTestUser(e.target.value)}
                  className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                >
                  {TEST_USERS.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
                <Input
                  id="test-password"
                  type="password"
                  placeholder='password: "test"'
                  value={testPass}
                  onChange={(e) => setTestPass(e.target.value)}
                />
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() =>
                    signIn("credentials", {
                      username: testUser,
                      password: testPass,
                      callbackUrl: "/home",
                    })
                  }
                >
                  Sign in as {testUser}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <p className="mt-10 mb-4 text-xs font-medium uppercase tracking-wider text-muted-foreground">What you get</p>
      <div className="grid w-full max-w-[700px] grid-cols-1 gap-4 sm:grid-cols-2">
        {FEATURES.map(({ icon: Icon, title, description }) => (
          <div key={title} className="flex gap-3 rounded-xl border bg-card p-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10">
              <Icon className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">{title}</p>
              <p className="mt-0.5 text-xs text-muted-foreground leading-relaxed">
                {description}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 flex gap-3 text-xs text-muted-foreground">
        <Link href="/privacy" className="underline hover:text-foreground">Privacy Policy</Link>
        <span>&middot;</span>
        <Link href="/terms" className="underline hover:text-foreground">Terms of Service</Link>
      </div>
    </div>
  );
}
