"""Tests for status functionality"""

import pytest
from pathlib import Path

from wiki import status


class TestFileCounting:
    """Tests for file counting"""

    def test_count_files_empty_dir(self, mock_kb_root):
        """Test counting files in empty directory"""
        empty_dir = mock_kb_root / "wiki" / "empty"
        empty_dir.mkdir()

        count = status.count_files(empty_dir)
        assert count == 0

    def test_count_files_nonexistent_dir(self, mock_kb_root):
        """Test counting files in nonexistent directory"""
        count = status.count_files(mock_kb_root / "nonexistent")
        assert count == 0

    def test_count_files_with_files(self, mock_kb_root):
        """Test counting files in directory with files"""
        sources_dir = mock_kb_root / "wiki" / "sources"
        (sources_dir / "file1.md").write_text("# File 1")
        (sources_dir / "file2.md").write_text("# File 2")
        (sources_dir / "file3.md").write_text("# File 3")

        count = status.count_files(sources_dir)
        assert count == 3


class TestFileList:
    """Tests for file listing"""

    def test_get_file_list_empty(self, mock_kb_root):
        """Test getting file list from empty directory"""
        empty_dir = mock_kb_root / "wiki" / "empty"
        empty_dir.mkdir()

        files = status.get_file_list(empty_dir)
        assert files == []

    def test_get_file_list_nonexistent(self, mock_kb_root):
        """Test getting file list from nonexistent directory"""
        files = status.get_file_list(mock_kb_root / "nonexistent")
        assert files == []

    def test_get_file_list_with_limit(self, mock_kb_root):
        """Test file list with limit"""
        sources_dir = mock_kb_root / "wiki" / "sources"
        for i in range(15):
            (sources_dir / f"file{i}.md").write_text(f"# File {i}")

        files = status.get_file_list(sources_dir, limit=10)
        assert len(files) == 10


class TestRecentLogs:
    """Tests for recent log reading"""

    def test_read_recent_logs_valid(self, sample_log_file):
        """Test reading recent logs with valid format"""
        logs = status.read_recent_logs(sample_log_file, limit=5)

        assert len(logs) == 3
        # Logs are returned in reverse order (oldest first after reversal)
        assert logs[0]["action"] == "delete"  # Oldest is "delete" in sample_log_file
        assert logs[0]["file"] == "wiki/sources/test.md"

    def test_read_recent_logs_empty(self, mock_kb_root):
        """Test reading from empty log file"""
        empty_log = mock_kb_root / "wiki" / "_meta" / "log.md"
        empty_log.parent.mkdir(parents=True, exist_ok=True)
        empty_log.write_text("")

        logs = status.read_recent_logs(empty_log)
        assert logs == []

    def test_read_recent_logs_limit(self, sample_log_file):
        """Test reading with limit"""
        logs = status.read_recent_logs(sample_log_file, limit=2)
        assert len(logs) == 2

    def test_read_recent_logs_nonexistent_file(self, mock_kb_root):
        """Test reading nonexistent log file"""
        logs = status.read_recent_logs(mock_kb_root / "nonexistent.log")
        assert logs == []


class TestKBStats:
    """Tests for knowledge base statistics"""

    def test_get_kb_stats_empty(self, mock_kb_root):
        """Test stats from empty knowledge base"""
        stats = status.get_kb_stats(mock_kb_root)

        assert "sources" in stats
        assert "concepts" in stats
        assert "entities" in stats
        assert "outputs" in stats
        assert "articles" in stats
        assert "total_wiki" in stats
        assert "total_raw" in stats

        # All should be 0 for empty dirs
        assert stats["total_wiki"] == 0
        assert stats["total_raw"] == 0

    def test_get_kb_stats_with_files(self, sample_markdown_files, mock_kb_root):
        """Test stats with files present"""
        stats = status.get_kb_stats(mock_kb_root)

        # test_page.md is in sources
        assert stats["sources"] >= 1
        # test-concept.md is in concepts
        assert stats["concepts"] >= 1
        # test-entity.md is in entities
        assert stats["entities"] >= 1

    def test_get_kb_stats_totals(self, sample_markdown_files, mock_kb_root):
        """Test that totals are calculated correctly"""
        stats = status.get_kb_stats(mock_kb_root)

        # total_wiki = sources + concepts + entities + outputs + articles
        expected_total = (
            stats["sources"]
            + stats["concepts"]
            + stats["entities"]
            + stats["outputs"]
            + stats["articles"]
        )
        assert stats["total_wiki"] == expected_total

        # total_raw = raw_articles + raw_pdfs + raw_transcripts
        expected_raw = (
            stats["raw_articles"]
            + stats["raw_pdfs"]
            + stats["raw_transcripts"]
        )
        assert stats["total_raw"] == expected_raw


class TestConfigLoading:
    """Tests for config loading (KeyError fix verification)"""

    def test_load_config_with_root_key(self, mock_config_file):
        """Test loading config with 'root' key"""
        config = status.load_config(mock_config_file)

        assert "knowledge_base" in config

    def test_load_config_with_data_dir_fallback(self, tmp_path):
        """Test loading config falls back to data_dir when root is missing"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Config with data_dir instead of root
        config_file = config_dir / "kb.yaml"
        config_file.write_text("""
knowledge_base:
  data_dir: "{data_dir}"

lint:
  exclude_dirs: []
""".format(data_dir=str(tmp_path / "data")))

        config = status.load_config(config_file)

        assert "knowledge_base" in config

    def test_load_config_file_not_found(self, tmp_path):
        """Test config loading raises error for missing file"""
        with pytest.raises(FileNotFoundError):
            status.load_config(tmp_path / "nonexistent.yaml")
