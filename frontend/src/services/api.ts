import type { ChatResponse } from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export async function sendChatMessage(
  userInput: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_input: userInput }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
