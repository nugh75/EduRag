import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
from sidebar.sidebar_config import sidebar_c  # Import the sidebar configuration function
from prompt.prompt_config import get_chat_prompt_template  # Importa il modulo del prompt
from utils.openai_m import openai_m


def init_session_state():
    """Initialize the session state."""
    session_vars = [
        "interazioni",
        "conversazione",
        "user_query",
        "last_response",
        "formatted_context",
        "user_api_key",
        "model_choice",
    ]

    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = "" if var != "interazioni" else []


def configure_ui():
    """Configure user interface elements."""
    


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


def add_interaction(domanda, risposta, temperatura, similarity_k, Indice, fonte):
    """Add an interaction to the list of interactions."""
    st.session_state.interazioni.append(
        {
            "domanda": domanda,
            "risposta": risposta,
            "temperatura": temperatura,
            "chunk da recuperare": similarity_k,
            "Indice": Indice,
            "fonte": fonte,
        }
    )

    # Update the conversation variable
    st.session_state.conversazione += (
        "-----------------------------\n"
        f"Domanda: {domanda}\n"
        f"Risposta: {risposta}\n"
        f"temperatura: {temperatura}, chunk da recuperare: {similarity_k}, Indice: {Indice}\n"
        "-----------------------------\n"
        f"Fonte: {fonte}\n\n"
    )


# def display_current_interaction(temperature, similarity_k, Indice, formatted_context):
#     """Display the current question and answer."""
#     st.write("-----------------------------")
#     st.write(f"**Domanda:** {st.session_state.interazioni[-1]['domanda']}")
#     st.write(f"**Risposta:** {st.session_state.last_response}")
#     st.write(f"**temperatura:** {temperature} - **chunk da recuperare:** {similarity_k} - **Indice:** {Indice}")
#     st.write("-----------------------------")
#     st.write(f"**Fonte:** {formatted_context}")

def display_current_interaction(temperature, similarity_k, Indice, formatted_context):
    """Display the current question and answer."""
    st.write("-----------------------------")
    st.write(f"**Domanda:** {st.session_state.interazioni[-1]['domanda']}")
    st.write(f"**Risposta:** {st.session_state.last_response}")
    
    # Aggiunta del toggle per mostrare/nascondere i chunk
    show_chunks = st.checkbox("Mostra i dettagli dei chunk", value=True)
    
    if show_chunks:
        st.write(f"**temperatura:** {temperature} - **chunk da recuperare:** {similarity_k} - **Indice:** {Indice}")
        st.write("-----------------------------")
        st.write(f"**Fonte:** {formatted_context}")
    else:
        st.write("Dettagli dei chunk nascosti. Utilizza il toggle per mostrarli.")


def display_interaction_history():
    """Display the interaction history."""
    st.write("### Storico delle conversazioni")
    for interazione in st.session_state.interazioni:
        st.write("-----------------------------")
        st.write(f"**Domanda:** {interazione['domanda']}")
        st.write(f"**Risposta:** {interazione['risposta']}")
        st.write(f"**temperatura:** {interazione['temperatura']} -  **chunk da recuperare:** {interazione['chunk da recuperare']} -  **Indice:** {interazione['Indice']}")
        st.write("-----------------------------")
        st.write(f"**Fonte:** {interazione['fonte']}")


def comuni():
    """Richiama tutte le funzioni insieme."""
    init_session_state()
    configure_ui()
    # Puoi aggiungere qui ulteriori funzioni se necessario, o chiamarle singolarmente altrove.
