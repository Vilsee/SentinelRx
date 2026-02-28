import json
import requests
import zipfile
import io
from kafka import KafkaProducer
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FAERSProducer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = 'faers_raw'

    def fetch_faers_data_sample(self):
        """
        In a real scenario, this would download the heavy XML/JSON zip from FDA.
        For this PRD implementation, we'll simulate fetching a subset of FAERS JSON.
        """
        # Mocking a small set of FAERS records
        mock_data = [
            {
                "primaryid": "12345678",
                "receiptdate": "20260115",
                "patient": {
                    "patientonsetage": "45",
                    "patientsex": "1",
                    "drug": [
                        {"medicinalproduct": "ASPIRIN", "drugindication": "Pain"},
                        {"medicinalproduct": "ZOSYN", "drugindication": "Infection"}
                    ],
                    "reaction": [
                        {"reactionmeddrapt": "Acute Kidney Injury"}
                    ]
                }
            },
            {
                "primaryid": "87654321",
                "receiptdate": "20260210",
                "patient": {
                    "patientonsetage": "62",
                    "patientsex": "2",
                    "drug": [
                        {"medicinalproduct": "HUMIRA", "drugindication": "Rheumatoid Arthritis"}
                    ],
                    "reaction": [
                        {"reactionmeddrapt": "Injection site rash"},
                        {"reactionmeddrapt": "Dizziness"}
                    ]
                }
            }
        ]
        return mock_data

    def run(self):
        logger.info("Starting FAERS Producer...")
        while True:
            records = self.fetch_faers_data_sample()
            for record in records:
                self.producer.send(self.topic, record)
                logger.info(f"Sent FAERS record: {record['primaryid']}")
            
            # Sleep to simulate quarterly or batch processing
            time.sleep(60)

if __name__ == "__main__":
    producer = FAERSProducer()
    producer.run()
