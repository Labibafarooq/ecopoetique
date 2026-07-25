"""
Cleans the new GOLD_narratologie.csv:
1. Converts semicolon separator to tab
2. Fixes known typos: NAR_AUTO→NAR_AUTOD, FIC_INT→FOC_INT, NAR_VAR→NAR_VAR(kept), MOD_DIA→MOD_DIA(kept)
3. Removes junk extra columns (ISBN, prize data etc)
4. Removes empty rows
5. Removes duplicate entries (keeps first occurrence)
6. Outputs clean tab-separated file ready for pipeline
"""

import csv
import io

INPUT  = "GOLD_narratologie.csv"
OUTPUT = "GOLD_narratologie_clean.csv"

# Known typo fixes
FIXES = {
    "NAR_AUTO":  "NAR_AUTOD",
    "FIC_INT":   "FOC_INT",
}

# Valid codes (expanded with new ones found in data)
VALID = {
    "TYPE NARRATEUR":  ["NAR_AUTOD", "NAR_TEM", "NAR_EXT", "NAR_VAR"],
    "FOCALISATION":    ["FOC_INT", "FOC_EXT", "FOC_ZERO", "FOC_VAR"],
    "MODE NARRATIF":   ["MOD_EVT", "MOD_DESC", "MOD_INTR", "MOD_MIX", "MOD_DIA"],
    "REGIME NARRATIF": ["REG_AUTO", "REG_REAL", "REG_FANT", "REG_SPEC"],
    "ESPACE":          ["ESP_UNIT", "ESP_FRAG", "ESP_ITIN", "ESP_IMAG"],
    "INTRIGUE":        ["INTR_LIN", "INTR_FRAG", "INTR_CYC"],
    "TEMPORALITÉ":     ["TEMP_LIN", "TEMP_DIS", "TEMP_DESORD"],
}

def fix_code(code):
    code = code.strip()
    return FIXES.get(code, code)

def is_valid(code, criterion):
    return code in VALID.get(criterion, [])

with open(INPUT, encoding="utf-8") as f:
    content = f.read()

lines = [l for l in content.split('\n') if l.strip() and ';' in l]

OUTPUT_FIELDS = [
    "File", "Year", "Author", "Title",
    "TYPE NARRATEUR", "Acceptable aussi: ",
    "FOCALISATION", "Acceptable aussi: .1",
    "MODE NARRATIF", "Acceptable aussi: .2",
    "REGIME NARRATIF", "Acceptable aussi: .3",
    "ESPACE", "Acceptable aussi: .4",
    "INTRIGUE", "Acceptable aussi: .5",
    "TEMPORALITÉ", "Acceptable aussi: .6",
]

rows = []
seen_files = set()
issues = []

for i, line in enumerate(lines[1:], 2):  # skip header
    cols = line.split(';')
    if len(cols) < 17:
        continue

    filename = cols[0].strip()
    year     = cols[1].strip()
    author   = cols[2].strip()
    title    = cols[3].strip()

    if not filename or not filename.endswith('.txt'):
        continue

    # Skip duplicates
    if filename in seen_files:
        issues.append(f"  ⚠️  Duplicate skipped: {filename}")
        continue
    seen_files.add(filename)

    # Extract and fix codes
    nar      = fix_code(cols[4])
    nar_alt  = fix_code(cols[5]) if len(cols) > 5 else ""
    foc      = fix_code(cols[6]) if len(cols) > 6 else ""
    foc_alt  = fix_code(cols[7]) if len(cols) > 7 else ""
    mod      = fix_code(cols[8]) if len(cols) > 8 else ""
    mod_alt  = fix_code(cols[9]) if len(cols) > 9 else ""
    reg      = fix_code(cols[10]) if len(cols) > 10 else ""
    reg_alt  = fix_code(cols[11]) if len(cols) > 11 else ""
    esp      = fix_code(cols[12]) if len(cols) > 12 else ""
    esp_alt  = fix_code(cols[13]) if len(cols) > 13 else ""
    intr     = fix_code(cols[14]) if len(cols) > 14 else ""
    intr_alt = fix_code(cols[15]) if len(cols) > 15 else ""
    temp     = fix_code(cols[16]) if len(cols) > 16 else ""
    temp_alt = fix_code(cols[17]) if len(cols) > 17 else ""

    # Check for remaining unknown codes
    checks = [
        (nar,      "TYPE NARRATEUR"),
        (foc,      "FOCALISATION"),
        (mod,      "MODE NARRATIF"),
        (reg,      "REGIME NARRATIF"),
        (esp,      "ESPACE"),
        (intr,     "INTRIGUE"),
        (temp,     "TEMPORALITÉ"),
    ]
    for code, crit in checks:
        if code and not is_valid(code, crit):
            issues.append(f"  ⚠️  Unknown code '{code}' for {crit} in {filename}")

    rows.append({
        "File":               filename,
        "Year":               year,
        "Author":             author,
        "Title":              title,
        "TYPE NARRATEUR":     nar,
        "Acceptable aussi: ": nar_alt,
        "FOCALISATION":       foc,
        "Acceptable aussi: .1": foc_alt,
        "MODE NARRATIF":      mod,
        "Acceptable aussi: .2": mod_alt,
        "REGIME NARRATIF":    reg,
        "Acceptable aussi: .3": reg_alt,
        "ESPACE":             esp,
        "Acceptable aussi: .4": esp_alt,
        "INTRIGUE":           intr,
        "Acceptable aussi: .5": intr_alt,
        "TEMPORALITÉ":        temp,
        "Acceptable aussi: .6": temp_alt,
    })

# Write clean output
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Clean gold set saved to: {OUTPUT}")
print(f"   Novels: {len(rows)}")
print(f"\nIssues found and handled:")
for issue in issues:
    print(issue)

print(f"\nValid codes now recognized:")
for crit, codes in VALID.items():
    print(f"  {crit:<20}: {', '.join(codes)}")
