import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough

# Define the main function
def openk():
    # Initialize session state
    init_session_state()

    # Configure the user interface
    configure_ui()

    # Input for API Key in the main interface
    openai_api_key = st.text_input("Inserisci la tua chiave API OpenAI", type="password")

    # Temperature slider
    temperature = st.slider(
        "Temperatura",
        0.0,
        1.0,
        0.2,
        help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività. Un'alta temperatura consente al modello di esplorare una gamma più ampia di opzioni, generando risposte più diverse e meno prevedibili.",
    )

    # User query input
    st.session_state.user_query = st.text_input(
        "Inserisci la tua domanda", st.session_state.user_query
    )
    
    # Retrieve subfolders from the 'db' directory
    db_path = "db"
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error(
            "Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca."
        )
        return

    # Topic selection (Note: st.selectbox returns the selected value, not the index)
    argomento = st.selectbox("Seleziona l'argomento", subfolders)

    # Slider for the number of chunks to retrieve
    similarity_k = st.slider(
        "chunk da recuperare",
        1,
        15,
        4,
        help="Nel contesto del Recupero delle Informazioni con i Grandi Modelli di Linguaggio (RAG), i chunk sono segmenti di testo suddivisi da documenti più grandi. Questa suddivisione ottimizza l'elaborazione del modello, mantiene il contesto semantico e migliora la precisione del recupero delle informazioni rilevanti per una query specifica.",
    )

    if st.button("Invia"):
        if not openai_api_key.startswith("sk-"):
            st.warning("Per favore, inserisci una chiave API OpenAI valida!", icon="⚠")
            return

        # Configuration settings
        model = ChatOpenAI(temperature=temperature, model_name="gpt-4o-mini", api_key=openai_api_key)
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')

        # Load or create the FAISS index with the specified folder
        faiss_index = get_faiss_index(os.path.join(db_path, argomento), embeddings)

        if faiss_index is None:
            st.error("Impossibile caricare o creare l'indice FAISS.")
            return

        retriever = faiss_index.as_retriever(
            search_type="similarity", search_kwargs={"k": similarity_k}
        )

        # Prompt configuration
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
            Concludi sempre dicendo che sei un'intelligenza artificiale e che le tue affermazioni devono essere sempre raffrontate con delle fonti affidabili. Inoltre, sempre alla fine cita la fonte delle tue affermazioni con testo da cui hai preso l'informazione e la pagina.
            """
        )

        rag_chain = build_rag_chain(prompt, model, retriever)

        # Execute the query and display the response
        try:
            st.session_state.last_response = query_stream(
                st.session_state.user_query, rag_chain
            )

            # Format retrieved documents to add them to the conversation
            st.session_state.formatted_context = format_documents(
                retriever.get_relevant_documents(st.session_state.user_query)
            )

            # Add the question, answer, and additional information to the list of interactions
            add_interaction(
                st.session_state.user_query,
                st.session_state.last_response,
                temperature,
                similarity_k,
                argomento,
                st.session_state.formatted_context,
            )

            # Reset the query after obtaining the response
            st.session_state.user_query = ""
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'esecuzione della query: {e}")
            return

    # Display the current question and answer
    if st.session_state.last_response:
        display_current_interaction(
            temperature, similarity_k, argomento, st.session_state.formatted_context
        )

    # Toggle to show/hide conversation history
    mostra_storico = st.checkbox("Mostra storico delle conversazioni", value=False)

    # Show conversation history if the checkbox is selected
    if mostra_storico:
        display_interaction_history()

    # Button to download the conversation
    if st.button("Scarica conversazione"):
        st.download_button(
            label="Scarica conversazione",
            data=st.session_state.conversazione,
            file_name="conversazione.txt",
            mime="text/plain",
        )

def init_session_state():
    """Initialize the session state."""
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
    """Configure user interface elements."""
    st.write(
        "Interagisci con il sistema di retrieval per ottenere risposte basate sui documenti."
    )


def list_subfolders(db_path):
    """Return a list of subfolders in the specified directory."""
    try:
        return [
            name for name in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, name))
        ]
    except FileNotFoundError:
        st.error("La cartella 'db' non esiste. Assicurati che la struttura delle cartelle sia corretta.")
        return []


def get_faiss_index(cartella, embeddings, splits=None):
    """Load or create the FAISS index."""
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


def build_rag_chain(prompt, model, retriever):
    """Create the RAG chain to execute the query."""
    return {
        "context": retriever,
        "question": RunnablePassthrough(),
    } | prompt | model | StrOutputParser()


def format_documents(all_documents):
    """Format retrieved documents for output."""
    formatted_docs = []
    for doc in all_documents:
        source = doc.metadata.get("title", "Sconosciuto")
        page = doc.metadata.get("page_number", "Sconosciuta")

        # Add relevant sections
        formatted_docs.append(
            f"Fonte: {source}, Pagina: {page}\n\n...{doc.page_content}..."
        )
    return "\n\n---------------------------\n\n".join(formatted_docs)


def query_stream(query, rag_chain):
    """Execute the query and return the response as a stream."""
    response = ""
    for chunk in rag_chain.stream(query):
        response += chunk
    return response


def add_interaction(domanda, risposta, temperatura, similarity_k, argomento, fonte):
    """Add an interaction to the list of interactions."""
    st.session_state.interazioni.append(
        {
            "domanda": domanda,
            "risposta": risposta,
            "temperatura": temperatura,
            "chunk da recuperare": similarity_k,
            "argomento": argomento,
            "fonte": fonte,
        }
    )

    # Update the conversation variable
    st.session_state.conversazione += (
        "-----------------------------\n"
        f"Domanda: {domanda}\n"
        f"Risposta: {risposta}\n"
        f"temperatura: {temperatura}, chunk da recuperare: {similarity_k}, Argomento: {argomento}\n"
        "-----------------------------\n"
        f"Fonte: {fonte}\n\n"
    )


def display_current_interaction(temperature, similarity_k, argomento, formatted_context):
    """Display the current question and answer."""
    st.write("-----------------------------")
    st.write(f"**Domanda:** {st.session_state.interazioni[-1]['domanda']}")
    st.write(f"**Risposta:** {st.session_state.last_response}")
    st.write(f"**temperatura:** {temperature} - **chunk da recuperare:** {similarity_k} - **Argomento:** {argomento}")
    st.write("-----------------------------")
    st.write(f"**Fonte:** {formatted_context}")


def display_interaction_history():
    """Display the interaction history."""
    st.write("### Storico delle conversazioni")
    for interazione in st.session_state.interazioni:
        st.write("-----------------------------")
        st.write(f"**Domanda:** {interazione['domanda']}")
        st.write(f"**Risposta:** {interazione['risposta']}")
        st.write(f"**temperatura:** {interazione['temperatura']} -  **chunk da recuperare:** {interazione['chunk da recuperare']} -  **Argomento:** {interazione['argomento']}")
        st.write("-----------------------------")
        st.write(f"**Fonte:** {interazione['fonte']}")


if __name__ == "__main__":
    openk()
