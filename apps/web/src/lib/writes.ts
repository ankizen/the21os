"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api, ApiError } from "@/lib/api";

export interface WriteResponse {
  status: "executed" | "dry_run" | "pending_approval" | "rejected";
  result: Record<string, unknown> | null;
  approval_id: string | null;
  reason: string | null;
}

function announce(response: WriteResponse) {
  switch (response.status) {
    case "executed":
      toast.success("Done");
      break;
    case "dry_run":
      toast.info("DRY_RUN — validated, not sent to Meta", {
        description: "Switch modes in Rules to actually execute writes.",
      });
      break;
    case "pending_approval":
      toast.info("Queued for approval", { description: "Review it on the Actions page." });
      break;
    case "rejected":
      toast.error("Rejected", { description: response.reason ?? undefined });
      break;
  }
}

/** POSTs/PATCHes a write endpoint, announces the pipeline's real outcome via
 * toast, and invalidates the given query keys so tables refresh. */
export function useWriteAction(
  path: string | ((vars: Record<string, unknown>) => string),
  options?: { method?: "POST" | "PATCH"; invalidate?: unknown[][] },
) {
  const queryClient = useQueryClient();
  const method = options?.method ?? "POST";

  return useMutation({
    mutationFn: async (vars: Record<string, unknown> = {}) => {
      const url = typeof path === "function" ? path(vars) : path;
      const fn = method === "PATCH" ? api.patch : api.post;
      return fn<WriteResponse>(url, vars);
    },
    onSuccess: (response) => {
      announce(response);
      for (const key of options?.invalidate ?? []) {
        queryClient.invalidateQueries({ queryKey: key });
      }
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        const detail =
          typeof err.body === "object" && err.body && "detail" in err.body
            ? String((err.body as { detail: unknown }).detail)
            : "Request failed";
        toast.error(detail);
      } else {
        toast.error("Could not reach the server");
      }
    },
  });
}
