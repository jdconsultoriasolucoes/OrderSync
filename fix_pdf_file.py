import os

file_path = r"e:\OrderSync\backend\services\pdf_service.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the start of duplicate block
start_idx = -1
for i, line in enumerate(lines):
    # We look for the line AFTER our try/except block
    # The try/except block ends with "            raise e" (around line 452)
    # The duplicate block starts with "    frete_table.setStyle("
    if "frete_table.setStyle(" in line and i > 450:
        start_idx = i
        break

# Find the start of the next function
end_idx = -1
for i, line in enumerate(lines):
    if "def gerar_pdf_pedido" in line and i > 450:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Removing lines {start_idx} to {end_idx} (exclusive)")
    new_lines = lines[:start_idx] + lines[end_idx:]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("File updated successfully.")
else:
    print(f"Could not find markers. Start: {start_idx}, End: {end_idx}")
