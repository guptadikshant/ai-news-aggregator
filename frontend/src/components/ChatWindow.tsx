import { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType } from "../types";
import ChatMessage from "./ChatMessage";
import LoadingIndicator from "./LoadingIndicator";

interface Props {
  messages: ChatMessageType[];
  loading: boolean;
}

export default function ChatWindow({ messages, loading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <main className="flex-1 overflow-y-auto px-4 py-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center py-24 text-center text-gray-400">
            <p className="text-lg font-medium">What news are you looking for?</p>
            <p className="mt-1 text-sm">
              Ask about any topic — AI, tech, finance, sports, and more.
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {loading && <LoadingIndicator />}
        <div ref={bottomRef} />
      </div>
    </main>
  );
}
