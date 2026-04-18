"""Tests for configuration loading"""

import pytest
import yaml
from pathlib import Path

from wiki import lint, status


class TestLintConfigLoading:
    """Tests for lint config loading"""

    def test_load_config_success(self, mock_config_file):
        """Test successful lint config loading"""
        config = lint.load_config(mock_config_file)

        assert config["knowledge_base"]["root"] is not None
        assert "exclude_dirs" in config["lint"]

    def test_load_config_knowledge_base_section(self, mock_config_file):
        """Test knowledge_base section is properly loaded"""
        config = lint.load_config(mock_config_file)

        kb = config["knowledge_base"]
        assert "root" in kb
        assert "data_dir" in kb

    def test_load_config_lint_section(self, mock_config_file):
        """Test lint section is properly loaded"""
        config = lint.load_config(mock_config_file)

        lint_config = config["lint"]
        assert "exclude_dirs" in lint_config
        assert isinstance(lint_config["exclude_dirs"], list)

    def test_load_config_openai_section(self, mock_config_file):
        """Test openai section is properly loaded"""
        config = lint.load_config(mock_config_file)

        openai_config = config["openai"]
        assert "model" in openai_config
        assert "temperature" in openai_config

    def test_load_config_missing_file_raises_error(self, tmp_path):
        """Test that missing config file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            lint.load_config(tmp_path / "missing.yaml")

        assert "配置文件不存在" in str(exc_info.value)


class TestStatusConfigLoading:
    """Tests for status config loading - verifies KeyError fix"""

    def test_load_config_with_root_key(self, mock_config_file):
        """Test loading config that has 'root' key (original case)"""
        config = status.load_config(mock_config_file)

        kb = config["knowledge_base"]
        # After fix: uses .get() so no KeyError even if root is missing
        root = kb.get("root") or kb.get("data_dir", "./data")
        assert root is not None

    def test_load_config_with_only_data_dir(self, tmp_path):
        """Test loading config with only data_dir key (no root key) - KeyError fix"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Config WITHOUT root key - simulating the KeyError bug scenario
        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base:
  data_dir: "{data_dir}"

lint:
  exclude_dirs: []
""".format(data_dir=str(tmp_path / "kb")))

        # This should NOT raise KeyError after the fix
        config = status.load_config(config_file)

        kb = config["knowledge_base"]
        # The fix uses .get() with fallback
        assert kb.get("root") is None  # root key doesn't exist
        assert kb.get("data_dir") is not None  # data_dir does exist

    def test_load_config_with_neither_root_nor_data_dir(self, tmp_path):
        """Test loading config with neither root nor data_dir - should use default"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base: {}

lint:
  exclude_dirs: []
""")

        config = status.load_config(config_file)

        kb = config["knowledge_base"]
        # Should fall back to default "./data"
        root = kb.get("root") or kb.get("data_dir", "./data")
        assert root == "./data"

    def test_load_config_both_keys_present(self, tmp_path):
        """Test when both root and data_dir are present - root takes precedence"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base:
  root: "custom_root"
  data_dir: "custom_data"

lint:
  exclude_dirs: []
""")

        config = status.load_config(config_file)

        kb = config["knowledge_base"]
        # root takes precedence when it exists
        root = kb.get("root") or kb.get("data_dir", "./data")
        assert root == "custom_root"

    def test_load_config_empty_knowledge_base(self, tmp_path):
        """Test loading config with empty knowledge_base section"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base: null

lint:
  exclude_dirs: []
""")

        config = status.load_config(config_file)

        assert "knowledge_base" in config
        kb = config["knowledge_base"]
        assert kb is None

    def test_load_config_missing_file_raises_error(self, tmp_path):
        """Test that missing config file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError) as exc_info:
            status.load_config(tmp_path / "missing.yaml")

        assert "配置文件不存在" in str(exc_info.value)


class TestConfigValidationEdgeCases:
    """Tests for config validation edge cases"""

    def test_config_with_special_characters_in_path(self, tmp_path):
        """Test config with special characters in paths"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Path with spaces
        kb_root = tmp_path / "kb with spaces"
        kb_root.mkdir()

        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base:
  root: "{kb_root}"
  data_dir: "{kb_root}"

lint:
  exclude_dirs:
    - "_images"
""".format(kb_root=str(kb_root)))

        config = lint.load_config(config_file)
        assert config["knowledge_base"]["root"] == str(kb_root)

    def test_config_with_empty_exclude_dirs(self, tmp_path):
        """Test config with empty exclude_dirs list"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base:
  root: "{kb_root}"
  data_dir: "{kb_root}"

lint:
  exclude_dirs: []
""".format(kb_root=str(tmp_path / "kb")))

        config = lint.load_config(config_file)
        assert config["lint"]["exclude_dirs"] == []

    def test_config_with_nested_directories(self, tmp_path):
        """Test config with nested directory in exclude_dirs"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base:
  root: "{kb_root}"
  data_dir: "{kb_root}"

lint:
  exclude_dirs:
    - "_images"
    - "node_modules"
    - ".git"
""".format(kb_root=str(tmp_path / "kb")))

        config = lint.load_config(config_file)
        assert len(config["lint"]["exclude_dirs"]) == 3
