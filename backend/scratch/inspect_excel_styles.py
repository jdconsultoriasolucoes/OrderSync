import openpyxl
import os
from reportlab.lib import colors

template_path = r"e:\OrderSync - Dev\backend\assets\template_supra.xlsx"

def hex_to_color(hex_str):
    if not hex_str or len(hex_str) < 6:
        return None
    if len(hex_str) == 8: # ARGB
        hex_str = hex_str[2:]
    try:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return colors.Color(r, g, b)
    except:
        return None

def inspect_styles():
    wb = openpyxl.load_workbook(template_path)
    ws = wb["Cadastro Parte 1"]
    
    print("Checking styles for key rows:")
    for r in range(6, 60):
        cell = ws.cell(row=r, column=1)
        fill = cell.fill
        fg = fill.fgColor
        color_hex = None
        if fg.type == 'rgb':
            color_hex = fg.rgb
        
        font = cell.font
        align = cell.alignment
        
        if color_hex and color_hex != '00000000':
             print(f"Row {r}: Color {color_hex}, Bold: {font.bold}, Align: {align.horizontal}")

if __name__ == "__main__":
    inspect_styles()
