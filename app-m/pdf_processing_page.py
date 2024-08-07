import os
import logging
import time
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
import pdfplumber
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError

def pdf_processing_page():
    # Configurazione del logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Caricamento dei file PDF tramite Streamlit
    st.title("Processo di caricamento e indicizzazione dei PDF")
    uploaded_files = st.file_uploader(
        "Carica i tuoi file PDF:", type=["pdf"], accept_multiple_files=True
    )

    # Variabile di sessione per memorizzare i metadati aggiornati e la conferma
    if "metadata_list" not in st.session_state:
        st.session_state.metadata_list = []

    if "metadata_confirmed" not in st.session_state:
        st.session_state.metadata_confirmed = False

    # Step 1: Verifica e modifica dei metadati
    if uploaded_files and not st.session_state.metadata_confirmed:
        st.header("Fase 1: Inserimento e Verifica dei Metadati")

        # Dizionario per tenere traccia dei metadati modificati
        updated_metadata = {}

        # Mostra il form di verifica e modifica dei metadati
        all_filled = True  # Variabile per verificare se tutti i campi sono riempiti

        for i, uploaded_file in enumerate(uploaded_files):
            st.subheader(f"Documento: {uploaded_file.name}")

            # Leggi i metadati del file e mostralo solo se non è stato ancora modificato
            if f"title_{i}" not in updated_metadata:
                initial_metadata = extract_metadata(uploaded_file)
                updated_metadata[f"title_{i}"] = initial_metadata["title"]
                updated_metadata[f"author_{i}"] = initial_metadata["author"]

            # Modifica i metadati solo se tutti i campi sono compilati
            title_input = st.text_input(
                f"Titolo per '{uploaded_file.name}':", updated_metadata[f"title_{i}"], key=f"title_{i}"
            )
            author_input = st.text_input(
                f"Autore per '{uploaded_file.name}':", updated_metadata[f"author_{i}"], key=f"author_{i}"
            )

            if title_input.strip() == "" or author_input.strip() == "":
                all_filled = False

            # Aggiorna i metadati nei dizionario intermedio
            updated_metadata[f"title_{i}"] = title_input
            updated_metadata[f"author_{i}"] = author_input

        # Bottone di conferma dei metadati
        if st.button("Carica Metadati"):
            if all_filled:
                # Applica i metadati aggiornati a st.session_state
                st.session_state.metadata_list = [
                    {
                        "file": uploaded_file,
                        "metadata": {
                            "title": updated_metadata[f"title_{i}"],
                            "author": updated_metadata[f"author_{i}"]
                        }
                    }
                    for i, uploaded_file in enumerate(uploaded_files)
                ]
                st.session_state.metadata_confirmed = True
                st.success("Metadati caricati con successo. Procedi al passo successivo.")
            else:
                st.error("Compila tutti i campi dei metadati prima di caricarli.")

    # Step 2: Embedding e creazione dell'indice FAISS
    if st.session_state.metadata_confirmed:
        st.header("Fase 2: Embedding e Creazione dell'Indice FAISS")

        # Mostra messaggio di caricamento dei metadati
        st.info("Caricamento metadati...")

        # Caricamento e parsing dei PDF
        all_documents = []
        for i, entry in enumerate(st.session_state.metadata_list):
            file = entry["file"]
            metadata = entry["metadata"]

            # Parse the PDF file for content
            documents, structured_content = load_pdf(file, metadata)
            all_documents.extend(documents)

            # Update metadata list with structured content
            st.session_state.metadata_list[i]["structured_content"] = structured_content

        # Input dell'utente tramite Streamlit
        chunk_size = st.number_input(
            "Dimensione dei chunk di testo:", min_value=100, max_value=5000, value=1500
        )
        chunk_overlap = st.number_input(
            "Sovrapposizione tra i chunk:", min_value=0, max_value=1000, value=200
        )
        min_chunk_length = st.number_input(
            "Lunghezza minima di un chunk:", min_value=50, max_value=1000, value=100
        )
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        subfolder_name = st.text_input(
            "Nome del database indicizzato:", "Inserisci il nome del database"
        )

        # Input per la descrizione dell'indice
        index_description = st.text_area(
            "Descrizione del database:",
            "Inserisci una breve descrizione del database indicizzato",
        )

        # Cartella per l'indice FAISS è fissata a 'db/<nome_sotto_cartella>'
        faiss_index_folder = os.path.join("db", subfolder_name)

        # Verifica se il database esiste già
        if not subfolder_name:
            st.error("Inserisci un nome valido per il database indicizzato.")
            return

        if st.button("Procedi con l'Embedding e la Creazione dell'Indice"):
            # Aggiorna il messaggio di stato
            progress_text = st.empty()
            progress_text.text("Divisione dei documenti in chunk...")

            # Inizializzare il Text Splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

            # Suddividere i documenti in chunk con i metadati aggiornati
            chunked_documents = []
            for entry in st.session_state.metadata_list:
                title = entry["metadata"]["title"]
                author = entry["metadata"]["author"]
                structured_content = entry["structured_content"]

                # Propaga i metadati aggiornati su tutti i chunk
                updated_metadata = {
                    "title": title,
                    "author": author,
                }
                for page_number, page_content in enumerate(structured_content, start=1):
                    chunks = text_splitter.split_text(page_content)
                    for chunk in chunks:
                        # Aggiungi il numero di pagina ai metadati
                        chunk_metadata = updated_metadata.copy()
                        chunk_metadata["page_number"] = page_number

                        chunked_documents.append(
                            Document(page_content=chunk, metadata=chunk_metadata)
                        )

            # Rimuovere i chunk troppo piccoli
            splits = [sp for sp in chunked_documents if len(sp.page_content) >= min_chunk_length]

            # Verifica che ci siano chunk validi prima di procedere
            if not splits:
                st.error("Nessun chunk valido è stato creato. Verifica i parametri di suddivisione.")
                logging.error("Nessun chunk valido è stato creato. Verifica i parametri di suddivisione.")
                return

            # **Visualizzare i primi 4 chunk completi**
            st.header("Primi 3 Chunk Estratti")
            for i, chunk in enumerate(splits[:3]):
                # Mostra i metadati del chunk
                st.subheader(f"Chunk {i + 1} - Metadati:")
                st.json(chunk.metadata)

                st.subheader(f"Contenuto del Chunk {i + 1}:")
                st.write(chunk.page_content)  # Mostra l'intero contenuto del chunk

            # Mostra messaggio di avanzamento mentre si crea l'indice
            progress_text.text("Creazione dell'indice FAISS...")

            # Aggiunge un effetto visivo di avanzamento
            for _ in range(5):
                for dots in range(1, 6):
                    progress_text.text(f"Sto elaborando il database{'.' * dots}")
                    time.sleep(0.5)

            # Creare i documenti per l'indice
            docs = [
                Document(page_content=split.page_content, metadata=split.metadata)
                for split in splits
            ]

            # Verifica se ci sono documenti da indicizzare
            if not docs:
                st.error(
                    "Nessun documento da indicizzare. Verifica che i documenti contengano testo valido."
                )
                logging.error(
                    "Nessun documento da indicizzare. Verifica che i documenti contengano testo valido."
                )
                return

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
                for entry in st.session_state.metadata_list:
                    desc_file.write(f"- {entry['metadata']['title']}\n")

            # Messaggio di successo finale
            progress_text.text(f"Indice '{subfolder_name}' creato con successo.")


def extract_metadata(file):
    """Estrae i metadati dal PDF."""
    metadata = {}
    try:
        # Utilizzo di PyPDF2 per estrarre i metadati
        reader = PdfReader(file)
        doc_info = reader.metadata

        # Verifica e aggiungi metadati disponibili
        metadata["title"] = doc_info.get(
            "/Title", "Sconosciuto"
        )  # Fallback a 'Sconosciuto' se il titolo non è specificato
        metadata["author"] = doc_info.get(
            "/Author", "Sconosciuto"
        )  # Fallback a 'Sconosciuto' se l'autore non è specificato

    except PDFSyntaxError as e:
        logging.error(
            f"Errore nell'estrazione dei metadati dal file {file.name}: {e}"
        )
    except PdfReadError as e:
        logging.error(f"Errore nella lettura del file {file.name} con PyPDF2: {e}")

    return metadata


def load_pdf(file, metadata):
    """Carica il documento PDF e restituisce i documenti con metadati e il contenuto strutturato."""
    try:
        structured_content = extract_structured_content(file)
        documents = create_documents_with_metadata(structured_content, metadata)
        return documents, structured_content
    except Exception as e:
        logging.error(f"Errore nel caricamento del file {file.name}: {str(e)}")
        return [], []


def extract_structured_content(file):
    """Estrae il contenuto strutturato dal PDF."""
    structured_content = []
    with pdfplumber.open(file) as pdf:
        for page_number, page in enumerate(pdf.pages):
            text = page.extract_text()
            structured_content.append(
                text
            )  # Mantieni il contenuto della pagina per la suddivisione

    return structured_content


def create_documents_with_metadata(chunks, metadata):
    """Crea documenti con metadati dai chunk di testo."""
    docs = []
    for chunk in chunks:
        doc = Document(page_content=chunk, metadata=metadata)
        docs.append(doc)
    return docs


if __name__ == "__main__":
    pdf_processing_page()
