#!/usr/bin/env python3
"""
Debug BE HTML Parser
===================
Debug version to see what's happening with the missing BE memories.
"""

from bs4 import BeautifulSoup
import re

def debug_parse():
    """Debug the HTML parsing to find missing BE memories."""
    
    with open(r'e:\Omnimon\utilities\VBE\sheet.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    rows = soup.find_all('tr')
    
    print(f"Total rows found: {len(rows)}")
    
    # Debug specific BE memories
    target_patterns = ['BE GAMMAMON', 'BE JELLYMON', 'BE 25TH ANNIVERSARY', 'BE iMPERIALDRAMON']
    
    for i, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        if len(cells) < 5:
            continue
            
        # Check first few cells for our target patterns
        for j, cell in enumerate(cells[:3]):
            text = cell.get_text(strip=True)
            softmerge_div = cell.find('div', class_='softmerge-inner')
            if softmerge_div:
                text = softmerge_div.get_text(strip=True)
            
            if any(pattern in text for pattern in target_patterns):
                print(f"\n🎯 FOUND PATTERN in row {i}, cell {j}: '{text}'")
                
                # Show this entire row's structure
                print("Row structure:")
                for k, cell in enumerate(cells[:8]):
                    cell_text = cell.get_text(strip=True)
                    softmerge_div = cell.find('div', class_='softmerge-inner')
                    if softmerge_div:
                        cell_text = softmerge_div.get_text(strip=True)
                    print(f"  Cell {k}: '{cell_text}'")
                
                # Look for D-code and character names
                d_code = None
                jp_name = None
                en_name = None
                
                for k, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    softmerge_div = cell.find('div', class_='softmerge-inner')
                    if softmerge_div:
                        cell_text = softmerge_div.get_text(strip=True)
                    
                    if re.match(r'D\d+_\d+', cell_text):
                        d_code = cell_text
                    elif k == 3 and cell_text and not cell_text.startswith('BE:'):  # JP name usually in column 3
                        jp_name = cell_text
                    elif k == 4 and cell_text and not cell_text.startswith('BE:'):  # EN name usually in column 4  
                        en_name = cell_text
                
                if d_code and (jp_name or en_name):
                    print(f"  ✅ Valid character: {d_code} -> JP: '{jp_name}' / EN: '{en_name}'")
                else:
                    print(f"  ❌ Incomplete: D-code: '{d_code}', JP: '{jp_name}', EN: '{en_name}'")

if __name__ == "__main__":
    debug_parse()