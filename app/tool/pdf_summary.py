import os
import logging
from io import BytesIO
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from docx import Document
import zipfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Get the OpenAI API key from an environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(reader):
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text

def split_text_into_chunks(text, num_chunks):
    chunk_size = len(text) // num_chunks
    overlap = chunk_size // 3  # 3% overlap
    logger.info(f"Splitting text into {num_chunks} chunks of approx. {chunk_size} characters with an overlap of {overlap} characters.")
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        chunks.append(chunk)
        start = end - overlap
    
    logger.info(f"Created {len(chunks)} chunks.")
    return chunks

def summarize_text_with_context(text, prev_chunk, next_chunk, language="Italian"):
    logger.info("Starting text summarization with context.")
    
    # Set up the chat model with the specific model and API key
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=openai_api_key
    )
    
    # Create a chat prompt template with context from previous and next chunks
    template = ChatPromptTemplate.from_messages([
        ("system", """
        Sei un assistente AI specializzato nel riassumere testi in italiano. Il tuo compito è creare un riassunto conciso, fluido e coeso del testo fornito.

        Per creare il riassunto, segui queste linee guida:

        1. Leggi attentamente l'intero testo.
        2. Identifica i punti chiave e le informazioni principali.
        3. Crea un riassunto che catturi l'essenza del testo originale.
        4. Assicurati che il riassunto sia fluido e coeso, evitando frasi introduttive come "il testo discute" o "il documento descrive" o "Il testo analizza".
        5. Mantieni un tono neutro e oggettivo, usa uno stile accademico.
        6. Il riassunto dovrebbe essere significativamente più breve del testo originale: non più di un quarto della lunghezza originale.
        7. Metti in evidenza definizioni ed esempi.
       
                
        8. Prendi in considerazione anche il contesto precedente e successivo per mantenere la continuità:
        - Testo precedente: {previous_chunk}
        - Testo successivo: {next_chunk}
        """),
        ("human", "{input}")
    ])
    
    # Format the prompt with the specific input and context
    chain = template.pipe(llm)
    response = chain.invoke({
        "previous_chunk": prev_chunk,
        "next_chunk": next_chunk,
        "input": text
    })
    
    logger.info("Text summarization with context completed.")
    return response.content

def create_docx(text):
    logger.info(f"Creating the .docx file in memory.")
    doc = Document()
    doc.add_paragraph(text)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    logger.info(f".docx file successfully created in memory.")
    return buffer

def create_txt(text):
    logger.info(f"Creating the .txt file in memory.")
    buffer = BytesIO()
    buffer.write(text.encode('utf-8'))
    buffer.seek(0)
    logger.info(f".txt file successfully created in memory.")
    return buffer

def create_zip_file(txt_data, docx_data, pdf_filename):
    logger.info(f"Creating a zip file containing both .txt and .docx files.")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr(f"{pdf_filename}_riassunto.txt", txt_data.getvalue().decode('utf-8'))
        zip_file.writestr(f"{pdf_filename}_riassunto.docx", docx_data.getvalue())
    zip_buffer.seek(0)
    logger.info("Zip file created successfully.")
    return zip_buffer

def pdf_summary():
    st.write("### Strumento per Riassumere ed Esportare PDF")
    
    # Upload PDF file
    uploaded_file = st.file_uploader("Carica un file PDF", type="pdf")
    
    if uploaded_file is not None:
        # Extract the filename without the extension
        pdf_filename = os.path.splitext(uploaded_file.name)[0]
        logger.info(f"Uploaded file: {uploaded_file.name}")
        
        reader = PyPDF2.PdfReader(uploaded_file)
        text = extract_text_from_pdf(reader)
        logger.info("Text extraction from PDF completed.")
        
        # Ask the user how many chunks they want
        num_chunks = st.number_input("In quanti pezzi vuoi dividere il PDF?", min_value=1, max_value=20, value=5)
        
        # Split the text into the specified number of chunks
        chunks = split_text_into_chunks(text, num_chunks)
        st.session_state['chunks'] = chunks
        st.success(f"Testo diviso in {len(chunks)-1} blocchi.")
        
        if 'chunks' in st.session_state:
            chunks = st.session_state['chunks']

            if st.button("Riassumi e Scarica"):
                summarized_text = f"Riassunto - {pdf_filename}\n\n"
                for i, chunk in enumerate(chunks):
                    prev_chunk = chunks[i-1] if i > 0 else ""
                    next_chunk = chunks[i+1] if i < len(chunks) - 1 else ""
                    
                    try:
                        summary = summarize_text_with_context(chunk, prev_chunk, next_chunk, language="Italian")
                        if not summary.strip():
                            summary = "Impossibile generare il riassunto."
                        logger.info(f"Blocco {i+1} riassunto con successo.")
                        
                    except Exception as e:
                        summary = "Errore durante la generazione del riassunto."
                        logger.error(f"Errore nel riassumere il blocco {i+1}: {e}")
                    
                    summarized_text += summary + "\n"

                txt_data = create_txt(summarized_text)
                docx_data = create_docx(summarized_text)
                
                zip_data = create_zip_file(txt_data, docx_data, pdf_filename)
                
                st.download_button(
                    label="Scarica il Riassunto come .zip",
                    data=zip_data,
                    file_name=f"{pdf_filename}_riassunto.zip",
                    mime="application/zip"
                )
                logger.info(f"Riassunto esportato come {pdf_filename}_riassunto.zip.")

if __name__ == "__main__":
   pdf_summary()
