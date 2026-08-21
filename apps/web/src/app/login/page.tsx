"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { useLogin } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [totpRequired, setTotpRequired] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const result = await login.mutateAsync({
        email,
        password,
        totp_code: totpRequired ? totpCode : undefined,
      });
      if (result.totp_required) {
        setTotpRequired(true);
        return;
      }
      router.push("/");
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.body === "object" && err.body && "detail" in err.body
            ? String((err.body as { detail: unknown }).detail)
            : "Login failed";
        toast.error(detail);
      } else {
        toast.error("Could not reach the server");
      }
    }
  }

  return (
    <div className="gradient-mesh-bg flex min-h-screen items-center justify-center px-4">
      <div className="glass-surface w-full max-w-sm rounded-2xl p-8 shadow-2xl shadow-black/40">
        <div className="mb-8 flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-[oklch(0.6_0.18_300)] text-sm font-heading font-bold text-primary-foreground">
            21
          </span>
          <span className="font-heading text-base font-semibold tracking-tight">
            The21OS <span className="text-muted-foreground font-normal">— AI Ads</span>
          </span>
        </div>

        <h1 className="font-heading text-2xl font-semibold tracking-tight">Welcome back</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Private control platform — sign in to continue.
        </p>

        <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={totpRequired}
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={totpRequired}
              required
            />
          </div>
          {totpRequired && (
            <div className="flex flex-col gap-2">
              <Label htmlFor="totp">Authentication code</Label>
              <Input
                id="totp"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                autoFocus
                required
              />
            </div>
          )}
          <Button
            type="submit"
            className="mt-2 bg-gradient-to-r from-primary to-[oklch(0.6_0.18_300)] text-primary-foreground hover:opacity-90"
            disabled={login.isPending}
          >
            {login.isPending ? "Signing in…" : totpRequired ? "Verify" : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}
