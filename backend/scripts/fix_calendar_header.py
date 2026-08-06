import os
import re

CALENDAR_INDEX = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'calendario', 'index.html'))
DASHBOARD_INDEX = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'dashboards.html'))

with open(DASHBOARD_INDEX, 'r', encoding='utf-8') as f:
    dashboard_html = f.read()

# Extract from <!-- ========== HEADER ========== --> to <div class="os-sidebar-overlay" id="overlay"></div>
pattern = re.compile(r'(<!-- ========== HEADER ========== -->.*?<div class="os-sidebar-overlay" id="overlay"></div>)', re.DOTALL)
match = pattern.search(dashboard_html)
header_sidebar_code = match.group(1)

with open(CALENDAR_INDEX, 'r', encoding='utf-8') as f:
    cal_html = f.read()

# Replace <nav class="os-navbar">...</nav> with the header_sidebar_code
cal_pattern = re.compile(r'<!-- Simulação do Navbar -->\s*<nav class="os-navbar">.*?</nav>', re.DOTALL)

new_cal_html = cal_pattern.sub(header_sidebar_code, cal_html)

# Also need to add sidebar_control.js script to calendario/index.html
if 'sidebar_control.js' not in new_cal_html:
    new_cal_html = new_cal_html.replace('</body>', '    <script src="/js/sidebar_control.js"></script>\n</body>')

with open(CALENDAR_INDEX, 'w', encoding='utf-8') as f:
    f.write(new_cal_html)

print("Calendario index.html atualizado!")
