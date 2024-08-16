import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def anthropic_m():
    # Aggiunta delle opzioni per selezionare il modello LLM e inserire la chiave API
    api_choice = st.sidebar.selectbox("Scegli la chiave API da usare", ["Usa chiave di sistema", "Inserisci la tua chiave API"], index=1)
    
    if api_choice == "Inserisci la tua chiave API":
        claude_api_key = st.sidebar.text_input("Inserisci la tua chiave API Anthropics", st.session_state.get("user_api_key", ""), type="password")
        st.session_state.user_api_key = claude_api_key  # Salva la chiave API inserita dall'utente
    else:
        # Get the API key from an environment variable
        claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["none", "claude-3-5-sonnet-20240620"], index=1)
    st.session_state.model_choice = model_choice  # Salva la scelta del modello
    
    return claude_api_key  # Return the API key
