import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import qrcode
from io import BytesIO
from PIL import Image

# Funzione per generare un codice basato sull'intervallo di 20 minuti corrente e un segreto
def genera_codice(ora_corrente, segreto):
    intervallo = ora_corrente.minute // 20
    hash_input = f"{ora_corrente.hour}-{intervallo}-{segreto}".encode()
    codice = hashlib.sha256(hash_input).hexdigest()[:6].upper()  # Prendi i primi 6 caratteri dell'hash
    return codice

# Funzione per creare un QR code
def crea_qr_code(codice):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(codice)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return img

def visualizza_codice_insegnante():
    st.header("Genera Codice Lezione")

    # Ottieni l'ora corrente
    ora_corrente = datetime.now()
    
    # Segreto conosciuto solo dal sistema
    segreto = "SegretoCondiviso"
    
    # Genera il codice della lezione basato sull'intervallo di 20 minuti corrente
    codice_lezione = genera_codice(ora_corrente, segreto)
    
    # Mostra il codice per l'insegnante da condividere con gli studenti
    st.write(f"Codice da condividere con gli studenti: {codice_lezione}")
    
    # Genera il QR code
    img = crea_qr_code(codice_lezione)
    
    # Converti l'immagine in un formato che Streamlit può visualizzare
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    st.image(buffer.getvalue())

    st.info("Condividi questo QR code con gli studenti per l'ora corrente. Scansionando il QR code, gli studenti potranno ottenere il codice direttamente sul loro dispositivo.")

def main():
    visualizza_codice_insegnante()

if __name__ == "__main__":
    main()
