import json
from kafka import KafkaConsumer, KafkaProducer
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NERConsumer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.consumer = KafkaConsumer(
            'faers_raw', 'reddit_raw',
            bootstrap_servers=bootstrap_servers,
            group_id='sentinelrx-ner-group',
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.output_topic = 'processed_entities'
        
        # Load BioBERT model
        # Using a publicly available biomedical NER model
        model_name = "dmis-lab/biobert-base-cased-v1.2"
        # We'll use a specific AE/drug extraction model if possible,
        # but for demonstration, let's use a common biomedical NER pipeline
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.ner_pipeline = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")

    def filter_medical_relevance(self, text):
        """
        Simple classifier to filter out noise, especially for social media.
        In a real scenario, this would be a separate BERT model.
        """
        keywords = ['drug', 'side effect', 'patient', 'doctor', 'pain', 'medication', 'pill', 'dose', 'rx']
        return any(kw in text.lower() for kw in keywords)

    def process_messages(self):
        logger.info("NER Consumer started. Listening for raw messages...")
        for message in self.consumer:
            raw_data = message.value
            source = message.topic
            
            # Extract text to process
            if source == 'faers_raw':
                # FAERS is structured, but we may want to process reaction text
                # For demonstration, we simulate extraction from FAERS
                processed_record = self.handle_faers(raw_data)
            else:
                text = f"{raw_data.get('title', '')} {raw_data.get('text', '')}"
                if self.filter_medical_relevance(text):
                    processed_record = self.handle_reddit(raw_data, text)
                else:
                    logger.info(f"Skipping Reddit post {raw_data.get('id')} - Not medically relevant.")
                    continue
            
            if processed_record:
                self.producer.send(self.output_topic, processed_record)
                logger.info(f"Processed and sent entity record from {source}")

    def handle_faers(self, data):
        # Structuring FAERS data for the signal analytics
        # Extract drug/reaction pairs
        drugs = [d['medicinalproduct'] for d in data['patient']['drug']]
        reactions = [r['reactionmeddrapt'] for r in data['patient']['reaction']]
        
        return {
            "source": "FAERS",
            "primaryid": data['primaryid'],
            "drugs": drugs,
            "reactions": reactions,
            "severity": "Unknown", # FAERS has specific fields for this
            "timestamp": data['receiptdate']
        }

    def handle_reddit(self, data, text):
        # Use BioBERT for Reddit text to extract drugs and reactions
        entities = self.ner_pipeline(text)
        
        # Mapping BioBERT entities (this is a simplified mapping)
        extracted_drugs = []
        extracted_reactions = []
        
        for ent in entities:
            # Simplified logic for demo: BioBERT identifies biomedical entities
            # In a production setup, we would use a model fine-tuned for AE/Drug specifically
            if ent['entity_group'] in ['B-DRUG', 'I-DRUG', 'DRUG']:
                extracted_drugs.append(ent['word'])
            elif ent['entity_group'] in ['B-REACTION', 'I-REACTION', 'REACTION', 'DISEASE']:
                extracted_reactions.append(ent['word'])

        if not extracted_drugs or not extracted_reactions:
            return None

        return {
            "source": "Reddit",
            "id": data['id'],
            "drugs": list(set(extracted_drugs)),
            "reactions": list(set(extracted_reactions)),
            "text_snippet": text[:200],
            "timestamp": data['created_utc']
        }

if __name__ == "__main__":
    consumer = NERConsumer()
    consumer.process_messages()
