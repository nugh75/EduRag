import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough

# Load environment variables from the .env file
load_dotenv()

# Obtain the API key from an environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Configure Streamlit
st.title("Query Assistant with FAISS and Language Models")

# Global variables
available_models = {
    "gpt-4o-mini": "gpt-4o-mini",
    "phi3": "phi3",
    "llama3": "llama3"  # Added llama3
}

# Initialize session state variables if not already done
# Proper initialization with .get() to avoid AttributeError
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = list(available_models.keys())[0]  # Default to first model
if 'interazioni' not in st.session_state:
    st.session_state.interazioni = []
if 'conversazione' not in st.session_state:
    st.session_state.conversazione = ""
if 'user_query' not in st.session_state:
    st.session_state.user_query = ""  # Properly initialize user_query
if 'last_response' not in st.session_state:
    st.session_state.last_response = ""
if 'formatted_context' not in st.session_state:
    st.session_state.formatted_context = ""

# Model selection (now before the query input field)
st.session_state.selected_model = st.selectbox(
    "Seleziona il modello LLM",
    list(available_models.keys()),
    index=list(available_models.keys()).index(st.session_state.selected_model),
    help="Seleziona il modello LLM che desideri utilizzare per l'elaborazione delle query."
)

# Slider for temperature
temperature = st.slider(
    "Temperatura",
    0.0,
    1.0,
    0.2,
    help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività. Un'alta temperatura consente al modello di esplorare una gamma più ampia di opzioni, generando risposte più diverse e meno prevedibili."
)

# Instantiate the selected model
def instantiate_model(selected_model, temperature):
    if selected_model in ["phi3", "llama3"]:
        # Specific configuration for models that do not require API keys
        return ChatOpenAI(
            base_url="http://localhost:11434/v1",
            temperature=temperature,
            model_name=available_models[selected_model],
            api_key="not-need"
        )
    else:
        # Configuration for models that require an API key
        return ChatOpenAI(
            temperature=temperature,
            model_name=available_models[selected_model],
            api_key=api_key
        )

model = instantiate_model(st.session_state.selected_model, temperature)

# Configure embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

def query_page():
    # Function to load or create the FAISS index
    def get_faiss_index(cartella, embeddings, splits=None):
        if os.path.exists(cartella) and os.path.exists(os.path.join(cartella, "index.faiss")):
            try:
                return FAISS.load_local(cartella, embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                st.error(f"Errore durante il caricamento dell'indice FAISS: {e}")
                return None
        else:
            if splits is not None:
                faiss_index = FAISS.from_documents(splits, embeddings)
                faiss_index.save_local(cartella)
                return faiss_index
            else:
                st.error("Non ci sono dati disponibili per creare l'indice FAISS.")
                return None

    # Function to get subfolders in the 'db' folder
    def list_subfolders(db_path):
        """Returns a list of subfolders in the specified folder."""
        try:
            return [name for name in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, name))]
        except FileNotFoundError:
            st.error("La cartella 'db' non esiste. Assicurati che la struttura delle cartelle sia corretta.")
            return []

    # Query input field (now appears after model selection)
    st.session_state.user_query = st.text_input("Inserisci la tua domanda", st.session_state.user_query)

    # Retrieve subfolders from the 'db' folder
    db_path = "db"
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error("Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca.")
        return

    # Topic selection (Note: st.selectbox returns the selected value, not the index)
    argomento = st.selectbox("Seleziona l'argomento", subfolders)

    # Slider for the chunk to retrieve
    similarity_k = st.slider(
        "chunk da recuperare",
        1,
        15,
        4,
        help="Nel contesto del Recupero delle Informazioni con i Grandi Modelli di Linguaggio (RAG), i chunk sono segmenti di testo suddivisi da documenti più grandi. Questa suddivisione ottimizza l'elaborazione del modello, mantiene il contesto semantico e migliora la precisione del recupero delle informazioni rilevanti per una query specifica"
    )

    if st.button("Invia"):
        # Load or create the FAISS index with the specified folder
        faiss_index = get_faiss_index(os.path.join(db_path, argomento), embeddings)

        if faiss_index is None:
            st.error("Impossibile caricare o creare l'indice FAISS.")
            return

        retriever = faiss_index.as_retriever(search_type="similarity", search_kwargs={"k": similarity_k})

        # Prompt configuration
        prompt = ChatPromptTemplate.from_template(
            "Sei un assistente preciso e attento; prima di tutto dai le definizioni o i termini più importati, poi nella spiegazione aiutati con degli esempi che possono essere tratti dalle tue conoscenze o inventati, se sono inventati da te specificalo. Rispondi a questa domanda in italiano: {question}, considera il seguente contesto {context}. Quando parli di contesto di \" secondo le mie conoscenze\" "
        )

        def format_documents(all_documents):
            formatted_docs = []
            for doc in all_documents:
                source = doc.metadata.get('source', 'Sconosciuto')
                page = doc.metadata.get('page', 'Sconosciuta')

                # Handle the case where the page is not a number
                try:
                    page_number = int(page) + 1
                except (ValueError, TypeError):
                    # If the page is not a number, keep 'Sconosciuta' or a default value
                    page_number = 'Sconosciuta'

                formatted_docs.append(f"Fonte: {source}, Pagina: {page_number} \n\n ...{doc.page_content}...")
            return "\n\n---------------------------\n\n".join(formatted_docs)

        rag_chain = (
            {
                "context": retriever | format_documents,
                "question": RunnablePassthrough()
            }
            | prompt
            | model
            | StrOutputParser()
        )

        def query(query):
            answer = rag_chain.invoke(query)
            return answer

        def queryStream(query):
            response = ""
            for chunk in rag_chain.stream(query):
                response += chunk
            return response

        # Execute the query and display the response
        st.session_state.last_response = queryStream(st.session_state.user_query)

        # Format the retrieved documents to add them to the conversation
        st.session_state.formatted_context = format_documents(retriever.get_relevant_documents(st.session_state.user_query))

        # Add the question, answer, and additional information to the list of interactions
        st.session_state.interazioni.append({
            "domanda": st.session_state.user_query,
            "risposta": st.session_state.last_response,
            "temperatura": temperature,
            "chunk da recuperare": similarity_k,
            "argomento": argomento,
            "fonte": st.session_state.formatted_context
        })

        # Update the conversation variable
        st.session_state.conversazione += (
            "-----------------------------\n"
            f"Domanda: {st.session_state.user_query}\n"
            f"Risposta: {st.session_state.last_response}\n"
            f"temperatura: {temperature}, chunk da recuperare: {similarity_k}, Argomento: {argomento}\n"
            "-----------------------------\n"
            f"Fonte: {st.session_state.formatted_context}\n\n"
        )

        # Reset the query after obtaining the answer
        st.session_state.user_query = ""

    # Display the current question and answer
    if st.session_state.last_response:
        st.write("-----------------------------")
        st.write(f"**Domanda:** {st.session_state.interazioni[-1]['domanda']}")
        st.write(f"**Risposta:** {st.session_state.last_response}")
        st.write(f"**temperatura:** {temperature} - **chunk da recuperare:** {similarity_k} - **Argomento:** {argomento}")
        st.write("-----------------------------")
        st.write(f"**Fonte:** {st.session_state.formatted_context}")

    # Toggle to show/hide the conversation history
    mostra_storico = st.checkbox("Mostra storico delle conversazioni", value=False)

    # Show conversation history if the checkbox is selected
    if mostra_storico:
        st.write("### Storico delle conversazioni")
        for interazione in st.session_state.interazioni:
            st.write("-----------------------------")
            st.write(f"**Domanda:** {interazione['domanda']}")
            st.write(f"**Risposta:** {interazione['risposta']}")
            st.write(f"**temperatura:** {interazione['temperatura']} -  **chunk da recuperare:** {interazione['chunk da recuperare']} -  **Argomento:** {interazione['argomento']}")
            st.write("-----------------------------")
            st.write(f"**Fonte:** {interazione['fonte']}")

    # Button to download the conversation
    st.download_button(
        label="Scarica conversazione",
        data=st.session_state.conversazione,
        file_name="conversazione.txt",
        mime="text/plain"
    )

# Execute the query_page function
query_page()
