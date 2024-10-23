import os
import logging
from io import BytesIO
import streamlit as st
import PyPDF2
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from docx import Document
import edge_tts
import tempfile
import asyncio
import re
import tiktoken  # For token estimation
import nltk  # For text processing
nltk.download('punkt')

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
    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["gpt-4o", "gpt-4o-mini"], index=0)
    st.session_state.model_choice = model_choice
    logger.debug(f"Model choice selected: {model_choice}")

    # Set the temperature for model response
    temperature_summary = st.sidebar.slider("Imposta la temperatura per il riassunto", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    temperature_revision = st.sidebar.slider("Imposta la temperatura per la revisione", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    st.session_state.temperature_summary = temperature_summary
    st.session_state.temperature_revision = temperature_revision
    logger.debug(f"Temperatures set to: summary={temperature_summary}, revision={temperature_revision}")

    # Select the language and speaker for TTS
    language = st.sidebar.selectbox("Seleziona la lingua per il riassunto e l'audio", ["Italian", "English", "Swedish"])
    speaker = st.sidebar.selectbox("Seleziona la voce per l'audio", list(language_dict[language].keys()))
    logger.debug(f"Language selected: {language}, Speaker selected: {speaker}")

    return openai_api_key, model_choice, temperature_summary, temperature_revision, language, speaker

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

# Extract text from a DOCX file
def extract_text_from_docx(doc_file):
    logger.info("Extracting text from DOCX file.")
    doc = Document(doc_file)
    # Join paragraphs with non-empty content
    text = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    logger.debug(f"Extracted text from DOCX file: {text[:100]}...")
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
    # Remove headers (# Header)
    text = re.sub(r'#+\s*(.*?)\n', r'\1\n', text)
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
        file_basename = os.path.splitext(uploaded_file.name)[0]
        logger.info(f"Uploaded file: {uploaded_file.name}")

        # Extract text based on file type
        if file_type == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = extract_text_from_pdf(reader)
        elif file_type == "docx":
            text = extract_text_from_docx(uploaded_file)
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
        return clean_markdown_formatting(text), file_basename
    else:
        logger.debug("No file uploaded")
        return None, None

# Identify sections based on headings
def split_text_by_headings(text, language="Italian"):
    logger.debug("Splitting text by headings")
    # Regular expression patterns for headings
    if language == "Italian":
        heading_patterns = [
            r'\n([A-Z][^\n]{0,100})\n',  # Lines with capitalized words
            r'\nCapitolo\s+\d+[:.\s]',   # Lines starting with "Capitolo X"
            r'\n[A-Z ]+\n',              # Lines with uppercase letters
        ]
    else:
        heading_patterns = [
            r'\n([A-Z][^\n]{0,100})\n',  # Similar patterns for other languages
        ]

    # Combine patterns
    combined_pattern = '|'.join(heading_patterns)
    sections = re.split(combined_pattern, text)
    # Filter out empty strings
    sections = [s.strip() for s in sections if s.strip()]
    logger.info(f"Identified {len(sections)} sections based on headings")
    return sections

# Estimate the token count of a text
def calculate_token_count(text, model_name="gpt-4o"):
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(text))
    return num_tokens

# Generate an outline from the text
def generate_outline(text, model_choice, temperature, openai_api_key, language="Italian", custom_prompt=""):
    logger.info(f"Generating outline in {language}")
    llm = ChatOpenAI(
        model_name=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )

    template = ChatPromptTemplate.from_messages([
        ("system", f"""
Sei un assistente AI esperto in creazione di outline in {language}. Il tuo compito è creare un outline dettagliato e ben strutturato del testo fornito. L'outline deve avere tre livelli di profondità e riflettere accuratamente la struttura del contenuto.

Ecco le istruzioni:

1. Leggi attentamente il testo fornito e identifica i punti principali.
2. Crea un outline con tre livelli:
    - **Livello 1**: Principali sezioni o capitoli.
    - **Livello 2**: Sotto-sezioni o argomenti all'interno delle sezioni principali.
    - **Livello 3**: Dettagli specifici o sotto-argomenti.

Mantieni coerenza e uniformità nello stile dell'outline. Presenta l'outline in un formato chiaro e organizzato, utilizzando numeri e lettere per indicare i livelli.

Se necessario, incorpora il seguente contesto aggiuntivo:

{custom_prompt}
"""),
        ("human", "{input}")
    ])

    chain = template.pipe(llm)
    response = chain.invoke({
        "input": text
    })

    outline = response.content.strip()
    logger.info(f"Outline generation in {language} completed.")
    logger.debug(f"Generated outline: {outline[:100]}...")
    return outline

# Summarize the text based on the outline and revise it
def summarize_and_revise(outline, text, model_choice, temperature_summary, temperature_revision, openai_api_key, language="Italian", custom_prompt=""):
    logger.info(f"Generating summary based on outline in {language}")
    llm_summary = ChatOpenAI(
        model_name=model_choice,
        temperature=temperature_summary,
        openai_api_key=openai_api_key
    )

    llm_revision = ChatOpenAI(
        model_name=model_choice,
        temperature=temperature_revision,
        openai_api_key=openai_api_key
    )

    # Step 1: Generate the initial summary based on the outline
    template_summary = ChatPromptTemplate.from_messages([
        ("system", f"""
Sei un assistente AI specializzato nel creare riassunti in {language}. Il tuo compito è scrivere un riassunto del testo fornito che sia circa un quarto della lunghezza originale. Usa l'outline fornito per guidare il riassunto, assicurandoti che ogni sezione sia coperta.

Ecco le istruzioni:

1. Usa l'outline per guidare il riassunto, coprendo ogni sezione.
2. Mantieni il riassunto chiaro, coeso e uniforme nello stile.
3. Assicurati che il riassunto sia comprensibile anche a lettori non esperti dell'argomento.
4. Il riassunto dovrebbe essere circa un quarto della lunghezza del testo originale.

Incorpora il seguente contesto aggiuntivo se necessario:

{custom_prompt}
"""),
        ("human", "Outline:\n{outline}\n\nTesto originale:\n{text}")
    ])

    chain_summary = template_summary.pipe(llm_summary)
    response_summary = chain_summary.invoke({
        "outline": outline,
        "text": text
    })

    initial_summary = response_summary.content.strip()
    logger.info(f"Initial summary generated.")

    # Step 2: Revise the summary
    template_revision = ChatPromptTemplate.from_messages([
        ("system", f"""
Sei un assistente AI specializzato nella revisione di testi in {language}. Il tuo compito è migliorare il riassunto fornito, assicurandoti che sia coeso, chiaro e ben strutturato. Correggi eventuali errori, migliora la fluidità, semplifica frasi complesse e rimuovi ambiguità. Garantisci che il riassunto rispecchi accuratamente il contenuto originale e mantenga la lunghezza richiesta.

Ecco le istruzioni:

1. Leggi attentamente il riassunto e confrontalo con l'outline se necessario.
2. Apporta modifiche per migliorare la chiarezza, la coesione e la uniformità dello stile.
3. Assicurati che il riassunto sia accurato, rappresenti fedelmente il testo originale e sia circa un quarto della lunghezza originale.

Incorpora il seguente contesto aggiuntivo se necessario:

{custom_prompt}
"""),
        ("human", "Riassunto iniziale:\n{initial_summary}")
    ])

    chain_revision = template_revision.pipe(llm_revision)
    response_revision = chain_revision.invoke({
        "initial_summary": initial_summary
    })

    revised_summary = response_revision.content.strip()
    logger.info(f"Summary revision completed.")
    logger.debug(f"Revised summary: {revised_summary[:100]}...")
    return revised_summary

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

# Main function to summarize the uploaded text file and generate outline
def pdf_summary():
    logger.info("Starting PDF summary process")
    text, file_basename = upload_and_extract_text()

    if text is not None:
        # Retrieve API key and model settings
        openai_api_key, model_choice, temperature_summary, temperature_revision, language, speaker = openai_m()

        # If API key or settings are incorrect, display an error
        if not openai_api_key or not model_choice:
            st.error("Configurazione non corretta. Verifica la chiave API e le altre impostazioni.")
            logger.error("Invalid API key or settings")
            return

        # Get custom prompt input from user
        custom_prompt = st.text_area("Inserisci eventuali istruzioni o contesto aggiuntivo per migliorare l'outline e il riassunto:", "")
        logger.debug(f"Custom prompt: {custom_prompt}")

        # Start the summarization process when the button is pressed
        if st.button("Avvia il processo di riassunto e outline"):
            # Split text based on headings
            sections = split_text_by_headings(text, language=language)
            outlines = []
            summaries = []

            # Generate outline and summary for each section
            for idx, section in enumerate(sections):
                try:
                    # Calculate the desired summary length
                    original_length = len(section)
                    desired_summary_length = original_length // 4
                    logger.info(f"Section {idx + 1} original length: {original_length} characters. Desired summary length: {desired_summary_length} characters.")

                    # Generate the outline for each section
                    outline = generate_outline(section, model_choice, temperature_summary, openai_api_key, language=language, custom_prompt=custom_prompt)
                    outlines.append(outline)
                    # Generate the summary based on the outline and revise it
                    summary = summarize_and_revise(outline, section, model_choice, temperature_summary, temperature_revision, openai_api_key, language=language, custom_prompt=custom_prompt)
                    # Truncate or extend summary to match desired length
                    summary = adjust_summary_length(summary, desired_summary_length)
                    summaries.append(summary)
                    logger.info(f"Section {idx + 1} processed successfully.")
                except Exception as e:
                    logger.error(f"Error processing section {idx + 1}: {e}")
                    st.error(f"Errore durante la generazione per la sezione {idx + 1}.")
                    return

            # Combine outlines and summaries into final versions
            final_outline = "\n\n".join(outlines)
            final_summary = "\n\n".join(summaries)

            # Display the final outline
            st.write("### Outline Generato:")
            st.write(final_outline, unsafe_allow_html=True)

            # Display the final summary
            st.write("### Riassunto Generato:")
            st.write(final_summary, unsafe_allow_html=True)

            # Create and save DOCX and TXT files for the summary and outline
            outline_docx = create_docx(final_outline)
            summary_docx = create_docx(final_summary)
            outline_txt = create_txt(final_outline)
            summary_txt = create_txt(final_summary)

            # Provide download options for the generated files
            st.download_button("Scarica l'Outline (DOCX)", outline_docx.getvalue(), f"{file_basename}_outline.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("Scarica il Riassunto (DOCX)", summary_docx.getvalue(), f"{file_basename}_riassunto.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.download_button("Scarica l'Outline (TXT)", outline_txt.getvalue(), f"{file_basename}_outline.txt", "text/plain")
            st.download_button("Scarica il Riassunto (TXT)", summary_txt.getvalue(), f"{file_basename}_riassunto.txt", "text/plain")
            logger.info("Outline and summary files generated and ready for download.")

# Function to adjust the summary length
def adjust_summary_length(summary, desired_length):
    current_length = len(summary)
    if current_length > desired_length:
        # Truncate the summary to the desired length
        summary = summary[:desired_length]
        # Ensure we don't cut off mid-sentence
        if '.' in summary:
            summary = '.'.join(summary.split('.')[:-1]) + '.'
    elif current_length < desired_length:
        # If the summary is too short, we might need to regenerate or expand it
        # For now, we can return the summary as is
        pass
    return summary

# Run the main function if the script is executed
def main():
    logger.info("Running main function")
    pdf_summary()

if __name__ == "__main__":
    main()
