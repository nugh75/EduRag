# main.py
import streamlit as st
from description import get_description
from amm.manage_indices import view_and_manage_db
from amm.crea_database import create_database
from amm.delete_file import delete_file_from_database
from query_database.query_gpt import query_db_gpt4
from query_database.query_claude import query_db_claude
from tool.pdf_summary import pdf_summary
from tool.pdf_summary_a import pdf_summary_a
#from tool.savickas_interview import savickas_interview
from tool.open_question import open_question
from utilizzo.uso import get_uso
from utilizzo.consigli import get_consigli
from mostra_indici import mostra_indici_disponibili
from tool.voce import voce




def display_main_menu():
    """
    Display the main menu in the sidebar and return the selected page.
    """
    # Define the main menu options
    menu_options = ["Home", "Come si usa", "Amministrazione", "Interrogazione db indicizzato", "Tool"]

    # Display the main menu and capture the selection
    selected_page = st.sidebar.selectbox(" ", menu_options)

    return selected_page

def display_sub_menu(selected_page):
    """
    Display the sub-menu for the selected main page and return the selected subpage.
    """
    sub_page = None

    # Define the sub-menu options for each main menu page
    if selected_page == "Amministrazione":
        sub_page_options = ["Gestione Indici", "Crea Database", "Elimina File"]
        sub_page = st.sidebar.selectbox("Seleziona una funzione:", sub_page_options)
        
        mostra_indici_disponibili()
    
    elif selected_page == "Come si usa":
        sub_page_options = ["Primo utilizzo","Consigli"]
        sub_page = st.sidebar.selectbox("Seleziona:", sub_page_options)
    
        
    elif selected_page == "Interrogazione db indicizzato":
        sub_page_options = ["Openai","Anthropic"]
        sub_page = st.sidebar.selectbox("Seleziona:", sub_page_options)

    elif selected_page == "Tool":
        sub_page_options = ["Riassunto PDF", "Riassunto PDF articoli scientifici", "Intervista Savickas", "Domande aperte", "TTS Edge"]
        sub_page = st.sidebar.selectbox("Seleziona un tool:", sub_page_options)

    return sub_page

# Define functions for each page and subpage
def mostra_home():
    st.title("EduRag")
    st.write(get_description())
    
def mostra_come_si_usa():
    st.title("Come si usa")
   
    # Mostra il sottomenu per "Come si usa"
    selected_subpage = display_sub_menu("Come si usa")

    # Mostra solo la funzione corretta per la sottopagina selezionata
    if selected_subpage == "Primo utilizzo":
        get_uso()
    elif selected_subpage == "Consigli":
        get_consigli()
        
def mostra_amministrazione():
    st.title("Amministrazione")
   
    # Mostra il sottomenu per le operazioni amministrative
    selected_subpage = display_sub_menu("Amministrazione")

    # Mostra solo la funzione corretta per la sottopagina selezionata
    if selected_subpage == "Gestione Indici":
        view_and_manage_db()
    elif selected_subpage == "Crea Database":
        create_database()
    elif selected_subpage == "Elimina File":
        delete_file_from_database()

def mostra_interrogazione_db():
    st.title("Interroga il db indicizzato")

    # Mostra il sottomenu per le operazioni di interrogazione db
    selected_subpage = display_sub_menu("Interrogazione db indicizzato")

    # Mostra solo la funzione corretta per la sottopagina selezionata
    if selected_subpage == "Openai":
        query_db_gpt4()
    elif selected_subpage == "Anthropic":
        query_db_claude()

def mostra_tool():
    st.title("Tool")
    #st.write("Funzioni di supporto.")

    # Mostra il sottomenu per le operazioni di Tool
    selected_subpage = display_sub_menu("Tool")

    # Mostra solo la funzione corretta per la sottopagina selezionata
    if selected_subpage == "Riassunto PDF":
        pdf_summary()
    elif selected_subpage == "Riassunto PDF articoli scientifici":
        pdf_summary_a()
  #  elif selected_subpage == "Intervista Savickas":
   #     savickas_interview()
    elif selected_subpage == "Domande aperte":
        open_question()
    elif selected_subpage == "TTS Edge":
        voce()


# Main application
def main():
    st.sidebar.title("Menu")

    # Display main menu
    selected_page = display_main_menu()

    # Execute main page function
    if selected_page == "Home":
        mostra_home()
        mostra_indici_disponibili()
    elif selected_page == "Come si usa":
        mostra_come_si_usa() 
    elif selected_page == "Amministrazione":
        mostra_amministrazione()
    elif selected_page == "Interrogazione db indicizzato":
        mostra_interrogazione_db()
    elif selected_page == "Tool":
        mostra_tool()
        

if __name__ == "__main__":
    main()
