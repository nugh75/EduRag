import tempfile
import streamlit as st
import edge_tts
import PyPDF2
import docx
import asyncio
import re
import os

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
    voice = language_dict[language_code][speaker]
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
        await communicate.save(tmp_path)
    return tmp_path

def text_to_speech_edge(text, language_code, speaker):
    return asyncio.run(text_to_speech_edge_async(text, language_code, speaker))

def clean_text(text):
    # Rimuovi gli accapo interni ai paragrafi
    text = re.sub(r'\n(?!\n)', ' ', text)
    return text

def read_pdf(filepath):
    with open(filepath, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return clean_text(text)

def read_docx(filepath):
    doc = docx.Document(filepath)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return clean_text(text)

def read_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        text = file.read()
    return clean_text(text)

def process_file(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            filepath = tmp_file.name
        return read_pdf(filepath)
    elif uploaded_file.name.endswith('.docx'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_file.write(uploaded_file.read())
            filepath = tmp_file.name
        return read_docx(filepath)
    elif uploaded_file.name.endswith('.txt'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(uploaded_file.read())
            filepath = tmp_file.name
        return read_txt(filepath)
    else:
        st.error("Formato del file non supportato. Carica un file PDF, DOCX o TXT.")
        return None

# Streamlit application
st.title("Multilingual TTS (Edge TTS)")
st.markdown("**Nota:** Questo strumento supporta Italiano, Inglese e Svedese.")

# Caricamento del file
uploaded_file = st.file_uploader("Carica un file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

# Testo inserito manualmente
manual_text = st.text_area("Oppure inserisci il testo manualmente", "")

extracted_text = ""

# Processa il file caricato o il testo inserito manualmente
if uploaded_file is not None:
    extracted_text = process_file(uploaded_file)
elif manual_text.strip() != "":
    extracted_text = clean_text(manual_text)

if extracted_text:
    # Selezione della lingua e dello Speaker
    language = st.selectbox("Seleziona la Lingua", list(language_dict.keys()))
    speakers = list(language_dict[language].keys())
    speaker = st.selectbox("Seleziona lo Speaker", speakers)

    # Generazione dell'audio
    if st.button("Genera Audio"):
        audio_path = text_to_speech_edge(extracted_text, language, speaker)
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button(
                label="Scarica l'audio",
                data=audio_bytes,
                file_name=os.path.basename(audio_path),
                mime="audio/mp3"
            )
