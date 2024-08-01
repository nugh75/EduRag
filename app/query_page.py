import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough

def query_page():
    # Variabile per memorizzare tutte le interazioni
    if 'interazioni' not in st.session_state:
        st.session_state.interazioni = []

    if 'conversazione' not in st.session_state:
        st.session_state.conversazione = ""

    if 'user_query' not in st.session_state:
        st.session_state.user_query = ""

    if 'last_response' not in st.session_state:
        st.session_state.last_response = ""

    if 'formatted_context' not in st.session_state:
        st.session_state.formatted_context = ""

    # Funzione per caricare o creare l'indice FAISS
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

    # Funzione per ottenere le sotto-cartelle nella cartella 'db'
    def list_subfolders(db_path):
        """Restituisce un elenco di sotto-cartelle nella cartella specificata."""
        try:
            return [name for name in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, name))]
        except FileNotFoundError:
            st.error("La cartella 'db' non esiste. Assicurati che la struttura delle cartelle sia corretta.")
            return []

    # Interfaccia Streamlit
    st.title("Edubot")

    # Allert informativo
    st.info("""
    Questo è un chatbot con un'intelligenza artificiale Llama3 che utilizza la tecnologia RAG (Retrieval-Augmented Generation) 
    per interagire su un contenuto specifico. RAG è una tecnologia avanzata che combina modelli di recupero delle informazioni 
    e modelli di generazione di testo per fornire risposte pertinenti e accurate basate su un contesto specifico.
    """)

    # Campo per la temperatura
    temperature = st.slider("Temperatura", 0.0, 1.0, 0.2, help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività. Un'alta temperatura consente al modello di esplorare una gamma più ampia di opzioni, generando risposte più diverse e meno prevedibili.")

    # Campo per la query
    st.session_state.user_query = st.text_input("Inserisci la tua domanda", st.session_state.user_query)

    # Recupera le sotto-cartelle dalla cartella 'db'
    db_path = "db"
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error("Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca.")
        return

    # Campo per l'argomento (Nota: st.selectbox ritorna il valore selezionato, non l'indice)
    argomento = st.selectbox("Seleziona l'argomento", subfolders)

    # Slider per il chunk da recuperare
    similarity_k = st.slider("chunk da recuperare", 1, 15, 4, help="Nel contesto del Recupero delle Informazioni con i Grandi Modelli di Linguaggio (RAG), i chunk sono segmenti di testo suddivisi da documenti più grandi. Questa suddivisione ottimizza l'elaborazione del modello, mantiene il contesto semantico e migliora la precisione del recupero delle informazioni rilevanti per una query specifica")

    if st.button("Invia"):
        # Impostazioni configurazione
        model = ChatOpenAI(base_url="http://localhost:11434/v1", temperature=temperature, api_key="not-need", model_name="llama3")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

        # Carica o crea l'indice FAISS con la cartella specificata
        faiss_index = get_faiss_index(os.path.join(db_path, argomento), embeddings)

        if faiss_index is None:
            st.error("Impossibile caricare o creare l'indice FAISS.")
            return

        retriever = faiss_index.as_retriever(search_type="similarity", search_kwargs={"k": similarity_k})

        # Configurazione del prompt
        prompt = ChatPromptTemplate.from_template("Sei un assistente preciso e attento; prima di tutto dai le definizioni o i termini più importati, poi nella spiegazione aiutati con degli esempi che possono essere tratti dalle tue conoscenze o inventati, se sono inventati da te specificalo. Rispondi a questa domanda in italiano: {question}, considera il seguente contesto {context}. Quando parli di contesto di \" secondo le mie conoscenze \" rispondi in italiano")

        def format_documents(all_documents):
            formatted_docs = []
            for doc in all_documents:
                source = doc.metadata.get('source', 'Sconosciuto')
                page = doc.metadata.get('page', 'Sconosciuta')
                formatted_docs.append(f"Fonte: {source}, Pagina: {int(page) + 1} \n\n ...{doc.page_content}...")
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

        # Esegui la query e mostra la risposta
        st.session_state.last_response = queryStream(st.session_state.user_query)

        # Formatta i documenti recuperati per aggiungerli alla conversazione
        st.session_state.formatted_context = format_documents(retriever.get_relevant_documents(st.session_state.user_query))

        # Aggiungi la domanda, la risposta e le informazioni aggiuntive alla lista delle interazioni
        st.session_state.interazioni.append({
            "domanda": st.session_state.user_query,
            "risposta": st.session_state.last_response,
            "temperatura": temperature,
            "chunk da recuperare": similarity_k,
            "argomento": argomento,
            "fonte": st.session_state.formatted_context
        })

        # Aggiorna la variabile conversazione
        st.session_state.conversazione += (
            "-----------------------------\n"
            f"Domanda: {st.session_state.user_query}\n"
            f"Risposta: {st.session_state.last_response}\n"
            f"temperatura: {temperature}, chunk da recuperare: {similarity_k}, Argomento: {argomento}\n"
            "-----------------------------\n"
            f"Fonte: {st.session_state.formatted_context}\n\n"
        )

        # Resetta la query dopo aver ottenuto la risposta
        st.session_state.user_query = ""

    # Mostra la domanda e la risposta corrente
    if st.session_state.last_response:
        st.write("-----------------------------")
        st.write(f"**Domanda:** {st.session_state.interazioni[-1]['domanda']}")
        st.write(f"**Risposta:** {st.session_state.last_response}")
        st.write(f"**temperatura:** {temperature} - **chunk da recuperare:** {similarity_k} - **Argomento:** {argomento}")
        st.write("-----------------------------")
        st.write(f"**Fonte:** {st.session_state.formatted_context}")

    # Toggle per mostrare/nascondere lo storico delle conversazioni
    mostra_storico = st.checkbox("Mostra storico delle conversazioni", value=False)

    # Mostra storico delle conversazioni se il checkbox è selezionato
    if mostra_storico:
        st.write("### Storico delle conversazioni")
        for interazione in st.session_state.interazioni:
            st.write("-----------------------------")
            st.write(f"**Domanda:** {interazione['domanda']}")
            st.write(f"**Risposta:** {interazione['risposta']}")
            st.write(f"**temperatura:** {interazione['temperatura']} -  **chunk da recuperare:** {interazione['chunk da recuperare']} -  **Argomento:** {interazione['argomento']}")
            st.write("-----------------------------")
            st.write(f"**Fonte:** {interazione['fonte']}")

    # Pulsante per scaricare la conversazione
    if st.button("Scarica conversazione"):
        st.download_button(
            label="Scarica conversazione",
            data=st.session_state.conversazione,
            file_name="conversazione.txt",
            mime="text/plain"
        )

