import { useState, useRef, useEffect, FormEvent } from 'react';
import { Send, Trash2, User, Bot, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useStore } from '../hooks/useStore';
import { sendMessage, clearChat } from '../services/api';
import type { ChatMessage } from '../types';

function ChatInterface() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    addMessage,
    clearMessages,
    isLoading,
    setLoading,
    threadId,
    setThreadId,
    isConnected,
  } = useStore();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput('');
    setLoading(true);

    try {
      const response = await sendMessage({
        message: userMessage.content,
        thread_id: threadId || undefined,
      });

      setThreadId(response.thread_id);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp),
        query_info: response.query_info,
      };

      addMessage(assistantMessage);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your configuration and try again.`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (threadId) {
      try {
        await clearChat(threadId);
      } catch (error) {
        console.error('Failed to clear chat:', error);
      }
    }
    clearMessages();
  };

  return (
    <div className="flex-1 flex flex-col bg-white border-x border-gray-200">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">
              Welcome to MongoDB AI Agent
            </h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Ask questions about your MongoDB data in natural language. For example:
            </p>
            <div className="mt-4 space-y-2">
              {[
                'What were the top-rated movies in 2020?',
                "What's the average rating by genre?",
                'Show me action movies with rating above 8',
                'How many movies were released each year?',
              ].map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => setInput(suggestion)}
                  className="block mx-auto px-4 py-2 text-sm text-green-600 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-green-600" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {message.role === 'assistant' ? (
                  <div className="markdown-content prose prose-sm max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p>{message.content}</p>
                )}

                {message.query_info && (
                  <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                    Query: {message.query_info.query_type} on {message.query_info.collection}
                  </div>
                )}
              </div>

              {message.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                  <User className="h-5 w-5 text-white" />
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
              <Bot className="h-5 w-5 text-green-600" />
            </div>
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleClear}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors"
              title="Clear chat"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          )}

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isConnected
                ? 'Ask a question about your MongoDB data...'
                : 'Configure your settings first...'
            }
            disabled={!isConnected || isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading || !isConnected}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="h-4 w-4" />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;
