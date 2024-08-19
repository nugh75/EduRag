import tempfile
import streamlit as st
import edge_tts
import PyPDF2
import docx
import asyncio
import re
import os

# Dizionario delle lingue e degli speaker
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
    try:
        voice = language_dict[language_code][speaker]
        communicate = edge_tts.Communicate(text, voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name
            await communicate.save(tmp_path)
        return tmp_path
    except Exception as e:
        st.error(f"Errore durante la generazione dell'audio: {e}")
        return None

def text_to_speech_edge(text, language_code, speaker):
    return asyncio.run(text_to_speech_edge_async(text, language_code, speaker))

def clean_text(text):
    text = re.sub(r'\n(?!\n)', ' ', text)
    return text

def read_pdf(filepath):
    try:
        with open(filepath, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return clean_text(text)
    except Exception as e:
        st.error(f"Errore durante la lettura del PDF: {e}")
        return ""

def read_docx(filepath):
    try:
        doc = docx.Document(filepath)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return clean_text(text)
    except Exception as e:
        st.error(f"Errore durante la lettura del DOCX: {e}")
        return ""

def read_txt(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()
        return clean_text(text)
    except Exception as e:
        st.error(f"Errore durante la lettura del TXT: {e}")
        return ""

def process_file(uploaded_file):
    try:
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
    except Exception as e:
        st.error(f"Errore durante l'elaborazione del file: {e}")
        return None

def voce():
    st.title("Multilingual TTS (Edge TTS)")
    st.markdown("**Nota:** Questo strumento supporta Italiano, Inglese e Svedese.")

    uploaded_file = st.file_uploader("Carica un file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    manual_text = st.text_area("Oppure inserisci il testo manualmente", "")

    extracted_text = ""

    if uploaded_file is not None:
        extracted_text = process_file(uploaded_file)
    elif manual_text.strip() != "":
        extracted_text = clean_text(manual_text)

    if extracted_text:
        st.write("Testo estratto (primi 500 caratteri):", extracted_text[:500])

        language = st.selectbox("Seleziona la Lingua", list(language_dict.keys()))
        speakers = list(language_dict[language].keys())
        speaker = st.selectbox("Seleziona lo Speaker", speakers)

        if st.button("Genera Audio"):
            st.write("Generazione audio in corso...")
            audio_path = text_to_speech_edge(extracted_text, language, speaker)
            if audio_path:
                st.write("Audio salvato in:", audio_path)
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label="Scarica l'audio",
                            data=audio_bytes,
                            file_name=os.path.basename(audio_path),
                            mime="audio/mp3"
                        )
                except Exception as e:
                    st.error(f"Errore durante il caricamento dell'audio: {e}")
                finally:
                    if os.path.exists(audio_path):
                        os.remove(audio_path)

if __name__ == "__main__":
    voce()
