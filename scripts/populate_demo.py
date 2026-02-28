import duckdb
import pandas as pd
import os
import json

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Connect to DuckDB
con = duckdb.connect('data/sentinelrx.duckdb')

# Create table
con.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id VARCHAR,
        source VARCHAR,
        drug VARCHAR,
        reaction VARCHAR,
        timestamp TIMESTAMP
    )
""")

# Insert sample data to trigger signals
# Signal criteria: PRR > 2 AND ROR lower CI > 1 AND n_cases >= 3
# Signal 1: HUMIRA -> Acute Kidney Injury (High signal)
# Signal 2: ZOSYN -> Dizziness (Low signal)

samples = [
    # HUMIRA + AKI (Signal)
    ('H1', 'FAERS', 'HUMIRA', 'Acute Kidney Injury', '2026-01-01'),
    ('H2', 'FAERS', 'HUMIRA', 'Acute Kidney Injury', '2026-01-02'),
    ('H3', 'Reddit', 'HUMIRA', 'Acute Kidney Injury', '2026-01-03'),
    ('H4', 'FAERS', 'HUMIRA', 'Headache', '2026-01-04'),
    
    # Background data (to make PRR work)
    ('B1', 'FAERS', 'ASPIRIN', 'Headache', '2026-01-05'),
    ('B2', 'FAERS', 'ASPIRIN', 'Headache', '2026-01-06'),
    ('B3', 'FAERS', 'ASPIRIN', 'Headache', '2026-01-07'),
    ('B4', 'FAERS', 'ASPIRIN', 'Headache', '2026-01-08'),
    ('B5', 'FAERS', 'ASPIRIN', 'Headache', '2026-01-09'),
    ('B6', 'FAERS', 'ASPIRIN', 'Acute Kidney Injury', '2026-01-10'), # Only 1 background AKI
]

for s in samples:
    con.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)", s)

# Create a sample narrative
narrative = {
    "drug": "HUMIRA",
    "reaction": "Acute Kidney Injury",
    "narrative": "### Signal Description\nAdalimumab (Humira) shows a statistically significant elevation in reports of Acute Kidney Injury (AKI) across both clinical FAERS data and social media discussions.\n\n### Statistical Evidence\n- **Cases**: 3\n- **PRR**: 4.5\n- **ROR CI**: 2.1 - 8.4\n\n### Priority: [High]\n### Regulatory Note\nThis is a statistical signal and does not confirm a causal link. Further clinical validation is required.",
    "timestamp": "2026-03-01T22:40:00Z"
}

with open('data/narratives.jsonl', 'w') as f:
    f.write(json.dumps(narrative) + '\n')

print("Mock data populated successfully.")
