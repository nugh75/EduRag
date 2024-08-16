# Usa un'immagine base di Python
FROM python:3.10.12

# Espone la porta 8501 (quella usata da Streamlit)
EXPOSE 8501

# Crea la directory di lavoro /app
RUN mkdir -p /app

# Imposta la directory di lavoro come /app
WORKDIR /app

# Copia il file requirements.txt nella directory di lavoro
COPY requirements.txt .

# Installa le dipendenze elencate in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice dell'applicazione nella directory di lavoro
COPY . .

# Definisce il comando di avvio per l'app Streamlit
ENTRYPOINT ["streamlit", "run", "app/main.py"]

