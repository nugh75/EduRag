import tempfile
import streamlit as st
import edge_tts
import PyPDF2
import docx
import asyncio
import re

language_dict = {
    "Italian": {
        "Isabella": "it-IT-IsabellaNeural",
        "Diego": "it-IT-DiegoNeural",
        "Elsa": "it-IT-ElsaNeural"
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

def read_pdf(filepath):
    with open(filepath, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    # Rimuovi gli accapo interni ai paragrafi
    text = re.sub(r'\n(?!\n)', ' ', text)
    return text

def read_docx(filepath):
    doc = docx.Document(filepath)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    # Rimuovi gli accapo interni ai paragrafi
    text = re.sub(r'\n(?!\n)', ' ', text)
    return text

def read_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        text = file.read()
    # Rimuovi gli accapo interni ai paragrafi
    text = re.sub(r'\n(?!\n)', ' ', text)
    return text

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
st.title("Italian TTS (Edge TTS)")
st.markdown("**Nota:** Questo strumento supporta solo la lingua italiana.")

# Caricamento del file
uploaded_file = st.file_uploader("Carica un file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

# Testo inserito manualmente
manual_text = st.text_area("Oppure inserisci il testo manualmente", "")

extracted_text = ""

# Processa il file caricato o il testo inserito manualmente
if uploaded_file is not None:
    extracted_text = process_file(uploaded_file)
elif manual_text.strip() != "":
    extracted_text = manual_text

if extracted_text:
    st.text_area("Testo Estratto", extracted_text, height=200)

    # Selezione dello Speaker
    language = "Italian"
    speakers = list(language_dict[language].keys())
    speaker = st.selectbox("Seleziona lo Speaker", speakers)

    # Generazione dell'audio
    if st.button("Genera Audio"):
        audio_path = text_to_speech_edge(extracted_text, language, speaker)
        st.audio(audio_path, format="audio/mp3")
