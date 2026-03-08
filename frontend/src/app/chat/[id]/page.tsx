"use client";

import { useMutation } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import type { FormEvent, ReactElement } from "react";
import { useEffect, useRef, useState } from "react";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Button } from "@/components/ui/button";
import { chatWithDocument } from "@/services/api";
import { ChatResponse } from "@/types/document";

interface Message {
  role: "user" | "assistant";
  text: string;
}

export default function ChatPage(): ReactElement {
  const params = useParams<{ id: string }>();
  const documentId = params.id;
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { mutate: ask, isPending } = useMutation({
    mutationFn: (question: string) => chatWithDocument(documentId, question),
    onSuccess: (data: ChatResponse) => {
      setMessages((prev) => [...prev, { role: "assistant", text: data.answer }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error al consultar el documento. ¿Está indexado?" },
      ]);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isPending) return;
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    ask(question);
  }

  return (
    <ProtectedRoute>
      <main className="flex min-h-[calc(100vh-57px)] flex-col bg-background">
        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-6">
          <h1 className="mb-4 text-xl font-semibold">Chat con documento</h1>

          {/* Message list */}
          <div className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-xl border bg-card p-4 shadow-sm">
            {messages.length === 0 && (
              <p className="m-auto text-sm text-muted-foreground">
                Haz una pregunta sobre el documento. Asegúrate de haber hecho clic en &quot;Indexar&quot; primero.
              </p>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${msg.role === "user"
                  ? "ml-auto bg-blue-600 text-white"
                  : "bg-muted text-foreground"
                  }`}
              >
                {msg.text}
              </div>
            ))}
            {isPending && (
              <div className="max-w-[85%] rounded-2xl bg-muted px-4 py-2 text-sm text-muted-foreground">
                Pensando...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
            <input
              className="flex-1 rounded-lg border bg-background px-4 py-2 text-sm shadow-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="Escribe tu pregunta..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isPending}
            />
            <Button type="submit" disabled={isPending || !input.trim()}>
              Enviar
            </Button>
          </form>
        </div>
      </main>
    </ProtectedRoute>
  );
}
