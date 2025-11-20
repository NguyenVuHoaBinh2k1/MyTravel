"use client";

import { useEffect, useRef, useState } from "react";
import { useChatStore } from "@/stores/chatStore";
import { chatApi, conversationsApi } from "@/lib/api";
import { Message } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { ChatSuggestions } from "./ChatSuggestions";
import { ChatInput } from "./ChatInput";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ChatInterfaceProps {
  tripId?: number;
  conversationId?: number;
  title?: string;
}

export function ChatInterface({
  tripId,
  conversationId: initialConversationId,
  title = "Tro ly du lich",
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [conversationId, setConversationId] = useState<number | undefined>(
    initialConversationId
  );
  const [suggestions, setSuggestions] = useState<string[]>([
    "Tim khach san",
    "Goi y mon an",
    "Lap lich trinh",
    "Tinh ngan sach",
  ]);

  const {
    messages,
    isLoading,
    setMessages,
    addMessage,
    setLoading,
  } = useChatStore();

  // Load existing messages if conversationId is provided
  useEffect(() => {
    const loadMessages = async () => {
      if (conversationId) {
        try {
          const existingMessages = await conversationsApi.getMessages(
            conversationId.toString()
          );
          setMessages(existingMessages);
        } catch (error) {
          console.error("Failed to load messages:", error);
        }
      } else {
        setMessages([]);
      }
    };

    loadMessages();
  }, [conversationId, setMessages]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Create optimistic user message
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId?.toString() || "",
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    addMessage(userMessage);
    setLoading(true);
    setSuggestions([]);

    try {
      // Send message to API
      const response = await chatApi.sendMessage(
        content,
        tripId,
        conversationId
      );

      // Update conversation ID if this is a new conversation
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: response.message.id.toString(),
        conversation_id: response.conversation_id.toString(),
        role: "assistant",
        content: response.message.content,
        agent_type: response.agent_type,
        metadata: response.message.metadata,
        created_at: response.message.created_at,
      };

      addMessage(assistantMessage);

      // Update suggestions
      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      } else {
        setSuggestions([
          "Tim khach san",
          "Goi y mon an",
          "Lap lich trinh",
          "Tinh ngan sach",
        ]);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        conversation_id: conversationId?.toString() || "",
        role: "assistant",
        content: "Xin loi, co loi xay ra. Vui long thu lai.",
        agent_type: "error",
        created_at: new Date().toISOString(),
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionSelect = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-muted-foreground">
                <p className="text-lg font-medium mb-2">Xin chao!</p>
                <p className="text-sm">
                  Toi la tro ly du lich cua ban. Hay hoi toi bat cu dieu gi
                  ve chuyen di cua ban.
                </p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex justify-start mb-4">
                  <div className="bg-muted rounded-lg px-4 py-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Suggestions */}
        <ChatSuggestions
          suggestions={suggestions}
          onSelect={handleSuggestionSelect}
          disabled={isLoading}
        />

        {/* Input */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={isLoading}
          placeholder="Nhap cau hoi ve chuyen di cua ban..."
        />
      </CardContent>
    </Card>
  );
}

export default ChatInterface;
