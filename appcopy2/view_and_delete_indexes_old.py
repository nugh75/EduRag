# view_and_delete_indexes.py
import os
import shutil
import streamlit as st

def leggi_descrizioni_e_documenti(db_path):
    """Legge le descrizioni e i documenti da ciascun indice nella cartella db."""
    indici_info = []
    try:
        # Ordina i sotto-cartelle alfabeticamente
        for subfolder in sorted(os.listdir(db_path)):
            subfolder_path = os.path.join(db_path, subfolder)
            if os.path.isdir(subfolder_path):
                description_file = os.path.join(subfolder_path, "description.txt")
                if os.path.exists(description_file):
                    with open(description_file, "r", encoding="utf-8") as file:
                        lines = file.readlines()
                        # Processa il file per ottenere descrizione e documenti
                        descrizione = ""
                        documenti = []
                        for line in lines:
                            if line.startswith("Descrizione dell'indice:"):
                                descrizione = line.replace("Descrizione dell'indice: ", "").strip()
                            elif line.startswith("-"):
                                documenti.append(line.strip("- ").strip())
                    indici_info.append({
                        "nome": subfolder,
                        "descrizione": descrizione,
                        "documenti": documenti
                    })
    except Exception as e:
        st.error(f"Errore nella lettura degli indici: {e}")
    return indici_info

def view_and_delete_indexes():
    # Percorso della cartella dove sono salvati gli indici FAISS
    faiss_index_folder = "db"

    # Controllo se la cartella degli indici esiste
    if not os.path.exists(faiss_index_folder):
        st.error("La cartella degli indici non esiste. Crea prima un indice.")
        return

    # Ottieni la lista degli indici
    indexes = sorted(os.listdir(faiss_index_folder))

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
                # Aggiorna la lista di indici dopo la cancellazione
                indexes.remove(selected_index)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Errore durante la cancellazione dell'indice '{selected_index}': {e}")
    else:
        st.write("Nessun indice disponibile.")

    # Visualizzazione degli indici, delle descrizioni e dei documenti nella barra laterale
    st.sidebar.header("Indici Disponibili")
    indici_info = leggi_descrizioni_e_documenti(faiss_index_folder)

    for indice in indici_info:
        with st.sidebar.expander(indice["nome"], expanded=False):
            st.write(f"**Descrizione:** {indice['descrizione']}")
            st.write("**Documenti:**")
            for doc in indice["documenti"]:
                st.write(f"- {doc}")

if __name__ == "__main__":
    view_and_delete_indexes()
