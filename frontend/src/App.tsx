import { useEffect, useState } from 'react';
import { Settings, Database, MessageSquare, AlertCircle, CheckCircle2 } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import SettingsModal from './components/SettingsModal';
import { useStore } from './hooks/useStore';
import { checkHealth, getConfig } from './services/api';

function App() {
  const { isConfigOpen, setConfigOpen, setConfig, setConnected, isConnected } = useStore();
  const [healthStatus, setHealthStatus] = useState<{
    mongodb: boolean;
    llm: boolean;
  }>({ mongodb: false, llm: false });
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const initialize = async () => {
      try {
        // Check health status
        const health = await checkHealth();
        setHealthStatus({
          mongodb: health.mongodb_connected,
          llm: health.llm_available,
        });
        setConnected(health.mongodb_connected && health.llm_available);

        // Get current config
        const config = await getConfig();
        setConfig(config);

        // Open settings if not configured
        if (!config.api_key_configured && config.provider === 'openai') {
          setConfigOpen(true);
        }
      } catch (error) {
        console.error('Failed to initialize:', error);
        setConnected(false);
      } finally {
        setIsInitializing(false);
      }
    };

    initialize();
    // Poll health every 30 seconds
    const interval = setInterval(initialize, 30000);
    return () => clearInterval(interval);
  }, [setConfig, setConfigOpen, setConnected]);

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to MongoDB AI Agent...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="h-8 w-8 text-green-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">MongoDB AI Agent</h1>
              <p className="text-xs text-gray-500">Natural language queries powered by AI</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Status Indicators */}
            <div className="flex items-center gap-3 text-sm">
              <div className="flex items-center gap-1">
                {healthStatus.mongodb ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                )}
                <span className={healthStatus.mongodb ? 'text-green-600' : 'text-red-600'}>
                  MongoDB
                </span>
              </div>
              <div className="flex items-center gap-1">
                {healthStatus.llm ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                )}
                <span className={healthStatus.llm ? 'text-green-600' : 'text-yellow-600'}>
                  LLM
                </span>
              </div>
            </div>

            {/* Settings Button */}
            <button
              onClick={() => setConfigOpen(true)}
              className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <Settings className="h-4 w-4" />
              <span className="text-sm font-medium">Settings</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        {!isConnected && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 m-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <strong>Configuration Required:</strong> Please configure your API key and MongoDB
                  connection in Settings to start using the agent.
                </p>
              </div>
            </div>
          </div>
        )}

        <ChatInterface />
      </main>

      {/* Settings Modal */}
      <SettingsModal isOpen={isConfigOpen} onClose={() => setConfigOpen(false)} />
    </div>
  );
}

export default App;
