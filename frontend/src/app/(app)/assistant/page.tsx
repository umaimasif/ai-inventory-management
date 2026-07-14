"use client";

import { useRef, useState, type FormEvent } from "react";

import { PageHeader } from "@/components/app-shell";
import { ApiError } from "@/lib/api";
import { agents } from "@/lib/resources";
import type { ChatResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  text: string;
  meta?: ChatResponse;
}

const SUGGESTIONS = [
  "What should I order today?",
  "Which products should I discount?",
  "Which customers spend the most?",
  "Why are sales down?",
  "What sold the most this month?",
  "What products are often bought together?",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [showFacts, setShowFacts] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function send(question: string) {
    if (!question.trim() || busy) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    try {
      const res = await agents.ask(question);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: res.answer, meta: res },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text:
            err instanceof ApiError
              ? `Error: ${err.message}`
              : "Something went wrong.",
        },
      ]);
    } finally {
      setBusy(false);
      requestAnimationFrame(() =>
        scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight),
      );
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="AI Assistant"
        subtitle="Ask about your business — answers come from your real data"
      />

      {messages.length === 0 && (
        <div className="mb-4">
          <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
            Try asking:
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-full border border-gray-300 px-3 py-1.5 text-sm text-gray-700 transition hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div
        ref={scrollRef}
        className="mb-4 flex-1 space-y-4 overflow-y-auto rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-950"
      >
        {messages.length === 0 ? (
          <p className="py-12 text-center text-sm text-gray-400">
            No messages yet. Ask a question to get started.
          </p>
        ) : (
          messages.map((m, i) => (
            <div
              key={i}
              className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                  m.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100"
                }`}
              >
                <p className="whitespace-pre-wrap">{m.text}</p>
                {m.meta && (
                  <div className="mt-2 flex items-center gap-2 border-t border-black/10 pt-2 text-xs dark:border-white/10">
                    <span className="rounded-full bg-black/10 px-2 py-0.5 dark:bg-white/10">
                      {m.meta.intent}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400">
                      {m.meta.llm_used ? "LLM-phrased" : "grounded template"}
                    </span>
                    <button
                      onClick={() => setShowFacts(showFacts === i ? null : i)}
                      className="text-indigo-600 hover:underline dark:text-indigo-400"
                    >
                      {showFacts === i ? "hide data" : "show data"}
                    </button>
                  </div>
                )}
                {m.meta && showFacts === i && (
                  <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-black/5 p-2 text-xs dark:bg-white/5">
                    {JSON.stringify(m.meta.grounded_on, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          ))
        )}
        {busy && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-gray-100 px-4 py-2.5 text-sm text-gray-500 dark:bg-gray-800 dark:text-gray-400">
              Thinking…
            </div>
          </div>
        )}
      </div>

      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white transition hover:bg-indigo-500 disabled:opacity-50"
        >
          Send
        </button>
      </form>
      <p className="mt-2 text-center text-xs text-gray-400">
        Answers are grounded in your database. Set GROQ_API_KEY to enable natural
        language phrasing.
      </p>
    </div>
  );
}
