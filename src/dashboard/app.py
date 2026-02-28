import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="SentinelRx - Pharmacovigilance Dashboard", layout="wide")

st.title("🛡️ SentinelRx Pharmacovigilance Agent")
st.markdown("### Signal Detection & Safety Narrative Dashboard")

# Refresh button
if st.sidebar.button("Refresh Signals"):
    st.rerun()

# Get Signals
try:
    response = requests.get("http://localhost:8000/signals/latest")
    signals_data = response.json().get('signals', [])
except:
    signals_data = []

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Detected Signals")
    if signals_data:
        df_signals = pd.DataFrame(signals_data)
        st.dataframe(df_signals, use_container_width=True)
    else:
        st.info("No emerging signals detected currently.")

with col2:
    st.header("Latest Narrative Reports")
    try:
        n_response = requests.get("http://localhost:8000/narratives")
        narratives = n_response.json().get('narratives', [])
        
        for n in reversed(narratives):
            with st.expander(f"Signal Report: {n['drug']} / {n['reaction']}"):
                st.markdown(n['narrative'])
                st.caption(f"Generated at: {n['timestamp']}")
    except:
        st.info("No narratives available.")

# Drug Look up section
st.divider()
st.header("Drug Event Lookup")
drug_query = st.text_input("Enter drug name (e.g., HUMIRA, ASPIRIN)")
if drug_query:
    try:
        e_response = requests.get(f"http://localhost:8000/drug/{drug_query}/events")
        events = e_response.json().get('events', [])
        if events:
            df_events = pd.DataFrame(events, columns=['id', 'source', 'drug', 'reaction', 'timestamp'])
            st.write(f"Total reports found for {drug_query}: {len(events)}")
            st.dataframe(df_events, use_container_width=True)
        else:
            st.warning(f"No events found for {drug_query}")
    except:
        st.error("Failed to connect to API.")

st.sidebar.markdown("""
---
**Tech Stack Metrics**
- **Ingestion**: Kafka
- **Detection**: DuckDB (PRR/ROR)
- **NER**: BioBERT
- **Narratives**: GPT-4o
""")
