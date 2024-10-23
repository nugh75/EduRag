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
    clean_text = clean_markdown_formatting(text)  # Rimuove la formattazione Markdown
    voice = language_dict[language_code][speaker]
    communicate = edge_tts.Communicate(clean_text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
        await communicate.save(tmp_path)
    return tmp_path

def text_to_speech_edge(text, language_code, speaker):
    return asyncio.run(text_to_speech_edge_async(text, language_code, speaker))

def openai_m():
    api_choice = st.sidebar.selectbox("Scegli la chiave API da usare", ["Usa chiave di sistema", "Inserisci la tua chiave API"], index=1)
    
    if api_choice == "Inserisci la tua chiave API":
        openai_api_key = st.sidebar.text_input("Inserisci la tua chiave API OpenAI", st.session_state.get("user_api_key", ""), type="password")
        st.session_state.user_api_key = openai_api_key
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        st.error("Errore: La chiave API non è stata inserita o non è configurata correttamente.")
        return None, None, None

    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["gpt-4o", "gpt-4o-mini"], index=1)
    st.session_state.model_choice = model_choice
    
    temperature = st.sidebar.slider("Imposta la temperatura del modello", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    st.session_state.temperature = temperature

    language = st.sidebar.selectbox("Seleziona la lingua per il riassunto e l'audio", ["Italian", "English", "Swedish"])
    speaker = st.sidebar.selectbox("Seleziona la voce per l'audio", list(language_dict[language].keys()))

    return openai_api_key, model_choice, temperature, language, speaker

def extract_text_from_pdf(reader):
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text

def extract_text_from_doc(doc_file):
    logger.info("Extracting text from DOC file.")
    doc = Document(doc_file)
    text = "\n\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_txt(txt_file):
    logger.info("Extracting text from TXT file.")
    text = txt_file.read().decode("utf-8")
    return text

def clean_markdown_formatting(text):
    # Rimuove simboli Markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Rimuove grassetto
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Rimuove corsivo
    text = re.sub(r'\#\#(.*?)\n', r'\1\n', text)  # Rimuove titoli di secondo livello
    text = re.sub(r'\#(.*?)\n', r'\1\n', text)    # Rimuove titoli di primo livello
    text = re.sub(r'[-*]\s', '', text)            # Rimuove elenchi puntati
    return text

def upload_and_extract_text():
    st.write("### Strumento per Riassumere ed Esportare PDF, DOCX, TXT e Audio")

    uploaded_file = st.file_uploader("Carica un file PDF, DOCX o TXT", type=["pdf", "docx", "txt"])

    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        pdf_filename = os.path.splitext(uploaded_file.name)[0]
        logger.info(f"Uploaded file: {uploaded_file.name}")

        if file_type == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = extract_text_from_pdf(reader)
        elif file_type == "docx":
            text = extract_text_from_doc(uploaded_file)
        elif file_type == "txt":
            text = extract_text_from_txt(uploaded_file)
        else:
            st.error("Formato file non supportato.")
            return None, None

        logger.info("Text extraction completed.")
        return clean_markdown_formatting(text), pdf_filename
    else:
        return None, None

def split_text_into_chunks(text, num_chunks):
    chunk_size = len(text) // num_chunks
    chunks = []
    start = 0
    
    for i in range(num_chunks):
        end = start + chunk_size
        if i == num_chunks - 1:
            end = len(text)
        chunk = text[start:end].strip()
        chunks.append(chunk)
        start = end
        logger.info(f"Chunk {i+1}: {chunk[:100]}...")
    
    return chunks

def summarize_text_with_context(text, prev_chunk, next_chunk, model_choice, temperature, openai_api_key, language="Italian", custom_prompt=""):
    logger.info(f"Starting text summarization with context in {language}.")
    
    llm = ChatOpenAI(
        model=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    template = ChatPromptTemplate.from_messages([
        ("system", f"""
        Sei un assistente AI specializzato nel analizzare testi in {language}. 
        
        Riassumi i testi in modo chiaro e conciso, mantenendo i punti principali e l'essenza del contenuto originale.

# Steps

1. Leggi il testo originale attentamente.
2. Identifica i punti principali e le idee centrali.
3. Elimina i dettagli superflui e la ridondanza.
4. Riformula le informazioni rilevanti in un linguaggio semplice e diretto.
5. Assicurati che il riassunto rispecchi fedelmente il significato del testo originale.

# Output Format

Un breve paragrafo che riassume il testo originale, contenente le idee principali in forma chiara e concisa.

# Examples

**Input:**
"Il mondo accademico sta affrontando una rivoluzione digitale, con sempre più università che adottano tecnologie avanzate per migliorare l'apprendimento e la ricerca. Tuttavia, ci sono preoccupazioni riguardanti la privacy e la sicurezza dei dati. Nonostante queste sfide, i benefici dell'innovazione tecnologica nel campo dell'istruzione stanno avendo un impatto positivo a lungo termine."

**Output:**
Le università stanno sempre più integrando le tecnologie digitali per migliorare l'apprendimento, nonostante le preoccupazioni di privacy e sicurezza. L'innovazione, comunque, offre un impatto positivo a lungo termine su istruzione e ricerca.

# Notes

- Mantieni il tono neutrale e oggettivo.
- Assicurati che il riassunto sia accessibile e comprensibile per un pubblico ampio.
- Fai attenzione a non introdurre nuove informazioni o opinioni personali.
- Considera il contesto fornito dai blocchi precedente e successivo per garantire continuità e coerenza.
- Testo precedente: {{previous_chunk}}
- Testo successivo: {{next_chunk}}
        """),
        ("human", "{input}")
    ])
    
    if custom_prompt:
        custom_text = f"\n\n{custom_prompt}"
        text += custom_text
    
    chain = template.pipe(llm)
    response = chain.invoke({
        "previous_chunk": prev_chunk,
        "next_chunk": next_chunk,
        "input": text
    })
    
    logger.info(f"Text summarization with context in {language} completed.")
    return response.content

def enhance_text_with_headings(summarized_text, model_choice, temperature, openai_api_key, language="Italian", num_parts=3, custom_prompt=""):
    logger.info(f"Starting text enhancement with headings in {language}.")
    
    llm = ChatOpenAI(
        model=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    text_parts = split_text_into_chunks(summarized_text, num_parts)
    
    enhanced_text = ""
    
    for part in text_parts:
        if custom_prompt:
            part += f"\n\n{custom_prompt}"
        
        template = ChatPromptTemplate.from_messages([
            ("system", f"""
            Sei un assistente AI specializzato nel migliorare testi riassunti  in {language}.

            Correggi la struttura e il lessico di un testo fornito in italiano.

Esamina il testo per errori grammaticali, sintattici o lessicali, e apporta le modifiche necessarie per garantire chiarezza e scorrevolezza. Considera anche il tono e lo stile del testo, facendo attenzione a mantenere o adattare lo stile in base al contesto e al pubblico di riferimento.

# Steps

1. Leggi attentamente il testo per comprendere il suo significato e il messaggio che vuole trasmettere.
2. Identifica gli errori grammaticali, di sintassi, o lessicali.
3. Valuta la scorrevolezza e la coerenza del testo.
4. Effettua le correzioni necessarie, includendo miglioramenti alla struttura delle frasi e al vocabolario utilizzato.
5. Verifica che il tono e lo stile siano appropriati per il pubblico target, apportando aggiustamenti se necessario.

# Output Format

Produci una versione corretta e migliorata del testo, rispettando il formato e la lunghezza del testo originale. Indica con chiarezza eventuali modifiche effettuate rispetto all'originale.

# Examples

**Input:**  
"Questa é una esempio di testo che necessita correzione, infatti ci sono diversi errori grammatici e sintattici."

**Output:**  
"Questo è un esempio di testo che necessita di correzione; infatti, ci sono diversi errori grammaticali e sintattici."

(Nota: gli esempi devono essere rappresentativi, ma i testi reali potrebbero essere più lunghi e complessi. Assicurati di applicare la stessa logica di revisione.)

# Notes

- Fai attenzione a non alterare il significato originale del testo.
- Considera le varianti regionali o stilistiche nel caso siano rilevanti.
            """),
            ("human", "{input}")
        ])
        
        chain = template.pipe(llm)
        response = chain.invoke({
            "input": part
        })
        
        enhanced_text += response.content + "\n"

    logger.info(f"Text enhancement with headings in {language} completed.")
    return enhanced_text

def generate_outline_from_enhanced_text(enhanced_text, model_choice, temperature, openai_api_key, language="Italian", num_parts=3):
    logger.info(f"Starting outline generation from enhanced text in {language}.")
    
    llm = ChatOpenAI(
        model=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    text_parts = split_text_into_chunks(enhanced_text, num_parts)
    
    outline_text = ""
    
    for i, part in enumerate(text_parts):
        template = ChatPromptTemplate.from_messages([
            ("system", f"""
            Sei un assistente AI specializzato nella creazione di outline dettagliati basati su testi migliorati. Il tuo compito è generare un outline che rifletta la struttura e i punti chiave del testo fornito, inclusi eventuali dati in formato tabellare e immagini presenti nel testo originale.

            1. Leggi attentamente la parte del testo.
            2. Identifica i punti principali, gli argomenti chiave, le tabelle e le immagini.
            3. Crea un outline gerarchico con sezioni e sottosezioni.
            4. Mantieni un tono neutro e oggettivo.
            """),
            ("human", "{input}")
        ])
        
        chain = template.pipe(llm)
        response = chain.invoke({
            "input": part
        })
        
        outline_text += f"{response.content}\n\n"  # Rimuovi la dicitura "Parte X:"

    logger.info(f"Outline generation from enhanced text in {language} completed.")
    return outline_text


def format_bibliography_in_apa(enhanced_text, model_choice, temperature, openai_api_key, language="Italian"):
    logger.info(f"Starting bibliography formatting in APA style in {language}.")
    
    llm = ChatOpenAI(
        model=model_choice,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    template = ChatPromptTemplate.from_messages([
        ("system", f"""
        Sei un assistente AI specializzato nel formattare bibliografie in stile APA in {language}. Il tuo compito è esaminare il testo fornito, identificare eventuali fonti bibliografiche e riformattarle secondo lo stile APA.

        Per formattare le fonti bibliografiche, segui queste linee guida:

        1. Cerca nel testo eventuali fonti bibliografiche.
        2. Riformatta ogni fonte bibliografica secondo lo stile APA.
        3. Inserisci le fonti riformattate in una sezione di bibliografia alla fine del testo.
        """),
        ("human", "{input}")
    ])
    
    chain = template.pipe(llm)
    response = chain.invoke({
        "input": enhanced_text
    })
    
    logger.info(f"Bibliography formatting in APA style in {language} completed.")
    
    final_text_with_bibliography = response.content
    return final_text_with_bibliography

def create_markdown_file(text, filename):
    """
    Crea un file markdown con il testo fornito.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)

def apply_text_formatting(paragraph, text):
    """
    Applica la formattazione di grassetto e corsivo al testo.
    """
    # Gestione del grassetto e del corsivo combinati: ***testo***
    matches = re.findall(r'\*\*\*(.*?)\*\*\*', text)
    for match in matches:
        run = paragraph.add_run(match)
        run.bold = True
        run.italic = True
        text = text.replace(f'***{match}***', '')

    # Gestione del grassetto: **testo**
    matches = re.findall(r'\*\*(.*?)\*\*', text)
    for match in matches:
        run = paragraph.add_run(match)
        run.bold = True
        text = text.replace(f'**{match}**', '')

    # Gestione del corsivo: *testo*
    matches = re.findall(r'\*(.*?)\*', text)
    for match in matches:
        run = paragraph.add_run(match)
        run.italic = True
        text = text.replace(f'*{match}*', '')

    # Aggiungi il testo rimanente senza formattazione
    paragraph.add_run(text)

def create_docx(text, sections=None):
    logger.info(f"Creating the .docx file in memory.")
    doc = Document()
    
    if sections is None:
        sections = [("Testo", text)]
    
    for section in sections:
        if isinstance(section, tuple) and len(section) == 2:
            section_name, section_text = section
            doc.add_heading(section_name, level=1)
            for paragraph_text in section_text.split("\n"):
                if paragraph_text.strip():
                    # Identifica e gestisci i titoli
                    if paragraph_text.startswith("###"):
                        doc.add_heading(paragraph_text.strip("# "), level=3)
                    elif paragraph_text.startswith("##"):
                        doc.add_heading(paragraph_text.strip("# "), level=2)
                    elif paragraph_text.startswith("#"):
                        doc.add_heading(paragraph_text.strip("# "), level=1)
                    else:
                        # Se non è un titolo, applica la formattazione
                        paragraph = doc.add_paragraph()
                        apply_text_formatting(paragraph, paragraph_text)
        else:
            logger.error(f"Invalid section format: {section}")
            raise ValueError("Each section should be a tuple with two elements: (section_name, section_text)")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    logger.info(f".docx file successfully created in memory.")
    return buffer

def create_outline_bibliography_docx(outline, bibliography):
    logger.info(f"Creating the outline and bibliography .docx file in memory.")
    
    sections = [("Outline", outline), ("Bibliografia", bibliography)]
    docx_buffer = create_docx("", sections=sections)
    
    logger.info(f"Outline and bibliography .docx file successfully created in memory.")
    return docx_buffer

def clean_markdown_formatting(text):
    """
    Rimuove la formattazione Markdown dal testo ma mantiene gli elenchi puntati.
    """
    # Rimuovi grassetto e corsivo combinati: ***testo***
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text)
    
    # Rimuovi grassetto: **testo**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Rimuovi corsivo: *testo*
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Rimuovi titoli di terzo livello: ### Titolo
    text = re.sub(r'###\s*(.*?)\s*', r'\1\n', text)
    
    # Rimuovi titoli di secondo livello: ## Titolo
    text = re.sub(r'##\s*(.*?)\s*', r'\1\n', text)
    
    # Rimuovi titoli di primo livello: # Titolo
    text = re.sub(r'#\s*(.*?)\s*', r'\1\n', text)
    
    # Mantieni gli elenchi puntati, non rimuovere i simboli `-` o `*` usati come marcatori di elenchi
    # Quindi, non aggiungiamo un'ulteriore espressione regolare qui.

    return text


def create_txt(text):
    logger.info(f"Creating the .txt file in memory.")
    text = clean_markdown_formatting(text)  # Rimuove la formattazione Markdown
    buffer = BytesIO()
    buffer.write(text.encode('utf-8'))
    buffer.seek(0)
    logger.info(f".txt file successfully created in memory.")
    return buffer


def create_md(text):
    logger.info(f"Creating the .md file in memory.")
    buffer = BytesIO()
    buffer.write(text.encode('utf-8'))
    buffer.seek(0)
    logger.info(f".md file successfully created in memory.")
    return buffer

def create_outline_bibliography_txt(outline, bibliography):
    logger.info(f"Creating the outline and bibliography .txt file in memory.")
    buffer = BytesIO()
    buffer.write(("Outline:\n" + outline + "\n\nBibliografia:\n" + bibliography).encode('utf-8'))
    buffer.seek(0)
    logger.info(f"Outline and bibliography .txt file successfully created in memory.")
    return buffer

def create_zip_file(main_txt_data, main_docx_data, outline_bibliography_txt_data, outline_bibliography_docx_data, audio_data, pdf_filename, main_md_data):
    logger.info(f"Creating a zip file containing .txt, .docx, .md files, and audio.")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr(f"{pdf_filename}_riassunto.txt", main_txt_data.getvalue().decode('utf-8'))
        zip_file.writestr(f"{pdf_filename}_riassunto.docx", main_docx_data.getvalue())
        zip_file.writestr(f"{pdf_filename}_outline_bibliografia.txt", outline_bibliography_txt_data.getvalue().decode('utf-8'))
        zip_file.writestr(f"{pdf_filename}_outline_bibliografia.docx", outline_bibliography_docx_data.getvalue())
        zip_file.writestr(f"{pdf_filename}_riassunto.md", main_md_data.getvalue().decode('utf-8'))
        zip_file.writestr(f"{pdf_filename}_audio.mp3", audio_data.getvalue())
    zip_buffer.seek(0)
    logger.info("Zip file created successfully.")
    return zip_buffer

def pdf_summary():
    text, pdf_filename = upload_and_extract_text()
    
    if text is not None:
        openai_api_key, model_choice, temperature, language, speaker = openai_m()
        
        if not openai_api_key or not model_choice or temperature is None:
            st.error("Configurazione non corretta. Verifica la chiave API e le altre impostazioni.")
            return
        
        # Box per aggiungere testo personalizzato ai prompt
        custom_prompt_first = st.text_area("A chi è rivolto il riassunto? ci sono istruzioni particolari che vorresti includere per fare il riassunto? (Riassunto)", "")
        custom_prompt_second = st.text_area("Ci sono istruzionio che vorresti includere per la revisione del riassunto? (Miglioramento e Titolazione)", "")
        
        num_chunks = st.number_input("In quanti pezzi vuoi dividere il testo per il riassunto?", min_value=1, max_value=20, value=5)
        num_parts = st.number_input("In quante parti vuoi dividere il testo per il miglioramento con titoletti?", min_value=1, max_value=10, value=3)

        # Attiva il processo solo dopo che l'utente ha fornito tutte le informazioni
        if st.button("Avvia il processo di riassunto e miglioramento"):
            chunks = split_text_into_chunks(text, num_chunks)
            st.success(f"Testo diviso in {len(chunks)} blocchi.")
            
            summarized_text = f"Riassunto - {pdf_filename} ({model_choice}, Temp: {temperature})\n\n"
            
            for i, chunk in enumerate(chunks):
                prev_chunk = chunks[i-1] if i > 0 else ""
                next_chunk = chunks[i+1] if i < len(chunks) - 1 else ""

                try:
                    summary = summarize_text_with_context(chunk, prev_chunk, next_chunk, model_choice, temperature, openai_api_key, language=language, custom_prompt=custom_prompt_first)
                    if not summary.strip():
                        summary = "Impossibile generare il riassunto."
                    logger.info(f"Blocco {i+1} riassunto con successo.")
                    
                    if i == 0:
                        st.write("### Primo Riassunto Generato:")
                        st.write(summary)
                    
                except Exception as e:
                    summary = "Errore durante la generazione del riassunto."
                    logger.error(f"Errore nel riassumere il blocco {i+1}: {e}")
                
                summarized_text += summary + "\n"
            
            enhanced_text = enhance_text_with_headings(summarized_text, model_choice, temperature, openai_api_key, language=language, num_parts=num_parts, custom_prompt=custom_prompt_second)

            outline_text = generate_outline_from_enhanced_text(enhanced_text, model_choice, temperature, openai_api_key, language=language, num_parts=num_parts)

            bibliography_text = format_bibliography_in_apa(enhanced_text, model_choice, temperature, openai_api_key, language=language)
            
            st.session_state['final_text'] = enhanced_text
            st.session_state['outline_text'] = outline_text
            st.session_state['bibliography_text'] = bibliography_text
            
            audio_text = re.sub(r'<img.*?>|<table.*?>.*?</table>', '', enhanced_text, flags=re.DOTALL)
            audio_path = text_to_speech_edge(audio_text, language, speaker)
            with open(audio_path, "rb") as audio_file:
                st.session_state['audio_bytes'] = BytesIO(audio_file.read())

            # Crea i file DOCX, TXT e MD per il riassunto principale
            main_txt_data = create_txt(enhanced_text)
            main_docx_data = create_docx(enhanced_text)
            main_md_data = create_md(enhanced_text)
            
            # Crea i file DOCX e TXT per l'outline e la bibliografia
            outline_bibliography_txt_data = create_outline_bibliography_txt(outline_text, bibliography_text)
            outline_bibliography_docx_data = create_outline_bibliography_docx(outline_text, bibliography_text)
            
            st.write("### Testo finale (Riassunto):")
            st.write(enhanced_text, unsafe_allow_html=True)
            
            st.write("### Outline e Bibliografia (in un altro file):")
            st.write(outline_text)
            st.write(bibliography_text)

            if all(key in st.session_state for key in ['final_text', 'outline_text', 'bibliography_text', 'audio_bytes']):
                zip_data = create_zip_file(main_txt_data, main_docx_data, outline_bibliography_txt_data, outline_bibliography_docx_data, st.session_state['audio_bytes'], pdf_filename, main_md_data)
                
                st.download_button(
                    label="Scarica il Riassunto, l'Outline, la Bibliografia e l'Audio come .zip",
                    data=zip_data,
                    file_name=f"{pdf_filename}_riassunto_outline_audio.zip",
                    mime="application/zip"
                )
                logger.info(f"Riassunto, outline, bibliografia e audio esportati come {pdf_filename}_riassunto_outline_audio.zip.")

if __name__ == "__main__":
   pdf_summary()
