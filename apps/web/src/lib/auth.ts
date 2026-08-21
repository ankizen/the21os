"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";
import type { LoginResponse, User } from "@/lib/types";

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: () => api.get<User>("/api/auth/me"),
    retry: false,
    // A 401 is an expected "not logged in" state here, not a transient error.
    throwOnError: (error) => !(error instanceof ApiError && error.status === 401),
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { email: string; password: string; totp_code?: string }) =>
      api.post<LoginResponse>("/api/auth/login", body),
    onSuccess: (data) => {
      if (data.user) {
        queryClient.setQueryData(["auth", "me"], data.user);
      }
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/api/auth/logout"),
    onSuccess: () => {
      queryClient.setQueryData(["auth", "me"], null);
    },
  });
}
