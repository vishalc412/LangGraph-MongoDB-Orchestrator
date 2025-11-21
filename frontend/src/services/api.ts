import axios from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  Config,
  ConfigUpdate,
  HealthStatus,
  ModelsResponse
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export async function checkHealth(): Promise<HealthStatus> {
  const response = await api.get<HealthStatus>('/health');
  return response.data;
}

// Configuration
export async function getConfig(): Promise<Config> {
  const response = await api.get<Config>('/config');
  return response.data;
}

export async function updateConfig(config: ConfigUpdate): Promise<Config> {
  const response = await api.post<Config>('/config', config);
  return response.data;
}

export async function getModels(): Promise<ModelsResponse> {
  const response = await api.get<ModelsResponse>('/models');
  return response.data;
}

// Chat
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat', request);
  return response.data;
}

export async function clearChat(threadId: string): Promise<void> {
  await api.delete(`/chat/${threadId}`);
}

// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

export default api;
