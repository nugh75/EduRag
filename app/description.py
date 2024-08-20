# description.py


def get_description():
    """
    Returns the description of the application.
    """
    description = """
    
### Perché Edubot

Negli ultimi anni, i **Large Language Models** (LLM), come GPT di OpenAI, sono diventati parte integrante della nostra vita. Questi modelli possono generare testo e interagire in linguaggio naturale, svolgendo compiti complessi in modo efficace. Gli LLM possono essere utili nello studio in molti modi:

1. **apprendimento personalizzato**:
   - creazione di esercizi personalizzati che si adattano al livello e alle esigenze dello studente.
   - sviluppo di mappe mentali per aiutare nella comprensione e memorizzazione delle informazioni.
   - analisi dei progressi dello studente per identificare aree di miglioramento e suggerire strategie di studio.

2. **supporto alla comprensione**:
   - fornitura di spiegazioni semplificate di concetti complessi.
   - riassunti di testi, anche in altre lingue, per facilitare la comprensione e l'assimilazione del materiale.
   - offerta di suggerimenti su come affrontare lo studio di argomenti nuovi e complessi.
   - preparazione di discorsi e presentazioni, aiutando lo studente a strutturare e articolare le proprie idee.
   - simulazione di esami o quiz per permettere allo studente di testare le proprie conoscenze.

3. **accesso a conoscenze esterne**:
   - fornitura di informazioni su campi di cui lo studente non ha conoscenza, ampliando così l'orizzonte di apprendimento.
   - consigli su risorse esterne (libri, articoli, video) per approfondire specifici argomenti.

4. **assistenza nella scrittura e organizzazione**:
   - suggerimenti su come scrivere saggi, articoli o relazioni in modo efficace.
   - aiuto nella redazione di riassunti chiari e concisi.
   - revisione automatizzata di bozze per migliorare la coerenza e la qualità del testo.
   - formattazione appropriata di un testo per migliorare la leggibilità e l'organizzazione dei contenuti.
   - organizzazione del materiale di studio e suggerimenti per la gestione del tempo, ecc.

Tuttavia, c'è il rischio che gli studenti li usino per completare i compiti senza comprenderli, e di fatto non mettino in atto quell'apprendimento attivo che è molto importante nello studio.


### Il progetto Edubot
Il progetto Edubot si propone di affrontare le sfide legate all'uso dei LLMs nell'istruzione, offrendo un esempio di approccio responsabile. Edubot ha l'obiettivo di sviluppare un chatbot didattico che supporti gli studenti nel loro apprendimento, non semplicemente fornendo risposte, ma guidandoli a comprendere e approfondire i contenuti. L'idea è di promuovere un apprendimento attivo e consapevole, integrando la tecnologia in modo etico e rispettoso delle metodologie pedagogiche moderne.

### Come è fatto Edubot e quali sono le tecnologie alla base
Edubot è uno software scritto in **python** che utilizza diverse librerie e framework. **Streamlit** e **LangChain** sono le principali. 

- Streamlit consente di costruire un'interfaccia grafica in HTML per l'inserimento di input e la visualizzazione di output, rendendo più intuitiva l'interazione con l'utente. 
- LangChain, invece, permette di gestire l’interazione con più LLMs in modo semplice, utilizzando un codice uniforme per ogni modello. Inoltre, LangChain include funzionalità avanzate che consentono la costruzione di prompt complessi — i prompt sono le istruzioni fornite agli LLMs — e permette di far interagire diversi LLMs tra loro, oltre a far dialogare questi modelli con funzioni esterne.

Alla base di Edubot vi sono due tecnologie chiave: **embedding** e **Retrieval-Augmented Generation** (RAG).

-	Embedding: l'embedding è un processo che trasforma il testo in vettori semantici, ovvero rappresentazioni numeriche che catturano il significato del testo in uno spazio multidimensionale. Questi vettori semantici consentono ai modelli di linguaggio di confrontare e operare su testi in modo più efficiente rispetto al testo grezzo. In Edubot, l'embedding viene implementato utilizzando HuggingFaceEmbeddings con il modello **sentence-transformers/all-MiniLM-L12-v2**. Questo modello specifico è una versione compatta e veloce, progettata per generare embeddings di alta qualità, utili per una varietà di applicazioni come la ricerca semantica, la classificazione dei testi e il clustering.
-	RAG (Retrieval-Augmented Generation): questa tecnologia combina il potere della generazione di testo con la capacità di recuperare informazioni rilevanti da grandi archivi di dati. In pratica, il sistema RAG di Edubot recupera vettori semantici simili da un archivio in risposta a un input dell'utente, utilizzando questi vettori per migliorare la generazione del testo, rendendo le risposte più accurate e contestualizzate. Ad esempio, dato un testo di input, il sistema può recuperare documenti simili da uno store di vettori e utilizzarli per generare una risposta più informata e pertinente.

Un aspetto cruciale nell'elaborazione del testo è la creazione di segmenti specifici, detti **chunk**, che possono essere embeddati e indicizzati per il recupero tramite la tecnologia RAG (Retrieval-Augmented Generation). Per suddividere il testo in questi chunk, Edubot utilizza Character Text Splitter, una funzionalità di LangChain progettata per dividere il testo rispettando delimitatori naturali come paragrafi e frasi, garantendo così una segmentazione coerente e efficace.
Invece per l'indicizzazione Edubot utilizza **Facebook AI Similarity Search** (FAISS), sviluppata da Facebook AI Research. Questa libreriaè progettata per la ricerca e il recupero rapido di vettori simili all'interno di grandi collezioni di dati.Inoltre è ottimizzata per funzionare sia su CPU che su GPU, FAISS assicura prestazioni elevate e una notevole efficienza nel processo di ricerca. 

### Cosa fa Edubot

 **Funzione principale**: Edubot è progettato per creare database indicizzati di documenti in formato PDF, DOC, TXT, che possono includere articoli scientifici, appunti personali, e molto altro, consentendo poi di effettuare interrogazioni su di essi.

- **Altre funzioni**:
  - Riassunto personalizzata di un testo.
  - Traduzione di un testo.
  - Creazioni di domande aperte e loro correzione
  - Funzioni di orientamento, come l'intervista Savickas.

A secondo del tipo di interazione con Edubot è possibile scaricare un file in formato txt o doc della conversazione. Inoltre, è possibile anche avere un file audio mp3 

    """
    return description
