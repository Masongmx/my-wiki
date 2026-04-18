#!/usr/bin/env python3
"""kb ingest: 处理 raw/ 素材到 wiki/

此模块已重构为 wiki/ingest/ 子包
"""

from wiki.ingest import ingest

if __name__ == "__main__":
    ingest()