import os
import logging
import pdfplumber
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.docstore.document import Document
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError

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

    # Variabile di sessione per memorizzare i metadati aggiornati e la conferma
    if "new_metadata_list" not in st.session_state:
        st.session_state.new_metadata_list = []

    if "new_metadata_confirmed" not in st.session_state:
        st.session_state.new_metadata_confirmed = False

    # Fase di conferma dei metadati
    if uploaded_files and not st.session_state.new_metadata_confirmed:
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
        if st.button("Conferma Metadati"):
            if all_filled:
                # Applica i metadati aggiornati a st.session_state
                st.session_state.new_metadata_list = [
                    {
                        "file": uploaded_file,
                        "metadata": {
                            "title": updated_metadata[f"title_{i}"],
                            "author": updated_metadata[f"author_{i}"]
                        }
                    }
                    for i, uploaded_file in enumerate(uploaded_files)
                ]
                st.session_state.new_metadata_confirmed = True
                st.success("Metadati caricati con successo. Procedi al passo successivo.")
            else:
                st.error("Compila tutti i campi dei metadati prima di caricarli.")

    # Step 2: Embedding e aggiornamento dell'indice FAISS
    if st.session_state.new_metadata_confirmed:
        st.header("Fase 2: Embedding e Aggiornamento dell'Indice FAISS")

        # Input dell'utente tramite Streamlit
        chunk_size = st.number_input("Dimensione dei chunk di testo:", min_value=100, max_value=5000, value=1500)
        chunk_overlap = st.number_input("Sovrapposizione tra i chunk:", min_value=0, max_value=1000, value=200)
        min_chunk_length = st.number_input("Lunghezza minima di un chunk:", min_value=50, max_value=1000, value=100)
        embeddings_model_name = "sentence-transformers/all-MiniLM-L12-v2"

        # Input per la descrizione dell'indice
        index_description = st.text_area("Descrizione dell'indice:", "Inserisci una breve descrizione dei nuovi documenti PDF")

        # Mostra messaggio di caricamento dei metadati
        st.info("Caricamento metadati...")

        # Caricamento e parsing dei PDF
        all_documents = []
        for i, entry in enumerate(st.session_state.new_metadata_list):
            file = entry["file"]
            metadata = entry["metadata"]

            # Parse the PDF file for content
            documents, structured_content = load_pdf(file, metadata)
            all_documents.extend(documents)

            # Update metadata list with structured content
            st.session_state.new_metadata_list[i]["structured_content"] = structured_content

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

        # Suddividere i documenti in chunk con i metadati aggiornati
        chunked_documents = []
        for entry in st.session_state.new_metadata_list:
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

        # Visualizzare i primi 10 chunk completi
        if splits:
            st.header("Primi 10 Chunk Estratti")
            for i, chunk in enumerate(splits[:10]):
                st.subheader(f"Chunk {i + 1} - Metadati:")
                st.json(chunk.metadata)
                st.subheader(f"Contenuto del Chunk {i + 1}:")
                st.write(chunk.page_content)  # Mostra l'intero contenuto del chunk
        else:
            st.warning("Nessun chunk generato dai documenti caricati. Verifica i parametri di suddivisione e il contenuto dei PDF.")
            return  # Exit if no valid chunks are generated

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
                for entry in st.session_state.new_metadata_list:
                    desc_file.write(f"- {entry['metadata']['title']}\n")

            st.success(f"PDF aggiunti con successo all'indice '{selected_index}'.")
        except Exception as e:
            st.error(f"Errore durante l'aggiornamento dell'indice: {str(e)}")

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
    add_pdfs_to_existing_index()
