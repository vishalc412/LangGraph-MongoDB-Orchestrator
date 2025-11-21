// Type definitions for MongoDB AI Agent UI

export type LLMProvider = 'openai' | 'ollama';

export interface Config {
  provider: LLMProvider;
  model: string;
  mongodb_database: string;
  mongodb_collection: string;
  api_key_configured: boolean;
  ollama_host?: string;
}

export interface ConfigUpdate {
  provider: LLMProvider;
  api_key?: string;
  model?: string;
  temperature?: number;
  mongodb_uri?: string;
  database?: string;
  collection?: string;
  ollama_host?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  query_info?: {
    query_type?: string;
    collection?: string;
  };
}

export interface ChatRequest {
  message: string;
  thread_id?: string;
}

export interface ChatResponse {
  response: string;
  thread_id: string;
  query_info?: {
    query_type?: string;
    collection?: string;
  };
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  mongodb_connected: boolean;
  llm_provider: string;
  llm_available: boolean;
  version: string;
  timestamp: string;
}

export interface ModelsResponse {
  openai_models: string[];
  ollama_models: string[];
}

export const OPENAI_MODELS = [
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Recommended)' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
];

export const OLLAMA_MODELS = [
  { value: 'llama3.1', label: 'Llama 3.1' },
  { value: 'llama3.2', label: 'Llama 3.2' },
  { value: 'mistral', label: 'Mistral' },
  { value: 'codellama', label: 'Code Llama' },
  { value: 'phi3', label: 'Phi-3' },
];
