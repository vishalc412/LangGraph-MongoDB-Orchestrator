# MongoDB AI Agent with LangGraph

> Production-ready AI agent system for natural language MongoDB queries using LangGraph orchestration

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Overview

MongoDB AI Agent enables users to interact with MongoDB databases using natural language questions. Built with LangGraph for robust workflow orchestration, it supports multiple LLM providers, conversation memory, and complex aggregation queries.

### Key Features

- ✅ **Natural Language Queries**: Ask questions in plain English
- 🔄 **LangGraph Orchestration**: Production-grade state management
- 🤖 **Multi-LLM Support**: OpenAI GPT-4o-mini, Llama via Ollama, extensible
- 💾 **Memory Checkpointing**: Persistent conversation history
- 📊 **Complex Aggregations**: Grouping, filtering, sorting, calculations
- 🏗️ **Extensible Architecture**: Clean, modular design
- 🛡️ **Production-Ready**: Error handling, logging, monitoring, testing

## ⚡ Quick Start

```bash
# Install
git clone https://github.com/yourusername/mongodb-ai-agent.git
cd mongodb-ai-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and MONGODB_URI

# Setup MongoDB with sample data
python scripts/setup_mongodb.py

# Run
python -m mongodb_agent.main chat
```

## 📖 Usage

### Interactive Chat

```bash
$ python -m mongodb_agent.main chat

You: What were the top-rated movies in 2020?
Assistant: Here are the top-rated movies from 2020:
1. Soul (8.1 rating)
2. Tenet (7.4 rating)
...
```

### Single Query

```bash
$ python -m mongodb_agent.main query "What's the average rating by genre?"
```

### With Different Provider

```bash
$ python -m mongodb_agent.main chat --provider ollama --collection users
```

## 🏗️ Architecture

```
┌─────────────┐
│   User CLI  │
└──────┬──────┘
       │
       v
┌──────────────────┐
│  LangGraph       │
│  Workflow        │
│                  │
│  ┌──────────┐   │
│  │Get Schema│   │
│  └─────┬────┘   │
│        │        │
│  ┌─────v──────┐ │
│  │Generate    │ │
│  │Query       │ │
│  └─────┬──────┘ │
│        │        │
│  ┌─────v──────┐ │
│  │Execute     │ │
│  │Query       │ │
│  └─────┬──────┘ │
│        │        │
│  ┌─────v──────┐ │
│  │Format      │ │
│  │Response    │ │
│  └────────────┘ │
└────┬───────┬────┘
     │       │
     v       v
┌──────┐ ┌────────┐
│  LLM │ │MongoDB │
└──────┘ └────────┘
```

### Components

- **Config**: Environment-based configuration management
- **Providers**: LLM provider abstraction (OpenAI, Ollama, extensible)
- **Database**: MongoDB client with connection pooling
- **Agents**: LangGraph state machine, nodes, workflow orchestration
- **Prompts**: Few-shot examples and templates
- **Utils**: Logging, retry logic, formatting

## 📝 Configuration

Edit `.env` file:

```env
# LLM Provider
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=sample_mflix
MONGODB_COLLECTION=movies

# Checkpointer
CHECKPOINTER_TYPE=sqlite
CHECKPOINTER_SQLITE_PATH=./data/checkpoints.db
```

See `.env.example` for all options.

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/mongodb_agent

# Specific test file
pytest tests/test_agents.py

# Test connection
python -m mongodb_agent.main test-connection
```

## 🚀 Deployment

### Docker

```bash
# Build
docker build -t mongodb-ai-agent:latest .

# Run
docker-compose up -d
```

### Cloud Platforms

See `docs/deployment/` for detailed guides:

- AWS (ECS, Lambda)
- Azure (Container Instances, Functions)
- GCP (Cloud Run, Functions)

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment/README.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

```bash
# Setup development environment
git clone <your-fork>
cd mongodb-ai-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/ --fix

# Type check
mypy src/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [OpenAI](https://openai.com/) and [Ollama](https://ollama.ai/)
- Database: [MongoDB](https://www.mongodb.com/)

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourusername/mongodb-ai-agent/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/mongodb-ai-agent/discussions)
- Email: support@example.com

---

**Made with ❤️ by AI Agent Development Team**
