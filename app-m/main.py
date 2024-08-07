import streamlit as st
from view_and_manage_indexes import vedi_e_gestisci_db  # Gestisce la visualizzazione, rinomina e cancellazione degli indici
from pdf_processing_page import pdf_processing_page     # Gestisce la creazione di nuovi database indicizzati
from add_pdfs_to_index import add_pdfs_to_existing_index # Aggiunge PDF a un database esistente
from remove_pdfs_from_index import remove_pdfs_from_index # Rimuove PDF da un database esistente
from query_page import query_page                       # Gestisce le query su un database specifico
from query_pageg import query_pageg                     # Gestisce le query su un database specifico usando GPT-4o-mini
from openk import openk                    # Gestisce le query su un database specifico usando GPT-4o-mini con le proprie chiavi

def descrizione_edubot():
    descrizione = """
    **Che cos'è Edubot?**

    Edubot è un assistente virtuale progettato per aiutare studenti e docenti a gestire e navigare facilmente documenti PDF nei corsi online. Permette di ottenere rapidamente risposte a domande specifiche e di evidenziare i passaggi importanti nei documenti per ulteriori approfondimenti.

    **Funzionalità Principali:**

    - **Indicizzazione dei Documenti PDF:** Edubot permette di creare e gestire database indicizzati dei tuoi documenti PDF, facilitando la ricerca e il recupero delle informazioni. Puoi organizzare i documenti in database specifici e fare ricerche mirate su di essi.
    - **Rinominare e Cancellare Indici:** Consente di rinominare e cancellare i database indicizzati esistenti.
    - **Aggiunta e Rimozione di PDF:** Puoi aggiungere nuovi documenti PDF a un database esistente o rimuoverne alcuni.
    - **Query sui Database:** Puoi interrogare i database per ottenere informazioni specifiche dai documenti PDF indicizzati.
    - **Interfaccia Intuitiva:** Interagisci con Edubot come faresti con un assistente umano, ricevendo risposte chiare e facili da capire.
    - **Storico delle Interazioni:** Accedi facilmente alle domande e risposte precedenti per un apprendimento continuo.

    **Tecnologie alla Base di Edubot:**

    **Chunk:**

    - **Che cos'è:** I chunk sono piccoli segmenti di testo creati dai documenti PDF. Ogni chunk rappresenta un passaggio significativo che può essere analizzato singolarmente.
    - **Come funziona:** Suddividendo i documenti in chunk, Edubot riesce a gestire meglio il contenuto e a trovare rapidamente le informazioni richieste.

    **Retrieval-Augmented Generation (RAG):**

    - **Che cos'è:** La tecnologia RAG combina il recupero delle informazioni con la generazione di testo. Edubot utilizza RAG per fornire risposte dettagliate e pertinenti basate sul contenuto dei documenti PDF.
    - **Come funziona:** Quando poni una domanda, Edubot recupera i passaggi pertinenti dai documenti e genera una risposta utilizzando questi elementi, fornendo un contesto chiaro e completo.

    **Embedding:**

    - **Che cos'è:** L’embedding è un metodo per rappresentare il testo sotto forma di numeri, catturando il significato e le relazioni tra le parole.
    - **Come funziona:** Edubot utilizza embedding per comprendere e confrontare i contenuti, migliorando la precisione delle risposte.

    **Indicizzazione con FAISS:**

    - **Che cos'è:** FAISS (Facebook AI Similarity Search) è un sistema che permette di creare database indicizzati dai documenti PDF. 
    - **Come funziona:** Questi database indicizzati consentono un rapido recupero delle informazioni, facilitando la ricerca di passaggi pertinenti e migliorando l'efficienza della risposta alle query.

    **Perché Usare Edubot?**

    - **Accesso Immediato alle Informazioni:** Trova velocemente le informazioni necessarie nei documenti PDF, senza dover cercare manualmente.
    - **Apprendimento Migliorato:** Consultare i passaggi suggeriti da Edubot permette di approfondire e comprendere meglio il materiale.
    - **Supporto ai Corsi Online:** Ideale per ambienti educativi, aiutando studenti e docenti a gestire i contenuti in modo più efficace.
    - **Flessibilità nell'Indicizzazione:** Consente di organizzare i documenti PDF in database specifici, facilitando ricerche mirate e personalizzate.

    Edubot rende la gestione dei documenti PDF più semplice ed efficace, migliorando l'accesso alle informazioni cruciali in contesti educativi.
    """
    return descrizione

def main():
    # Configurazione della pagina
    st.set_page_config(page_title="Interfaccia di Edubot", layout="wide")

    st.title("Edubot")

    # Barra di navigazione in alto
    menu = [
        "Home", 
        "Gestisci Indici", 
        "Crea db indicizzato", 
        "Aggiungi PDF a db", 
        "Rimuovi PDF da db", 
        "Esegui Query con Ollama",
        "Esegui Query con GPT-4o-mini",
        "Esegui Query con GPT-40-mini con la tua Key"
    ]
    pagina = st.radio("Navigazione", menu, horizontal=True)

    # Messaggio di benvenuto nella barra laterale
    st.sidebar.title("Benvenuto nell'Interfaccia di Edubot")
    st.sidebar.write("""
    Usa la barra di navigazione in alto per cambiare pagina:
    - **Gestisci Indici**: visualizza, rinomina o cancella un indice esistente nella directory db.
    - **Crea db indicizzato**: crea un nuovo database indicizzato dai documenti PDF.
    - **Aggiungi PDF a db**: aggiungi nuovi documenti PDF a un database indicizzato esistente.
    - **Rimuovi PDF da db**: rimuovi documenti PDF esistenti da un database indicizzato.
    - **Esegui Query**: interroga un database indicizzato per ottenere informazioni specifiche.
    - **Esegui Query con GPT-4o-mini**: interroga un database indicizzato utilizzando GPT-4o-mini.
    - **Esegui Query con GPT-4o-mini**: interroga un database indicizzato utilizzando GPT-4o-mini con la tua key.
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

    elif pagina == "Gestisci Indici":
        st.header("Gestisci Indici")
        vedi_e_gestisci_db()

    elif pagina == "Crea db indicizzato":
        st.header("Crea db indicizzato")
        pdf_processing_page()

    elif pagina == "Aggiungi PDF a db":
        st.header("Aggiungi PDF a db")
        add_pdfs_to_existing_index()

    elif pagina == "Rimuovi PDF da db":
        st.header("Rimuovi PDF da db")
        remove_pdfs_from_index()

    elif pagina == "Esegui Query con Ollama":
        st.header("Esegui Query con Ollama")
        query_page()

    elif pagina == "Esegui Query con GPT-4o-mini":
        st.header("Esegui Query con GPT-4o-mini")
        query_pageg()
        
    elif pagina == "Esegui Query con GPT-40-mini con la tua Key":
        st.header("Esegui Query con GPT-40-mini con la tua Key")
        openk()

if __name__ == "__main__":
    main()
