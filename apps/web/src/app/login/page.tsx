"use client";

import { Eye, EyeOff, Lock, LogIn, Mail, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { useLogin } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [totpCode, setTotpCode] = useState("");
  const [totpRequired, setTotpRequired] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const result = await login.mutateAsync({
        email,
        password,
        remember,
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
      <div className="glass-surface w-full max-w-sm rounded-2xl p-8 shadow-[0_0_0_1px_oklch(0.68_0.18_258/25%),0_0_60px_-10px_oklch(0.6_0.2_290/45%),0_20px_60px_-10px_rgb(0_0_0/60%)]">
        <div className="mb-8 flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-[oklch(0.6_0.18_300)] text-sm font-heading font-bold text-primary-foreground shadow-[0_0_16px_-2px_oklch(0.68_0.18_258/60%)]">
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
            <Label htmlFor="email">Email address</Label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={totpRequired}
                required
                className="pl-9"
              />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={totpRequired}
                required
                className="pl-9 pr-9"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
          </div>

          {totpRequired ? (
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
          ) : (
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox checked={remember} onCheckedChange={(v) => setRemember(v === true)} />
              Remember me
            </label>
          )}

          <Button
            type="submit"
            className="mt-2 gap-2 bg-gradient-to-r from-primary to-[oklch(0.6_0.18_300)] text-primary-foreground hover:opacity-90"
            disabled={login.isPending}
          >
            <LogIn className="size-4" />
            {login.isPending ? "Signing in…" : totpRequired ? "Verify" : "Sign in"}
          </Button>
        </form>

        <div className="mt-6 flex items-center gap-2 border-t border-border pt-5 text-xs text-muted-foreground">
          <ShieldCheck className="size-3.5" />
          Secure &amp; private — single-operator access only
        </div>
      </div>
    </div>
  );
}
