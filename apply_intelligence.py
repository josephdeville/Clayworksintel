#!/usr/bin/env python3
import csv
import re

def extract_company_intelligence(filepath):
    """Extract GTM Context and Acquisition Angles from a batch intelligence file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    companies = {}
    
    # Split by company sections (## N. COMPANY_NAME)
    sections = re.split(r'\n## \d+\. ', content)
    
    for section in sections[1:]:  # Skip first empty section
        # Extract company name from first line
        lines = section.split('\n')
        first_line = lines[0]
        
        # Extract company name (before "(Company Score:")
        match = re.match(r'([A-Z][A-Z\s&]+?)\s+\(Company Score:', first_line)
        if not match:
            continue
        
        company_name = match.group(1).strip()
        
        # Extract GTM Context
        gtm_start = section.find('### GTM CONTEXT')
        gtm_end = section.find('### ACQUISITION ANGLES')
        
        if gtm_start == -1 or gtm_end == -1:
            continue
        
        gtm_content = section[gtm_start:gtm_end]
        # Remove header and extract content after ":"
        gtm_lines = gtm_content.split('\n')[1:]  # Skip "### GTM CONTEXT..." line
        gtm_text = '\n'.join(gtm_lines).strip()
        
        # Extract Acquisition Angles
        angles_start = gtm_end
        # Find next section (---) or end
        next_section = section.find('\n---', angles_start)
        
        if next_section == -1:
            angles_content = section[angles_start:]
        else:
            angles_content = section[angles_start:next_section]
        
        # Remove header and extract content
        angles_lines = angles_content.split('\n')[1:]  # Skip "### ACQUISITION ANGLES..." line
        angles_text = '\n'.join(angles_lines).strip()
        
        companies[company_name] = {
            'gtm': gtm_text,
            'angles': angles_text
        }
    
    return companies

# Extract intelligence from all batch files
all_intelligence = {}

for batch_file in ['batch1_intelligence.md', 'batch2_intelligence.md', 'batch3_intelligence.md']:
    try:
        intelligence = extract_company_intelligence(f'/home/user/Clayworksintel/{batch_file}')
        all_intelligence.update(intelligence)
        print(f"Extracted {len(intelligence)} companies from {batch_file}")
    except Exception as e:
        print(f"Error processing {batch_file}: {e}")

print(f"\nTotal companies extracted: {len(all_intelligence)}")
print(f"Companies: {list(all_intelligence.keys())}\n")

# Read original CSV
input_file = '/home/user/Clayworksintel/Complete_Contacts_Scored.csv'
output_file = '/home/user/Clayworksintel/Complete_Contacts_Deep_Research.csv'

with open(input_file, 'r', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    rows = list(reader)

# Enrich rows - match company names
enriched_count = 0
companies_matched = set()

for row in rows:
    company = row['Company'].strip().upper() if row['Company'] else ""
    
    # Try to match with intelligence
    matched = False
    for intel_company, data in all_intelligence.items():
        intel_upper = intel_company.upper()
        
        # Direct match or contains match
        if intel_upper == company or intel_upper in company or company in intel_upper:
            row['GTM Context'] = data['gtm']
            row['Acquisition Angle'] = data['angles']
            enriched_count += 1
            companies_matched.add(intel_company)
            matched = True
            break
    
    if not matched and company:
        # Check for special cases
        for intel_company, data in all_intelligence.items():
            if (
                ("ELEVEN" in company and "ELEVENLABS" in intel_company) or
                ("TUNECORE" in company and "TUNECORE" in intel_company) or
                ("DISTROKID" in company and "DISTROKID" in intel_company) or
                (company == "AVID TECHNOLOGY" and intel_company == "AVID") or
                ("GAMEANALYTICS" in company and "GAMEANALYTICS" in intel_company) or
                ("LANDR" in company and "LANDR" in intel_company)
            ):
                row['GTM Context'] = data['gtm']
                row['Acquisition Angle'] = data['angles']
                enriched_count += 1
                companies_matched.add(intel_company)
                break

# Write enriched CSV
with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
    if rows:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

print(f"✅ Generated {output_file}")
print(f"✅ Total contacts: {len(rows)}")
print(f"✅ Enriched contacts: {enriched_count}")
print(f"✅ Unique companies enriched: {len(companies_matched)}")
print(f"✅ Companies enriched: {sorted(companies_matched)}")
