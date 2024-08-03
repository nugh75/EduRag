# view_and_delete_indexes.py
import os
import shutil
import streamlit as st

def view_and_delete_indexes():
    # Percorso della cartella dove sono salvati gli indici FAISS
    faiss_index_folder = "db"

    # Controllo se la cartella degli indici esiste
    if not os.path.exists(faiss_index_folder):
        st.error("La cartella degli indici non esiste. Crea prima un indice.")
        return

    # Ottieni la lista degli indici
    indexes = os.listdir(faiss_index_folder)

    # Mostra gli indici disponibili
    st.header("Indici Disponibili")
    if indexes:
        selected_index = st.selectbox("Seleziona un indice per visualizzare o cancellare:", indexes)

        # Mostra i dettagli dell'indice selezionato
        st.write(f"Indice selezionato: {selected_index}")

        # Bottone per cancellare l'indice selezionato
        if st.button("Cancella Indice"):
            index_path = os.path.join(faiss_index_folder, selected_index)
            try:
                shutil.rmtree(index_path)
                st.success(f"Indice '{selected_index}' cancellato con successo.")
            except Exception as e:
                st.error(f"Errore durante la cancellazione dell'indice '{selected_index}': {e}")
    else:
        st.write("Nessun indice disponibile.")
        
if __name__ == "__main__":
    view_and_delete_indexes()
