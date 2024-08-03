# add_pdfs_to_index.py
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def add_pdfs_to_existing_index():
    # Configurazione del logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Percorso della cartella dove sono salvati gli indici FAISS
    faiss_index_folder = "db"

    # Controllo se la cartella degli indici esiste
    if not os.path.exists(faiss_index_folder):
        st.error("La cartella degli indici non esiste. Crea prima un indice.")
        return

    # Ottieni la lista degli indici esistenti
    indexes = os.listdir(faiss_index_folder)

    # Seleziona un indice esistente
    selected_index = st.selectbox("Seleziona un indice esistente:", indexes)

    # Input dell'utente tramite Streamlit
    folder_path = st.text_input("Percorso della cartella contenente i nuovi PDF:", "/home/nugh75/git-repository/Edubot/emedia-M")
    chunk_size = st.number_input("Dimensione dei chunk di testo:", min_value=100, max_value=5000, value=1500)
    chunk_overlap = st.number_input("Sovrapposizione tra i chunk:", min_value=0, max_value=1000, value=200)
    min_chunk_length = st.number_input("Lunghezza minima di un chunk:", min_value=50, max_value=1000, value=100)
    embeddings_model_name = "sentence-transformers/all-MiniLM-L12-v2"

    # Input per la descrizione dell'indice
    index_description = st.text_area("Descrizione dell'indice:", "Inserisci una breve descrizione dei nuovi documenti PDF")

    # Bottone per iniziare il processamento
    if st.button("Aggiungi PDF all'Indice"):
        # Funzione per caricare documenti PDF e ottenere titoli
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

            # Inizializzare l'oggetto di embeddings
            embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

            # Caricare l'indice esistente
            index_path = os.path.join(faiss_index_folder, selected_index)
            if not os.path.exists(index_path):
                st.error(f"L'indice selezionato '{selected_index}' non esiste.")
                return

            # Carica l'indice FAISS
            index = FAISS.load(index_path, embeddings)

            # Aggiungere i nuovi chunk all'indice esistente
            for split in splits:
                index.add_text(split.page_content)

            # Salvare l'indice aggiornato
            index.save(index_path)

            # Salvare la descrizione e i titoli dei PDF
            description_file_path = os.path.join(index_path, "description.txt")
            with open(description_file_path, "w") as desc_file:
                desc_file.write(f"Descrizione dell'indice: {index_description}\n")
                desc_file.write("Titoli dei documenti PDF:\n")
                for title in pdf_titles:
                    desc_file.write(f"- {title}\n")

            st.success(f"PDF aggiunti con successo all'indice '{selected_index}'.")

if __name__ == "__main__":
    add_pdfs_to_existing_index()
