import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def openai_m():
    # Aggiunta delle opzioni per selezionare il modello LLM e inserire la chiave API
    api_choice = st.sidebar.selectbox("Scegli la chiave API da usare", ["Usa chiave di sistema", "Inserisci la tua chiave API"], index=1)
    
    if api_choice == "Inserisci la tua chiave API":
        openai_api_key = st.sidebar.text_input("Inserisci la tua chiave API OpenAI", st.session_state.get("user_api_key", ""), type="password")
        st.session_state.user_api_key = openai_api_key  # Salva la chiave API inserita dall'utente
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["gpt-4o", "gpt-4o-mini"], index=1)
    st.session_state.model_choice = model_choice  # Salva la scelta del modello

    return openai_api_key  # Return the API key
