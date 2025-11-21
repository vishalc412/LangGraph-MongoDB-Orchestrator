# MongoDB AI Agent - React UI

Modern React frontend for the MongoDB AI Agent, providing a beautiful chat interface with model selection and configuration options.

## Features

- **Chat Interface**: Clean, intuitive chat UI for natural language queries
- **Model Selection**: Choose between OpenAI models (GPT-4o-mini, GPT-4o) or Ollama models (Llama, Mistral)
- **API Key Configuration**: Securely configure your OpenAI API key
- **MongoDB Settings**: Configure database and collection to query
- **Real-time Status**: See connection status for MongoDB and LLM
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Ready**: Built with Tailwind CSS for easy theming

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Zustand** - Lightweight state management
- **Axios** - HTTP client
- **Lucide React** - Beautiful icons
- **React Markdown** - Render markdown responses

## Quick Start

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn
- Backend API running (see main README)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`.

### Build for Production

```bash
# Build optimized bundle
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ChatInterface.tsx    # Main chat UI
│   │   └── SettingsModal.tsx    # Settings dialog
│   ├── hooks/               # Custom hooks
│   │   └── useStore.ts          # Zustand store
│   ├── services/            # API services
│   │   └── api.ts               # API client
│   ├── types/               # TypeScript types
│   │   └── index.ts             # Type definitions
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── package.json             # Dependencies
├── vite.config.ts           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
└── tsconfig.json            # TypeScript configuration
```

## Configuration

### API Proxy

The development server proxies `/api` requests to `http://localhost:8000` (backend server). Configure this in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

### Environment Variables

Create `.env.local` for local overrides:

```env
VITE_API_URL=http://localhost:8000
```

## Usage Guide

### 1. Start Backend Server

```bash
# From project root
uvicorn mongodb_agent.api.server:app --reload
```

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

### 3. Configure Settings

1. Click **Settings** button in the header
2. Select your LLM provider (OpenAI or Ollama)
3. Enter your API key (for OpenAI)
4. Configure MongoDB connection
5. Click **Save Settings**

### 4. Start Chatting

Ask questions in natural language:

- "What were the top-rated movies in 2020?"
- "What's the average rating by genre?"
- "Show me action movies with rating above 8"
- "How many movies were released each year?"

## Customization

### Styling

Modify `tailwind.config.js` to customize colors, fonts, and other design tokens:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom primary color
      },
    },
  },
},
```

### Adding New Features

1. **New Components**: Add to `src/components/`
2. **State Management**: Extend `src/hooks/useStore.ts`
3. **API Endpoints**: Add to `src/services/api.ts`
4. **Types**: Define in `src/types/index.ts`

## Development

### Linting

```bash
npm run lint
```

### Type Checking

```bash
npx tsc --noEmit
```

## Troubleshooting

### API Connection Failed

1. Ensure backend is running on `http://localhost:8000`
2. Check CORS configuration in backend
3. Verify proxy settings in `vite.config.ts`

### Build Errors

1. Clear node_modules: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf node_modules/.vite`

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add my feature"`
4. Push to branch: `git push origin feature/my-feature`
5. Open Pull Request

## License

MIT License - see main LICENSE file for details.
