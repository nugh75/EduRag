# add_pdfs_to_index.py

import os
import logging
import pdfplumber
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document

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

    # Trascina o carica i nuovi file PDF
    uploaded_files = st.file_uploader(
        "Trascina qui i nuovi PDF o clicca per caricarli",
        type="pdf",
        accept_multiple_files=True
    )

    chunk_size = st.number_input("Dimensione dei chunk di testo:", min_value=100, max_value=5000, value=1500)
    chunk_overlap = st.number_input("Sovrapposizione tra i chunk:", min_value=0, max_value=1000, value=200)
    min_chunk_length = st.number_input("Lunghezza minima di un chunk:", min_value=50, max_value=1000, value=100)
    embeddings_model_name = "sentence-transformers/all-MiniLM-L12-v2"

    # Input per la descrizione dell'indice
    index_description = st.text_area("Descrizione dell'indice:", "Inserisci una breve descrizione dei nuovi documenti PDF")

    # Bottone per iniziare il processamento
    if st.button("Aggiungi PDF all'Indice"):
        if not uploaded_files:
            st.error("Nessun file PDF caricato. Trascina o seleziona almeno un file PDF.")
            return

        # Funzione per caricare documenti PDF e ottenere titoli
        def load_pdf(file):
            try:
                with pdfplumber.open(file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                if text:
                    logging.info(f"Caricato: {file.name} con successo.")
                    return [Document(page_content=text)], file.name
                else:
                    logging.warning(f"Nessun contenuto trovato in {file.name}")
                    return [], file.name
            except Exception as e:
                logging.error(f"Errore nel caricamento del file {file.name}: {str(e)}")
                return [], file.name

        # Lista per memorizzare tutti i documenti caricati e i loro titoli
        all_documents = []
        pdf_titles = []

        # Caricamento parallelo dei documenti PDF
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(load_pdf, file) for file in uploaded_files]
            
            for future in futures:
                documents, filename = future.result()
                all_documents.extend(documents)
                pdf_titles.extend([filename] * len(documents))  # Associa ogni documento al suo titolo

        # Verifica se ci sono documenti caricati
        if not all_documents:
            st.error("Nessun documento PDF è stato caricato. Verifica i file caricati.")
            logging.error("Nessun documento PDF è stato caricato. Verifica i file caricati.")
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

        # Visualizzare i primi 10 chunk completi
        if splits:
            st.header("Primi 10 Chunk Estratti")
            for i, chunk in enumerate(splits[:10]):
                st.subheader(f"Chunk {i + 1}")
                st.write(chunk.page_content)  # Mostra l'intero contenuto del chunk
        else:
            st.warning("Nessun chunk generato dai documenti caricati. Verifica i parametri di suddivisione e il contenuto dei PDF.")

        # Inizializzare l'oggetto di embeddings
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

        # Caricare l'indice esistente
        index_path = os.path.join(faiss_index_folder, selected_index)
        if not os.path.exists(index_path):
            st.error(f"L'indice selezionato '{selected_index}' non esiste.")
            return

        try:
            # Carica l'indice FAISS utilizzando il metodo corretto
            index = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

            # Aggiungere i nuovi chunk all'indice esistente
            for split in splits:
                index.add_documents([split])

            # Salvare l'indice aggiornato
            index.save_local(index_path)

            # Salvare la descrizione e i titoli dei PDF
            description_file_path = os.path.join(index_path, "description.txt")
            with open(description_file_path, "a", encoding="utf-8") as desc_file:  # Usa 'a' per aggiungere senza sovrascrivere
                desc_file.write(f"\nDescrizione aggiuntiva dell'indice: {index_description}\n")
                desc_file.write("Titoli dei nuovi documenti PDF:\n")
                for title in pdf_titles:
                    desc_file.write(f"- {title}\n")

            st.success(f"PDF aggiunti con successo all'indice '{selected_index}'.")
        except Exception as e:
            st.error(f"Errore durante l'aggiornamento dell'indice: {str(e)}")

if __name__ == "__main__":
    add_pdfs_to_existing_index()