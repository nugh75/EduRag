#sidebar_config.py
import streamlit as st

def sidebar_c(db_path, list_subfolders):
    """Configure the sidebar elements."""
    
    # Add a small decorative bar in the sidebar
    st.sidebar.markdown("---")

    # Temperature slider
    temperature = st.sidebar.slider(
        "Temperatura",
        0.0,
        1.0,
        0.2,
        help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività. Un'alta temperatura consente al modello di esplorare una gamma più ampia di opzioni, generando risposte più diverse e meno prevedibili.",
    )

    # Slider for the number of chunks to retrieve
    similarity_k = st.sidebar.slider(
        "chunk da recuperare",
        1,
        25,
        4,
        help="Nel contesto del Retrieval-Augmented Generation (RAG), i chunk sono segmenti di testo suddivisi da documenti più grandi. Questa suddivisione ottimizza l'elaborazione del modello, mantiene il contesto semantico e migliora la precisione del recupero delle informazioni rilevanti per una query specifica.",
    )

    # Retrieve subfolders from the 'db' directory
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error(
            "Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca."
        )
        return None, None

    # Topic selection (Note: st.selectbox returns the selected value, not the index)
    Indice = st.selectbox("Seleziona il db indicizzato", subfolders)

    return temperature, similarity_k, Indice
