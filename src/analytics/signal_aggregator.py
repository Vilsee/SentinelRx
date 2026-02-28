import duckdb
import json
from kafka import KafkaConsumer
import logging
import pandas as pd
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalAggregator:
    def __init__(self, db_path='data/sentinelrx.duckdb'):
        self.con = duckdb.connect(db_path)
        self.init_db()
        self.consumer = KafkaConsumer(
            'processed_entities',
            bootstrap_servers=['localhost:9092'],
            group_id='sentinelrx-aggregator-group',
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )

    def init_db(self):
        # Create tables for events
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id VARCHAR,
                source VARCHAR,
                drug VARCHAR,
                reaction VARCHAR,
                timestamp TIMESTAMP
            )
        """)
        logger.info("Initialized DuckDB tables.")

    def insert_event(self, drug, reaction, source, event_id, timestamp):
        # Flattening drug-reaction pairs
        self.con.execute("""
            INSERT INTO events VALUES (?, ?, ?, ?, ?)
        """, (event_id, source, drug, reaction, timestamp))

    def calculate_disproportionality(self, target_drug, target_reaction):
        """
        PRR = (a / (a + b)) / (c / (c + d))
        a: reports with target drug and target reaction
        b: reports with target drug and NOT target reaction
        c: reports with NOT target drug and target reaction
        d: reports with NOT target drug and NOT target reaction
        """
        query = f"""
        WITH counts AS (
            SELECT
                COUNT(*) FILTER (WHERE drug = '{target_drug}' AND reaction = '{target_reaction}') as a,
                COUNT(*) FILTER (WHERE drug = '{target_drug}' AND reaction != '{target_reaction}') as b,
                COUNT(*) FILTER (WHERE drug != '{target_drug}' AND reaction = '{target_reaction}') as c,
                COUNT(*) FILTER (WHERE drug != '{target_drug}' AND reaction != '{target_reaction}') as d
            FROM events
        )
        SELECT a, b, c, d FROM counts;
        """
        result = self.con.execute(query).fetchone()
        a, b, c, d = result
        
        if (a + b) == 0 or (c + d) == 0 or c == 0:
            return None
        
        prr = (a / (a + b)) / (c / (c + d))
        
        # Reporting Odds Ratio (ROR)
        # ROR = (a/c) / (b/d)
        if b == 0 or c == 0:
            ror = float('inf')
        else:
            ror = (a / c) / (b / d) if d > 0 else float('inf')
            
        # Lower confidence interval for ROR
        # ln(ROR) - 1.96 * sqrt(1/a + 1/b + 1/c + 1/d)
        if a > 0 and b > 0 and c > 0 and d > 0:
            se_ln_ror = math.sqrt(1/a + 1/b + 1/c + 1/d)
            ror_lower_ci = math.exp(math.log(ror) - 1.96 * se_ln_ror)
        else:
            ror_lower_ci = 0

        return {
            "prr": prr,
            "ror": ror,
            "ror_lower_ci": ror_lower_ci,
            "n_cases": a
        }

    def detect_signals(self):
        # Identify all unique drug-reaction pairs
        pairs = self.con.execute("SELECT DISTINCT drug, reaction FROM events").fetchall()
        signals = []
        for drug, reaction in pairs:
            metrics = self.calculate_disproportionality(drug, reaction)
            if metrics:
                # PRR > 2 AND ROR lower CI > 1, flag as emerging signal
                if metrics['prr'] > 2 and metrics['ror_lower_ci'] > 1 and metrics['n_cases'] >= 3:
                    signals.append({
                        "drug": drug,
                        "reaction": reaction,
                        **metrics
                    })
        return signals

    def run(self):
        logger.info("Signal Aggregator started. Ingesting from Kafka...")
        for message in self.consumer:
            data = message.value
            source = data['source']
            event_id = data.get('primaryid') or data.get('id')
            timestamp = pd.to_datetime(data['timestamp'], unit='s') if source == 'Reddit' else pd.to_datetime(data['timestamp'])
            
            for drug in data['drugs']:
                for reaction in data['reactions']:
                    self.insert_event(drug, reaction, source, event_id, timestamp)
            
            # Periodically check for signals
            # In a production environment, this would be scheduled
            # For this demo, check every 10 messages
            if message.offset % 10 == 0:
                detected = self.detect_signals()
                if detected:
                    logger.warning(f"DETECTED {len(detected)} POTENTIAL SIGNALS: {detected}")
                    # Trigger narrative generation for one of the signals (Step 4 preview)
                    # This would ideally be sent to another Kafka topic 'detected_signals'

if __name__ == "__main__":
    import os
    if not os.path.exists('data'):
        os.makedirs('data')
    aggregator = SignalAggregator()
    aggregator.run()
