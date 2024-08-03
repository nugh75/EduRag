# main.py

import os
import streamlit as st

def descrizione_edubot():
    descrizione = """
    **Che cos'è Edubot?**

    Edubot è un assistente virtuale progettato per aiutare studenti e docenti a gestire e navigare facilmente documenti PDF nei corsi online. Permette di ottenere rapidamente risposte a domande specifiche e di evidenziare i passaggi importanti nei documenti per ulteriori approfondimenti.

    **Funzionalità Principali:**

    - **Indicizzazione dei Documenti PDF:** Edubot permette di creare e gestire db indicizzati dei tuoi documenti PDF, facilitando la ricerca e il recupero delle informazioni. Puoi organizzare i documenti in db specifici e fare ricerche mirate su di essi.
    - **Ricerca Rapida e Precisa:** Edubot analizza i documenti PDF per trovare le informazioni rilevanti e restituisce passaggi specifici per approfondimenti successivi.
    - **Interfaccia Intuitiva:** Interagisci con Edubot come faresti con un assistente umano, ricevendo risposte chiare e facili da capire.
    - **Storico delle Interazioni:** Accedi facilmente alle domande e risposte precedenti per un apprendimento continuo.
    - **Gestione dei Chunk:** Gli utenti possono decidere quanto devono essere grandi i segmenti di testo (chunk) analizzati, ottimizzando il recupero delle informazioni in base alle loro esigenze.

    **Tecnologie alla Base di Edubot**

    **Chunk:**

    - **Che cos'è:** I chunk sono piccoli segmenti di testo creati dai documenti PDF. Ogni chunk rappresenta un passaggio significativo che può essere analizzato singolarmente.
    - **Come funziona:** Suddividendo i documenti in chunk, Edubot riesce a gestire meglio il contenuto e a trovare rapidamente le informazioni richieste. La dimensione dei chunk può essere regolata per soddisfare le esigenze specifiche di ogni utente.

    **Retrieval-Augmented Generation (RAG):**

    - **Che cos'è:** La tecnologia RAG combina il recupero delle informazioni con la generazione di testo. Edubot utilizza RAG per fornire risposte dettagliate e pertinenti basate sul contenuto dei documenti PDF.
    - **Come funziona:** Quando poni una domanda, Edubot recupera i passaggi pertinenti dai documenti e genera una risposta utilizzando questi elementi, fornendo un contesto chiaro e completo.

    **Embedding:**

    - **Che cos'è:** L’embedding è un metodo per rappresentare il testo sotto forma di numeri, catturando il significato e le relazioni tra le parole.
    - **Come funziona:** Edubot utilizza embedding per comprendere e confrontare i contenuti, migliorando la precisione delle risposte.

    **Indicizzazione con FAISS:**

    - **Che cos'è:** FAISS (Facebook AI Similarity Search) è un sistema che permette di creare db indicizzati dai documenti PDF. 
    - **Come funziona:** Questi db indicizzati consentono un rapido recupero delle informazioni, facilitando la ricerca di passaggi pertinenti e migliorando l'efficienza della risposta alle query.

    **Architettura del Progetto:**

    - **Modelli di Linguaggio Naturale:** Edubot impiega modelli avanzati di linguaggio per generare risposte in modo chiaro e naturale, simulando un’interazione umana.
    - **Integrazione con Streamlit:** La piattaforma Streamlit offre un’interfaccia semplice e interattiva, facilitando il caricamento dei documenti e l’interazione con Edubot.

    **Perché Usare Edubot?**

    - **Accesso Immediato alle Informazioni:** Trova velocemente le informazioni necessarie nei documenti PDF, senza dover cercare manualmente.
    - **Apprendimento Migliorato:** Consultare i passaggi suggeriti da Edubot permette di approfondire e comprendere meglio il materiale.
    - **Supporto ai Corsi Online:** Ideale per ambienti educativi, aiutando studenti e docenti a gestire i contenuti in modo più efficace.
    - **Flessibilità nell'Indicizzazione:** Consente di organizzare i documenti PDF in db specifici, facilitando ricerche mirate e personalizzate.

    Edubot rende la gestione dei documenti PDF più semplice ed efficace, migliorando l'accesso alle informazioni cruciali in contesti educativi.
    """
    return descrizione

def leggi_descrizioni_e_documenti(db_path):
    """Legge le descrizioni e i documenti da ciascun indice nella cartella db."""
    indici_info = []
    try:
        for subfolder in sorted(os.listdir(db_path)):  # Ordina alfabeticamente
            subfolder_path = os.path.join(db_path, subfolder)
            if os.path.isdir(subfolder_path):
                description_file = os.path.join(subfolder_path, "description.txt")
                if os.path.exists(description_file):
                    with open(description_file, "r", encoding="utf-8") as file:
                        lines = file.readlines()
                        # Processa il file per ottenere descrizione e documenti
                        descrizione = ""
                        documenti = []
                        for line in lines:
                            if line.startswith("Descrizione dell'indice:"):
                                descrizione = line.replace("Descrizione dell'indice: ", "").strip()
                            elif line.startswith("-"):
                                documenti.append(line.strip("- ").strip())
                    indici_info.append({
                        "nome": subfolder,
                        "descrizione": descrizione,
                        "documenti": documenti
                    })
    except Exception as e:
        st.error(f"Errore nella lettura degli indici: {e}")
    return indici_info

def main():
    # Configurazione della pagina
    st.set_page_config(page_title="Interfaccia di Edubot", layout="wide")

    st.title("Edubot")

    # Barra di navigazione in alto
    menu = ["Home", "Creazione db indicizzato", "Query","Query gpt-4o-mini", "Visualizza e rimuovi db indicizzato", "Aggiungi PDF a db indicizzato", "Rimuovi PDF a db indicizzato"]
    pagina = st.radio("Navigazione", menu, horizontal=True)

    # Messaggio di benvenuto nella barra laterale
    st.sidebar.title("Benvenuto nell'Interfaccia di Edubot")
    st.sidebar.write("""
    Usa la barra di navigazione in alto per cambiare pagina:
    - **Creazione db**: crea o carica un db indicizzato per facilitare la ricerca e il recupero delle informazioni.
    - **Query**: tramite un LLM da te scelto puoi interrogare uno dei db da te creati.
    - **Visualizza e cancella db indicizzati**: Visualizza e cancella i db indicizzati esistenti.
    - **Aggiungi PDF**: aggiungi nuovi documenti PDF a un db indicizzato esistente.
    - **Rimuovi PDF**: rimuovi PDF esistenti e i loro chunk associati da un db indicizzato esistente.
    """)

    # Disclaimer
    st.sidebar.markdown("""
    ---
    **Disclaimer:**
    Le informazioni fornite da Edubot devono essere verificate. I modelli di linguaggio possono dare risposte non sempre accurate. È consigliabile controllare le fonti.
    
    
    """)

    # Logica per visualizzare il contenuto della pagina selezionata
    if pagina == "Home":
        st.header("Home")
        st.markdown(descrizione_edubot())

    elif pagina == "Creazione db indicizzato":
        st.header("Creazione db indicizzato")
        from pdf_processing_page import pdf_processing_page
        pdf_processing_page()

    elif pagina == "Query":
        st.header("Query")
        from query_page import query_page
        query_page()
        
    elif pagina == "Query gpt-4o-mini":
        st.header("Query gpt-4o-mini")
        from query_pageg import query_pageg
        query_pageg()
        
    elif pagina == "Visualizza e rimuovi db indicizzato":
        st.header("Visualizza e rimuovi db indicizzato")
        from view_and_delete_indexes import view_and_delete_indexes
        view_and_delete_indexes()

    elif pagina == "Aggiungi PDF a db indicizzato":
        st.header("Aggiungi PDF a db indicizzato")
        from add_pdfs_to_index import add_pdfs_to_existing_index
        add_pdfs_to_existing_index()

    elif pagina == "Rimuovi PDF a db indicizzato":
        st.header("Rimuovi PDF a db indicizzato")
        from remove_pdfs_from_index import remove_pdfs_from_index
        remove_pdfs_from_index()

    # Visualizzazione degli indici, delle descrizioni e dei documenti alla fine della barra laterale
    st.sidebar.header("db indicizzati Disponibili")
    db_path = "db"
    indici_info = leggi_descrizioni_e_documenti(db_path)

    for indice in indici_info:
        with st.sidebar.expander(indice["nome"], expanded=False):
            st.write(f"**Descrizione:** {indice['descrizione']}")
            st.write("**Documenti:**")
            for doc in indice["documenti"]:
                st.write(f"- {doc}")

if __name__ == "__main__":
    main()
