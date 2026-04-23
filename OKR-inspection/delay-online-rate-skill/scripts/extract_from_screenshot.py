#!/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python
# -*- coding: utf-8 -*-
"""
从延期上线率查询结果截图中提取数据
"""
from pathlib import Path
from PIL import Image
import pytesseract
import json
import sys

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "out"

def extract_text_from_screenshot(screenshot_path: Path) -> str:
    """从截图中提取文本"""
    if not screenshot_path.exists():
        raise FileNotFoundError(f"截图不存在：{screenshot_path}")
    
    img = Image.open(screenshot_path)
    text = pytesseract.image_to_string(img, lang='chi_sim')
    return text

def parse_metrics_from_text(text: str) -> dict:
    """解析指标文本"""
    metrics = {
        "planned_online_requirements": None,
        "delayed_online_requirements": None,
        "delay_online_rate": None
    }
    
    # 查找"计划上线需求数"
    import re
    planned_match = re.search(r'计划上线需求数.*?(\d+)', text)
    if planned_match:
        metrics["planned_online_requirements"] = int(planned_match.group(1))
    
    # 查找"延期上线需求数"
    delayed_match = re.search(r'延期上线需求数.*?(\d+)', text)
    if delayed_match:
        metrics["delayed_online_requirements"] = int(delayed_match.group(1))
    
    # 查找"延期上线率"
    rate_match = re.search(r'延期上线率.*?([\d.]+)%?', text)
    if rate_match:
        metrics["delay_online_rate"] = float(rate_match.group(1))
    
    return metrics

def main():
    screenshot_path = OUT_DIR / "05_after_query.png"
    
    if not screenshot_path.exists():
        print(f"错误：截图不存在 {screenshot_path}")
        sys.exit(1)
    
    print(f"正在解析：{screenshot_path}")
    text = extract_text_from_screenshot(screenshot_path)
    print("提取的文本：")
    print("=" * 60)
    print(text)
    print("=" * 60)
    
    metrics = parse_metrics_from_text(text)
    print(f"\n解析结果：{json.dumps(metrics, indent=2, ensure_ascii=False)}")

if __name__ == '__main__':
    main()
