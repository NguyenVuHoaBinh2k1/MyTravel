"use client";

import { Message } from "@/types";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={cn(
        "flex w-full mb-4",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-3",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted",
          isAssistant && "border border-border"
        )}
      >
        {/* Agent type badge */}
        {isAssistant && message.agent_type && (
          <div className="text-xs font-medium text-muted-foreground mb-1 capitalize">
            {getAgentLabel(message.agent_type)}
          </div>
        )}

        {/* Message content */}
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>

        {/* Timestamp */}
        <div
          className={cn(
            "text-xs mt-2",
            isUser ? "text-primary-foreground/70" : "text-muted-foreground"
          )}
        >
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  );
}

function getAgentLabel(agentType: string): string {
  const labels: Record<string, string> = {
    accommodation: "Khach san",
    food: "Am thuc",
    transport: "Di chuyen",
    itinerary: "Lich trinh",
    budget: "Ngan sach",
    general: "Tro ly",
    error: "Loi",
  };
  return labels[agentType] || agentType;
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default ChatMessage;
