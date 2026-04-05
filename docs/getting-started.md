# Getting Started

This guide will help you set up My Wiki in 5 minutes.

## Prerequisites

- Python 3.8+
- An LLM API key (OpenAI, Anthropic, or compatible)

## Installation

```bash
# Clone the repository
git clone https://github.com/Masongmx/my-wiki.git
cd my-wiki

# Install dependencies
pip install click pyyaml loguru openai
```

## Configuration

1. Copy the example config:

```bash
mkdir -p config
cp config/kb.yaml.example config/kb.yaml
```

2. Edit `config/kb.yaml`:

```yaml
knowledge_base:
  root: /path/to/your/knowledge-base

llm:
  provider: openai
  model: gpt-4o-mini
  # Option 1: Set API key in config
  api_key: sk-your-api-key
  # Option 2: Use environment variable
  # export OPENAI_API_KEY=sk-xxx
```

## Initialize

```bash
# Create directory structure
wiki init
```

This creates:
```
knowledge-base/
├── raw/
│   ├── articles/
│   ├── pdfs/
│   └── transcripts/
└── wiki/
    ├── concepts/
    ├── entities/
    ├── sources/
    ├── outputs/
    └── _meta/
```

## Your First Ingest

1. Save an article to `raw/articles/my-first-article.md`

2. Run:

```bash
wiki ingest raw/articles/my-first-article.md
```

3. Check the results:

```bash
# View generated concepts
ls wiki/concepts/

# View generated sources
ls wiki/sources/

# View index
cat wiki/_index.md
```

## Your First Query

```bash
wiki query "What is the main topic of my first article?"
```

## Next Steps

- [Configuration Guide](configuration.md) — Customize behavior
- [Ingest Guide](ingest.md) — Learn about the ingest process
- [Query Guide](query.md) — Master different query types
- [Obsidian Integration](obsidian.md) — Visualize your knowledge graph