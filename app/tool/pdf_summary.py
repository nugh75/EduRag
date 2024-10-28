import os
import logging
from io import BytesIO
import streamlit as st
import PyPDF2
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import zipfile
import edge_tts
import tempfile
import asyncio
import re

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configura il logger
logger = logging.getLogger(__name__)

def openai_m():
    logger.debug("Fetching OpenAI API settings from user")
    api_choice = st.sidebar.selectbox(
        "Scegli la fonte del modello LLM",
        ["Usa modello AI locale", "Usa chiave di sistema", "Inserisci la tua chiave API"],
        index=0,
    )

    if api_choice == "Usa modello AI locale":
        openai_api_key = None
        model_choice = st.sidebar.selectbox(
            "Seleziona il modello LLM locale", ["llama3", "phi3", "gemma2"]
        )
        st.session_state.model_choice = model_choice
        logger.debug(f"Local model choice selected: {model_choice}")
        api_source = "local"
    else:
        if api_choice == "Inserisci la tua chiave API":
            openai_api_key = st.sidebar.text_input(
                "Inserisci la tua chiave API OpenAI",
                st.session_state.get("user_api_key", ""),
                type="password",
            )
            st.session_state.user_api_key = openai_api_key
            logger.debug("User-provided OpenAI API key retrieved")
        else:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            logger.debug("System OpenAI API key retrieved")

        if not openai_api_key:
            logger.error("No OpenAI API key provided")
            st.error("Errore: La chiave API non è stata inserita o non è configurata correttamente.")
            return None, None, None, None, None, None, None

        model_choice = st.sidebar.selectbox(
            "Seleziona il modello LLM OpenAI", ["gpt-4o", "gpt-4o-mini"], index=0
        )
        st.session_state.model_choice = model_choice
        logger.debug(f"OpenAI model choice selected: {model_choice}")
        api_source = "openai"

    temperature_summary = st.sidebar.slider(
        "Imposta la temperatura per il riassunto",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
    )
    st.session_state.temperature_summary = temperature_summary
    logger.debug(f"Temperature set to: summary={temperature_summary}")

    language = st.sidebar.selectbox(
        "Seleziona la lingua per il riassunto e l'audio", ["Italian", "English", "Swedish"]
    )
    speaker = st.sidebar.selectbox(
        "Seleziona la voce per l'audio", ["Speaker1", "Speaker2", "Speaker3"]
    )
    logger.debug(f"Language selected: {language}, Speaker selected: {speaker}")

    return openai_api_key, model_choice, temperature_summary, language, speaker, api_source

def load_text(file):
    file_type = file.type.split('/')[-1]
    if file_type == "pdf":
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    elif file_type == "docx":
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
    else:
        text = file.read().decode("utf-8")
    return text

def generate_outline(text, model):
    outline_prompt = f"Genera un outline per questo testo:\n\n{text}"
    outline = model.generate(outline_prompt)
    return outline

def summarize_sections(outline, text, model):
    summaries = []
    sections = re.split(r'(Capitolo \d+|Sezione \d+)', text)
    for section in sections:
        summary_prompt = f"Riassumi questa sezione:\n\n{section}"
        summary = model.generate(summary_prompt)
        summaries.append(summary)
    return summaries

async def synthesize_text(text, speaker):
    communicate = edge_tts.Communicate(text, voice=speaker)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as output_file:
        await communicate.save(output_file.name)
        return output_file.name

def pdf_summary():
    st.title("Riassunto e sintesi vocale per file PDF")

    openai_api_key, model_choice, temperature_summary, language, speaker, api_source = openai_m()
    if openai_api_key is None and api_source == "openai":
        return

    model = ChatOpenAI(api_key=openai_api_key, model=model_choice)
    
    uploaded_file = st.file_uploader("Carica un file PDF o DOCX:", type=["pdf", "docx"])
    manual_input = st.text_area("Oppure inserisci il testo manualmente:")

    if uploaded_file is not None:
        text = load_text(uploaded_file)
    elif manual_input:
        text = manual_input
    else:
        st.warning("Carica un file o inserisci un testo manualmente")
        return

    outline = generate_outline(text, model)
    st.subheader("Outline generato")
    st.write(outline)

    summaries = summarize_sections(outline, text, model)
    st.subheader("Riassunti delle sezioni")
    for i, summary in enumerate(summaries):
        st.write(f"Sezione {i + 1}:")
        st.write(summary)

    if st.button("Genera audio"):
        async def generate_audio():
            audio_file = await synthesize_text(text, speaker)
            st.audio(audio_file)

        asyncio.run(generate_audio())

if __name__ == "__main__":
    pdf_summary()
