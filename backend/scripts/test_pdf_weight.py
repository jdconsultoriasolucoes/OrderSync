import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal
import re

def _parse_peso(val):
    if not val:
        return 0.0
    try:
        txt = str(val).replace(',', '.').strip()
        num_only = re.sub(r'[^\d\.]', '', txt)
        return float(num_only) if num_only else 0.0
    except Exception:
        return 0.0

def test_hardcoded():
    print("Testing parser:")
    print("10,00 KG ->", _parse_peso("10,00 KG"))
    print(" 5.5  ->", _parse_peso(" 5.5 "))
    print("2,50kg ->", _parse_peso("2,50kg"))
    print("nan ->", _parse_peso("nan"))
    print("None ->", _parse_peso(None))

if __name__ == "__main__":
    test_hardcoded()
