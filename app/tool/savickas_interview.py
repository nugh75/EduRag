import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
from prompt.prompt_configs import get_chat_prompt_template  # Importa il modulo del prompt
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

def savickas_interview():
    # Initialize session state
    init_session_state()

    # Configure the user interface
    configure_ui()

    # Sidebar configuration for API key and model selection
    api_choice = st.sidebar.selectbox("Scegli la chiave API da usare", ["Usa chiave di sistema", "Inserisci la tua chiave API"], index=0)

    if api_choice == "Inserisci la tua chiave API":
        openai_api_key = st.sidebar.text_input("Inserisci la tua chiave API OpenAI", st.session_state.get("user_api_key", ""), type="password")
        st.session_state.user_api_key = openai_api_key  # Salva la chiave API inserita dall'utente
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")

    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["gpt-4o", "gpt-4o-mini"], index=1)
    st.session_state.model_choice = model_choice  # Salva la scelta del modello

    # Temperature slider
    temperature = st.sidebar.slider(
        "Temperatura",
        0.0,
        1.0,
        0.2,
        help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività. Un'alta temperatura consente al modello di esplorare una gamma più ampia di opzioni, generando risposte più diverse e meno prevedibili.",
    )

    # Slider for the number of chunks to retrieve
    similarity_k = st.sidebar.slider(
        "chunk da recuperare",
        1,
        15,
        4,
        help="Nel contesto del Recupero delle Informazioni con i Grandi Modelli di Linguaggio (RAG), i chunk sono segmenti di testo suddivisi da documenti più grandi. Questa suddivisione ottimizza l'elaborazione del modello, mantiene il contesto semantico e migliora la precisione del recupero delle informazioni rilevanti per una query specifica.",
    )

    # Creazione del contenitore per le domande di career counseling di Mark Savickas
    with st.container():
        st.write("### Career Counseling con Mark Savickas")

        # Prima domanda: Role Models
        question1 = st.text_area("**1. Chi sono stati i tuoi modelli di ruolo? Spiega cosa ti ha colpito di loro.**")

        # Seconda domanda: Magazines/Television Shows
        question2 = st.text_area("**2. Quali sono le tue riviste o programmi televisivi preferiti? Perché?**")

        # Terza domanda: Favorite Story
        question3 = st.text_area("**3. Qual è la tua storia o libro preferito? Perché?**")

        # Quarta domanda: Favorite Saying
        question4 = st.text_area("**4. Qual è il tuo motto preferito o una frase che ti rappresenta?**")

        # Quinta domanda: Early Memories
        question5 = st.text_area("**5. Racconta un ricordo d'infanzia significativo.**")

        # Concatenate all questions to form the user query
        st.session_state.user_query = (
            f"Role Models: {question1}\n"
            f"Magazines/Television Shows: {question2}\n"
            f"Favorite Story: {question3}\n"
            f"Favorite Saying: {question4}\n"
            f"Early Memories: {question5}\n"
        )

    # Retrieve subfolders from the 'db' directory
    db_path = "app/db"
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error(
            "Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca."
        )
        return

    Indice = "app/db/Career Counseling"

    if st.button("Invia"):
        if not openai_api_key.startswith("sk-"):
            st.warning("Per favore, inserisci una chiave API OpenAI valida!", icon="⚠")
            return

        # Configuration settings
        model = ChatOpenAI(temperature=temperature, model_name=st.session_state.model_choice, api_key=openai_api_key)
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2')

        # Load or create the FAISS index with the specified folder
        faiss_index = get_faiss_index(os.path.join(db_path, Indice), embeddings)

        if faiss_index is None:
            st.error("Impossibile caricare o creare l'indice FAISS.")
            return

        retriever = faiss_index.as_retriever(
            search_type="similarity", search_kwargs={"k": similarity_k}
        )

        # Prompt configuration
        prompt = get_chat_prompt_template()  # Usa il prompt esterno

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
                Indice,
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
            temperature, similarity_k, Indice, st.session_state.formatted_context
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
        "user_api_key",
        "model_choice",
    ]

    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = "" if var != "interazioni" else []

def configure_ui():
    """Configure user interface elements."""
    st.write(
        "Interagisci con il modello di linguaggio GPT per l'intervista di career counseling."
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

def display_current_interaction(temperature, similarity_k, Indice, formatted_context):
    """Display the current question and answer."""
    st.write("-----------------------------")
    st.write(f"**Domanda:** {st.session_state.interazioni[-1]['domanda']}")
    st.write(f"**Risposta:** {st.session_state.last_response}")
    st.write(f"**temperatura:** {temperature} - **chunk da recuperare:** {similarity_k} - **Indice:** {Indice}")
    st.write("-----------------------------")
    st.write(f"**Fonte:** {formatted_context}")

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

if __name__ == "__main__":
    savickas_interview()
