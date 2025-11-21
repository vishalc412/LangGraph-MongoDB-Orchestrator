import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage, Config, LLMProvider } from '../types';

interface AppState {
  // Configuration
  config: Config | null;
  isConfigOpen: boolean;
  setConfig: (config: Config) => void;
  setConfigOpen: (open: boolean) => void;

  // Messages
  messages: ChatMessage[];
  threadId: string | null;
  isLoading: boolean;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setThreadId: (id: string) => void;

  // Connection status
  isConnected: boolean;
  setConnected: (connected: boolean) => void;

  // Local settings (persisted)
  savedApiKey: string;
  savedProvider: LLMProvider;
  savedModel: string;
  setSavedApiKey: (key: string) => void;
  setSavedProvider: (provider: LLMProvider) => void;
  setSavedModel: (model: string) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Configuration
      config: null,
      isConfigOpen: false,
      setConfig: (config) => set({ config }),
      setConfigOpen: (isConfigOpen) => set({ isConfigOpen }),

      // Messages
      messages: [],
      threadId: null,
      isLoading: false,
      addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),
      clearMessages: () => set({ messages: [], threadId: null }),
      setLoading: (isLoading) => set({ isLoading }),
      setThreadId: (threadId) => set({ threadId }),

      // Connection status
      isConnected: false,
      setConnected: (isConnected) => set({ isConnected }),

      // Local settings (persisted)
      savedApiKey: '',
      savedProvider: 'openai',
      savedModel: 'gpt-4o-mini',
      setSavedApiKey: (savedApiKey) => set({ savedApiKey }),
      setSavedProvider: (savedProvider) => set({ savedProvider }),
      setSavedModel: (savedModel) => set({ savedModel }),
    }),
    {
      name: 'mongodb-agent-storage',
      partialize: (state) => ({
        savedApiKey: state.savedApiKey,
        savedProvider: state.savedProvider,
        savedModel: state.savedModel,
      }),
    }
  )
);
