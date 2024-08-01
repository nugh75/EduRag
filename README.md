# Edubot

Edubot è un assistente virtuale progettato per supportare studenti e docenti nella gestione e nell'analisi di documenti PDF nei corsi online. Utilizza tecnologie avanzate di elaborazione del linguaggio naturale e indicizzazione per fornire risposte pertinenti e dettagliate a domande specifiche sui documenti.

## Funzionalità

- **Indicizzazione dei Documenti PDF**: Crea e gestisci indici dai tuoi documenti PDF, facilitando la ricerca e il recupero delle informazioni.
- **Ricerca Rapida e Precisa**: Analizza i documenti PDF per trovare le informazioni rilevanti e restituisce passaggi specifici per approfondimenti successivi.
- **Interfaccia Intuitiva**: Interagisci con Edubot attraverso una semplice interfaccia web, ricevendo risposte chiare e facili da capire.
- **Gestione dei Chunk**: Personalizza la dimensione dei segmenti di testo (chunk) analizzati per ottimizzare il recupero delle informazioni in base alle tue esigenze.
- **Storico delle Interazioni**: Accedi facilmente alle domande e risposte precedenti per un apprendimento continuo.

## Tecnologie Utilizzate

- **FAISS (Facebook AI Similarity Search)**: Utilizzato per creare indici dai documenti PDF e migliorare l'efficienza delle ricerche.
- **Retrieval-Augmented Generation (RAG)**: Combina il recupero delle informazioni con la generazione di testo per fornire risposte dettagliate e pertinenti.
- **Embedding**: Rappresenta il testo sotto forma di numeri per comprendere e confrontare i contenuti.
- **Streamlit**: Fornisce un'interfaccia utente semplice e interattiva per l'interazione con Edubot.

## Requisiti di Sistema

- **Python**: Assicurati di avere Python 3.10 installato sul tuo sistema.

## Installazione

Per eseguire Edubot localmente, segui questi passaggi:

### 1. Clona il Repository

Apri il terminale e clona il repository del progetto:

```bash
git clone https://github.com/tuo-utente/edubot.git
cd edubot
```
### 2. Crea un Ambiente Virtuale
Assicurati di avere Python 3.10 installato sul tuo sistema. Puoi verificare la versione di Python con il seguente comando:

```bash
python3 --version
```

Crea un ambiente virtuale utilizzando venv:

```bash
python3.10 -m venv myenv
```

Attiva l'ambiente virtuale:

Su macOS o Linux:

```bash
source myenv/bin/activate
```

Su Windows:

```bash
myenv\\Scripts\\activate

```
###3. Installa le Dipendenze
Installa i pacchetti richiesti utilizzando il file requirements.txt:

```bash
pip install -r requirements.txt
```


Assicurati che il file requirements.txt contenga tutti i pacchetti necessari per eseguire Edubot. Puoi aggiungere o rimuovere pacchetti in base alle esigenze specifiche del tuo progetto.

###4. Esegui l'Applicazione
Esegui l'applicazione Streamlit:

```bash
streamlit run main.py
```
###Utilizzo
Dopo aver avviato l'applicazione, utilizza la barra di navigazione in alto per esplorare le diverse funzionalità:

Home: Introduzione e descrizione delle funzionalità di Edubot.
Elaborazione PDF: Carica e gestisci gli indici PDF per facilitare il recupero delle informazioni.
Query: Poni domande specifiche utilizzando i documenti indicizzati.
Contribuire

Contribuzioni e miglioramenti sono i benvenuti! Se vuoi contribuire a Edubot, segui questi passaggi:

Fai un fork del repository.
Crea un nuovo branch per la tua feature o correzione: git checkout -b feature/nome-feature.
Fai commit delle tue modifiche: git commit -m 'Aggiungi una nuova feature'.
Fai push al branch: git push origin feature/nome-feature.
Invia una pull request.

##Disclaimer
Le informazioni fornite da Edubot devono essere verificate. I modelli di linguaggio possono dare risposte non sempre accurate. È consigliabile controllare le fonti.

##Licenza
Questo progetto è distribuito sotto la licenza GPL3. Vedi il file LICENSE per i dettagli.
