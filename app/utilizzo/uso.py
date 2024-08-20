import streamlit as st

def get_uso():
    """
    Displays the guide for the first use of Edubot, including specific use cases and settings for LLM selection and API keys.
    """
    st.markdown("""
    # Guida al Primo Utilizzo (DA SISTEMARE)

    Benvenuto in Edubot! Questa guida ti aiuterà a configurare e utilizzare al meglio le funzionalità disponibili.

    ## Impostazioni Principali

    ### Selezione del Modello di Linguaggio (LLM)
    Edubot supporta diversi modelli di linguaggio (LLM) tra cui scegliere, come GPT-4 di OpenAI e Claude di Anthropic. La selezione del modello può influenzare la qualità delle risposte e la modalità di interazione. 

    **Come scegliere il LLM:**
    - **GPT-4 di OpenAI:** Ideale per compiti che richiedono risposte più dettagliate e creative.
    - **Claude di Anthropic:** Può essere preferito per interazioni più concise e specifiche.

    Puoi selezionare il modello di linguaggio desiderato dal menù di interrogazione del database indicizzato.

    ### Utilizzo delle Proprie Chiavi API
    In alcuni casi, potresti voler utilizzare le tue chiavi API per accedere ai servizi LLM, specialmente se hai un abbonamento con OpenAI o un altro provider.

    **Come impostare la tua chiave API:**
    - Vai nella sezione delle impostazioni all'interno dell'applicazione.
    - Inserisci la tua chiave API personale per il servizio LLM che desideri utilizzare (ad esempio, OpenAI o Anthropic).
    - Salva le impostazioni. Le tue chiavi saranno utilizzate per le chiamate API quando interagisci con il modello di linguaggio selezionato.

    ### Temperatura
    La temperatura controlla il livello di creatività delle risposte generate. Un valore basso (es. 0.2) rende le risposte più deterministiche e prevedibili, mentre un valore alto (es. 0.8) le rende più varie e creative. Puoi regolare la temperatura in base alle tue esigenze.

    ### Chunk
    I chunk sono segmenti di testo che vengono creati quando un documento viene caricato e processato. Questi chunk vengono utilizzati per indicizzare e recuperare le informazioni in modo efficiente. È importante scegliere una dimensione di chunk che bilanci la precisione della ricerca con le risorse computazionali.

    ### File Audio
    Edubot ti permette di scaricare le risposte in formato audio (mp3). Questa funzionalità è utile se desideri ascoltare i riassunti o le spiegazioni mentre fai altro.

    ## Funzioni Principali

    ### Creare un Database Indicizzato
    Puoi creare un database indicizzato caricando documenti in formato PDF, DOC, TXT. Una volta indicizzati, potrai effettuare ricerche su di essi e ottenere risposte contestualizzate.

    ### Riassunto
    Puoi richiedere a Edubot di creare un riassunto personalizzato di un testo. È possibile settare la lunghezza e il dettaglio del riassunto a seconda delle tue esigenze.

    ### Traduzione
    Edubot offre la possibilità di tradurre testi in varie lingue. Questa funzionalità è utile per studiare materiali non disponibili nella tua lingua madre.

    ### Creazione di Domande Aperte e Correzione
    Edubot può generare domande aperte basate su un testo e fornire correzioni alle tue risposte. Questo è uno strumento potente per testare la comprensione e migliorare le tue capacità di scrittura.

    ### Orientamento con l'Intervista Savickas
    Puoi usare la funzione di intervista Savickas per orientarti professionalmente. Questa intervista aiuta a esplorare i tuoi interessi, valori e competenze per guidare le tue scelte di carriera.

       Spero che questa guida ti sia utile! Buon lavoro con Edubot!
    """)
