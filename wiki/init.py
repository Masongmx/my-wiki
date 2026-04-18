#!/usr/bin/env python3
"""kb init: Initialize knowledge base directory structure"""

from pathlib import Path
import click


def create_directory_structure(kb_root: Path) -> int:
    """Create the standard knowledge base directory structure."""
    
    directories = [
        # Raw directories
        "raw/articles",
        "raw/pdfs", 
        "raw/transcripts",
        "raw/assets",
        
        # Wiki directories
        "wiki/concepts",
        "wiki/entities",
        "wiki/sources",
        "wiki/outputs",
        "wiki/_meta",
        
        # Config
        "config",
    ]
    
    for dir_path in directories:
        full_path = kb_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
    # Create initial files
    index_file = kb_root / "wiki" / "_index.md"
    if not index_file.exists():
        index_file.write_text("""# Knowledge Base Index

> Last updated: {date}

## Sources
> Sources will be listed here after ingest

## Concepts
> Concepts will be listed here after ingest

## Entities  
> Entities will be listed here after ingest

## Outputs
> Query results saved with --save will appear here
""".format(date="pending"))
    
    log_file = kb_root / "wiki" / "_meta" / "log.md"
    if not log_file.exists():
        log_file.write_text("""# Operation Log

Operations will be logged here automatically.

---
_Log created: pending_
""")
    
    return len(directories)


@click.command()
@click.option('--path', default='.', help='Path to create knowledge base (default: current directory)')
def init(path: str) -> None:
    """Initialize knowledge base directory structure.
    
    Creates raw/, wiki/, and config/ directories with proper structure.
    """
    kb_root = Path(path).resolve()
    
    if kb_root.exists() and any(kb_root.iterdir()):
        if not click.confirm(f"Directory {kb_root} is not empty. Continue?"):
            click.echo("Aborted.")
            return
    
    click.echo(f"Initializing knowledge base at {kb_root}")
    
    count = create_directory_structure(kb_root)
    
    click.echo(f"✓ Created {count} directories")
    click.echo(f"""
Next steps:
1. Create config/kb.yaml (see config/kb.yaml.example)
2. Add articles to raw/articles/
3. Run: wiki ingest raw/articles/your-article.md
4. Query: wiki query "your question"
""")


if __name__ == "__main__":
    init()