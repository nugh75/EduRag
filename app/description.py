# description.py

def get_description():
    """
    Returns the description of the application.
    """
    description = """
    
    Edubot è un assistente virtuale progettato per aiutare studenti e docenti a gestire e navigare facilmente documenti PDF nei corsi online. Permette di ottenere rapidamente risposte a domande specifiche e di evidenziare i passaggi importanti nei documenti per ulteriori approfondimenti.

    ### **Funzionalità Principali:**

    - **Indicizzazione dei Documenti PDF:** Edubot permette di creare e gestire database indicizzati dei tuoi documenti PDF, facilitando la ricerca e il recupero delle informazioni. Puoi organizzare i documenti in database specifici e fare ricerche mirate su di essi.
    - **Rinominare e Cancellare Indici:** Consente di rinominare e cancellare i database indicizzati esistenti.
    - **Rimozione di PDF:** Puoi rimuovere PDF da un database esistentese.
    - **Query sui Database:** Puoi interrogare i database per ottenere informazioni specifiche dai documenti PDF indicizzati.
    - **Interfaccia Intuitiva:** Interagisci con Edubot come faresti con un assistente umano, ricevendo risposte chiare e facili da capire.
    - **Storico delle Interazioni:** Accedi facilmente alle domande e risposte precedenti per un apprendimento continuo.

    ### **Tecnologie alla Base di Edubot:**

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

    ### **Perché Usare Edubot?**

    - **Accesso Immediato alle Informazioni:** Trova velocemente le informazioni necessarie nei documenti PDF, senza dover cercare manualmente.
    - **Apprendimento Migliorato:** Consultare i passaggi suggeriti da Edubot permette di approfondire e comprendere meglio il materiale.
    - **Supporto ai Corsi Online:** Ideale per ambienti educativi, aiutando studenti e docenti a gestire i contenuti in modo più efficace.
    - **Flessibilità nell'Indicizzazione:** Consente di organizzare i documenti PDF in database specifici, facilitando ricerche mirate e personalizzate.

    Edubot rende la gestione dei documenti PDF più semplice ed efficace, migliorando l'accesso alle informazioni cruciali in contesti educativi.
    """
    return description
