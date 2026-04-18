#!/usr/bin/env python3
"""wiki fetch: 抓取链接内容

功能：
1. URL自动识别平台类型
2. 调用对应抓取逻辑
3. 保存到 raw/ 目录
"""

import click
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import urllib.request
import urllib.parse


def detect_platform(url: str) -> Optional[str]:
    """识别链接平台类型"""
    if "x.com" in url or "twitter.com" in url:
        return "twitter"
    elif "weibo.com" in url or "m.weibo.cn" in url:
        return "weibo"
    elif "mp.weixin.qq.com" in url:
        return "wechat"
    elif "xiaohongshu.com" in url:
        return "xiaohongshu"
    else:
        return "web"


def extract_tweet_id(url: str) -> Optional[str]:
    """从Twitter URL提取推文ID"""
    match = re.search(r"status/(\d+)", url)
    return match.group(1) if match else None


def fetch_tweet(tweet_id: str) -> Dict[str, Any]:
    """抓取Twitter推文（使用FxTwitter API）"""
    url = f"https://api.fxtwitter.com/status/{tweet_id}"
    
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        if "tweet" in data:
            tweet = data["tweet"]
            return {
                "success": True,
                "platform": "twitter",
                "data": {
                    "text": tweet.get("text", ""),
                    "author": tweet.get("author", ""),
                    "likes": tweet.get("likes", 0),
                    "retweets": tweet.get("retweets", 0),
                    "created_at": tweet.get("created_at", ""),
                    "url": tweet.get("url", "")
                }
            }
        return {"success": False, "error": "No tweet data"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_weibo_ids(url: str) -> Optional[tuple]:
    """从微博URL提取ID"""
    # https://weibo.com/uid/bid
    match = re.search(r"weibo\.com/(\d+)/(\w+)", url)
    if match:
        return match.group(1), match.group(2)
    
    # https://m.weibo.cn/detail/bid
    match = re.search(r"m\.weibo\.cn/detail/(\w+)", url)
    if match:
        return None, match.group(1)
    
    return None


def fetch_weibo(post_id: str) -> Dict[str, Any]:
    """抓取微博（使用移动API）"""
    url = f"https://m.weibo.cn/statuses/extend?id={post_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "Accept": "application/json"
    }
    
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        if "data" in data:
            post = data["data"]
            return {
                "success": True,
                "platform": "weibo",
                "data": {
                    "text": post.get("text", ""),
                    "user_name": post.get("user", {}).get("screen_name", ""),
                    "likes": post.get("attitudes_count", 0),
                    "comments": post.get("comments_count", 0),
                    "created_at": post.get("created_at", "")
                }
            }
        return {"success": False, "error": "No post data"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_web(url: str) -> Dict[str, Any]:
    """抓取通用网页"""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode("utf-8", errors="ignore")
        
        # 简单提取标题和正文
        title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
        title = title_match.group(1) if title_match else "无标题"
        
        # 简单清理HTML标签
        text = re.sub(r"<[^>]+>", "", content)
        text = re.sub(r"\s+", " ", text).strip()[:5000]
        
        return {
            "success": True,
            "platform": "web",
            "data": {
                "title": title,
                "text": text,
                "url": url
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@click.command()
@click.argument("url")
@click.option("--save", is_flag=True, help="保存到raw目录")
@click.pass_obj
def fetch(config: dict, url: str, save: bool):
    """抓取链接内容
    
    \b
    支持平台：
    - X/Twitter (零依赖)
    - 微博 Weibo (零依赖)
    - 微信公众号 WeChat (需playwright)
    - 小红书 Xiaohongshu (需aiohttp)
    - 通用网页 Web
    
    \b
    示例：
    wiki fetch "https://x.com/user/status/123456"
    wiki fetch "https://weibo.com/uid/bid" --save
    """
    platform = detect_platform(url)
    
    click.echo(f"🔍 识别平台: {platform or '未知'}")
    
    # 根据平台调用不同抓取逻辑
    result = {"success": False, "error": "不支持的平台"}
    
    if platform == "twitter":
        tweet_id = extract_tweet_id(url)
        if tweet_id:
            result = fetch_tweet(tweet_id)
    
    elif platform == "weibo":
        ids = extract_weibo_ids(url)
        if ids:
            _, post_id = ids
            result = fetch_weibo(post_id)
    
    elif platform == "web":
        result = fetch_web(url)
    
    elif platform in ("wechat", "xiaohongshu"):
        click.echo(f"⚠️ {platform} 抓取需要额外依赖安装")
        click.echo("  微信公众号: pip install playwright && playwright install chromium")
        click.echo("  小红书: pip install aiohttp pycryptodome")
        return
    
    # 显示结果
    if result.get("success"):
        data = result["data"]
        click.echo(f"\n✅ 抓取成功\n")
        
        if platform == "twitter":
            click.echo(f"作者: {data.get('author', '未知')}")
            click.echo(f"点赞: {data.get('likes', 0)} | 转发: {data.get('retweets', 0)}")
            click.echo(f"\n{data.get('text', '')[:500]}")
        
        elif platform == "weibo":
            click.echo(f"作者: {data.get('user_name', '未知')}")
            click.echo(f"点赞: {data.get('likes', 0)} | 评论: {data.get('comments', 0)}")
            click.echo(f"\n{data.get('text', '')[:500]}")
        
        elif platform == "web":
            click.echo(f"标题: {data.get('title', '未知')}")
            click.echo(f"\n{data.get('text', '')[:500]}")
        
        # 保存到raw目录
        if save:
            kb_root = Path(config["knowledge_base"]["root"])
            raw_dir = kb_root / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r"[^\w\s-]", "", data.get("title", "")[:30])
            filename = f"{timestamp}_{platform}_{safe_title}.md"
            
            raw_file = raw_dir / filename
            with open(raw_file, "w", encoding="utf-8") as f:
                f.write(f"# {data.get('title', '')}\n\n")
                f.write(f"来源: {url}\n")
                f.write(f"平台: {platform}\n")
                f.write(f"抓取时间: {datetime.now().isoformat()}\n\n")
                f.write("---\n\n")
                f.write(data.get("text", ""))
            
            click.echo(f"\n✅ 已保存: {raw_file}")
    else:
        click.echo(f"❌ 抓取失败: {result.get('error', '未知错误')}")