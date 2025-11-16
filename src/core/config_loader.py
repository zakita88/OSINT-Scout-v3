from pathlib import Path
import json

CFG_PATH = Path(__file__).resolve().parents[1].parent / "data" / "config.json"

def load_config():
    txt = CFG_PATH.read_text(encoding="utf-8")
    return json.loads(txt)
