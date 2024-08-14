import os
import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import logging
from prompt_config import get_chat_prompt_template

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
load_dotenv()

# Get the API key from an environment variable
api_key = os.getenv("ANTHROPIC_API_KEY")

def init_session_state():
    """Initialize the session state."""
    session_vars = [
        "interazioni",
        "conversazione",
        "last_response",
        "formatted_context",
    ]

    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = [] if var == "interazioni" else ""

def configure_ui():
    """Configure user interface elements."""
    st.title("Chat interattiva con memoria")
    st.write("Interagisci con Cloude.")

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

def query_stream(query, rag_chain):
    """Execute the query and return the response as a stream."""
    response = ""
    for chunk in rag_chain.stream(query):
        response += chunk
    return response

def add_interaction(domanda, risposta, temperatura, similarity_k, indice):
    """Add an interaction to the list of interactions."""
    st.session_state.interazioni.append({
        "domanda": domanda,
        "risposta": risposta,
        "temperatura": temperatura,
        "chunk da recuperare": similarity_k,
        "indice": indice,
    })

def display_interactions():
    """Display the list of interactions."""
    for interaction in st.session_state.interazioni:
        st.write("-----------------------------")
        st.write(f"**Domanda:** {interaction['domanda']}")
        st.write(f"**Risposta:** {interaction['risposta']}")
        st.write(f"**Temperatura:** {interaction['temperatura']} - **Chunk da recuperare:** {interaction['chunk da recuperare']} - **Indice:** {interaction['indice']}")
    st.write("\n\n")

def chatbotc():
    # Initialize session state
    init_session_state()

    # Configure the user interface
    configure_ui()

    # Temperature slider
    temperature = st.slider(
        "Temperatura",
        0.0,
        1.0,
        0.2,
        help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività.",
    )

    # Slider for the number of chunks to retrieve
    similarity_k = st.slider(
        "Chunk da recuperare",
        1,
        15,
        4,
        help="I chunk sono segmenti di testo suddivisi da documenti più grandi per ottimizzare l'elaborazione e il recupero delle informazioni rilevanti.",
    )

    # Retrieve subfolders from the 'db' directory
    db_path = "db"
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error("Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca.")
        return

    # Topic selection
    indice = st.selectbox("Seleziona l'indice", subfolders)

    # Display past interactions
    display_interactions()

    # Input for the current question
    user_query = st.text_input("Inserisci la tua domanda", key=f"user_query_{len(st.session_state.interazioni)}")

    if st.button("Invia"):
        if user_query:
            try:
                # Configuration settings
                model = ChatAnthropic(
                    temperature=temperature, 
                    model_name="claude-3-5-sonnet-20240620"
                )
            except Exception as e:
                st.error(f"Errore durante la configurazione del modello: {str(e)}")
                return

            embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2')

            # Load or create the FAISS index with the specified folder
            faiss_index = get_faiss_index(os.path.join(db_path, indice), embeddings)

            if faiss_index is None:
                st.error("Impossibile caricare o creare l'indice FAISS.")
                return

            retriever = faiss_index.as_retriever(
                search_type="mmr", search_kwargs={"k": similarity_k}
            )

            # Prompt configuration
            prompt = get_chat_prompt_template()  # Usa il prompt esterno
            
            rag_chain = build_rag_chain(prompt, model, retriever)

            # Execute the query and display the response
            try:
                response = query_stream(user_query, rag_chain)

                # Add the question, answer, and additional information to the list of interactions
                add_interaction(
                    user_query,
                    response,
                    temperature,
                    similarity_k,
                    indice,
                )

            except Exception as e:
                st.error(f"Si è verificato un errore durante l'esecuzione della query: {e}")
                return

    # Display the current interaction
    display_interactions()

    # Button to download the conversation
    if st.button("Scarica conversazione"):
        conversation_text = "\n".join(
            [f"Domanda: {i['domanda']}\nRisposta: {i['risposta']}\n"
             for i in st.session_state.interazioni]
        )
        st.download_button(
            label="Scarica conversazione",
            data=conversation_text,
            file_name="conversazione.txt",
            mime="text/plain",
        )

if __name__ == "__main__":
    chatbotc()
