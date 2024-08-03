import os
import logging
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def pdf_processing_page():
    # Configurazione del logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Input dell'utente tramite Streamlit
    folder_path = st.text_input("Percorso della cartella contenente i PDF:", "/home/nugh75/git-repository/Edubot/emedia-M")
    chunk_size = st.number_input("Dimensione dei chunk di testo:", min_value=100, max_value=5000, value=1500)
    chunk_overlap = st.number_input("Sovrapposizione tra i chunk:", min_value=0, max_value=1000, value=200)
    min_chunk_length = st.number_input("Lunghezza minima di un chunk:", min_value=50, max_value=1000, value=100)
    embeddings_model_name = st.text_input("Modello di embeddings:", "sentence-transformers/all-MiniLM-L12-v2")
    subfolder_name = st.text_input("Indice:", "Qui metti il nome dell'indice")

    # Cartella per l'indice FAISS è fissata a 'db/<nome_sotto_cartella>'
    faiss_index_folder = os.path.join("db", subfolder_name)

    # Bottone per iniziare il processamento
    if st.button("Esegui"):
        # Funzione per caricare documenti PDF
        def load_pdf(file_path):
            try:
                loader = PyPDFLoader(file_path=file_path)
                documents = loader.load()
                logging.info(f"Caricato: {file_path}")
                if not documents:
                    logging.warning(f"Nessun contenuto trovato in {file_path}")
                return documents
            except Exception as e:
                logging.error(f"Errore nel caricamento del file {file_path}: {e}")
                return []

        # Lista per memorizzare tutti i documenti caricati
        all_documents = []

        # Verifica se la cartella esiste
        if os.path.exists(folder_path):
            # Caricamento parallelo dei documenti PDF
            with ThreadPoolExecutor() as executor:
                futures = []
                for filename in os.listdir(folder_path):
                    if filename.endswith(".pdf"):
                        pdf_path = os.path.join(folder_path, filename)
                        futures.append(executor.submit(load_pdf, pdf_path))
                
                for future in futures:
                    all_documents.extend(future.result())

            # Verifica se ci sono documenti caricati
            if not all_documents:
                st.error("Nessun documento PDF è stato caricato. Verifica i file nella cartella specificata.")
                logging.error("Nessun documento PDF è stato caricato. Verifica i file nella cartella specificata.")
                return

            # Inizializzare il Text Splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            # Suddividere i documenti in chunk
            splits = text_splitter.split_documents(all_documents)

            # Rimuovere i chunk troppo piccoli
            splits = [sp for sp in splits if len(sp.page_content) >= min_chunk_length]

            # Selezionare i primi 15 splits, se disponibili
            first_15_splits = splits[:15]

            # Stampare i dettagli dei primi 15 splits
            for i, split in enumerate(first_15_splits):
                st.write(f"Chunk #{i+1}, size: {len(split.page_content)}")
                st.text_area("Contenuto del chunk:", value=split.page_content, height=150)
