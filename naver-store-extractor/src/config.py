import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"


def get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
    return key


def load_selectors() -> dict:
    with open(CONFIG_DIR / "selectors.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompts() -> dict:
    with open(CONFIG_DIR / "prompts.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
