import os
import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough
from sidebar.sidebar_config import sidebar_c  # Import the sidebar configuration function
from prompt.prompt_config import get_chat_prompt_template  # Importa il modulo del prompt
from dotenv import load_dotenv
from utils.anthropic_m import anthropic_m 
from utils.def_comuny import *


# Define the main function
def query_db_claude():
    # Initialize session state
    init_session_state()

    # Configure the user interface
    configure_ui()

    claude_api_key = anthropic_m()  # Capture the API key returned by the function
    
    # Sidebar configuration
    db_path = "app/db"
    temperature, similarity_k, Indice = sidebar_c(db_path, list_subfolders)

    if Indice is None:
        return  # Early return if there was an error with the subfolders

    # User query input
    st.session_state.user_query = st.text_area(
        "Inserisci la tua domanda", st.session_state.user_query
    )

    if st.button("Invia"):
        if not claude_api_key:
            st.warning("Per favore, inserisci una chiave API valida!", icon="⚠")
            return

        # Configuration settings
        model = ChatAnthropic(temperature=temperature, model_name=st.session_state.model_choice, api_key=claude_api_key)
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L12-v2')

        # Load or create the FAISS index with the specified folder
        faiss_index = get_faiss_index(os.path.join(db_path, Indice), embeddings)

        if faiss_index is None:
            st.error("Impossibile caricare o creare l'indice FAISS.")
            return

        retriever = faiss_index.as_retriever(
            search_type="mmr", search_kwargs={"k": similarity_k}
        )

       # Prompt configuration
        prompt = get_chat_prompt_template()  # Usa il prompt esterno

        rag_chain = build_rag_chain(prompt, model, retriever)

        # Execute the query and display the response
        try:
            st.session_state.last_response = query_stream(
                st.session_state.user_query, rag_chain
            )

            # Format retrieved documents to add them to the conversation
            st.session_state.formatted_context = format_documents(
                retriever.get_relevant_documents(st.session_state.user_query)
            )

            # Add the question, answer, and additional information to the list of interactions
            add_interaction(
                st.session_state.user_query,
                st.session_state.last_response,
                temperature,
                similarity_k,
                Indice,
                st.session_state.formatted_context,
            )

            # Reset the query after obtaining the response
            st.session_state.user_query = ""
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'esecuzione della query: {e}")
            return

    # Display the current question and answer
    if st.session_state.last_response:
        display_current_interaction(
            temperature, similarity_k, Indice, st.session_state.formatted_context
        )

    # Pulsante per resettare la visualizzazione corrente mantenendo i parametri nella sidebar
    if st.button("Resetta e fai una nuova domanda"):
        st.session_state.user_query = ""
        st.session_state.last_response = ""
        st.session_state.formatted_context = ""

    # Toggle to show/hide conversation history
    mostra_storico = st.checkbox("Mostra storico delle conversazioni", value=False)

    # Show conversation history if the checkbox is selected
    if mostra_storico:
        display_interaction_history()

    # Button to download the conversation
    if st.button("Scarica conversazione"):
        st.download_button(
            label="Scarica conversazione",
            data=st.session_state.conversazione,
            file_name="conversazione.txt",
            mime="text/plain",
        )
comuni()

if __name__ == "__main__":
    query_db_claude()
