import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from dotenv import load_dotenv
import json
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NarrativeAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        self.prompt_template = PromptTemplate(
            input_variables=["drug", "reaction", "prr", "ror", "n_cases"],
            template="""
            You are a Pharmacovigilance Specialist Agent.
            Generate a structured safety narrative for a potential adverse event signal.
            
            Signal Data:
            - Drug Name: {drug}
            - Adverse Event (AE): {reaction}
            - Proportional Reporting Ratio (PRR): {prr}
            - Reporting Odds Ratio (ROR): {ror}
            - Total Cases Found: {n_cases}
            
            Requirements:
            1. Describe the signal and state the statistical elevation clearly.
            2. Mention that this is based on statistical reporting and does not imply causality.
            3. Suggest a priority level based on the signal strength.
            4. Keep it professional and structured.
            
            Format:
            - Signal Description: ...
            - Statistical Evidence: ...
            - Priority: [Low/Medium/High]
            - Regulatory Note: [Mandatory Disclaimer]
            """
        )

    def generate_narrative(self, signal_data):
        logger.info(f"Generating narrative for {signal_data['drug']} - {signal_data['reaction']}")
        full_prompt = self.prompt_template.format(
            drug=signal_data['drug'],
            reaction=signal_data['reaction'],
            prr=round(signal_data['prr'], 2),
            ror=round(signal_data['ror'], 2),
            n_cases=signal_data['n_cases']
        )
        
        try:
            response = self.llm.invoke(full_prompt)
            narrative = response.content
            
            # Save the narrative (mocking storage)
            self.save_narrative(signal_data, narrative)
            return narrative
            
        except Exception as e:
            logger.error(f"Error generating narrative: {e}")
            return None

    def save_narrative(self, signal_data, narrative):
        # In production, this would go into a DB (DuckDB or Postgres)
        report = {
            "drug": signal_data['drug'],
            "reaction": signal_data['reaction'],
            "narrative": narrative,
            "timestamp": "2026-03-01T00:00:00Z"
        }
        # Appending to a local JSON for demo
        with open('data/narratives.jsonl', 'a') as f:
            f.write(json.dumps(report) + '\n')
            
if __name__ == "__main__":
    agent = NarrativeAgent()
    # Mock signal
    mock_signal = {
        "drug": "HUMIRA",
        "reaction": "Acute Kidney Injury",
        "prr": 3.45,
        "ror": 4.12,
        "n_cases": 12
    }
    narrative = agent.generate_narrative(mock_signal)
    print(narrative)
