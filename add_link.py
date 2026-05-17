import os
import re

html_files = [f for f in os.listdir('.') if f.endswith('.html')]
link = """      <li>
        <a href="charts.html">
          <i class="fa-solid fa-chart-pie"></i>
          <span>Charts</span>
        </a>
      </li>
"""

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'charts.html' not in content and '<!-- ================= SIDEBAR ================= -->' in content:
        # Insert after the last <li> before </ul> in sidebar-nav
        new_content = re.sub(r'(</ul>\s*</nav>)', link + r'\1', content)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)

print(f"Added charts.html to {len(html_files)} files.")
