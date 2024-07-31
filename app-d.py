import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.document_loaders import PyPDFLoader
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableParallel, RunnableLambda
#from IPython.display import JSON
import json
#from unstructured_client import UnstructuredClient
#from unstructured_client.models import shared
#from unstructured_client.models.errors import SDKError
#from unstructured.partition.html import partition_html
#from unstructured.partition.pdf import partition_pdf
#from unstructured.staging.base import dict_to_elements, elements_to_json
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Variabile per memorizzare tutte le interazioni
if 'interazioni' not in st.session_state:
    st.session_state.interazioni = []

if 'conversazione' not in st.session_state:
    st.session_state.conversazione = ""

if 'user_query' not in st.session_state:
    st.session_state.user_query = ""

if 'last_response' not in st.session_state:
    st.session_state.last_response = ""

# Funzione per caricare o creare l'indice FAISS
def get_faiss_index(cartella, embeddings):
    if os.path.exists(cartella):
        return FAISS.load_local(cartella, embeddings, allow_dangerous_deserialization=True)
    else:
        # Supponiamo che 'splits' sia già definito altrove nel tuo codice
        faiss_index = FAISS.from_documents(splits, embeddings)
        faiss_index.save_local(cartella)
        return faiss_index

# Interfaccia Streamlit
st.title("Chatbot del corso di E-learning")

# Allert informativo
st.info("""
Questo è un chatbot con un'intelligenza artificiale Llama3 che utilizza la tecnologia RAG (Retrieval-Augmented Generation) 
per interagire su un contenuto specifico. RAG è una tecnologia avanzata che combina modelli di recupero delle informazioni 
e modelli di generazione di testo per fornire risposte pertinenti e accurate basate su un contesto specifico.
""")

# Campo per la temperatura
temperature = st.slider("Gradi di accuratezza-fantasia", 0.0, 1.0, 0.5, help="0 è il massimo di accuratezza e 1 è il massimo di fantasia")

# Campo per la query
st.session_state.user_query = st.text_input("Inserisci la tua domanda", st.session_state.user_query)

# Campo per l'argomento
argomento = st.selectbox("Seleziona l'argomento", ["Emedia","algoritmo3", "linguistica"])

# Slider per il grado di similarità
similarity_k = st.slider("Grado di similarità", 1, 15, 4, help="Determina il numero di documenti simili da recuperare (1-15)")

if st.button("Invia"):
    # Impostazioni configurazione
    model = ChatOpenAI(base_url="http://localhost:11434/v1", temperature=temperature, api_key="not-need", model_name="llama3")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")
    
    # Carica o crea l'indice FAISS con la cartella specificata
    faiss_index = get_faiss_index(argomento, embeddings)
    retriever = faiss_index.as_retriever(search_type="similarity", search_kwargs={"k": similarity_k})
    
    # Configurazione del prompt
    prompt = ChatPromptTemplate.from_template("Sei un assistente preciso e attento; Rispondi a questa domanda in italiano: {question}, considera il seguente contesto {context}. rispondi in italiano")
    
    def format_documents(all_documents):
        return "\n\n".join(doc.page_content for doc in all_documents)

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
    
    # Aggiungi la domanda, la risposta e le informazioni aggiuntive alla lista delle interazioni
    st.session_state.interazioni.append({
        "domanda": st.session_state.user_query,
        "risposta": st.session_state.last_response,
        "accuratezza_fantasia": temperature,
        "similarita": similarity_k,
        "argomento": argomento
    })
    
    # Aggiorna la variabile conversazione
    st.session_state.conversazione += (
        f"Domanda: {st.session_state.user_query}\n"
        f"Risposta: {st.session_state.last_response}\n"
        f"Grado di accuratezza-fantasia: {temperature}\n"
        f"Grado di similarità: {similarity_k}\n"
        f"Argomento: {argomento}\n\n"
    )
    
    # Resetta la query dopo aver ottenuto la risposta
    st.session_state.user_query = ""

# Mostra la domanda e la risposta corrente
if st.session_state.last_response:
    st.write(f"**Domanda:** {st.session_state.user_query}")
    st.write(f"**Risposta:** {st.session_state.last_response}")
    st.write(f"**Grado di accuratezza-fantasia:** {temperature}")
    st.write(f"**Grado di similarità:** {similarity_k}")
    st.write(f"**Argomento:** {argomento}")

# Toggle per mostrare/nascondere lo storico delle conversazioni
mostra_storico = st.checkbox("Mostra storico delle conversazioni", value=False)

# Mostra storico delle conversazioni se il checkbox è selezionato
if mostra_storico:
    st.write("### Storico delle conversazioni")
    for interazione in st.session_state.interazioni:
        st.write(f"**Domanda:** {interazione['domanda']}")
        st.write(f"**Risposta:** {interazione['risposta']}")
        st.write(f"**Grado di accuratezza-fantasia:** {interazione['accuratezza_fantasia']}")
        st.write(f"**Grado di similarità:** {interazione['similarita']}")
        st.write(f"**Argomento:** {interazione['argomento']}")

# Pulsante per scaricare la conversazione
if st.button("Scarica conversazione"):
    st.download_button(
        label="Scarica conversazione",
        data=st.session_state.conversazione,
        file_name="conversazione.txt",
        mime="text/plain"
    )

