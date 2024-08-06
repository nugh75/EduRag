# pdf_processing_page.py

import os
import logging
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
import fitz  # PyMuPDF
import pdfplumber

def pdf_processing_page():
    # Configurazione del logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Input dell'utente tramite Streamlit
    folder_path = st.text_input("Percorso della cartella contenente i PDF:", "/home/nugh75/git-repository/Edubot/appcopy2/pdfs")
    chunk_size = st.number_input("Dimensione dei chunk di testo:", min_value=100, max_value=5000, value=1500)
    chunk_overlap = st.number_input("Sovrapposizione tra i chunk:", min_value=0, max_value=1000, value=200)
    min_chunk_length = st.number_input("Lunghezza minima di un chunk:", min_value=50, max_value=1000, value=100)
    embeddings_model_name = "sentence-transformers/all-MiniLM-L12-v2"
    subfolder_name = st.text_input("Nome del database indicizzato:", "Inserisci il nome del database")

    # Input per la descrizione dell'indice
    index_description = st.text_area("Descrizione del database:", "Inserisci una breve descrizione del database indicizzato")

    # Cartella per l'indice FAISS è fissata a 'db/<nome_sotto_cartella>'
    faiss_index_folder = os.path.join("db", subfolder_name)

    # Bottone per iniziare il processamento
    if st.button("Crea database indicizzato"):
        # Funzione per caricare documenti PDF e ottenere titoli
        def load_pdf(file_path):
            try:
                # Caricare i metadati del PDF
                metadata = extract_metadata(file_path)
                
                # Caricare il contenuto strutturato del PDF
                structured_content = extract_structured_content(file_path)
                
                # Creare documenti con i metadati
                documents = create_documents_with_metadata(structured_content, metadata)
                
                if documents:
                    logging.info(f"Caricato: {file_path} con {len(documents)} documenti.")
                else:
                    logging.warning(f"Nessun contenuto trovato in {file_path}")
                return documents
            except Exception as e:
                logging.error(f"Errore nel caricamento del file {file_path}: {str(e)}")
                return []

        # Lista per memorizzare tutti i documenti caricati e i loro titoli
        all_documents = []
        pdf_titles = []

        # Verifica se la cartella esiste
        if os.path.exists(folder_path):
            # Caricamento parallelo dei documenti PDF
            with ThreadPoolExecutor() as executor:
                futures = []
                for filename in os.listdir(folder_path):
                    if filename.endswith(".pdf"):
                        pdf_path = os.path.join(folder_path, filename)
                        futures.append(executor.submit(load_pdf, pdf_path))
                        pdf_titles.append(filename)  # Memorizza il titolo del PDF

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

            # **Visualizzare i primi 10 chunk completi**
            st.header("Primi 10 Chunk Estratti")
            for i, chunk in enumerate(splits[:10]):
                st.subheader(f"Chunk {i + 1}")
                st.write(chunk.page_content)  # Mostra l'intero contenuto del chunk

            # Inizializzare l'oggetto di embeddings
            embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

            # Creare i documenti per l'indice
            docs = [Document(page_content=split.page_content, metadata={"title": pdf_titles[i % len(pdf_titles)]}) for i, split in enumerate(splits)]

            # Creare l'indice FAISS
            index = FAISS.from_documents(docs, embeddings)

            # Creare la cartella dell'indice se non esiste
            if not os.path.exists(faiss_index_folder):
                os.makedirs(faiss_index_folder)

            # Salvare l'indice nella cartella specificata
            index.save_local(faiss_index_folder)

            # Salvare la descrizione e i titoli dei PDF
            description_file_path = os.path.join(faiss_index_folder, "description.txt")
            with open(description_file_path, "w") as desc_file:
                desc_file.write(f"Descrizione dell'indice: {index_description}\n")
                desc_file.write("Titoli dei documenti PDF:\n")
                for title in pdf_titles:
                    desc_file.write(f"- {title}\n")

            st.success(f"Indice '{subfolder_name}' creato con successo.")

def extract_metadata(file_path):
    metadata = {}
    with fitz.open(file_path) as doc:
        metadata = doc.metadata
    return metadata

def extract_structured_content(file_path):
    with pdfplumber.open(file_path) as pdf:
        structured_content = []
        for page in pdf.pages:
            text = page.extract_text()
            # Suddivisione logica in base a sezioni del testo
            sections = text.split('\n\n')  # Suddivisione basata su paragrafi
            structured_content.extend(sections)
    return structured_content

def create_documents_with_metadata(chunks, metadata):
    docs = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk,
            metadata=metadata
        )
        docs.append(doc)
    return docs

if __name__ == "__main__":
    pdf_processing_page()
