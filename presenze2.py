import streamlit as st
import pandas as pd
from datetime import datetime

# File CSV per il salvataggio dei dati
PRESENZE_CSV = "presenze.csv"
USERS_CSV = "users.csv"

import hashlib
from datetime import datetime

# Funzione per generare un codice basato sull'intervallo di 20 minuti corrente e un segreto
def genera_codice(ora_corrente, segreto):
    intervallo = ora_corrente.minute // 20
    hash_input = f"{ora_corrente.hour}-{intervallo}-{segreto}".encode()
    codice = hashlib.sha256(hash_input).hexdigest()[:6].upper()  # Prendi i primi 6 caratteri dell'hash
    return codice

def load_data():
    try:
        st.session_state.presenze_db = pd.read_csv(PRESENZE_CSV)
        
        # Verifica se la colonna 'codice_lezione' esiste, altrimenti aggiungila
        if 'codice_lezione' not in st.session_state.presenze_db.columns:
            st.session_state.presenze_db['codice_lezione'] = None
            
    except FileNotFoundError:
        st.session_state.presenze_db = pd.DataFrame(columns=[
            'lezione', 'tipo_lezione', 'nome', 'cognome', 'ora', 'data_lezione', 'ora_inizio', 'codice_lezione'
        ])
    
    try:
        st.session_state.users_db = pd.read_csv(USERS_CSV)
    except FileNotFoundError:
        st.session_state.users_db = pd.DataFrame(columns=['nome', 'cognome', 'email', 'password', 'ruolo', 'confermato'])


# Funzione per caricare i dati dal file CSV
def load_data():
    try:
        st.session_state.presenze_db = pd.read_csv(PRESENZE_CSV)
    except FileNotFoundError:
        st.session_state.presenze_db = pd.DataFrame(columns=['lezione', 'tipo_lezione', 'nome', 'cognome', 'data_ora'])
    
    try:
        st.session_state.users_db = pd.read_csv(USERS_CSV)
    except FileNotFoundError:
        st.session_state.users_db = pd.DataFrame(columns=['nome', 'cognome', 'email', 'password', 'ruolo', 'confermato'])

# Funzione per salvare i dati nei file CSV
def save_data():
    st.session_state.presenze_db.to_csv(PRESENZE_CSV, index=False)
    st.session_state.users_db.to_csv(USERS_CSV, index=False)

# Funzione per accedere all'account
def login():
    st.sidebar.title("Login")
    email = st.sidebar.text_input("Email Istituzionale:")
    password = st.sidebar.text_input("Password:", type="password")
    
    if st.sidebar.button("Accedi"):
        user = st.session_state.users_db[(st.session_state.users_db['email'] == email) & (st.session_state.users_db['password'] == password)]
        if not user.empty:
            if user.iloc[0]['confermato']:
                st.session_state.logged_in_user = user.iloc[0]
                st.sidebar.success(f"Accesso effettuato come {user.iloc[0]['nome']} {user.iloc[0].get('cognome', '')}")
            
        else:
            st.sidebar.error("Credenziali non valide.")


def visualizza_tutti_studenti():
    st.header("Percentuali di Tutti gli Studenti")
    
    # Recupero dei dati
    filtered_data = st.session_state.presenze_db.copy()
    
    # Filtro per tipo di lezione
    tipo_lezione = st.selectbox("Filtra per tipo di lezione", ["Tutti", "Disciplinare", "Trasversale"])
    if tipo_lezione != "Tutti":
        filtered_data = filtered_data[filtered_data['tipo_lezione'] == tipo_lezione]
    
    # Filtro per data
    date_filter = st.date_input("Filtra per data", [])
    if date_filter:
        filtered_data = filtered_data[pd.to_datetime(filtered_data['data_ora']).dt.date == date_filter]
    
    # Assicuriamoci che i valori nella colonna 'ora' siano numerici
    filtered_data['ora'] = pd.to_numeric(filtered_data['ora'], errors='coerce').fillna(0)
    
    # Calcolo delle percentuali per ciascun studente
    studenti = filtered_data[['nome', 'cognome']].drop_duplicates()
    studenti['Percentuale Disciplinare'] = 0
    studenti['Percentuale Trasversale'] = 0
    studenti['Percentuale Ore Totali'] = 0

    for i, row in studenti.iterrows():
        nome, cognome = row['nome'], row['cognome']
        student_data = filtered_data[(filtered_data['nome'] == nome) & (filtered_data['cognome'] == cognome)]
        
        total_disciplinare = student_data[student_data['tipo_lezione'] == 'Disciplinare']['ora'].sum()
        total_trasversale = student_data[student_data['tipo_lezione'] == 'Trasversale']['ora'].sum()
        total_ore = total_disciplinare + total_trasversale
        
        perc_disciplinare = (total_disciplinare / 96) * 100 if total_disciplinare > 0 else 0
        perc_trasversale = (total_trasversale / 85) * 100 if total_trasversale > 0 else 0
        perc_totale_ore = (total_ore / (96 + 85)) * 100 if total_ore > 0 else 0
        
        studenti.at[i, 'Percentuale Disciplinare'] = perc_disciplinare
        studenti.at[i, 'Percentuale Trasversale'] = perc_trasversale
        studenti.at[i, 'Percentuale Ore Totali'] = perc_totale_ore
    
    # Visualizzazione della tabella con le percentuali per ogni studente
    st.dataframe(studenti)


def visualizza_lezioni():
    st.header("Lezioni Registrate")
    user = st.session_state.logged_in_user
    
    if user['ruolo'] == "Insegnante":
        # Dropdown per selezionare uno studente
        all_students = st.session_state.presenze_db[['nome', 'cognome']].drop_duplicates()
        all_students['nome_completo'] = all_students['nome'] + " " + all_students['cognome']
        
        selected_student = st.selectbox("Seleziona uno studente", all_students['nome_completo'])
        
        # Visualizzazione di un singolo studente
        nome, cognome = selected_student.split(" ")
        filtered_data = st.session_state.presenze_db[(st.session_state.presenze_db['nome'] == nome) & 
                                                     (st.session_state.presenze_db['cognome'] == cognome)]
        
        # Filtro per tipo di lezione
        tipo_lezione = st.selectbox("Filtra per tipo di lezione", ["Tutti", "Disciplinare", "Trasversale"])
        if tipo_lezione != "Tutti":
            filtered_data = filtered_data[filtered_data['tipo_lezione'] == tipo_lezione]

        # Filtro per data
        date_filter = st.date_input("Filtra per data", [])
        if date_filter:
            filtered_data = filtered_data[pd.to_datetime(filtered_data['data_ora']).dt.date == date_filter]

        # Assicuriamoci che i valori nella colonna 'ora' siano numerici
        filtered_data['ora'] = pd.to_numeric(filtered_data['ora'], errors='coerce').fillna(0)
        
        # Calcolo delle ore disciplinari e trasversali per lo studente selezionato
        total_disciplinare = filtered_data[filtered_data['tipo_lezione'] == 'Disciplinare']['ora'].sum()
        total_trasversale = filtered_data[filtered_data['tipo_lezione'] == 'Trasversale']['ora'].sum()
        total_ore = total_disciplinare + total_trasversale
        
        # Calcolo delle percentuali relative al singolo studente rispetto alle ore previste
        perc_disciplinare = (total_disciplinare / 96) * 100 if total_disciplinare > 0 else 0
        perc_trasversale = (total_trasversale / 85) * 100 if total_trasversale > 0 else 0
        perc_totale_ore = (total_ore / (96 + 85)) * 100 if total_ore > 0 else 0

        # Visualizzazione delle percentuali sopra la tabella su una riga
        col1, col2, col3 = st.columns(3)
        col1.metric("Percentuale Disciplinare", f"{perc_disciplinare:.2f}%")
        col2.metric("Percentuale Trasversale", f"{perc_trasversale:.2f}%")
        col3.metric("Percentuale Ore Totali", f"{perc_totale_ore:.2f}%")
        
        # Visualizzazione dei dati filtrati
        st.dataframe(filtered_data)
    
    else:
        # Se l'utente è uno studente, visualizza solo le sue presenze
        filtered_data = st.session_state.presenze_db[st.session_state.presenze_db['nome'] == user['nome']]
        
        # Filtro per tipo di lezione
        tipo_lezione = st.selectbox("Filtra per tipo di lezione", ["Tutti", "Disciplinare", "Trasversale"])
        if tipo_lezione != "Tutti":
            filtered_data = filtered_data[filtered_data['tipo_lezione'] == tipo_lezione]

        # Filtro per data
        date_filter = st.date_input("Filtra per data", [])
        if date_filter:
            filtered_data = filtered_data[pd.to_datetime(filtered_data['data_ora']).dt.date == date_filter]
        
        # Assicuriamoci che i valori nella colonna 'ora' siano numerici
        filtered_data['ora'] = pd.to_numeric(filtered_data['ora'], errors='coerce').fillna(0)
        
        # Calcolo delle ore disciplinari e trasversali per lo studente loggato
        total_disciplinare = filtered_data[filtered_data['tipo_lezione'] == 'Disciplinare']['ora'].sum()
        total_trasversale = filtered_data[filtered_data['tipo_lezione'] == 'Trasversale']['ora'].sum()
        total_ore = total_disciplinare + total_trasversale
        
        # Calcolo delle percentuali relative al singolo studente rispetto alle ore previste
        perc_disciplinare = (total_disciplinare / 96) * 100 if total_disciplinare > 0 else 0
        perc_trasversale = (total_trasversale / 85) * 100 if total_trasversale > 0 else 0
        perc_totale_ore = (total_ore / (96 + 85)) * 100 if total_ore > 0 else 0

        # Visualizzazione delle percentuali sopra la tabella su una riga
        col1, col2, col3 = st.columns(3)
        col1.metric("Percentuale Disciplinare", f"{perc_disciplinare:.2f}%")
        col2.metric("Percentuale Trasversale", f"{perc_trasversale:.2f}%")
        col3.metric("Percentuale Ore Totali", f"{perc_totale_ore:.2f}%")
        
        # Visualizzazione dei dati filtrati
        st.dataframe(filtered_data)

def inserisci_presenze():
    st.header("Inserisci Presenze")

    # Carica l'elenco degli studenti
    all_students = st.session_state.presenze_db[['nome', 'cognome']].drop_duplicates()
    all_students['nome_completo'] = all_students['nome'] + " " + all_students['cognome']

    # Seleziona uno o più studenti
    selected_students = st.multiselect("Seleziona gli studenti", all_students['nome_completo'].tolist())

    # Inserisci i dettagli della lezione
    lezione = st.text_input("Lezione:")
    tipo_lezione = st.selectbox("Tipo di Lezione:", ["Disciplinare", "Trasversale"])
    ora = st.number_input("Ore di lezione", min_value=1, max_value=10, value=1, step=1)
    
    # Inserimento della data e ora separatamente
    data_lezione = st.date_input("Data della lezione")
    ora_inizio = st.time_input("Ora di inizio della lezione")

    if st.button("Registra Presenza"):
        for student in selected_students:
            nome, cognome = student.split(" ")
            new_row = pd.DataFrame({
                'lezione': [lezione],
                'tipo_lezione': [tipo_lezione],
                'nome': [nome],
                'cognome': [cognome],
                'ora': [ora],
                'data_lezione': [data_lezione.strftime("%d/%m/%Y")],  # Formato data italiana
                'ora_inizio': [ora_inizio.strftime("%H:%M")],  # Formato ora HH:MM
            })
            st.session_state.presenze_db = pd.concat([st.session_state.presenze_db, new_row], ignore_index=True)
        save_data()
        st.success("Presenza registrata con successo per gli studenti selezionati.")

def rimuovi_presenze():
    st.header("Rimuovi Presenze")

    # Visualizzazione delle lezioni registrate con filtraggio solo per data e lezione
    lezioni = st.session_state.presenze_db[['lezione', 'data_lezione']].drop_duplicates().copy()
    lezioni['descrizione'] = lezioni.apply(lambda row: f"{row['data_lezione']} - {row['lezione']}", axis=1)
    
    # Seleziona la lezione e la data da cui rimuovere la presenza
    selected_lesson = st.selectbox("Seleziona la lezione e la data", lezioni['descrizione'].unique())
    
    # Filtra le presenze in base alla lezione e alla data selezionata
    data_lezione, lezione = selected_lesson.split(" - ")
    studenti_in_lezione = st.session_state.presenze_db[
        (st.session_state.presenze_db['data_lezione'] == data_lezione) &
        (st.session_state.presenze_db['lezione'] == lezione)
    ]

    # Seleziona gli studenti da rimuovere
    selected_students_to_remove = st.multiselect(
        "Seleziona gli studenti da rimuovere",
        studenti_in_lezione['nome'] + " " + studenti_in_lezione['cognome']
    )
    
    if st.button("Rimuovi Presenza"):
        for student in selected_students_to_remove:
            nome, cognome = student.split(" ")
            st.session_state.presenze_db = st.session_state.presenze_db.drop(
                st.session_state.presenze_db[
                    (st.session_state.presenze_db['nome'] == nome) & 
                    (st.session_state.presenze_db['cognome'] == cognome) & 
                    (st.session_state.presenze_db['lezione'] == lezione) & 
                    (st.session_state.presenze_db['data_lezione'] == data_lezione)
                ].index
            )
        save_data()
        st.success("Presenza rimossa con successo per gli studenti selezionati.")


        
def visualizza_database_completo():
    st.header("Visualizza Database Completo")

    # Caricamento del database delle presenze
    presenze_db = st.session_state.presenze_db.copy()

    # Filtraggio per nome lezione
    lezioni = presenze_db['lezione'].unique().tolist()
    selected_lezione = st.selectbox("Filtra per Lezione", ["Tutte"] + lezioni)
    if selected_lezione != "Tutte":
        presenze_db = presenze_db[presenze_db['lezione'] == selected_lezione]

    # Filtraggio per intervallo di date (facoltativo)
    start_date = st.date_input("Data di inizio", value=None)
    end_date = st.date_input("Data di fine", value=None)

    if start_date and end_date:
        # Conversione delle date in stringhe nel formato italiano
        start_date_str = start_date.strftime("%d/%m/%Y")
        end_date_str = end_date.strftime("%d/%m/%Y")
        
        # Filtraggio per l'intervallo di date
        presenze_db['data_lezione'] = pd.to_datetime(presenze_db['data_lezione'], format="%d/%m/%Y")
        presenze_db = presenze_db[(presenze_db['data_lezione'] >= pd.to_datetime(start_date_str, format="%d/%m/%Y")) &
                                  (presenze_db['data_lezione'] <= pd.to_datetime(end_date_str, format="%d/%m/%Y"))]

    # Filtraggio per nome studente
    studenti = presenze_db[['nome', 'cognome']].drop_duplicates()
    studenti['nome_completo'] = studenti['nome'] + " " + studenti['cognome']
    selected_students = st.multiselect("Filtra per Studenti", studenti['nome_completo'].tolist())
    
    if selected_students:
        # Filtro per studenti concatenando nome e cognome
        presenze_db['nome_completo'] = presenze_db['nome'] + " " + presenze_db['cognome']
        presenze_db = presenze_db[presenze_db['nome_completo'].isin(selected_students)]

    # Visualizzazione del database filtrato
    st.dataframe(presenze_db)


def inserisci_lezione_studente():
    st.header("Inserisci Lezione")

    # Recupera i dettagli dello studente loggato
    user = st.session_state['logged_in_user']
    nome = user['nome']
    cognome = user['cognome']

    # Segreto condiviso (deve essere lo stesso usato nello script di generazione del codice)
    segreto = "SegretoCondiviso"
    
    # Ottieni l'ora corrente
    ora_corrente = datetime.now()
    
    # Genera il codice della lezione basato sull'intervallo di 20 minuti corrente
    codice_lezione = genera_codice(ora_corrente, segreto)
    
    # Inserisci il codice della lezione
    codice_inserito = st.text_input("Inserisci il codice della lezione:")

    # Verifica se il codice è già stato utilizzato dallo studente
    if codice_inserito:
        codice_usato = st.session_state.presenze_db[
            (st.session_state.presenze_db['nome'] == nome) & 
            (st.session_state.presenze_db['cognome'] == cognome) & 
            (st.session_state.presenze_db['codice_lezione'] == codice_inserito)
        ]

        if not codice_usato.empty:
            st.error("Hai già registrato una lezione con questo codice.")
            return
        
        if codice_inserito == codice_lezione:
            st.success("Codice corretto. Presenza registrata con successo!")
            # Procedi con la registrazione della presenza
            lezione = st.text_input("Lezione:")
            tipo_lezione = st.selectbox("Tipo di Lezione:", ["Disciplinare", "Trasversale"])
            ora = st.number_input("Ore di lezione", min_value=1, max_value=10, value=1, step=1)
            data_lezione = st.date_input("Data della lezione")
            ora_inizio = st.time_input("Ora di inizio della lezione")

        if st.button("Registra Presenza"):
            new_row = pd.DataFrame({
            'lezione': [lezione],
            'tipo_lezione': [tipo_lezione],
            'nome': [nome],
            'cognome': [cognome],
            'ora': [ora],
            'data_lezione': [data_lezione.strftime("%d/%m/%Y")],  # Formato data italiana
            'ora_inizio': [ora_inizio.strftime("%H:%M")],  # Formato ora HH:MM
            'codice_lezione': [codice_inserito]  # Aggiungi il codice della lezione al database
                })
            st.session_state.presenze_db = pd.concat([st.session_state.presenze_db, new_row], ignore_index=True)
            save_data()
            st.success("Presenza registrata con successo.")
        else:
            st.error("Codice errato. Controlla il codice e riprova.")

# Funzione per salvare i dati (assumendo che tu stia usando un CSV come database)
def save_data():
    st.session_state.presenze_db.to_csv("presenze.csv", index=False)



def visualizza_lezioni_studente():
    st.header("Lezioni Registrate")
    
    # Filtra le lezioni solo per lo studente loggato
    user = st.session_state['logged_in_user']
    filtered_data = st.session_state.presenze_db[(st.session_state.presenze_db['nome'] == user['nome']) & 
                                                 (st.session_state.presenze_db['cognome'] == user['cognome'])]
    
    # Mostra le lezioni dello studente
    st.dataframe(filtered_data)

def main():
    st.title("Gestione Presenze Studenti")
    load_data()

    if 'logged_in_user' not in st.session_state:
        login()
    else:
        user = st.session_state['logged_in_user']
        user_role = user.get('ruolo', 'Studente')

        if user_role == "Insegnante":
            menu = st.sidebar.selectbox("Menu", ["Visualizza Lezioni", "Visualizza Tutti gli Studenti", "Visualizza Database Completo", "Inserisci Presenze", "Genera Codice Lezione", "Rimuovi Presenze", "Logout"])
            if menu == "Inserisci Presenze":
                inserisci_presenze()
            elif menu == "Genera Codice Lezione":
                visualizza_codice_insegnante()
            elif menu == "Rimuovi Presenze":
                rimuovi_presenze()
            elif menu == "Visualizza Lezioni":
                visualizza_lezioni()
            elif menu == "Visualizza Tutti gli Studenti":
                visualizza_tutti_studenti()
            elif menu == "Visualizza Database Completo":
                visualizza_database_completo()
            elif menu == "Logout":
                logout()
        elif user_role == "Studente":
            menu = st.sidebar.selectbox("Menu", ["Visualizza Lezioni", "Inserisci Lezione", "Logout"])
            if menu == "Visualizza Lezioni":
                visualizza_lezioni_studente()
            elif menu == "Inserisci Lezione":
                inserisci_lezione_studente()
            elif menu == "Logout":
                logout()


def logout():
    st.session_state.clear()  # Clear the session state
    st.sidebar.success("Logout effettuato con successo.")
    st.rerun()  # Rerun the script to simulate a "refresh"

if __name__ == "__main__":
    main()