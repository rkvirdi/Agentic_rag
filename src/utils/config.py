import yaml
from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class CrawlerConfig:
    user_agent: str
    throttle_seconds: float
    request_timeout: int
    max_depth: int
    max_pages: int

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_crawler_cfg(cfg: Dict[str, Any]) -> CrawlerConfig:
    c = cfg.get("crawler", {})
    return CrawlerConfig(
        user_agent=c.get("user_agent", "AgenticRAG-DevScraper/0.1 (+local dev)"),
        throttle_seconds=float(c.get("throttle_seconds", 0.75)),
        request_timeout=int(c.get("request_timeout", 20)),
        max_depth=int(c.get("max_depth", 3)),
        max_pages=int(c.get("max_pages", 250)),
    )
