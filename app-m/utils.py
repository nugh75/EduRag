# utils.py

import streamlit as st
import os

def leggi_descrizioni_e_documenti(db_path):
    """Legge le descrizioni e i documenti da ciascun indice nella cartella db."""
    indici_info = []
    try:
        for subfolder in sorted(os.listdir(db_path)):  # Ordina alfabeticamente
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
