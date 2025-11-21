import { useState, useEffect } from 'react';
import { X, Key, Database, Cpu, Save, Loader2, Eye, EyeOff } from 'lucide-react';
import { useStore } from '../hooks/useStore';
import { updateConfig, getConfig, checkHealth } from '../services/api';
import type { LLMProvider, ConfigUpdate } from '../types';
import { OPENAI_MODELS, OLLAMA_MODELS } from '../types';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const {
    savedApiKey,
    savedProvider,
    savedModel,
    setSavedApiKey,
    setSavedProvider,
    setSavedModel,
    setConfig,
    setConnected,
  } = useStore();

  const [provider, setProvider] = useState<LLMProvider>(savedProvider);
  const [apiKey, setApiKey] = useState(savedApiKey);
  const [model, setModel] = useState(savedModel);
  const [ollamaHost, setOllamaHost] = useState('http://localhost:11434');
  const [mongoUri, setMongoUri] = useState('mongodb://localhost:27017');
  const [database, setDatabase] = useState('sample_mflix');
  const [collection, setCollection] = useState('movies');
  const [temperature, setTemperature] = useState(0);

  const [isSaving, setIsSaving] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Load current config on open
  useEffect(() => {
    if (isOpen) {
      const loadConfig = async () => {
        try {
          const config = await getConfig();
          setProvider(config.provider as LLMProvider);
          setModel(config.model);
          setDatabase(config.mongodb_database);
          setCollection(config.mongodb_collection);
          if (config.ollama_host) {
            setOllamaHost(config.ollama_host);
          }
        } catch (err) {
          console.error('Failed to load config:', err);
        }
      };
      loadConfig();
    }
  }, [isOpen]);

  // Update model when provider changes
  useEffect(() => {
    if (provider === 'openai') {
      setModel(savedModel.startsWith('gpt') ? savedModel : 'gpt-4o-mini');
    } else {
      setModel(savedModel.startsWith('llama') || savedModel === 'mistral' ? savedModel : 'llama3.1');
    }
  }, [provider]);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const configUpdate: ConfigUpdate = {
        provider,
        model,
        temperature,
        database,
        collection,
      };

      if (provider === 'openai' && apiKey) {
        configUpdate.api_key = apiKey;
      }

      if (provider === 'ollama') {
        configUpdate.ollama_host = ollamaHost;
      }

      if (mongoUri) {
        configUpdate.mongodb_uri = mongoUri;
      }

      // Update config
      const newConfig = await updateConfig(configUpdate);
      setConfig(newConfig);

      // Save to local storage
      setSavedProvider(provider);
      setSavedModel(model);
      if (provider === 'openai' && apiKey) {
        setSavedApiKey(apiKey);
      }

      // Check health after update
      const health = await checkHealth();
      setConnected(health.mongodb_connected && health.llm_available);

      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const models = provider === 'openai' ? OPENAI_MODELS : OLLAMA_MODELS;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Error/Success Messages */}
          {error && (
            <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg text-sm">
              Settings saved successfully!
            </div>
          )}

          {/* LLM Provider Section */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Cpu className="h-5 w-5 text-gray-500" />
              <h3 className="font-medium">LLM Provider</h3>
            </div>

            <div className="space-y-3">
              <div className="flex gap-2">
                <button
                  onClick={() => setProvider('openai')}
                  className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                    provider === 'openai'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  OpenAI
                </button>
                <button
                  onClick={() => setProvider('ollama')}
                  className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
                    provider === 'ollama'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  Ollama (Local)
                </button>
              </div>

              {/* Model Selection */}
              <div>
                <label className="block text-sm text-gray-600 mb-1">Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {models.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* API Key (OpenAI only) */}
              {provider === 'openai' && (
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    <Key className="h-4 w-4 inline mr-1" />
                    API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Get your API key from{' '}
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-600 hover:underline"
                    >
                      OpenAI Dashboard
                    </a>
                  </p>
                </div>
              )}

              {/* Ollama Host */}
              {provider === 'ollama' && (
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Ollama Host</label>
                  <input
                    type="text"
                    value={ollamaHost}
                    onChange={(e) => setOllamaHost(e.target.value)}
                    placeholder="http://localhost:11434"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Make sure Ollama is running and model is pulled: <code>ollama pull {model}</code>
                  </p>
                </div>
              )}

              {/* Temperature */}
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Temperature: {temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full"
                />
                <p className="text-xs text-gray-500">
                  Lower = more deterministic, Higher = more creative
                </p>
              </div>
            </div>
          </div>

          {/* MongoDB Section */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Database className="h-5 w-5 text-gray-500" />
              <h3 className="font-medium">MongoDB Connection</h3>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Connection URI</label>
                <input
                  type="text"
                  value={mongoUri}
                  onChange={(e) => setMongoUri(e.target.value)}
                  placeholder="mongodb://localhost:27017"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Database</label>
                  <input
                    type="text"
                    value={database}
                    onChange={(e) => setDatabase(e.target.value)}
                    placeholder="sample_mflix"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Collection</label>
                  <input
                    type="text"
                    value={collection}
                    onChange={(e) => setCollection(e.target.value)}
                    placeholder="movies"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Settings
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
