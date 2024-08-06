import os
import logging
import streamlit as st
from utils import leggi_descrizioni_e_documenti

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def vedi_e_rinomina_db():
    # Percorso della cartella dove sono salvati gli indici FAISS
    faiss_index_folder = "db"

    # Controllo se la cartella degli indici esiste
    if not os.path.exists(faiss_index_folder):
        logging.error("La cartella degli indici non esiste. Creane uno prima di procedere.")
        st.error("La cartella degli indici non esiste. Crea prima un indice.")
        return

    # Visualizzazione degli indici, delle descrizioni e dei documenti nella barra laterale
    st.sidebar.header("Indici Disponibili")
    indici_info = leggi_descrizioni_e_documenti(faiss_index_folder)

    for indice in indici_info:
        with st.sidebar.expander(indice["nome"], expanded=False):
            st.write(f"**Descrizione:** {indice['descrizione']}")
            st.write("**Documenti:**")
            for doc in indice["documenti"]:
                st.write(f"- {doc}")

    # Mostra gli indici disponibili
    if indici_info:
        # Usa selectbox per selezionare un indice da rinominare
        indice_nomi = [indice['nome'] for indice in indici_info]
        selected_index = st.selectbox("Seleziona un indice per rinominare:", indice_nomi, key='selected_index')

        logging.info(f"Indice selezionato per la rinominazione: {selected_index}")

        # Mostra i dettagli dell'indice selezionato
        selected_info = next((indice for indice in indici_info if indice["nome"] == selected_index), None)
        if selected_info:
            st.write(f"**Indice selezionato:** {selected_info['nome']}")
            st.write(f"**Descrizione:** {selected_info['descrizione']}")
            st.write("**Documenti:**")
            for doc in selected_info['documenti']:
                st.write(f"- {doc}")

        # Funzione per rinominare l'indice selezionato
        st.write("### Rinomina Indice")
        new_index_name = st.text_input("Inserisci un nuovo nome per l'indice:", key='new_index_name')
        if st.button("Rinomina Indice"):
            if new_index_name:
                if new_index_name in indice_nomi:
                    st.error("Esiste già un indice con questo nome. Scegli un altro nome.")
                    logging.warning(f"Tentativo di rinominare l'indice in un nome già esistente: {new_index_name}")
                else:
                    try:
                        # Rinomina la cartella dell'indice
                        old_path = os.path.join(faiss_index_folder, selected_index)
                        new_path = os.path.join(faiss_index_folder, new_index_name)
                        logging.info(f"Tentativo di rinominare la directory da {old_path} a {new_path}")
                        os.rename(old_path, new_path)
                        st.success(f"Indice '{selected_index}' rinominato in '{new_index_name}'.")
                        logging.info(f"Indice '{selected_index}' rinominato in '{new_index_name}' con successo.")
                        # Clear session state to force refresh
                        st.session_state.pop('selected_index', None)
                        st.session_state.pop('new_index_name', None)
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Errore durante la rinominazione: {e}")
                        logging.error(f"Errore durante la rinominazione dell'indice '{selected_index}': {e}")
            else:
                st.warning("Inserisci un nome valido per rinominare l'indice.")
                logging.warning("Tentativo di rinominare senza fornire un nuovo nome.")
    else:
        st.write("Nessun indice disponibile.")
        logging.info("Nessun indice disponibile per la visualizzazione o la rinominazione.")

if __name__ == "__main__":
    vedi_e_rinomina_db()
