"""ingest LLM module - LLM 客户端和提取逻辑"""

import re
import os
import hashlib
from pathlib import Path
from typing import Any, Optional
from openai import OpenAI


def compute_file_hash(file_path: Path) -> str:
    """计算文件 hash"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_api_key(config: dict[str, Any]) -> str:
    """从配置或 key.txt 获取 API key"""
    kb_root = Path(config["knowledge_base"]["root"])

    # 优先从 key.txt 读取
    key_file = kb_root / "key.txt"
    if key_file.exists():
        with open(key_file, "r") as f:
            return f.read().strip()

    # 其次从 litellm_config.yaml 读取
    litellm_file = kb_root / "config" / "litellm_config.yaml"
    if litellm_file.exists():
        with open(litellm_file, "r") as f:
            litellm_cfg = __import__("yaml").safe_load(f)
            if litellm_cfg.get("model_list"):
                return litellm_cfg["model_list"][0]["litellm_params"]["api_key"]

    # 最后从环境变量
    api_key = os.getenv("BAILIAN_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    raise ValueError("找不到 API key（检查 key.txt 或 litellm_config.yaml）")


def get_llm_client(config: dict[str, Any]) -> tuple[OpenAI, str]:
    """获取 LLM 客户端"""
    api_key = get_api_key(config)
    llm_config = config["llm"]

    return OpenAI(
        api_key=api_key,
        base_url=llm_config["base_url"]
    ), llm_config["model"]


# JSON 示例（单独定义，避免 f-string 大括号冲突）
_JSON_EXAMPLE = '''{
  "title": "来源标题（简洁）",
  "overview": "整体概览（100-200字）",
  "insights": [
    {
      "title": "洞察标题",
      "content": "洞察内容（100-150字）"
    }
  ],
  "concepts": [
    {
      "name": "概念名称",
      "definition": "一句话定义（不超过50字）",
      "importance": "为什么重要（不超过100字）",
      "key_points": ["要点1", "要点2", "要点3"]
    }
  ],
  "entities": [
    {
      "name": "实体名称",
      "type": "tool|person|company|project",
      "info": "关键信息（不超过200字）",
      "features": ["特点1", "特点2"]
    }
  ],
  "follow_up_questions": ["值得深入探索的问题"]
}'''


def llm_extract_source(
    client: OpenAI,
    model: str,
    content: str,
    filename: str
) -> Optional[dict[str, Any]]:
    """调用 LLM 提取来源页内容"""

    prompt = f"""分析以下内容，生成结构化的来源页（source page）。

内容（来自文件 {filename}）：
{content[:6000]}

请以 JSON 格式返回（只返回 JSON，不要其他内容）：
{_JSON_EXAMPLE}

提取规则：
- concepts：不超过 20 个，只提取核心概念（全文围绕论述或首次定义）
- entities：不超过 10 个，只提取主要对象或关键配角
- insights：提取 3-5 个最有价值的洞察"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        result_text = response.choices[0].message.content.strip()

        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            return json.loads(json_match.group())
        else:
            return None
    except Exception:
        return None