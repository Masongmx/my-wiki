"""Tests for lint functionality"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from wiki import lint


class TestLinkExtraction:
    """Tests for link extraction"""

    def test_extract_wiki_links(self, tmp_path):
        """Test wiki link extraction"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""
This is a test page with [[wiki-link-one]] and [[wiki-link-two]].

Also [[another-link]] with anchor.
""")

        links = lint.extract_links(test_file)

        assert len(links["wiki_links"]) == 3
        assert "wiki-link-one" in links["wiki_links"]
        assert "wiki-link-two" in links["wiki_links"]
        assert "another-link" in links["wiki_links"]

    def test_extract_md_links(self, tmp_path):
        """Test markdown link extraction"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""
Check out [this link](internal-page.md) for more info.

Also [external](https://example.com) link.
""")

        links = lint.extract_links(test_file)

        assert len(links["md_links"]) == 1
        assert "internal-page.md" in links["md_links"]

    def test_extract_embeds(self, tmp_path):
        """Test embed extraction"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""
Here is an image: ![[embedded-image.png]]

And a chart: ![[chart]]
""")

        links = lint.extract_links(test_file)

        assert len(links["embeds"]) == 2
        assert "embedded-image.png" in links["embeds"]
        assert "chart" in links["embeds"]

    def test_extract_links_empty_file(self, tmp_path):
        """Test link extraction from empty file"""
        test_file = tmp_path / "empty.md"
        test_file.write_text("No links here.")

        links = lint.extract_links(test_file)

        assert links["wiki_links"] == []
        assert links["md_links"] == []
        assert links["embeds"] == []

    def test_extract_links_invalid_file(self, tmp_path):
        """Test link extraction with unreadable file"""
        with patch("builtins.open", side_effect=IOError("Mocked error")):
            links = lint.extract_links(tmp_path / "nonexistent.md")
            assert links["wiki_links"] == []
            assert links["md_links"] == []


class TestFileIndex:
    """Tests for file index building"""

    def test_build_file_index(self, sample_markdown_files, mock_kb_root):
        """Test building file index"""
        exclude_dirs = ["_images", "_code"]

        index = lint.build_file_index(mock_kb_root, exclude_dirs)

        # Should contain both stem and relative path versions
        assert "test_page" in index
        assert "test-concept" in index
        assert "test-entity" in index

    def test_build_file_index_excludes_dirs(self, mock_kb_root):
        """Test that excluded directories are not indexed"""
        # Create file in excluded directory
        excluded_dir = mock_kb_root / "_images"
        excluded_dir.mkdir(parents=True)
        excluded_file = excluded_dir / "excluded.md"
        excluded_file.write_text("# Excluded")

        exclude_dirs = ["_images"]
        index = lint.build_file_index(mock_kb_root, exclude_dirs)

        assert "excluded" not in index


class TestBrokenLinks:
    """Tests for broken link detection"""

    def test_check_broken_links_none_found(self, mock_kb_root):
        """Test when no broken links exist"""
        # Create files without broken links
        good_file = mock_kb_root / "wiki" / "sources" / "good.md"
        good_file.parent.mkdir(parents=True, exist_ok=True)
        good_file.write_text("# Good Page\n\nThis has no broken links.")

        exclude_dirs = ["_images", "_code"]
        files = list(mock_kb_root.rglob("*.md"))
        index = lint.build_file_index(mock_kb_root, exclude_dirs)

        results = lint.check_broken_links(mock_kb_root, files, index)

        assert results["total_links"] >= 0
        assert len(results["broken_links"]) == 0

    def test_check_broken_links_wiki_link(self, sample_markdown_files, mock_kb_root):
        """Test detection of broken wiki links"""
        exclude_dirs = ["_images", "_code"]
        files = list(mock_kb_root.rglob("*.md"))
        index = lint.build_file_index(mock_kb_root, exclude_dirs)

        results = lint.check_broken_links(mock_kb_root, files, index)

        # Should find broken link to [[non-existent-page]]
        assert len(results["broken_links"]) > 0

        broken_types = [b["type"] for b in results["broken_links"]]
        assert "wiki" in broken_types

    def test_check_broken_links_md_link(self, sample_markdown_files, mock_kb_root):
        """Test detection of broken markdown links"""
        exclude_dirs = ["_images", "_code"]
        files = list(mock_kb_root.rglob("*.md"))
        index = lint.build_file_index(mock_kb_root, exclude_dirs)

        results = lint.check_broken_links(mock_kb_root, files, index)

        broken_types = [b["type"] for b in results["broken_links"]]
        assert "markdown" in broken_types


class TestOrphanedPages:
    """Tests for orphaned page detection"""

    def test_check_orphans_finds_orphans(self, sample_markdown_files, mock_kb_root):
        """Test detection of orphaned pages"""
        exclude_dirs = ["_images", "_code"]
        files = list(mock_kb_root.rglob("*.md"))
        index = lint.build_file_index(mock_kb_root, exclude_dirs)

        results = lint.check_orphans(mock_kb_root, files, index)

        assert results["total_files"] == len(files)
        assert len(results["orphans"]) > 0

    def test_check_orphans_excludes_index(self, sample_markdown_files, mock_kb_root):
        """Test that index files are excluded from orphans"""
        exclude_dirs = ["_images", "_code"]
        files = list(mock_kb_root.rglob("*.md"))
        index = lint.build_file_index(mock_kb_root, exclude_dirs)

        results = lint.check_orphans(mock_kb_root, files, index)

        # _index.md should not be reported as orphan
        for orphan in results["orphans"]:
            assert "_index" not in orphan


class TestOutdated:
    """Tests for outdated content detection"""

    def test_check_outdated_finds_old_sources(self, mock_kb_root):
        """Test detection of outdated sources"""
        # Create old source
        sources_dir = mock_kb_root / "wiki" / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)

        old_file = sources_dir / "old-source.md"
        old_file.write_text("""---
date: 2020-01-01
---

# Old Source

This source is from 2020.
""")

        results = lint.check_outdated(mock_kb_root, days=365)

        assert len(results["outdated"]) > 0

    def test_check_outdated_none_old(self, mock_kb_root):
        """Test when no sources are outdated"""
        # Create recent source (yesterday - should never be outdated)
        sources_dir = mock_kb_root / "wiki" / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)

        recent_file = sources_dir / "recent.md"
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        recent_file.write_text(f"""---
date: {yesterday}
---

# Recent Source

This source is recent.
""")

        results = lint.check_outdated(mock_kb_root, days=365)

        assert len(results["outdated"]) == 0


class TestLogFormat:
    """Tests for log format checking"""

    def test_check_log_format_valid(self, sample_log_file, mock_kb_root):
        """Test with valid log format"""
        results = lint.check_log_format(mock_kb_root)

        assert len(results["issues"]) == 0

    def test_check_log_format_missing(self, mock_kb_root):
        """Test when log file is missing"""
        results = lint.check_log_format(mock_kb_root)

        assert "日志文件不存在" in results["issues"]

    def test_check_log_format_invalid(self, tmp_path):
        """Test with invalid log format"""
        log_file = tmp_path / "wiki" / "_meta" / "log.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text("Invalid log content without proper format.")

        results = lint.check_log_format(tmp_path)

        assert len(results["issues"]) > 0


class TestReportGeneration:
    """Tests for report generation"""

    def test_generate_report_complete(self, mock_kb_root):
        """Test generating a complete report"""
        results = {
            "broken": {
                "broken_links": [{"file": "test.md", "link": "[[missing]]", "type": "wiki"}],
                "files_with_broken": {"test.md": ["[[missing]]"]},
                "total_links": 10
            },
            "orphans": {
                "orphans": ["orphan.md"],
                "total_files": 5
            },
            "contradictions": {"contradictions": []},
            "outdated": {"outdated": []},
            "log": {"issues": []}
        }

        report = lint.generate_report(mock_kb_root, results)

        assert "健康检查报告" in report
        assert "缺失页" in report
        assert "孤立页" in report


class TestConfigLoading:
    """Tests for config loading"""

    def test_load_config_success(self, mock_config_file):
        """Test successful config loading"""
        config = lint.load_config(mock_config_file)

        assert "knowledge_base" in config
        assert "lint" in config
        assert "openai" in config

    def test_load_config_file_not_found(self, tmp_path):
        """Test config loading with missing file"""
        with pytest.raises(FileNotFoundError):
            lint.load_config(tmp_path / "nonexistent.yaml")
