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

async def text_to_speech_edge_async(text, language_code, speaker):
    # Rimozione di segni di marcatura che potrebbero creare problemi nella lettura ad alta voce
    clean_text = re.sub(r'[#*]', '', text)
    voice = language_dict[language_code][speaker]
    communicate = edge_tts.Communicate(clean_text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
        await communicate.save(tmp_path)
    return tmp_path

def text_to_speech_edge(text, language_code, speaker):
    return asyncio.run(text_to_speech_edge_async(text, language_code, speaker))

def openai_m():
    # Aggiunta delle opzioni per selezionare il modello LLM e inserire la chiave API
    api_choice = st.sidebar.selectbox("Scegli la chiave API da usare", ["Usa chiave di sistema", "Inserisci la tua chiave API"], index=1)
    
    if api_choice == "Inserisci la tua chiave API":
        openai_api_key = st.sidebar.text_input("Inserisci la tua chiave API OpenAI", st.session_state.get("user_api_key", ""), type="password")
        st.session_state.user_api_key = openai_api_key  # Salva la chiave API inserita dall'utente
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Controlla se la chiave API è stata impostata
    if not openai_api_key:
        st.error("Errore: La chiave API non è stata inserita o non è configurata correttamente.")
        return None, None, None  # Restituisci valori None per evitare il crash

    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["gpt-4o", "gpt-4o-mini"], index=1)
    st.session_state.model_choice = model_choice  # Salva la scelta del modello
    
    # Aggiunta dello slider per la temperatura
    temperature = st.sidebar.slider("Imposta la temperatura del modello", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    st.session_state.temperature = temperature  # Salva la temperatura scelta

    # Slider per selezionare la lingua del riassunto e della voce dell'audio
    language = st.sidebar.selectbox("Seleziona la lingua per il riassunto e l'audio", ["Italian", "English", "Swedish"])
    
    # Slider per selezionare la voce dell'audio
    speaker = st.sidebar.selectbox("Seleziona la voce per l'audio", list(language_dict[language].keys()))

    return openai_api_key, model_choice, temperature, language, speaker

def extract_text_from_pdf(reader):
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text

def split_text_into_chunks(text, num_chunks):
    chunk_size = len(text) // num_chunks
    chunks = []
    start = 0
    
    for i in range(num_chunks):
        end = start + chunk_size
        if i == num_chunks - 1:  # L'ultimo chunk prende tutto il testo rimanente
            end = len(text)
        chunk = text[start:end].strip()
        chunks.append(chunk)
        start = end
        logger.info(f"Chunk {i+1}: {chunk[:100]}...")  # Mostra l'inizio di ciascun chunk per verifica
    
    return chunks

def summarize_text_with_context(text, prev_chunk, next_chunk, model_choice, temperature, openai_api_key, language="Italian"):
    logger.info(f"Starting text summarization with context in {language}.")
    
    # Set up the chat model with the specific model, temperature, and API key
    llm = ChatOpenAI(
        model=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    # Create a chat prompt template with context from previous and next chunks
    template = ChatPromptTemplate.from_messages([
        ("system", f"""
        Sei un assistente AI specializzato nel riassumere testi in {language}. Il tuo compito è creare un riassunto conciso, fluido e coeso del testo fornito.

        Per creare il riassunto, segui queste linee guida:

        1. Leggi attentamente l'intero testo.
        2. Identifica i punti chiave e le informazioni principali.
        3. Crea un riassunto che catturi l'essenza del testo originale.
        4. Assicurati che il riassunto sia fluido e coeso, evitando frasi introduttive come "il testo discute" o "il documento descrive" o "Il testo analizza".
        5. Mantieni un tono neutro e oggettivo, usa uno stile accademico.
        6. Il riassunto dovrebbe essere significativamente più breve del testo originale: non più di un quarto della lunghezza originale.
        7. Metti in evidenza definizioni ed esempi.
        8. Riporta quando li trovi i riferimenti bibliografi così come sono nel testo
        9. Considera il contesto fornito dai blocchi precedente e successivo per garantire continuità e coerenza.
                - Testo precedente: {{previous_chunk}}
                - Testo successivo: {{next_chunk}}
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
    
    logger.info(f"Text summarization with context in {language} completed.")
    return response.content

def enhance_text_with_headings(summarized_text, model_choice, temperature, openai_api_key, language="Italian"):
    logger.info(f"Starting text enhancement with headings in {language}.")
    
    # Set up the chat model with the specific model, temperature, and API key
    llm = ChatOpenAI(
        model=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    # Create a chat prompt template to improve the text and add headings
    template = ChatPromptTemplate.from_messages([
        ("system", f"""
        Sei un assistente AI specializzato nel migliorare testi riassunti e aggiungere titoletti appropriati in {language}. Il tuo compito è rivedere il testo fornito, migliorarlo e inserire titoletti che riflettano il contenuto di ciascuna sezione.

        Per migliorare il testo, segui queste linee guida:

        1. Leggi attentamente il testo riassunto.
        2. Identifica le sezioni principali e aggiungi titoli e sottotitoli descrittivi.
        3. Se è un paper scientifico dividi il testo in queste parti con dei titoli: introduzione, letteratura, obiettivi della ricerca, metodologia, risultati, discussione conclusione. 
        3. Assicurati che il testo sia fluido, coeso e ben organizzato.
        4. Mantieni un tono neutro e oggettivo, usa uno stile accademico.
        5. Metti in **grassetto** le definizioni.
        6. Metti in *corsivo* gli esempi.
        7. fai una sezione alla fine con la bibliografia in stile APA i testi devono essere presi esclusivamente dal testo. Se non ci sono riferimenti bibliografici non li mettere.
        """),
        ("human", "{input}")
    ])
    
    # Format the prompt with the specific input
    chain = template.pipe(llm)
    response = chain.invoke({
        "input": summarized_text
    })
    
    logger.info(f"Text enhancement with headings in {language} completed.")
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

def create_zip_file(txt_data, docx_data, audio_data, pdf_filename):
    logger.info(f"Creating a zip file containing .txt, .docx files, and audio.")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr(f"{pdf_filename}_riassunto.txt", txt_data.getvalue().decode('utf-8'))
        zip_file.writestr(f"{pdf_filename}_riassunto.docx", docx_data.getvalue())
        zip_file.writestr(f"{pdf_filename}_audio.mp3", audio_data.getvalue())
    zip_buffer.seek(0)
    logger.info("Zip file created successfully.")
    return zip_buffer

def pdf_summary_a():
    st.write("### Strumento per Riassumere ed Esportare PDF e Audio")
    
    # Upload PDF file
    uploaded_file = st.file_uploader("Carica un file PDF", type="pdf")
    
    if uploaded_file is not None:
        # Extract the filename without the extension
        pdf_filename = os.path.splitext(uploaded_file.name)[0]
        logger.info(f"Uploaded file: {uploaded_file.name}")
        
        reader = PyPDF2.PdfReader(uploaded_file)
        text = extract_text_from_pdf(reader)
        logger.info("Text extraction from PDF completed.")
        
        # Usa la funzione openai_m per ottenere la chiave API, il modello, la temperatura, la lingua e la voce
        openai_api_key, model_choice, temperature, language, speaker = openai_m()
        
        # Verifica che i valori siano stati correttamente restituiti
        if not openai_api_key or not model_choice or temperature is None:
            st.error("Configurazione non corretta. Verifica la chiave API e le altre impostazioni.")
            return
        
        # Ask the user how many chunks they want
        num_chunks = st.number_input("In quanti pezzi vuoi dividere il PDF?", min_value=1, max_value=20, value=5)
        
        # Split the text into the specified number of chunks
        chunks = split_text_into_chunks(text, num_chunks)
        st.session_state['chunks'] = chunks
        st.success(f"Testo diviso in {len(chunks)} blocchi.")
        
        if 'chunks' in st.session_state:
            chunks = st.session_state['chunks']

            if st.button("Riassumi e Scarica"):
                summarized_text = f"Riassunto - {pdf_filename} ({model_choice}, Temp: {temperature})\n\n"
                
                for i, chunk in enumerate(chunks):
                    prev_chunk = chunks[i-1] if i > 0 else ""
                    next_chunk = chunks[i+1] if i < len(chunks) - 1 else ""

                    try:
                        # Generate summary with context for the current chunk
                        summary = summarize_text_with_context(chunk, prev_chunk, next_chunk, model_choice, temperature, openai_api_key, language=language)
                        if not summary.strip():
                            summary = "Impossibile generare il riassunto."
                        logger.info(f"Blocco {i+1} riassunto con successo.")
                        
                    except Exception as e:
                        summary = "Errore durante la generazione del riassunto."
                        logger.error(f"Errore nel riassumere il blocco {i+1}: {e}")
                    
                    summarized_text += summary + "\n"
                
                # Display the summarized text before enhancement
                st.write("### Testo riassunto prima del miglioramento:")
                st.write(summarized_text)
                
                # Enhance the summarized text and add headings using the same language
                enhanced_text = enhance_text_with_headings(summarized_text, model_choice, temperature, openai_api_key, language=language)
                
                # Display the enhanced text with headings
                st.write("### Testo migliorato con titoletti:")
                st.write(enhanced_text)

                txt_data = create_txt(enhanced_text)
                docx_data = create_docx(enhanced_text)
                
                # Genera immediatamente il file audio
                audio_path = text_to_speech_edge(enhanced_text, language, speaker)
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = BytesIO(audio_file.read())

                # Crea un file ZIP contenente il testo e l'audio
                zip_data = create_zip_file(txt_data, docx_data, audio_bytes, pdf_filename)
                
                st.download_button(
                    label="Scarica il Riassunto e l'Audio come .zip",
                    data=zip_data,
                    file_name=f"{pdf_filename}_riassunto_audio.zip",
                    mime="application/zip"
                )
                logger.info(f"Riassunto e audio esportati come {pdf_filename}_riassunto_audio.zip.")

if __name__ == "__main__":
   pdf_summary_a()
