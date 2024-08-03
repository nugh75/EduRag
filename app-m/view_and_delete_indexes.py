# view_and_delete_indexes.py

import os
import shutil
import streamlit as st
from utils import leggi_descrizioni_e_documenti, conferma_azione

def view_and_delete_indexes():
    # Percorso della cartella dove sono salvati gli indici FAISS
    faiss_index_folder = "db"

    # Controllo se la cartella degli indici esiste
    if not os.path.exists(faiss_index_folder):
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
        # Usa selectbox per selezionare un indice da visualizzare o cancellare
        indice_nomi = [indice['nome'] for indice in indici_info]
        selected_index = st.selectbox("Seleziona un indice per visualizzare o cancellare:", indice_nomi)

        # Mostra i dettagli dell'indice selezionato
        selected_info = next((indice for indice in indici_info if indice["nome"] == selected_index), None)
        if selected_info:
            st.write(f"**Indice selezionato:** {selected_info['nome']}")
            st.write(f"**Descrizione:** {selected_info['descrizione']}")
            st.write("**Documenti:**")
            for doc in selected_info['documenti']:
                st.write(f"- {doc}")

        # Bottone per cancellare l'indice selezionato
        if st.button("Cancella Indice"):
            if conferma_azione(f"Sei sicuro di voler cancellare l'indice '{selected_index}'?"):
                index_path = os.path.join(faiss_index_folder, selected_index)
                try:
                    shutil.rmtree(index_path)
                    st.success(f"Indice '{selected_index}' cancellato con successo.")
                    st.experimental_rerun()  # Aggiorna l'interfaccia per riflettere le modifiche
                except Exception as e:
                    st.error(f"Errore durante la cancellazione dell'indice '{selected_index}': {e}")
    else:
        st.write("Nessun indice disponibile.")

if __name__ == "__main__":
    view_and_delete_indexes()
