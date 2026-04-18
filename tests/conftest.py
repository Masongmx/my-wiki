"""pytest configuration and shared fixtures"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime


@pytest.fixture
def mock_kb_root(tmp_path):
    """Create a temporary knowledge base root for testing"""
    kb_root = tmp_path / "kb"
    kb_root.mkdir()

    # Create basic directory structure
    (kb_root / "wiki").mkdir()
    (kb_root / "wiki" / "_meta").mkdir()
    (kb_root / "wiki" / "sources").mkdir()
    (kb_root / "wiki" / "concepts").mkdir()
    (kb_root / "wiki" / "entities").mkdir()
    (kb_root / "wiki" / "outputs").mkdir()
    (kb_root / "wiki" / "articles").mkdir()
    (kb_root / "raw").mkdir()
    (kb_root / "raw" / "articles").mkdir()
    (kb_root / "raw" / "pdfs").mkdir()
    (kb_root / "raw" / "transcripts").mkdir()
    (kb_root / "config").mkdir()

    return kb_root


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a mock config file"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_file = config_dir / "kb.yaml"
    config_content = """
knowledge_base:
  root: "{kb_root}"
  data_dir: "{kb_root}"

lint:
  exclude_dirs:
    - "_images"
    - "_code"
    - "node_modules"

openai:
  model: "gpt-4"
  temperature: 0.7

query:
  max_results: 10
"""
    config_file.write_text(config_content.format(kb_root=str(tmp_path / "kb")))
    return config_file


@pytest.fixture
def sample_markdown_files(mock_kb_root):
    """Create sample markdown files for testing"""
    files = {}

    # A page that links to other pages
    files["test_page"] = mock_kb_root / "wiki" / "sources" / "test_page.md"
    files["test_page"].write_text("""---
date: 2024-01-15
---

# Test Page

This is a test page that references [[concepts/test-concept]] and [[entities/test-entity]].

See also [another page](another-page.md).
""")

    # A concept page
    files["concept"] = mock_kb_root / "wiki" / "concepts" / "test-concept.md"
    files["concept"].write_text("""---
date: 2024-01-10
---

# Test Concept

## 定义

A test concept for unit testing.

## 描述

This concept is used in testing.
""")

    # An entity page
    files["entity"] = mock_kb_root / "wiki" / "entities" / "test-entity.md"
    files["entity"].write_text("""---
date: 2024-01-12
---

# Test Entity

A test entity for unit testing.
""")

    # A page with broken links
    files["broken_links"] = mock_kb_root / "wiki" / "sources" / "broken_links.md"
    files["broken_links"].write_text("""---
date: 2024-01-14
---

# Broken Links Page

This page links to [[non-existent-page]] and [missing](does-not-exist.md).
""")

    # An orphan page (not linked from anywhere)
    files["orphan"] = mock_kb_root / "wiki" / "sources" / "orphan_page.md"
    files["orphan"].write_text("""---
date: 2024-01-13
---

# Orphan Page

This page is not linked from any other page.
""")

    # Index file (should be excluded from orphans)
    files["index"] = mock_kb_root / "wiki" / "_index.md"
    files["index"].write_text("# Index")

    return files


@pytest.fixture
def sample_log_file(mock_kb_root):
    """Create a sample log file"""
    log_file = mock_kb_root / "wiki" / "_meta" / "log.md"
    log_file.write_text("""## 2024-01-01 10:00 | create | wiki/sources/test.md
## 2024-01-02 14:30 | update | wiki/concepts/example.md
## 2024-01-03 09:15 | delete | wiki/sources/old.md
""")
    return log_file


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    with patch("wiki.lint.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Mocked LLM response"))]
        mock_client.chat.completions.create.return_value = mock_response
        yield mock_client
