# remove_pdfs_from_index.py

import os
import logging
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.docstore.document import Document

def remove_pdfs_from_index():
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

    # Percorso dell'indice selezionato
    index_path = os.path.join(faiss_index_folder, selected_index)

    # Carica l'indice FAISS
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")
    try:
        index = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        st.error(f"Errore durante il caricamento dell'indice: {str(e)}")
        return

    # Leggi il file di descrizione per ottenere i titoli dei PDF
    description_file_path = os.path.join(index_path, "description.txt")
    if not os.path.exists(description_file_path):
        st.error("Il file di descrizione non esiste.")
        return

    with open(description_file_path, "r", encoding="utf-8") as desc_file:
        lines = desc_file.readlines()

    # Estrai i titoli dei PDF dal file di descrizione
    pdf_titles = [line.strip("- \n") for line in lines if line.startswith("-")]

    # Seleziona i PDF da rimuovere
    selected_pdfs = st.multiselect("Seleziona i PDF da rimuovere:", pdf_titles)

    # Bottone per iniziare la rimozione
    if st.button("Rimuovi PDF e Chunk"):
        if not selected_pdfs:
            st.error("Nessun PDF selezionato per la rimozione.")
            return

        # Ricostruisci l'indice escludendo i documenti selezionati
        remaining_documents = []
        for doc in index.docstore._dict.values():
            if doc.metadata.get("title") not in selected_pdfs:
                remaining_documents.append(doc)

        # Verifica se ci sono documenti rimanenti
        if not remaining_documents:
            st.warning("Nessun documento rimanente dopo la rimozione.")
            return

        # Crea un nuovo indice con i documenti rimanenti
        new_index = FAISS.from_documents(remaining_documents, embeddings)

        # Salva il nuovo indice
        new_index.save_local(index_path)

        # Aggiorna il file di descrizione
        with open(description_file_path, "w", encoding="utf-8") as desc_file:
            for line in lines:
                if not any(pdf in line for pdf in selected_pdfs):
                    desc_file.write(line)

        st.success(f"PDF e chunk associati rimossi con successo dall'indice '{selected_index}'.")

if __name__ == "__main__":
    remove_pdfs_from_index()


