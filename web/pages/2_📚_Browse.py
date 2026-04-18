#!/usr/bin/env python3
"""Browse 页面 - 浏览概念、实体、来源"""

import streamlit as st
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_kb_root


def get_file_list(directory: Path) -> list[Path]:
    """获取文件列表"""
    if not directory.exists():
        return []

    files = sorted(directory.glob("*.md"))
    return files


def read_file_preview(file_path: Path, max_length: int = 500) -> tuple[str, str]:
    """读取文件预览"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取标题和定义/概览
        title_match = re.search(r'^#\s+([^\n]+)', content)
        title = title_match.group(1) if title_match else file_path.stem

        # 提取定义或概览（前几行内容）
        preview_lines = []
        lines = content.split('\n')

        # 跳过 frontmatter
        in_fm = False
        for line in lines:
            if line.strip() == '---':
                in_fm = not in_fm
                continue

            if in_fm:
                continue

            # 跳过标题
            if line.startswith('#'):
                continue

            # 跳过空行
            if not line.strip():
                continue

            preview_lines.append(line)

            if len(preview_lines) >= 5:
                break

        preview = '\n'.join(preview_lines)

        if len(preview) > max_length:
            preview = preview[:max_length] + "..."

        return title, preview
    except Exception as e:
        return file_path.stem, f"读取失败: {e}"


def read_full_file(file_path: Path) -> str:
    """读取完整文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取失败: {e}"


def main() -> None:
    st.set_page_config(
        page_title="Browse - My Wiki",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 浏览知识库")
    
    kb_root = get_kb_root()
    
    # 选择类型
    view_type = st.selectbox(
        "选择类型",
        ["concepts", "entities", "sources", "outputs"],
        key="browse_type"
    )
    
    # 获取文件列表
    directory = kb_root / "wiki" / view_type
    files = get_file_list(directory)
    
    if not files:
        st.warning(f"暂无 {view_type} 内容")
        return
    
    st.subheader(f"{view_type} 列表（共 {len(files)} 个）")
    
    # 文件列表
    selected_file = st.selectbox(
        "选择文件",
        files,
        format_func=lambda f: f.stem,
        key="browse_file"
    )
    
    # 显示内容
    if selected_file:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("预览")
            title, preview = read_file_preview(selected_file)
            st.markdown(f"**{title}**")
            st.text(preview)
        
        with col2:
            st.subheader("完整内容")
            full_content = read_full_file(selected_file)
            st.markdown(full_content)
        
        # 文件信息
        st.markdown("---")
        st.caption(f"文件路径: `{selected_file.relative_to(kb_root)}`")


if __name__ == "__main__":
    main()