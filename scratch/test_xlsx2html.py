import io
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

try:
    from xlsx2html import xlsx2html
    from pathlib import Path
    
    template_path = Path('e:/OrderSync - Dev/backend/assets/template_supra.xlsx')
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
        
    out_stream = io.StringIO()
    xlsx2html(str(template_path), out_stream)
    html_content = out_stream.getvalue()
    
    print("SUCCESS")
    print(f"HTML length: {len(html_content)}")
    print(html_content[:500])
except Exception as e:
    import traceback
    traceback.print_exc()
