import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Message, Conversation } from "@/types";

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;

  // Actions
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addConversation: (conversation: Conversation) => void;

  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  appendToLastMessage: (content: string) => void;

  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      conversations: [],
      currentConversation: null,
      messages: [],
      isLoading: false,
      isStreaming: false,

      setConversations: (conversations) => set({ conversations }),

      setCurrentConversation: (conversation) =>
        set({ currentConversation: conversation }),

      addConversation: (conversation) =>
        set((state) => ({
          conversations: [...state.conversations, conversation],
        })),

      setMessages: (messages) => set({ messages }),

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      updateMessage: (messageId, updates) =>
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === messageId ? { ...m, ...updates } : m
          ),
        })),

      appendToLastMessage: (content) =>
        set((state) => {
          const messages = [...state.messages];
          if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            messages[messages.length - 1] = {
              ...lastMessage,
              content: lastMessage.content + content,
            };
          }
          return { messages };
        }),

      setLoading: (isLoading) => set({ isLoading }),
      setStreaming: (isStreaming) => set({ isStreaming }),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: "chat-storage",
      partialize: (state) => ({
        conversations: state.conversations,
        currentConversation: state.currentConversation,
      }),
    }
  )
);
