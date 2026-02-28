import json
import time
import random
from kafka import KafkaProducer

# SIDER (Side Effect Resource) Mock Data
# This represents "known" side effects documented in labels
SIDER_KNOWN_EFFECTS = {
    "SEMAGLUTIDE": ["Nausea", "Vomiting", "Diarrhea", "Abdominal Pain"],
    "NIVOLUMAB": ["Fatigue", "Rash", "Nausea", "Pruritus"],
    "APIXABAN": ["Gingival bleeding", "Epistaxis", "Hematoma"],
    "ASPIRIN": ["Dyspepsia", "Gastritis", "Headache"],
    "ADALIMUMAB": ["Injection site reaction", "Headache", "Rash"]
}

def get_kafka_producer():
    try:
        return KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        print(f"Kafka Producer Error: {e}")
        return None

def produce_sider_data():
    producer = get_kafka_producer()
    print("🚀 Starting SIDER Data Producer (Known Adverse Events Repository)...")
    
    for drug, effects in SIDER_KNOWN_EFFECTS.items():
        for effect in effects:
            data = {
                "source": "SIDER_DB",
                "drug_name": drug,
                "adverse_event": effect,
                "evidence_type": "Label_Indicated",
                "timestamp": time.time()
            }
            if producer:
                producer.send('sider_known_events', value=data)
            print(f"✅ Ingested SIDER Ground Truth: {drug} -> {effect}")
            time.sleep(0.1)
    
    if producer:
        producer.flush()
    print("🏁 SIDER Data Ingestion Complete.")

if __name__ == "__main__":
    produce_sider_data()
