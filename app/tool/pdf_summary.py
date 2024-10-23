import os
import logging
from io import BytesIO
import streamlit as st
import PyPDF2
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from docx import Document
import zipfile
import edge_tts
import tempfile
import asyncio
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# Dictionary mapping languages to their corresponding neural voices for TTS
language_dict = {
    "Italian": {
        "Isabella": "it-IT-IsabellaNeural",
        "Diego": "it-IT-DiegoNeural",
        "Elsa": "it-IT-ElsaNeural"
    },
    "English": {
        "Jenny": "en-US-JennyNeural",
        "Guy": "en-US-GuyNeural",
        "Aria": "en-US-AriaNeural"
    },
    "Swedish": {
        "Sofie": "sv-SE-SofieNeural",
        "Mattias": "sv-SE-MattiasNeural"
    }
}

# Asynchronous function to generate TTS audio using edge_tts
async def text_to_speech_edge_async(text, language_code, speaker):
    logger.debug(f"Starting text_to_speech_edge_async with language_code={language_code}, speaker={speaker}")
    # Clean the input text to remove any Markdown formatting
    clean_text = clean_markdown_formatting(text)
    logger.debug(f"Clean text for TTS: {clean_text[:100]}...")
    voice = language_dict[language_code][speaker]
    communicate = edge_tts.Communicate(clean_text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
        # Save the generated audio to a temporary file
        await communicate.save(tmp_path)
        logger.info(f"Audio saved to temporary file: {tmp_path}")
    return tmp_path

# Wrapper function to run the asynchronous TTS function synchronously
def text_to_speech_edge(text, language_code, speaker):
    logger.debug(f"Starting text_to_speech_edge with language_code={language_code}, speaker={speaker}")
    return asyncio.run(text_to_speech_edge_async(text, language_code, speaker))

# Function to get OpenAI API key and model settings from the user
def openai_m():
    logger.debug("Fetching OpenAI API settings from user")
    # Choose between using system API key or a user-provided key
    api_choice = st.sidebar.selectbox("Scegli la chiave API da usare", ["Usa chiave di sistema", "Inserisci la tua chiave API"], index=1)
    
    if api_choice == "Inserisci la tua chiave API":
        # Get the user's API key from sidebar input
        openai_api_key = st.sidebar.text_input("Inserisci la tua chiave API OpenAI", st.session_state.get("user_api_key", ""), type="password")
        st.session_state.user_api_key = openai_api_key
        logger.debug("User-provided OpenAI API key retrieved")
    else:
        # Load the system API key from environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        logger.debug("System OpenAI API key retrieved")
    
    # If no API key is provided, display an error message
    if not openai_api_key:
        logger.error("No OpenAI API key provided")
        st.error("Errore: La chiave API non è stata inserita o non è configurata correttamente.")
        return None, None, None, None, None

    # Select the LLM model to use
    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["gpt-4o", "gpt-4o-mini"], index=1)
    st.session_state.model_choice = model_choice
    logger.debug(f"Model choice selected: {model_choice}")
    
    # Set the temperature for model response
    temperature = st.sidebar.slider("Imposta la temperatura del modello", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    st.session_state.temperature = temperature
    logger.debug(f"Temperature set to: {temperature}")

    # Select the language and speaker for TTS
    language = st.sidebar.selectbox("Seleziona la lingua per il riassunto e l'audio", ["Italian", "English", "Swedish"])
    speaker = st.sidebar.selectbox("Seleziona la voce per l'audio", list(language_dict[language].keys()))
    logger.debug(f"Language selected: {language}, Speaker selected: {speaker}")

    return openai_api_key, model_choice, temperature, language, speaker

# Extract text from a PDF file
def extract_text_from_pdf(reader):
    logger.debug("Extracting text from PDF file")
    text = ""
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        # Append text from each page if available
        if page_text:
            text += page_text + "\n\n"
            logger.debug(f"Extracted text from page {page_num}: {page_text[:100]}...")
    return text

# Extract text from a DOC file
def extract_text_from_doc(doc_file):
    logger.info("Extracting text from DOC file.")
    doc = Document(doc_file)
    # Join paragraphs with non-empty content
    text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    logger.debug(f"Extracted text from DOC file: {text[:100]}...")
    return text

# Extract text from a TXT file
def extract_text_from_txt(txt_file):
    logger.info("Extracting text from TXT file.")
    text = txt_file.read().decode("utf-8")
    logger.debug(f"Extracted text from TXT file: {text[:100]}...")
    return text

# Clean Markdown formatting from text
def clean_markdown_formatting(text):
    logger.debug("Cleaning Markdown formatting from text")
    # Remove bold formatting (**text**)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove italic formatting (*text*)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove second-level headers (## Header)
    text = re.sub(r'\#\#(.*?)\n', r'\1\n', text)
    # Remove first-level headers (# Header)
    text = re.sub(r'\#(.*?)\n', r'\1\n', text)
    # Remove bullet points (- or *)
    text = re.sub(r'[-*]\s', '', text)
    logger.debug(f"Cleaned text: {text[:100]}...")
    return text

# Upload a file and extract its text content
def upload_and_extract_text():
    st.write("### Strumento per Riassumere ed Esportare PDF, DOCX, TXT e Audio")

    uploaded_file = st.file_uploader("Carica un file PDF, DOCX o TXT", type=["pdf", "docx", "txt"])

    if uploaded_file is not None:
        # Determine the file type
        file_type = uploaded_file.name.split('.')[-1].lower()
        pdf_filename = os.path.splitext(uploaded_file.name)[0]
        logger.info(f"Uploaded file: {uploaded_file.name}")

        # Extract text based on file type
        if file_type == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = extract_text_from_pdf(reader)
        elif file_type == "docx":
            text = extract_text_from_doc(uploaded_file)
        elif file_type == "txt":
            text = extract_text_from_txt(uploaded_file)
        else:
            st.error("Formato file non supportato.")
            logger.error("Unsupported file format")
            return None, None

        # Check if the extracted text is empty
        if not text.strip():
            st.error("Errore: Il file caricato non contiene testo estraibile.")
            logger.error("Extracted text is empty")
            return None, None

        logger.info("Text extraction completed.")
        # Clean the extracted text and return it
        return clean_markdown_formatting(text), pdf_filename
    else:
        logger.debug("No file uploaded")
        return None, None

# Split the text into chunks for easier processing
def split_text_into_chunks(text, num_chunks):
    logger.debug(f"Splitting text into {num_chunks} chunks")
    # Calculate the size of each chunk, ensuring it's at least 1 character
    chunk_size = max(1, len(text) // num_chunks)
    chunks = []
    start = 0
    
    for i in range(num_chunks):
        end = start + chunk_size
        # Ensure the last chunk captures any remaining text
        if i == num_chunks - 1:
            end = len(text)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
        logger.info(f"Chunk {i+1} created with length {len(chunk)}: {chunk[:100]}...")
    
    return chunks

# Summarize a given chunk of text with context from surrounding chunks using Chain of Thought prompting
def summarize_text_with_context(text, prev_chunk, next_chunk, model_choice, temperature, openai_api_key, language="Italian", custom_prompt=""):
    logger.info(f"Starting text summarization with context in {language}.")
    logger.debug(f"Summarizing text: {text[:100]}... with prev_chunk: {prev_chunk[:50]}... and next_chunk: {next_chunk[:50]}...")
    
    # Create the LLM object
    llm = ChatOpenAI(
        model=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    # Define the prompt template for summarization using advanced prompt engineering techniques
    template = ChatPromptTemplate.from_messages([
        ("system", f"""
        Sei un assistente AI avanzato. Il tuo compito è riassumere il testo fornito in maniera chiara, concisa, e completa.
        Utilizzeremo la strategia "Chain of Thought" per garantire che ogni passo del riassunto sia accuratamente elaborato.

        ### Passaggi per il Riassunto
        1. **Comprensione del Testo**: Leggi attentamente il testo fornito. Identifica i concetti principali e le idee centrali. Considera il contesto dei testi precedente e successivo.
        2. **Catena di Pensieri**: Esprimi passo dopo passo le tue riflessioni sul testo. Inizia descrivendo cosa pensi che siano i punti più importanti e le connessioni logiche tra di essi.
        3. **Sintesi**: Dopo aver espresso i tuoi pensieri, formula un riassunto completo che includa le idee chiave e che rispetti il flusso del contenuto originale.
        4. **Azione Come...**: Agisci come un esperto in questo argomento e rendi il riassunto utile anche per chi non ha familiarità con il tema. Mantieni un tono educativo ma accessibile.
        5. **Elimina Dettagli Superflui**: Rimuovi dettagli non necessari e ridondanze. Privilegia la chiarezza e la precisione.
        
        ### Contesto Aggiuntivo
        - Testo precedente: {prev_chunk}
        - Testo successivo: {next_chunk}

        Tieni presente che il tuo obiettivo è produrre un riassunto accurato e utilizzabile, capace di riflettere i principali aspetti del contenuto in maniera chiara, utilizzando la "Catena di Pensieri" per migliorare la qualità della sintesi.
        """),
        ("human", "{input}")
    ])
    
    # Add custom prompt text if provided
    if custom_prompt:
        custom_text = f"\n\n{custom_prompt}"
        text += custom_text
        logger.debug(f"Custom prompt added: {custom_prompt}")
    
    # Pipe the prompt to the model and generate the response
    chain = template.pipe(llm)
    response = chain.invoke({
        "previous_chunk": prev_chunk,
        "next_chunk": next_chunk,
        "input": text
    })
    
    logger.info(f"Text summarization with context in {language} completed.")
    logger.debug(f"Summary generated: {response.content[:100]}...")
    return response.content

# Generate an outline from the summarized text on three levels
def generate_outline_from_summary(summary):
    logger.info("Generating outline from summary")
    outline = ""
    # Split the summary into sentences or phrases to create structured outline
    lines = summary.split(". ")
    level_1 = 1
    for line in lines:
        # Use heuristics to identify hierarchical levels, this can be more complex if needed
        if len(line.split()) > 10:  # Level 1: Main points
            outline += f"{level_1}. {line.strip()}.\n"
            level_1 += 1
            level_2 = 'a'
        elif len(line.split()) > 5:  # Level 2: Sub-points
            outline += f"    {level_2}) {line.strip()}.\n"
            level_2 = chr(ord(level_2) + 1)
        else:  # Level 3: Minor details
            outline += f"        - {line.strip()}.\n"
    logger.info("Outline generation completed")
    return outline

# Main function to summarize the uploaded text file and generate outline
def pdf_summary():
    logger.info("Starting PDF summary process")
    text, pdf_filename = upload_and_extract_text()
    
    if text is not None:
        # Retrieve API key and model settings
        openai_api_key, model_choice, temperature, language, speaker = openai_m()
        
        # If API key or settings are incorrect, display an error
        if not openai_api_key or not model_choice or temperature is None:
            st.error("Configurazione non corretta. Verifica la chiave API e le altre impostazioni.")
            logger.error("Invalid API key or settings")
            return
        
        # Get custom prompt input from user
        custom_prompt_first = st.text_area("A chi è rivolto il riassunto? ci sono istruzioni particolari che vorresti includere per fare il riassunto? (Riassunto)", "")
        logger.debug(f"Custom prompt for summary: {custom_prompt_first}")
        
        # Determine the number of chunks for splitting the text
        num_chunks = st.number_input("In quanti pezzi vuoi dividere il testo per il riassunto?", min_value=1, max_value=20, value=5)
        logger.info(f"Number of chunks selected: {num_chunks}")

        # Start the summarization process when the button is pressed
        if st.button("Avvia il processo di riassunto"):
            chunks = split_text_into_chunks(text, num_chunks)
            summarized_text = ""
            
            for i, chunk in enumerate(chunks):
                prev_chunk = chunks[i-1] if i > 0 else ""
                next_chunk = chunks[i+1] if i < len(chunks) - 1 else ""

                try:
                    # Generate the summary for each chunk
                    summary = summarize_text_with_context(chunk, prev_chunk, next_chunk, model_choice, temperature, openai_api_key, language=language, custom_prompt=custom_prompt_first)
                    summarized_text += summary + "\n"
                    logger.info(f"Chunk {i+1} summarized successfully.")
                except Exception as e:
                    logger.error(f"Error summarizing chunk {i+1}: {e}")
                    summarized_text += "Errore durante la generazione del riassunto.\n"

            # Display the summarized text
            st.write("### Riassunto Generato:")
            st.write(summarized_text, unsafe_allow_html=True)
            
            # Generate the outline from the summarized text
            outline_text = generate_outline_from_summary(summarized_text)
            
            # Display the outline
            st.write("### Outline Generato:")
            st.write(outline_text, unsafe_allow_html=True)

            # Create and save DOCX and TXT files for the summary and outline
            summary_docx = create_docx(summarized_text)
            outline_docx = create_docx(outline_text)
            summary_txt = create_txt(summarized_text)
            outline_txt = create_txt(outline_text)

            # Provide download options for the generated files
            st.download_button("Scarica il Riassunto (DOCX)", summary_docx.getvalue(), f"{pdf_filename}_riassunto.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("Scarica l'Outline (DOCX)", outline_docx.getvalue(), f"{pdf_filename}_outline.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("Scarica il Riassunto (TXT)", summary_txt.getvalue(), f"{pdf_filename}_riassunto.txt", "text/plain")
            st.download_button("Scarica l'Outline (TXT)", outline_txt.getvalue(), f"{pdf_filename}_outline.txt", "text/plain")
            logger.info("Summary and outline files generated and ready for download.")

# Create a DOCX file in memory from the given text
def create_docx(text):
    logger.info("Creating DOCX file in memory")
    doc = Document()
    for paragraph in text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    logger.info("DOCX file created successfully")
    return buffer

# Create a TXT file in memory from the given text
def create_txt(text):
    logger.info("Creating TXT file in memory")
    buffer = BytesIO()
    buffer.write(text.encode('utf-8'))
    buffer.seek(0)
    logger.info("TXT file created successfully")
    return buffer

# Run the main function if the script is executed
def main():
    logger.info("Running main function")
    pdf_summary()

if __name__ == "__main__":
    main()

