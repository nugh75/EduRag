# main.py
import streamlit as st
from description import get_description
#from menu import display_main_menu, display_sub_menu
from amm.manage_indices import view_and_manage_db
#from mostra_indici import mostra_indici_disponibili
from amm.crea_database import create_database
from amm.delete_file import delete_file_from_database
from query_databasae.query_pageg import query_db_gpt4_mini
from query_databasae.query_pagec import query_db_claude
from query_databasae.query_pagec_k import query_db_gpt4_mini_k
from tool.pdf_summary import pdf_summary
from tool.savickas_interview import savickas_interview


def display_main_menu():
    """
    Display the main menu in the sidebar and return the selected page.
    """
    # Define the main menu options
    menu_options = ["Home", "Amministrazione", "Interrogazione db", "Tool"]

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

    elif selected_page == "Interrogazione db":
        sub_page_options = ["Gpt-4o-mini", "Gpt-4o-mini con chiave","Claude-3-5-sonnet-20240620"]
        sub_page = st.sidebar.selectbox("Seleziona un modello:", sub_page_options)

    elif selected_page == "Tool":
        sub_page_options = ["Riassunto PDF", "Savickas intervista"]
        sub_page = st.sidebar.selectbox("Seleziona un tool:", sub_page_options)

    return sub_page

# Define functions for each page and subpage
def mostra_home():
    st.title("Edubot")
    st.write(get_description())

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
    selected_subpage = display_sub_menu("Interrogazione db")

    # Mostra solo la funzione corretta per la sottopagina selezionata
    if selected_subpage == "Gpt-4o-mini":
        query_db_gpt4_mini()
    elif selected_subpage == "Gpt-4o-mini con chiave":
        query_db_gpt4_mini_k
    elif selected_subpage == "Claude-3-5-sonnet-20240620":
        query_db_claude()

def mostra_tool():
    st.title("Tool")
    st.write("Funzioni di supporto.")

    # Mostra il sottomenu per le operazioni di Tool
    selected_subpage = display_sub_menu("Tool")

    # Mostra solo la funzione corretta per la sottopagina selezionata
    if selected_subpage == "Riassunto PDF":
        pdf_summary()
    elif selected_subpage == "Savickas intervista":
        savickas_interview()


# Main application
def main():
    st.sidebar.title("Menu")

    # Display main menu
    selected_page = display_main_menu()

    # Execute main page function
    if selected_page == "Home":
        mostra_home()
    elif selected_page == "Amministrazione":
        mostra_amministrazione()
    elif selected_page == "Interrogazione db":
        mostra_interrogazione_db()
    elif selected_page == "Tool":
        mostra_tool()

if __name__ == "__main__":
    main()
