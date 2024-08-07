import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
import json


def query_page():
    # Inizializza le variabili di sessione
    init_session_state()

    # Configura l'interfaccia utente
    configure_ui()

    # Campo per la temperatura
    temperature = st.slider(
        "Temperatura",
        0.0,
        1.0,
        0.2,
        help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività. Un'alta temperatura consente al modello di esplorare una gamma più ampia di opzioni, generando risposte più diverse e meno prevedibili.",
    )

    # Campo per la query
    st.session_state.user_query = st.text_input(
        "Inserisci la tua domanda", st.session_state.user_query
    )

    # Recupera le sotto-cartelle dalla cartella 'db'
    db_path = "db"
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error(
            "Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca."
        )
        return

    # Campo per l'argomento (Nota: st.selectbox ritorna il valore selezionato, non l'indice)
    argomento = st.selectbox("Seleziona l'argomento", subfolders)

    # Slider per il chunk da recuperare
    similarity_k = st.slider(
        "chunk da recuperare",
        1,
        15,
        4,
        help="Nel contesto del Recupero delle Informazioni con i Grandi Modelli di Linguaggio (RAG), i chunk sono segmenti di testo suddivisi da documenti più grandi. Questa suddivisione ottimizza l'elaborazione del modello, mantiene il contesto semantico e migliora la precisione del recupero delle informazioni rilevanti per una query specifica",
    )

    if st.button("Invia"):
        # Impostazioni configurazione
        model = ChatOpenAI(
            base_url="http://localhost:11434/v1",
            temperature=temperature,
            api_key="not-need",
            model_name="phi3",
        )
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

        # Carica o crea l'indice FAISS con la cartella specificata
        faiss_index = get_faiss_index(os.path.join(db_path, argomento), embeddings)

        if faiss_index is None:
            st.error("Impossibile caricare o creare l'indice FAISS.")
            return

        retriever = faiss_index.as_retriever(
            search_type="similarity", search_kwargs={"k": similarity_k}
        )

        # Carica la mappa dei documenti
        document_map = load_document_map(os.path.join(db_path, argomento))

        # Configurazione del prompt
        prompt = ChatPromptTemplate.from_template(
           """
            Sei un assistente preciso e attento. Rispondi alla seguente domanda in italiano: {question}. Usa il contesto fornito: {context}.
            
            Struttura la tua risposta scegliendo l'approccio più adatto in base al tipo di domanda:

            - **Definizione di un concetto:**
              - **Definizione chiara:** Inizia con una definizione precisa e concisa dei termini o concetti chiave.
              - **Dettagli aggiuntivi:** Approfondisci con dettagli rilevanti che migliorano la comprensione del concetto.
              - **Esempi:** Fornisci esempi concreti, specificando se sono inventati.

            - **Confronto tra concetti:**
              - **Introduzione ai concetti:** Presenta brevemente i due concetti principali coinvolti nel confronto.
              - **Somiglianze e differenze:** Esplora le somiglianze e le differenze tra i concetti.
              - **Esempi:** Usa esempi per chiarire i punti di confronto, specificando se sono inventati.

            - **Argomentazioni su una domanda:**
              - **Introduzione alla questione:** Fornisci una breve panoramica della domanda o del problema.
              - **Argomentazione a favore:** Sviluppa argomenti a sostegno della domanda o tesi.
              - **Argomentazione contro:** Presenta argomenti contrari o critici.
              - **Esempi:** Illustra le argomentazioni con esempi specifici, indicando se sono inventati.

            - **Possibili riflessioni su una domanda:**
              - **Analisi critica:** Offri un'analisi critica della domanda, esplorando diverse prospettive.
              - **Implicazioni:** Discuti le implicazioni della domanda nei diversi contesti.
              - **Conclusione:** Concludi con una riflessione personale, collegando il tutto al contesto fornito.

            Durante la tua risposta, integra sempre il contesto fornito ({context}) per arricchire e specificare le informazioni. Utilizza un linguaggio chiaro e formale, assicurandoti che la risposta sia coerente e ben strutturata.
              Concludi sempre dicendo che sei un intelligenza artificiale e che le tue affermazioni devono essere sempre raffrontate con delle fonti affidabili. Inoltre, sempre alla fine cita la fonte delle tue affermazioni con testo da cui hai preso l'informazione e la pagina
            """
        )

        rag_chain = build_rag_chain(prompt, model, retriever, document_map)

        # Esegui la query e mostra la risposta
        st.session_state.last_response = query_stream(
            st.session_state.user_query, rag_chain
        )

        # Formatta i documenti recuperati per aggiungerli alla conversazione
        st.session_state.formatted_context = format_documents(
            retriever.get_relevant_documents(st.session_state.user_query),
            document_map
        )

        # Aggiungi la domanda, la risposta e le informazioni aggiuntive alla lista delle interazioni
        add_interaction(
            st.session_state.user_query,
            st.session_state.last_response,
            temperature,
            similarity_k,
            argomento,
            st.session_state.formatted_context,
        )

        # Resetta la query dopo aver ottenuto la risposta
        st.session_state.user_query = ""

    # Mostra la domanda e la risposta corrente
    if st.session_state.last_response:
        display_current_interaction(
            temperature, similarity_k, argomento, st.session_state.formatted_context
        )

    # Toggle per mostrare/nascondere lo storico delle conversazioni
    mostra_storico = st.checkbox("Mostra storico delle conversazioni", value=False)

    # Mostra storico delle conversazioni se il checkbox è selezionato
    if mostra_storico:
        display_interaction_history()

    # Pulsante per scaricare la conversazione
    if st.button("Scarica conversazione"):
        st.download_button(
            label="Scarica conversazione",
            data=st.session_state.conversazione,
            file_name="conversazione.txt",
            mime="text/plain",
        )


def init_session_state():
    """Inizializza lo stato della sessione."""
    session_vars = [
        "interazioni",
        "conversazione",
        "user_query",
        "last_response",
        "formatted_context",
    ]

    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = "" if var != "interazioni" else []


def configure_ui():
    """Configura gli elementi dell'interfaccia utente."""
    #st.title("Sistema di Recupero delle Informazioni")
    st.write(
        "Interagisci con il sistema di retrieval per ottenere risposte basate sui documenti."
    )


def list_subfolders(db_path):
    """Restituisce un elenco di sotto-cartelle nella cartella specificata."""
    try:
        return [name for name in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, name))]
    except FileNotFoundError:
        st.error("La cartella 'db' non esiste. Assicurati che la struttura delle cartelle sia corretta.")
        return []


def get_faiss_index(cartella, embeddings, splits=None):
    """Carica o crea l'indice FAISS."""
    index_path = os.path.join(cartella, "index.faiss")
    if os.path.exists(cartella) and os.path.exists(index_path):
        try:
            return FAISS.load_local(cartella, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            st.error(f"Errore durante il caricamento dell'indice FAISS: {e}")
            return None
    elif splits is not None:
        faiss_index = FAISS.from_documents(splits, embeddings)
        faiss_index.save_local(cartella)
        return faiss_index
    else:
        st.error("Non ci sono dati disponibili per creare l'indice FAISS.")
        return None


def load_document_map(cartella):
    """Carica la mappa dei documenti da file."""
    map_path = os.path.join(cartella, "document_map.json")
    try:
        with open(map_path, "r") as map_file:
            return json.load(map_file)
    except FileNotFoundError:
        st.error("Impossibile trovare la mappa dei documenti.")
        return {}


def build_rag_chain(prompt, model, retriever, document_map):
    """Crea la catena RAG per eseguire la query."""
    return {
        "context": retriever | format_documents_with_map(document_map),
        "question": RunnablePassthrough(),
    } | prompt | model | StrOutputParser()


def format_documents(all_documents, document_map):
    """Formatta i documenti recuperati per l'output."""
    formatted_docs = []
    for doc in all_documents:
        source = doc.metadata.get("title", "Sconosciuto")
        page = doc.metadata.get("page", "Sconosciuta")
        sections = document_map.get(source, {}).get(f"Page {page}", {}).get("sections", [])

        # Gestire il caso in cui la pagina non sia un numero
        try:
            page_number = int(page) + 1
        except (ValueError, TypeError):
            # Se la pagina non è un numero, mantieni 'Sconosciuta' o un valore predefinito
            page_number = "Sconosciuta"

        # Aggiungi le sezioni pertinenti
        relevant_sections = "\n\n".join(sections[:3])  # Prendi solo le prime 3 sezioni come esempio

        formatted_docs.append(
            f"Fonte: {source}, Pagina: {page_number}\n\nSezioni rilevanti:\n{relevant_sections}\n\n...{doc.page_content}..."
        )
    return "\n\n---------------------------\n\n".join(formatted_docs)


def format_documents_with_map(document_map):
    """Formatta i documenti con l'uso della mappa per l'output."""
    def inner(all_documents):
        return format_documents(all_documents, document_map)
    return inner


def query_stream(query, rag_chain):
    """Esegue la query e restituisce la risposta sotto forma di flusso."""
    response = ""
    for chunk in rag_chain.stream(query):
        response += chunk
    return response


def add_interaction(domanda, risposta, temperatura, similarity_k, argomento, fonte):
    """Aggiunge un'interazione alla lista delle interazioni."""
    st.session_state.interazioni.append(
        {
            "domanda": domanda,
            "risposta": risposta,
            "temperatura": temperatura,
            "chunk da recuperare": similarity_k,
            "indice": argomento,
            "fonte": fonte,
        }
    )

    # Aggiorna la variabile conversazione
    st.session_state.conversazione += (
        "-----------------------------\n"
        f"Domanda: {domanda}\n"
        f"Risposta: {risposta}\n"
        f"temperatura: {temperatura}, chunk da recuperare: {similarity_k}, Indice: {argomento}\n"
        "-----------------------------\n"
        f"Fonte: {fonte}\n\n"
    )


def display_current_interaction(temperature, similarity_k, argomento, formatted_context):
    """Mostra la domanda e la risposta corrente."""
    st.write("-----------------------------")
    st.write(f"**Domanda:** {st.session_state.interazioni[-1]['domanda']}")
    st.write(f"**Risposta:** {st.session_state.last_response}")
    st.write(f"**temperatura:** {temperature} - **chunk da recuperare:** {similarity_k} - **Indice:** {argomento}")
    st.write("-----------------------------")
    st.write(f"**Fonte:** {formatted_context}")


def display_interaction_history():
    """Mostra lo storico delle interazioni."""
    st.write("### Storico delle conversazioni")
    for interazione in st.session_state.interazioni:
        st.write("-----------------------------")
        st.write(f"**Domanda:** {interazione['domanda']}")
        st.write(f"**Risposta:** {interazione['risposta']}")
        st.write(f"**temperatura:** {interazione['temperatura']} -  **chunk da recuperare:** {interazione['chunk da recuperare']} -  **Indice:** {interazione['argomento']}")
        st.write("-----------------------------")
        st.write(f"**Fonte:** {interazione['fonte']}")


if __name__ == "__main__":
    query_page()
