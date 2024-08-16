# description.py

def get_description():
    """
    Returns the description of the application.
    """
    description = """
    
### Il problema

Negli ultimi anni, i Large Language Models (LLM), come GPT di OpenAI, sono diventati parte integrante della nostra vita. Questi modelli possono generare testo e interagire in linguaggio naturale, svolgendo compiti complessi in modo efficace. Tuttavia, c'è il rischio che gli studenti li usino per completare i compiti senza comprenderli, minacciando l'apprendimento attivo, ritenuto da molti pedagogisti il metodo più efficace. D'altro canto, gli LLM possono essere utili nello studio, fornendo chiarimenti e spiegazioni personalizzate. L'approccio didattico a questi strumenti non è semplice e dipende da vari fattori, come lo scopo dell'uso e la comprensione del loro funzionamento.

### Il progetto Edubot
Il progetto Edubot si propone di affrontare le sfide legate all'uso dei Large Language Models (LLM) nell'istruzione, offrendo un esempio di approccio responsabile. Edubot ha l'obiettivo di sviluppare un chatbot didattico che supporti gli studenti nel loro apprendimento, non semplicemente fornendo risposte, ma guidandoli a comprendere e approfondire i contenuti. L'idea è di promuovere un apprendimento attivo e consapevole, integrando la tecnologia in modo etico e rispettoso delle metodologie pedagogiche moderne.

### Come è fatto Edubot e quali sono le tecnologie alla base
Edubot è uno script Python che utilizza diverse librerie e framework, con Streamlit e LangChain come principali. Streamlit consente di costruire un'interfaccia grafica in HTML per l'inserimento di input e la visualizzazione di output, rendendo più intuitiva l'interazione con l'utente. LangChain, invece, permette di gestire l’interazione con più LLMs (Large Language Models) in modo semplice, utilizzando un codice uniforme per ogni modello. Inoltre, LangChain include funzionalità avanzate che consentono la costruzione di prompt complessi — i prompt sono le istruzioni fornite agli LLMs — e permette di far interagire diversi LLMs tra loro, oltre a far dialogare questi modelli con funzioni esterne.

Alla base di Edubot vi sono due tecnologie chiave: embedding e RAG (Retrieval-Augmented Generation).
-	Embedding: l'embedding è un processo che trasforma il testo in vettori semantici, ovvero rappresentazioni numeriche che catturano il significato del testo in uno spazio multidimensionale. Questi vettori semantici consentono ai modelli di linguaggio di confrontare e operare su testi in modo più efficiente rispetto al testo grezzo. In Edubot, l'embedding viene implementato utilizzando HuggingFaceEmbeddings con il modello 'sentence-transformers/all-MiniLM-L12-v2'. Questo modello specifico è una versione compatta e veloce, progettata per generare embeddings di alta qualità, utili per una varietà di applicazioni come la ricerca semantica, la classificazione dei testi e il clustering.
-	RAG (Retrieval-Augmented Generation): questa tecnologia combina il potere della generazione di testo con la capacità di recuperare informazioni rilevanti da grandi archivi di dati. In pratica, il sistema RAG di Edubot recupera vettori semantici simili da un archivio in risposta a un input dell'utente, utilizzando questi vettori per migliorare la generazione del testo, rendendo le risposte più accurate e contestualizzate. Ad esempio, dato un testo di input, il sistema può recuperare documenti simili da uno store di vettori e utilizzarli per generare una risposta più informata e pertinente.

Un aspetto cruciale di Edubot riguarda le strategie di chunking, ovvero la suddivisione di un testo in parti più piccole chiamate "chunk" e la loro successiva indicizzazione. Per garantire che le parole non vengano troncate e che le frasi rimangano complete, Edubot utilizza Character Text Splitter, una funzionalità di LangChain che divide il testo rispettando delimitatori come paragrafi e frasi.
Per facilitare il recupero efficiente di questi chunk, Edubot implementa l'indicizzazione tramite FAISS (Facebook AI Similarity Search). Sviluppata da Facebook AI Research, FAISS è una libreria progettata per la ricerca e il recupero rapido di vettori simili all'interno di grandi collezioni di dati, contenenti milioni o addirittura miliardi di vettori. Ottimizzata per funzionare sia su CPU che su GPU, FAISS assicura prestazioni elevate e una notevole efficienza nel processo di ricerca. 

### Cosa fa Edubot

- La funzione principale di Edubot è la creazione di database indicizzati di documenti PDF, che possono includere articoli scientifici, appunti personali, e altro ancora. Attualmente, l'unica limitazione è che i documenti devono essere in formato PDF.
- La seconda funzione di Edubot consiste nell'interrogare questi database utilizzando diversi modelli linguistici di grandi dimensioni (LLMs), tra cui quelli di OpenAI e Anthropic. Inoltre, tramite l'interfaccia, è possibile integrare la propria chiave API per i servizi desiderati.
- Una terza funzione è la capacità di riassumere documenti PDF.
Successivamente, c'è una funzione di orientamento professionale basata sull'intervista di Savickas. Questa funzione simula un'intervista orientativa sul lavoro e fornisce un feedback all'intervistato, basandosi su appunti universitari di un corso di orientamento professionale.
- Infine, Edubot offre la possibilità di generare domande aperte sui testi e correggere le risposte degli studenti.

Altre funzionalità saranno aggiunte con il progredire dello sviluppo.

Un elemento centrale di Edubot, non visibile all'utente, è il sistema di prompt e la loro concatenazione. Questi prompt forniscono istruzioni efficaci su come il chatbot deve rispondere, basandosi su una visione pedagogica moderna.

Edubot permette inoltre di scaricare tenere traccia delle conversazioni e di scaricarle in formato doc e txt.

    """
    return description
