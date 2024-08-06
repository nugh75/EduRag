# utils.py

import os
import streamlit as st

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
                        descrizione = ""
                        documenti = set()  # Usa un set per evitare duplicati
                        for line in lines:
                            if line.startswith("Descrizione dell'indice:"):
                                descrizione = line.replace("Descrizione dell'indice: ", "").strip()
                            elif line.startswith("-"):
                                documenti.add(line.strip("- ").strip())
                    indici_info.append({
                        "nome": subfolder,
                        "descrizione": descrizione,
                        "documenti": sorted(documenti)  # Ordina i documenti
                    })
    except Exception as e:
        st.error(f"Errore nella lettura degli indici: {e}")
    return indici_info

def conferma_azione(messaggio):
    """Mostra un messaggio di conferma e ritorna True se l'utente conferma."""
    return st.confirm(messaggio)
