from fastapi import FastAPI
import duckdb
import json
import os

app = FastAPI(title="SentinelRx Signal API")
DB_PATH = 'data/sentinelrx.duckdb'

@app.get("/signals/latest")
def get_latest_signals():
    con = duckdb.connect(DB_PATH)
    # Rerun signal detection on current state
    # This is a bit inefficient for a live API but works for the MVP
    from src.analytics.signal_aggregator import SignalAggregator
    aggregator = SignalAggregator(db_path=DB_PATH)
    signals = aggregator.detect_signals()
    return {"signals": signals}

@app.get("/drug/{name}/events")
def get_drug_events(name: str):
    con = duckdb.connect(DB_PATH)
    events = con.execute("SELECT * FROM events WHERE drug = ?", (name.upper(),)).fetchall()
    return {"drug": name, "events": events}

@app.get("/narratives")
def get_narratives():
    if not os.path.exists('data/narratives.jsonl'):
        return {"narratives": []}
    
    narratives = []
    with open('data/narratives.jsonl', 'r') as f:
        for line in f:
            narratives.append(json.loads(line))
    return {"narratives": narratives}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
