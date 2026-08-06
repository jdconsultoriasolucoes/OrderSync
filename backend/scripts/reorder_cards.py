import re

FILE_PATH = r"e:\OrderSync\frontend\index.html"

with open(FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract Calendario card
cal_pattern = re.compile(r'(\s*<a href="/calendario/index\.html" class="os-module-card" id="card-calendario">.*?</a>)', re.DOTALL)
cal_match = cal_pattern.search(content)

if cal_match:
    cal_html = cal_match.group(1)
    # Remove from its original position
    content = content[:cal_match.start()] + content[cal_match.end():]
    
    # Find Dashboards card end
    dash_pattern = re.compile(r'(<a href="/dashboards\.html" class="os-module-card" id="card-dashboards">.*?</a>)', re.DOTALL)
    dash_match = dash_pattern.search(content)
    
    if dash_match:
        # Insert after Dashboards card
        new_content = content[:dash_match.end()] + cal_html + content[dash_match.end():]
        
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success")
    else:
        print("Dashboards card not found")
else:
    print("Calendario card not found")
