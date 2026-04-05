<p align="center">
  <h1 align="center">📝 My Wiki</h1>
  <p align="center">
    <strong>LLM-powered Personal Knowledge Base</strong>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#usage">Usage</a> •
    <a href="#documentation">Documentation</a> •
    <a href="#contributing">Contributing</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  </p>
</p>

---

## What is My Wiki?

**My Wiki** is a personal knowledge management system powered by LLMs. Unlike traditional RAG systems that re-discover knowledge on every query, My Wiki maintains a **persistent, structured wiki** that compounds over time.

### The Problem with RAG

```
Traditional RAG:
  Upload files → Retrieve chunks → Generate answer
  Next question? Start over. No accumulation.
```

### Our Approach

```
My Wiki:
  New source → Extract knowledge → Integrate into wiki
  Next question? Search wiki. Knowledge compounds.
```

**Key insight**: Instead of retrieving from raw documents every time, the LLM builds and maintains a structured wiki. Knowledge is compiled once and kept current, not re-derived on every query.

---

## Features

- 🔄 **Ingest** — Automatically extract concepts, entities, and insights from articles, PDFs, transcripts
- 🔍 **Query** — Ask questions against your wiki with natural language
- 🏥 **Lint** — Health checks for contradictions, orphan pages, missing links
- 📊 **Status** — Track your knowledge base growth over time
- 🔗 **Bidirectional Links** — Concepts automatically linked both ways
- 📝 **Obsidian Compatible** — Works seamlessly with Obsidian for visualization

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Masongmx/my-wiki.git
cd my-wiki

# Install dependencies
pip install click pyyaml loguru openai
```

### Configuration

Create `config/kb.yaml`:

```yaml
knowledge_base:
  root: /path/to/your/knowledge-base
  
llm:
  provider: openai  # or bailian, anthropic, etc.
  model: gpt-4
  api_key: YOUR_API_KEY  # or set env var
  base_url: https://api.openai.com/v1  # optional
```

### Initialize

```bash
# Initialize your knowledge base
wiki init

# Ingest your first article
wiki ingest raw/articles/my-article.md

# Query your knowledge
wiki query "What is the main concept?"
```

---

## Usage

### Ingest (Process New Sources)

```bash
# Process a single file
wiki ingest raw/articles/article.md

# Process all files in a directory
wiki ingest raw/articles/

# Preview without writing
wiki ingest raw/articles/article.md --dry-run
```

**What happens during ingest:**
1. Read source content
2. Extract key insights → `wiki/sources/`
3. Extract concepts → `wiki/concepts/`
4. Extract entities → `wiki/entities/`
5. Build bidirectional links
6. Update `wiki/_index.md`
7. Log to `wiki/_meta/log.md`

### Query (Ask Questions)

```bash
# Ask a question
wiki query "What is Agent Operating System?"

# Save answer for future reference
wiki query "Compare Skill vs MCP" --save
```

**Question types supported:**
| Type | Example | Output |
|------|---------|--------|
| Definition | "What is X?" | Definition + key points |
| Comparison | "X vs Y?" | Comparison table |
| Relation | "How do X and Y relate?" | Relationship description |
| List | "What are the types of X?" | List with details |

### Lint (Health Check)

```bash
# Full health check
wiki lint

# Quick check (wiki only)
wiki lint --quick

# Check specific issues
wiki lint --orphans    # Orphan pages
wiki lint --outdated   # Outdated content
```

### Status (Statistics)

```bash
# View statistics
wiki status

# Show recent activity
wiki status --recent
```

---

## Architecture

```
knowledge-base/
├── raw/                  # Your source materials (read-only)
│   ├── articles/         # Articles
│   ├── pdfs/             # PDF documents
│   └── transcripts/      # Audio/video transcripts
│
├── wiki/                 # LLM-maintained structured content
│   ├── concepts/         # Concept pages (definitions)
│   ├── entities/         # Entity pages (people, projects, tools)
│   ├── sources/          # Source pages (summaries)
│   ├── outputs/          # Output pages (your analyses)
│   ├── _index.md         # Global index
│   └── _meta/
│       ├── log.md        # Operation log
│       └── lint-report.md
│
└── config/
    └── kb.yaml           # Configuration
```

### Three Layers

| Layer | Who Writes | Who Reads | Purpose |
|-------|------------|-----------|---------|
| `raw/` | You (curate) | LLM (read) | Source materials |
| `wiki/` | LLM (generate) | You (read) | Structured knowledge |
| `outputs/` | LLM (generate) | You (read) | Your analyses |

---

## Philosophy

### 6 Design Principles

1. **Raw is read-only** — Source materials stay untouched
2. **Wiki is LLM-written** — LLM maintains consistency
3. **Humans read wiki** — You don't edit wiki directly
4. **Every operation compounds** — Ingest results, query answers all persist
5. **Incremental updates** — New sources update existing pages
6. **Bidirectional links** — Concepts reference each other both ways

---

## Integration with Obsidian

My Wiki generates markdown files that work seamlessly with [Obsidian](https://obsidian.md):

1. Open Obsidian
2. Select your `knowledge-base` folder as vault
3. Browse `wiki/concepts/`, `wiki/entities/`, etc.
4. Click links to explore your knowledge graph
5. Use Graph View to visualize connections

---

## Examples

See `examples/demo-kb/` for a small example knowledge base with:
- Sample articles
- Generated concepts and entities
- Example queries and outputs

---

## Documentation

- [Getting Started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Ingest Guide](docs/ingest.md)
- [Query Guide](docs/query.md)
- [Lint Guide](docs/lint.md)
- [API Reference](docs/api.md)

---

## Roadmap

- [ ] Web UI for browsing wiki
- [ ] Vector search for large knowledge bases
- [ ] Multi-language support
- [ ] Import from Notion, Roam, etc.
- [ ] Export to static site

---

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

---

## Acknowledgments

Inspired by [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) methodology.

---

## License

[MIT License](LICENSE)