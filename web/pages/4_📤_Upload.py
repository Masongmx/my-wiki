#!/usr/bin/env python3
"""Upload 页面 - 上传素材文件"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_kb_root


def get_upload_dir(category: str) -> Path:
    """获取上传目录"""
    kb_root = get_kb_root()

    dirs = {
        "articles": kb_root / "raw" / "articles",
        "pdfs": kb_root / "pdfs",
        "transcripts": kb_root / "raw" / "transcripts",
        "assets": kb_root / "raw" / "assets",
    }

    return dirs.get(category, kb_root / "raw" / "articles")


def save_uploaded_file(
    uploaded_file,
    target_dir: Path,
    filename: str | None = None
) -> Path:
    """保存上传的文件"""
    if not filename:
        filename = uploaded_file.name

    target_path = target_dir / filename
    target_dir.mkdir(parents=True, exist_ok=True)

    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return target_path


def main() -> None:
    st.set_page_config(
        page_title="Upload - My Wiki",
        page_icon="📤",
        layout="wide"
    )
    
    st.title("📤 上传素材")
    
    kb_root = get_kb_root()
    
    # 选择素材类型
    category = st.selectbox(
        "选择素材类型",
        ["articles", "pdfs", "transcripts", "assets"],
        key="upload_category"
    )
    
    st.info(f"""
    素材类型说明：
    - **articles**: 文章原文（.md, .txt）
    - **pdfs**: PDF 文档
    - **transcripts**: 音频/视频转录（.md, .txt）
    - **assets**: 图片、附件等
    """)
    
    # 文件上传
    uploaded_files = st.file_uploader(
        "选择文件",
        accept_multiple_files=True,
        key="upload_files"
    )
    
    # 自定义文件名
    custom_filename = st.text_input(
        "自定义文件名（可选，不含扩展名）",
        key="upload_filename"
    )
    
    if not uploaded_files:
        st.warning("请选择要上传的文件")
        return
    
    # 显示待上传文件
    st.subheader(f"待上传文件（{len(uploaded_files)} 个）")
    
    for file in uploaded_files:
        st.text(f"- {file.name} ({file.size} bytes)")
    
    # 上传按钮
    if st.button("确认上传", key="upload_button"):
        target_dir = get_upload_dir(category)
        
        success_count = 0
        
        for uploaded_file in uploaded_files:
            try:
                # 确定文件名
                if custom_filename and len(uploaded_files) == 1:
                    ext = Path(uploaded_file.name).suffix
                    filename = f"{custom_filename}{ext}"
                else:
                    # 自动生成文件名（时间戳）
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    ext = Path(uploaded_file.name).suffix
                    filename = f"{timestamp}-{uploaded_file.name}"
                
                # 保存文件
                target_path = save_uploaded_file(uploaded_file, target_dir, filename)
                success_count += 1
                
                st.success(f"上传成功: `{target_path.relative_to(kb_root)}`")
            except Exception as e:
                st.error(f"上传失败: {uploaded_file.name} - {e}")
        
        st.markdown("---")
        st.info(f"""
        共上传 {success_count} 个文件
        
        **下一步**：
        1. 在命令行运行 `kb ingest raw/{category}/` 处理素材
        2. 或使用 `kb ingest --batch` 批量处理
        """)
    
    # 显示现有文件
    st.markdown("---")
    st.subheader("现有素材文件")
    
    target_dir = get_upload_dir(category)
    
    if target_dir.exists():
        files = sorted(target_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
        
        if files:
            for file in files[:10]:
                st.text(f"- {file.name}")
        else:
            st.text("暂无文件")
    else:
        st.text("目录不存在")


if __name__ == "__main__":
    main()