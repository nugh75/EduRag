import streamlit as st
from description import get_description
from amm.manage_indices import view_and_manage_db
from amm.crea_database import create_database
from amm.delete_file import delete_file_from_database
from query_database.query_gpt import query_db_gpt4
from query_database.query_claude import query_db_claude
from tool.pdf_summary import pdf_summary
from tool.pdf_summary_a import pdf_summary_a
from tool.open_question import open_question
from utilizzo.uso import get_uso
from utilizzo.consigli import get_consigli
from mostra_indici import mostra_indici_disponibili
from tool.voce import voce
from dotenv import load_dotenv
import os


# Carica le variabili dal file .env
load_dotenv()

# Definisci le credenziali per gli utenti caricandole dal file .env
users = {
    os.getenv("ADMIN_USER"): {"password": os.getenv("ADMIN_PASSWORD"), "role": "admin"},
    os.getenv("USER_USER"): {"password": os.getenv("USER_PASSWORD"), "role": "user"}
}

def login():
    """
    Funzione di login che autentica l'utente e ritorna il ruolo dell'utente.
    Mostra un form per inserire username e password e verifica le credenziali.
    Se l'autenticazione ha successo, imposta lo stato di sessione come loggato.
    """
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        # Controlla se l'username e la password corrispondono
        if username in users and users[username]["password"] == password:
            # Se autenticato, salva lo stato dell'utente nella sessione
            st.session_state["logged_in"] = True
            st.session_state["role"] = users[username]["role"]
            st.session_state["username"] = username
            st.success(f"Benvenuto, {username}!")
        else:
            st.error("Credenziali non valide. Riprova.")
    return None

def logout():
    """
    Funzione per effettuare il logout.
    Ripristina lo stato della sessione e disconnette l'utente.
    """
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

def display_main_menu(role):
    """
    Visualizza il menu principale nella sidebar in base al ruolo dell'utente (admin o user).
    Restituisce la pagina selezionata dall'utente.
    
    Args:
        role (str): Ruolo dell'utente ("admin" o "user").
    
    Returns:
        selected_page (str): La pagina selezionata dal menu.
    """
    if role == "admin":
        # L'admin ha accesso a tutte le pagine
        menu_options = ["Home", "Come si usa", "Amministrazione", "Interrogazione db indicizzato", "Tool"]
    else:
        # Gli utenti normali non hanno accesso alla sezione "Amministrazione"
        menu_options = ["Home", "Come si usa", "Interrogazione db indicizzato", "Tool"]

    # Mostra il menu e restituisce la pagina selezionata
    selected_page = st.sidebar.selectbox(" ", menu_options)
    return selected_page

def display_sub_menu(selected_page):
    """
    Visualizza il sottomenu per le diverse pagine selezionate dal menu principale.
    Restituisce la funzione selezionata dal sottomenu.
    
    Args:
        selected_page (str): La pagina selezionata dal menu principale.
    
    Returns:
        sub_page (str): La pagina selezionata dal sottomenu (se presente).
    """
    sub_page = None

    # Definisce il sottomenu per le pagine amministrative
    if selected_page == "Amministrazione":
        sub_page_options = ["Gestione Indici", "Crea Database", "Elimina File"]
        sub_page = st.sidebar.selectbox("Seleziona una funzione:", sub_page_options)
        mostra_indici_disponibili()  # Mostra gli indici disponibili per la gestione
    
    # Definisce il sottomenu per la pagina "Come si usa"
    elif selected_page == "Come si usa":
        sub_page_options = ["Primo utilizzo", "Consigli"]
        sub_page = st.sidebar.selectbox("Seleziona:", sub_page_options)
    
    # Definisce il sottomenu per la pagina di interrogazione del database
    elif selected_page == "Interrogazione db indicizzato":
        sub_page_options = ["Openai", "Anthropic"]
        sub_page = st.sidebar.selectbox("Seleziona:", sub_page_options)

    # Definisce il sottomenu per la pagina dei tool
    elif selected_page == "Tool":
        sub_page_options = ["Riassunto PDF", "Riassunto PDF articoli scientifici", "Domande aperte", "TTS Edge"]
        sub_page = st.sidebar.selectbox("Seleziona un tool:", sub_page_options)

    return sub_page

# MODIFICA: La descrizione rimane visibile solo nella Home
def mostra_home():
    """
    Mostra la pagina Home del progetto EduRag.
    La descrizione del progetto viene visualizzata in questa pagina.
    """
    st.title("EduRag")
    st.write(get_description())  # Descrizione visibile solo nella home

def mostra_come_si_usa():
    """
    Mostra la pagina "Come si usa" con le sottosezioni relative al primo utilizzo
    e consigli pratici sull'uso del software.
    """
    st.title("Come si usa")
    selected_subpage = display_sub_menu("Come si usa")

    if selected_subpage == "Primo utilizzo":
        get_uso()  # Mostra le istruzioni per il primo utilizzo
    elif selected_subpage == "Consigli":
        get_consigli()  # Mostra consigli generali sull'uso

def mostra_amministrazione():
    """
    Mostra la pagina Amministrazione, con opzioni per gestire gli indici, creare il database
    e eliminare file dal database.
    Disponibile solo per gli utenti con ruolo admin.
    """
    st.title("Amministrazione")
    selected_subpage = display_sub_menu("Amministrazione")

    if selected_subpage == "Gestione Indici":
        view_and_manage_db()  # Funzione per la gestione degli indici
    elif selected_subpage == "Crea Database":
        create_database()  # Funzione per creare il database
    elif selected_subpage == "Elimina File":
        delete_file_from_database()  # Funzione per eliminare un file dal database

def mostra_interrogazione_db():
    """
    Mostra la pagina per interrogare il database indicizzato.
    Permette di selezionare tra vari metodi di interrogazione come OpenAI o Anthropic.
    """
    st.title("Interroga il db indicizzato")
    selected_subpage = display_sub_menu("Interrogazione db indicizzato")

    if selected_subpage == "Openai":
        query_db_gpt4()  # Interrogazione con GPT-4
    elif selected_subpage == "Anthropic":
        query_db_claude()  # Interrogazione con Claude

def mostra_tool():
    """
    Mostra la pagina "Tool" che offre vari strumenti di supporto, come il riassunto di PDF,
    la generazione di domande aperte, e il Text-To-Speech (TTS Edge).
    """
    st.title("Tool")
    selected_subpage = display_sub_menu("Tool")

    if selected_subpage == "Riassunto PDF":
        pdf_summary()  # Riassunto di un file PDF
    elif selected_subpage == "Riassunto PDF articoli scientifici":
        pdf_summary_a()  # Riassunto specifico per articoli scientifici
    elif selected_subpage == "Domande aperte":
        open_question()  # Generazione di domande aperte
    elif selected_subpage == "TTS Edge":
        voce()  # Funzione di sintesi vocale (Text-to-Speech)

def main():
    """
    Funzione principale dell'applicazione.
    Controlla lo stato di login dell'utente e visualizza le diverse pagine in base al ruolo
    dell'utente e alla pagina selezionata nel menu.
    """
    st.sidebar.title("Menu")

    # Controlla se l'utente è loggato nella sessione
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    # Se non loggato, mostra la home con descrizione e il login
    if not st.session_state["logged_in"]:
        mostra_home()  # MODIFICA: Mostra la descrizione solo nella home
        login()  # Chiede il login
    else:
        # Dopo il login, mostra il menu principale e le funzioni
        role = st.session_state["role"]
        st.sidebar.write(f"Accesso come: {st.session_state['username']} ({role})")
        logout()  # Mostra il pulsante di logout

        # Mostra il menu principale in base al ruolo dell'utente
        selected_page = display_main_menu(role)

        if selected_page == "Home":
            mostra_home()  # MODIFICA: La descrizione resta nella home anche dopo il login
        elif selected_page == "Come si usa":
            mostra_come_si_usa()
        elif selected_page == "Amministrazione" and role == "admin":
            mostra_amministrazione()
        elif selected_page == "Interrogazione db indicizzato":
            mostra_interrogazione_db()
        elif selected_page == "Tool":
            mostra_tool()

if __name__ == "__main__":
    main()
