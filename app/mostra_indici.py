# mostra_indici.py

import os
import streamlit as st
from utils.utils import leggi_descrizioni_e_documenti

def mostra_indici_disponibili():
    # Percorso della cartella dove sono salvati gli indici FAISS
    faiss_index_folder = "db"

    # Controllo se la cartella degli indici esiste
    if not os.path.exists(faiss_index_folder):
        st.sidebar.error("La cartella degli indici non esiste. Creane uno prima di procedere.")
        return

    try:
        # Ottieni le informazioni sugli indici esistenti
        indici_info = leggi_descrizioni_e_documenti(faiss_index_folder)
    except Exception as e:
        st.sidebar.error("Errore durante la lettura degli indici.")
        return

    if not indici_info:
        st.sidebar.write("Nessun indice disponibile.")
        return

    # Elenco dei nomi degli indici
    indice_nomi = [indice["nome"] for indice in indici_info]

    # Aggiungi un menu a tendina per selezionare un indice
    selected_index_name = st.sidebar.selectbox(
        "Seleziona un indice:",
        indice_nomi
    )

    # Trova le informazioni dell'indice selezionato
    selected_index_info = next((indice for indice in indici_info if indice["nome"] == selected_index_name), None)

    # Mostra i dettagli dell'indice selezionato
    if selected_index_info:
       # st.sidebar.subheader(f"Dettagli per l'indice '{selected_index_name}':")
        st.sidebar.write("**Documenti:**")
        for doc in selected_index_info['documenti']:
            st.sidebar.write(f"- {doc}")

        # Variabile di stato per gestire la modalità modifica
        edit_mode_key = f"{selected_index_name}_edit_mode"
        if edit_mode_key not in st.session_state:
            st.session_state[edit_mode_key] = False

        # Mostra la descrizione attuale
        st.sidebar.write(f"**Descrizione:** {selected_index_info['descrizione']}")

        # Pulsante per attivare la modalità modifica
        if not st.session_state[edit_mode_key]:
            if st.sidebar.button("Modifica Descrizione"):
                st.session_state[edit_mode_key] = True

        # Modalità modifica attiva
        if st.session_state[edit_mode_key]:
            # Mostra l'attuale descrizione e consenti la modifica
            new_description = st.sidebar.text_area(
                "Modifica la descrizione dell'indice:",
                selected_index_info['descrizione'],
                key=f"new_description_{selected_index_name}"
            )

            # Pulsante per salvare la nuova descrizione
            if st.sidebar.button("Salva Descrizione"):
                # Aggiorna il file di descrizione
                try:
                    # Percorso del file di descrizione
                    description_file_path = os.path.join(faiss_index_folder, selected_index_name, "description.txt")

                    # Aggiorna la descrizione nel file
                    with open(description_file_path, "w") as desc_file:
                        desc_file.write(f"Descrizione dell'indice: {new_description}\n")
                        desc_file.write("Titoli dei documenti PDF:\n")
                        for doc in selected_index_info['documenti']:
                            desc_file.write(f"- {doc}\n")

                    # Mostra un messaggio di successo
                    st.sidebar.success("Descrizione aggiornata con successo.")
                    
                    # Disabilita la modalità modifica e rimuovi il box
                    st.session_state[edit_mode_key] = False

                    # Usare un trucco per forzare l'aggiornamento dell'interfaccia
                    st.experimental_set_query_params(update_time=os.urandom(16).hex())

                except Exception as e:
                    st.sidebar.error(f"Errore nell'aggiornamento della descrizione: {e}")
