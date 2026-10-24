from pathlib import Path
import pandas as pd
import sys

downloads = Path.home() / "Downloads"
candidates = list(downloads.glob("*pasta1*.xlsx")) + list(downloads.glob("*Pasta1*.xlsx"))
print(f"Candidates for pasta1 in Downloads: {candidates}")

if not candidates:
    all_xlsx = list(downloads.glob("*.xlsx"))
    print(f"All xlsx files in Downloads ({len(all_xlsx)}):")
    for x in all_xlsx[:10]:
        print("  -", x.name)
    sys.exit(0)

target = candidates[0]
print(f"\nAnalyzing target file: {target} (Size: {target.stat().st_size} bytes)")

try:
    excel_file = pd.ExcelFile(target)
    print("Sheet names:", excel_file.sheet_names)
    for sheet in excel_file.sheet_names:
        df = pd.read_excel(target, sheet_name=sheet)
        print(f"\n--- Sheet: {sheet} ---")
        print(f"Shape: {df.shape}")
        print("Columns:", list(df.columns))
        print("First 5 rows:")
        print(df.head(5))
        print("\nLast 3 rows:")
        print(df.tail(3))
except Exception as e:
    import traceback
    print("Error reading excel:", e)
    traceback.print_exc()
