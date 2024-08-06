import os
import shutil
import logging
import streamlit as st
from utils import leggi_descrizioni_e_documenti

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def vedi_e_gestisci_db():
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
        # Usa selectbox per selezionare un indice da gestire
        indice_nomi = [indice['nome'] for indice in indici_info]
        selected_index = st.selectbox("Seleziona un indice per gestire:", indice_nomi, key='selected_index')

        logging.info(f"Indice selezionato: {selected_index}")

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
                        # Trigger page refresh
                        try:
                            st.experimental_rerun()
                        except:
                            st.write('<script>window.location.reload();</script>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Errore durante la rinominazione: {e}")
                        logging.error(f"Errore durante la rinominazione dell'indice '{selected_index}': {e}")
            else:
                st.warning("Inserisci un nome valido per rinominare l'indice.")
                logging.warning("Tentativo di rinominare senza fornire un nuovo nome.")

        # Funzione per cancellare l'indice selezionato
        st.write("### Cancella Indice")
        if st.checkbox(f"Conferma la cancellazione dell'indice '{selected_index}'"):
            if st.button("Cancella Indice"):
                index_path = os.path.join(faiss_index_folder, selected_index)
                logging.info(f"Tentativo di cancellazione dell'indice: {selected_index} nel percorso {index_path}")
                if os.path.exists(index_path):
                    try:
                        logging.info(f"Sto per cancellare la directory: {index_path}")
                        shutil.rmtree(index_path)
                        logging.info(f"shutil.rmtree eseguito per: {index_path}")
                        if not os.path.exists(index_path):  # Verifica che la directory sia stata effettivamente rimossa
                            st.success(f"Indice '{selected_index}' cancellato con successo.")
                            logging.info(f"Indice '{selected_index}' cancellato con successo.")
                            # Trigger page refresh
                            try:
                                st.experimental_rerun()
                            except:
                                st.write('<script>window.location.reload();</script>', unsafe_allow_html=True)
                        else:
                            st.error(f"Non è stato possibile cancellare l'indice '{selected_index}'.")
                            logging.error(f"Non è stato possibile cancellare l'indice '{selected_index}'. La cartella esiste ancora.")
                    except Exception as e:
                        st.error(f"Errore durante la cancellazione dell'indice '{selected_index}': {e}")
                        logging.error(f"Errore durante la cancellazione dell'indice '{selected_index}': {e}")
                else:
                    st.warning(f"L'indice '{selected_index}' non esiste o è già stato cancellato.")
                    logging.warning(f"Tentativo di cancellazione di un indice inesistente: {selected_index}")
    else:
        st.write("Nessun indice disponibile.")
        logging.info("Nessun indice disponibile per la visualizzazione o la rinominazione.")

if __name__ == "__main__":
    vedi_e_gestisci_db()
