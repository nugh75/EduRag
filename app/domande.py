import os
import random
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Define the main function
def open_question():
    # Initialize session state
    init_session_state()

    # Configure the user interface
    configure_ui()

    # Sidebar configuration
    db_path = "app/db"
    subfolders = list_subfolders(db_path)

    if not subfolders:
        st.error("Nessuna sotto-cartella trovata nella cartella 'db'. Assicurati che ci siano dati disponibili per la ricerca.")
        return

    # Aggiunta delle opzioni per selezionare il modello LLM e inserire la chiave API
    api_choice = st.sidebar.selectbox("Scegli la chiave API da usare", ["Usa chiave di sistema", "Inserisci la tua chiave API"], index=0)
    
    if api_choice == "Inserisci la tua chiave API":
        openai_api_key = st.sidebar.text_input("Inserisci la tua chiave API OpenAI", st.session_state.get("user_api_key", ""), type="password")
        st.session_state.user_api_key = openai_api_key  # Salva la chiave API inserita dall'utente
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")

    model_choice = st.sidebar.selectbox("Seleziona il modello LLM", ["gpt-4o", "gpt-4o-mini"], index=1)
    st.session_state.model_choice = model_choice  # Salva la scelta del modello

    # Slider per impostare la temperatura per la generazione della domanda e valutazione della risposta
    temperature_gen = st.sidebar.slider(
        "Temperatura per la generazione della domanda",
        0.0,
        1.0,
        0.2,
        help="La temperatura nei modelli di linguaggio (LLM) regola la casualità delle risposte generate: valori bassi (vicini a 0) rendono le risposte più deterministiche e ripetitive, mentre valori più alti introducono maggiore variabilità e creatività.",
    )

    temperature_eval = st.sidebar.slider(
        "Temperatura per la valutazione della risposta",
        0.0,
        1.0,
        0.2,
        help="La temperatura per la valutazione della risposta regola l'accuratezza e la creatività del giudizio.",
    )

    # Slider per il numero di chunk da recuperare
    similarity_k = st.sidebar.slider(
        "Numero di chunk da recuperare",
        3,  # Set a default value of 3
        15,
        3,
        help="Nel contesto del Recupero delle Informazioni con i Grandi Modelli di Linguaggio (RAG), i chunk sono segmenti di testo suddivisi da documenti più grandi.",
    )

    # Selezione dell'indice FAISS
    Indice = st.selectbox("Seleziona l'indice", subfolders)

    if st.button("Genera Domanda"):
        if not openai_api_key.startswith("sk-"):
            st.warning("Per favore, inserisci una chiave API OpenAI valida!", icon="⚠")
            return

        # Configuration settings
        model_gen = ChatOpenAI(temperature=temperature_gen, model_name=model_choice, api_key=openai_api_key)
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2')

        # Load or create the FAISS index with the specified folder
        if "faiss_index" not in st.session_state or st.session_state.faiss_index is None:
            faiss_index = get_faiss_index(os.path.join(db_path, Indice), embeddings)
            st.session_state.faiss_index = faiss_index
        else:
            faiss_index = st.session_state.faiss_index

        if faiss_index is None:
            st.error("Impossibile caricare o creare l'indice FAISS.")
            return

        retriever = faiss_index.as_retriever(
            search_type="mmr", search_kwargs={"k": similarity_k}
        )
        st.session_state.retriever = retriever

        # Recupera i chunk selezionati
        relevant_docs = retriever.get_relevant_documents("")
        selected_docs = random.sample(relevant_docs, 3)  # Seleziona casualmente 3 chunk

        combined_context = " ".join([doc.page_content for doc in selected_docs])

        # Prompt configuration for question generation
        messages = [
            SystemMessagePromptTemplate.from_template("Sei un assistente utile che genera domande in italiano basate sui contenuti forniti."),
            HumanMessagePromptTemplate.from_template("Genera una domanda basata su questi contenuti: {context}")
        ]
        prompt_gen = ChatPromptTemplate.from_messages(messages)

        rag_chain = build_rag_chain(prompt_gen, model_gen, retriever)

        # Execute the query and display the response
        try:
            st.session_state.last_question = query_stream(
                combined_context, rag_chain
            )

            st.session_state.formatted_context = format_documents(selected_docs)

            # Salva l'interazione nello storico
            st.session_state.interazioni.append({
                "domanda": st.session_state.last_question,
                "risposta": "",
                "valutazione": "",
                "indice": Indice,
                "temperatura": temperature_gen,
                "chunk da recuperare": similarity_k,
                "fonte": st.session_state.formatted_context
            })

        except Exception as e:
            st.error(f"Si è verificato un errore durante la generazione della domanda: {e}")
            return

    # Mostra la domanda generata se esiste
    if "last_question" in st.session_state and st.session_state.last_question:
        st.text_area("Domanda generata:", st.session_state.last_question, height=150)

        # Input for the user's answer
        st.session_state.user_answer = st.text_area(
            "Inserisci la tua risposta", st.session_state.get("user_answer", ""), height=100
        )

        # Contatore di caratteri per la risposta
        user_answer = st.session_state.user_answer if st.session_state.user_answer is not None else ""
        st.write(f"Numero di caratteri della risposta: {len(user_answer)}")

        if st.button("Valuta Risposta"):
            if not st.session_state.last_question or not st.session_state.user_answer:
                st.warning("Per favore, genera prima una domanda e inserisci la tua risposta!", icon="⚠")
                return

            if "retriever" not in st.session_state or st.session_state.retriever is None:
                st.error("Non è stato possibile recuperare il contesto per la valutazione della risposta.")
                return

            retriever = st.session_state.retriever

            # Recupera i chunk più simili per la valutazione
            eval_chunks = retriever.get_relevant_documents(st.session_state.user_answer)
            eval_context = " ".join([doc.page_content for doc in eval_chunks])

            # Configuration settings for answer evaluation
            model_eval = ChatOpenAI(temperature=temperature_eval, model_name=model_choice, api_key=openai_api_key)

            # Generazione della proposta di risposta
            proposed_answer_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template("Sei un assistente utile che propone una risposta alla domanda basata sui contenuti forniti."),
                HumanMessagePromptTemplate.from_template("Proponi una risposta alla seguente domanda: {question}\n\nBasata su questo contesto: {context}")
            ])

            proposed_answer_chain = proposed_answer_prompt | model_eval | StrOutputParser()

            try:
                proposed_answer = query_stream(
                    {"question": st.session_state.last_question, "context": eval_context},
                    proposed_answer_chain
                )
                st.session_state.proposed_answer = proposed_answer

            except Exception as e:
                st.error(f"Si è verificato un errore durante la generazione della proposta di risposta: {e}")
                return

            # Valutazione della risposta dell'utente con feedback positivo
            evaluation_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template("Sei un assistente utile che valuta le risposte basate su una griglia di valutazione e fornisce suggerimenti per migliorare la risposta."),
                HumanMessagePromptTemplate.from_template("""
                Domanda: {question}
                Proposta di risposta: {proposed_answer}
                Risposta dell'utente: {user_answer}

                Valuta la risposta dell'utente in base ai seguenti criteri:
                1. Comprensione del contenuto: 
                2. Organizzazione:
                3. Argomentazione:
                4. Grammatica e stile:

                Suggerisci un giudizio complessivo sulla risposta dell'utente e fornisci eventuali suggerimenti per migliorarla:
                """)
            ])

            evaluation_chain = evaluation_prompt | model_eval | StrOutputParser()

            try:
                evaluation_input = {
                    "question": st.session_state.last_question,
                    "proposed_answer": st.session_state.proposed_answer,
                    "user_answer": st.session_state.user_answer,
                }

                st.session_state.evaluation = query_stream(
                    evaluation_input,
                    evaluation_chain
                )

                # Scala di giudizi
                giudizio = ""
                if "eccellente" in st.session_state.evaluation.lower():
                    giudizio = "La tua risposta è eccellente! Ottimo lavoro!"
                elif "molto buona" in st.session_state.evaluation.lower():
                    giudizio = "La tua risposta è molto buona, continua così!"
                elif "sufficiente" in st.session_state.evaluation.lower():
                    giudizio = "La tua risposta è sufficiente, ma c'è margine per migliorare."
                else:
                    giudizio = "Devi rivedere la tua risposta. Non preoccuparti, con un po' di lavoro puoi migliorare!"

                # Aggiungi suggerimenti motivazionali
                if "migliorare" in st.session_state.evaluation.lower():
                    suggerimento = "Hai risposto bene, ma potresti considerare di aggiungere questo dettaglio: "
                    st.session_state.evaluation = st.session_state.evaluation.replace("Suggerimenti per migliorare la risposta:", suggerimento)

                # Aggiorna l'ultima interazione con la risposta e la valutazione
                st.session_state.interazioni[-1]["risposta"] = st.session_state.user_answer
                st.session_state.interazioni[-1]["valutazione"] = f"{giudizio}\n\n{st.session_state.evaluation}"

                # Mostra la valutazione della risposta
                st.write(f"**Valutazione della risposta:** {giudizio}\n\n{st.session_state.evaluation}")

                # Mostra la proposta di risposta
                st.write(f"**Proposta di risposta:** {st.session_state.proposed_answer}")

            except Exception as e:
                st.error(f"Si è verificato un errore durante la valutazione della risposta: {e}")
                return

        # Pulsante per creare una nuova domanda
        if st.button("Crea un'altra domanda", on_click=reset_for_new_question):
            st.experimental_rerun()

    # Toggle to show/hide conversation history
    mostra_storico = st.checkbox("Mostra storico delle conversazioni", value=False)

    # Show conversation history if the checkbox is selected
    if mostra_storico:
        display_interaction_history()

    # Button to download the conversation
    if st.button("Scarica conversazione"):
        st.download_button(
            label="Scarica conversazione",
            data=generate_conversation_text(),
            file_name="conversazione.txt",
            mime="text/plain",
        )

def init_session_state():
    """Initialize the session state."""
    session_vars = [
        "interazioni",
        "conversazione",
        "user_query",
        "last_question",
        "user_answer",
        "evaluation",
        "formatted_context",
        "faiss_index",
        "retriever",
        "proposed_answer",
    ]

    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = None if var in ["faiss_index", "retriever", "proposed_answer"] else []

def configure_ui():
    """Configure user interface elements."""
    st.write(
        "Interagisci con GPT di OpenAI"
    )

def list_subfolders(db_path):
    """Return a list of subfolders in the specified directory."""
    try:
        return [
            name for name in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, name))
        ]
    except FileNotFoundError:
        st.error("La cartella 'db' non esiste. Assicurati che la struttura delle cartelle sia corretta.")
        return []

def get_faiss_index(cartella, embeddings, splits=None):
    """Load or create the FAISS index."""
    index_path = os.path.join(cartella, "index.faiss")
    if os.path.exists(cartella) and os.path.exists(index_path):
        try:
            return FAISS.load_local(cartella, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            st.error(f"Errore durante il caricamento dell'indice FAISS: {e}")
            return None
    elif splits is not None:
        faiss_index = FAISS.from_documents(splits, embeddings)
        faiss_index.save_local(cartella)
        return faiss_index
    else:
        st.error("Non ci sono dati disponibili per creare l'indice FAISS.")
        return None

def build_rag_chain(prompt, model, retriever):
    """Create the RAG chain to execute the query."""
    return {
        "context": retriever,
        "question": RunnablePassthrough(),
    } | prompt | model | StrOutputParser()

def format_documents(all_documents):
    """Format retrieved documents for output."""
    formatted_docs = []
    for doc in all_documents:
        source = doc.metadata.get("title", "Sconosciuto")
        page = doc.metadata.get("page_number", "Sconosciuta")

        # Add relevant sections
        formatted_docs.append(
            f"Fonte: {source}, Pagina: {page}\n\n...{doc.page_content}..."
        )
    return "\n\n---------------------------\n\n".join(formatted_docs)

def query_stream(query, rag_chain):
    """Execute the query and return the response as a stream."""
    response = ""
    for chunk in rag_chain.stream(query):
        response += chunk
    return response

def reset_for_new_question():
    """Reset session state variables for a new question."""
    st.session_state.last_question = None
    st.session_state.user_answer = None
    st.session_state.proposed_answer = None
    st.session_state.evaluation = None
    st.session_state.formatted_context = None

def display_interaction_history():
    """Display the interaction history."""
    st.write("### Storico delle conversazioni")
    for interazione in st.session_state.interazioni:
        st.write("-----------------------------")
        st.write(f"**Domanda:** {interazione['domanda']}")
        st.write(f"**Risposta:** {interazione['risposta']}")
        st.write(f"**Valutazione:** {interazione['valutazione']}")
        st.write(f"**Temperatura:** {interazione['temperatura']} -  **Chunk da recuperare:** {interazione['chunk da recuperare']} -  **Indice:** {interazione['indice']}")
        st.write("-----------------------------")
        st.write(f"**Fonte:** {interazione['fonte']}")

def generate_conversation_text():
    """Generate the text for the conversation download."""
    conversation_text = ""
    for interazione in st.session_state.interazioni:
        conversation_text += f"Domanda: {interazione['domanda']}\n"
        conversation_text += f"Risposta: {interazione['risposta']}\n"
        conversation_text += f"Valutazione: {interazione['valutazione']}\n"
        conversation_text += f"Fonte: {interazione['fonte']}\n"
        conversation_text += "-----------------------------\n"
    return conversation_text

if __name__ == "__main__":
    open_question()
