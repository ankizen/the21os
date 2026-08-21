"use client";

import { useMutation } from "@tanstack/react-query";
import { Bot, Loader2, Send, User as UserIcon, Wrench } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/page-header";
import { api, ApiError } from "@/lib/api";
import { describeTool } from "@/lib/command-center-format";
import type { CommandCenterAskResponse, CommandCenterMessage, CommandCenterTrace } from "@/lib/types";

interface Turn {
  role: "user" | "assistant";
  text: string;
  trace?: CommandCenterTrace[];
  error?: boolean;
}

export default function CommandCenterPage() {
  const [conversation, setConversation] = useState<CommandCenterMessage[]>([]);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () =>
    queueMicrotask(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }));

  const ask = useMutation({
    mutationFn: (messages: CommandCenterMessage[]) =>
      api.post<CommandCenterAskResponse>("/api/command-center/ask", { messages }),
    onSuccess: (response) => {
      setConversation(response.messages);
      setTurns((prev) => [...prev, { role: "assistant", text: response.reply, trace: response.trace }]);
      scrollToBottom();
    },
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof err.body === "object" && err.body && "detail" in err.body
          ? String((err.body as { detail: unknown }).detail)
          : "Could not reach the server";
      setTurns((prev) => [...prev, { role: "assistant", text: detail, error: true }]);
      scrollToBottom();
    },
  });

  function send() {
    const text = input.trim();
    if (!text || ask.isPending) return;
    const nextMessages = [...conversation, { role: "user" as const, content: text }];
    setConversation(nextMessages);
    setTurns((prev) => [...prev, { role: "user", text }]);
    setInput("");
    ask.mutate(nextMessages);
    scrollToBottom();
  }

  return (
    <>
      <PageHeader
        title="AI Command Center"
        description={'Ask Claude about your campaigns — e.g. "Which ads are wasting money?"'}
      />
      <div className="flex h-[calc(100vh-14rem)] flex-col overflow-hidden rounded-xl ring-1 ring-foreground/10">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {turns.length === 0 && !ask.isPending && (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
              <Bot className="size-8 text-muted-foreground" />
              <p className="max-w-sm text-sm text-muted-foreground">
                Ask about performance, correlate Meta spend with GA4, or ask Claude to pause/resume ads and
                adjust budgets — every write still goes through your operational mode and safety ceilings.
              </p>
            </div>
          )}
          {turns.map((turn, i) => (
            <ChatTurn key={i} turn={turn} />
          ))}
          {ask.isPending && (
            <div className="flex items-center gap-2 pl-8 text-sm text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" />
              Thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <div className="glass-surface flex items-center gap-2 border-t p-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Ask Claude…"
            disabled={ask.isPending}
          />
          <Button size="icon" onClick={send} disabled={ask.isPending || !input.trim()}>
            <Send className="size-4" />
          </Button>
        </div>
      </div>
    </>
  );
}

function ChatTurn({ turn }: { turn: Turn }) {
  const isUser = turn.role === "user";
  return (
    <div className={`flex gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="mt-1 flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
          <Bot className="size-3.5" />
        </div>
      )}
      <div className="max-w-[75%] space-y-2">
        <div
          className={`rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ${
            isUser
              ? "bg-primary text-primary-foreground"
              : turn.error
                ? "bg-destructive/10 text-destructive"
                : "bg-card ring-1 ring-foreground/10"
          }`}
        >
          {turn.text}
        </div>
        {turn.trace && turn.trace.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {turn.trace.map((t, i) => (
              <ToolChip key={i} entry={t} />
            ))}
          </div>
        )}
      </div>
      {isUser && (
        <div className="mt-1 flex size-6 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
          <UserIcon className="size-3.5" />
        </div>
      )}
    </div>
  );
}

function ToolChip({ entry }: { entry: CommandCenterTrace }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="text-xs">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 rounded-full border border-border bg-muted px-2 py-0.5 text-muted-foreground transition-colors hover:text-foreground"
      >
        <Wrench className="size-3" />
        {describeTool(entry.tool)}
      </button>
      {open && (
        <pre className="mt-1 max-w-md overflow-x-auto rounded-lg bg-muted p-2 text-[0.7rem] text-muted-foreground">
          {JSON.stringify({ input: entry.input, result: entry.result }, null, 2)}
        </pre>
      )}
    </div>
  );
}
