import streamlit as st

def get_consigli():
    """
    Displays tips and specific use cases for using Edubot.
    """
    st.markdown("""
    ## Casi d'Uso( DA SISTEMARE)

    ### 1. Preparazione agli Esami
    **Scenario:** Hai un esame tra due settimane e devi studiare un grande volume di materiale, inclusi articoli scientifici, appunti presi durante le lezioni e documenti PDF.

    **Come usare Edubot:**
    - **Crea un database indicizzato:** Carica tutti i tuoi documenti su Edubot e indicizzali. Questo ti permetterà di fare ricerche rapide su argomenti specifici.
    - **Genera riassunti:** Usa la funzione di riassunto per creare versioni condensate degli articoli più lunghi. Questo ti aiuterà a concentrarti sugli aspetti chiave del materiale.
    - **Simula esami:** Utilizza la funzione di creazione di domande aperte per generare possibili domande d'esame e rispondi ad esse per testare la tua preparazione.

    ### 2. Scrittura di una Tesi
    **Scenario:** Stai lavorando alla tua tesi e hai bisogno di raccogliere informazioni da diverse fonti, organizzare il contenuto e scrivere una bozza coerente.

    **Come usare Edubot:**
    - **Ricerca semantica:** Carica le fonti su Edubot e usa la funzione di interrogazione per estrarre informazioni specifiche da articoli scientifici o libri.
    - **Creazione di riassunti:** Usa i riassunti per ottenere una panoramica di ogni fonte e integrare queste informazioni nel corpo della tesi.
    - **Assistenza nella scrittura (DA IMPLEMENTARE):** Usa Edubot per suggerimenti su come strutturare i capitoli, scrivere introduzioni, o riformulare frasi per migliorarne la chiarezza.

    ### 3. Apprendimento di una Nuova Lingua
    **Scenario:** Stai cercando di imparare una nuova lingua e hai bisogno di praticare la comprensione di testi complessi.

    **Come usare Edubot:**
    - **Traduzione:** Usa la funzione di traduzione per capire il significato dei testi in una lingua che stai imparando.
    - **Riassunto in lingua straniera:** Chiedi a Edubot di creare riassunti di testi complessi nella lingua che stai studiando per rafforzare la comprensione.
    - **Domande aperte:** Rispondi a domande aperte generate da Edubot per praticare l'uso della nuova lingua in modo attivo.

    ### 4. Preparazione di una Presentazione
    **Scenario:** Devi preparare una presentazione per una conferenza o un incontro di lavoro e vuoi assicurarti che sia ben strutturata e completa.

    **Come usare Edubot:**
    - **Strutturazione della presentazione:** Usa Edubot per creare una bozza della struttura della tua presentazione, includendo i punti chiave che vuoi trattare.
    - **Revisione (DA IMPLEMENTARE):** Chiedi a Edubot di rivedere il testo della presentazione per assicurarti che sia chiaro e ben organizzato.
    - **Creazione di slide (DA IMPLEMENTARE):** Usa i riassunti e le sezioni generate da Edubot come base per le slide della tua presentazione.

    ## Suggerimenti Utili

    - Inizia con un piccolo set di documenti per familiarizzare con le funzionalità.
    - Sperimenta con diverse impostazioni di temperatura per vedere come cambia lo stile delle risposte.
    - Utilizza la funzionalità di riassunto per creare versioni condensate dei testi più lunghi che devi studiare.
    """)
