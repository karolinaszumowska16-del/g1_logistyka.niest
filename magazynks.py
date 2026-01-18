import streamlit as st
import sqlite3
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Zarządzanie Produktami", layout="wide")

# Funkcja łącząca z bazą danych
def get_connection():
    conn = sqlite3.connect('magazyn.db')
    return conn

# Inicjalizacja bazy danych (tworzenie tabel zgodnie ze schematem)
def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Tworzenie tabeli kategoria
    c.execute('''
        CREATE TABLE IF NOT EXISTS kategoria (
            id INTEGER PRIMARY KEY,
            nazwa TEXT NOT NULL,
            opis TEXT
        )
    ''')
    
    # Tworzenie tabeli produkty
    c.execute('''
        CREATE TABLE IF NOT EXISTS produkty (
            id INTEGER PRIMARY KEY,
            nazwa TEXT NOT NULL,
            liczba INTEGER,
            cena REAL,
            kategoria_id INTEGER,
            FOREIGN KEY (kategoria_id) REFERENCES kategoria (id)
        )
    ''')
    
    # Dodanie przykładowych danych, jeśli tabele są puste
    c.execute("SELECT COUNT(*) FROM kategoria")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO kategoria VALUES (1, 'Elektronika', 'Sprzęt RTV i AGD')")
        c.execute("INSERT INTO kategoria VALUES (2, 'Biuro', 'Artykuły biurowe')")
        c.execute("INSERT INTO produkty VALUES (1, 'Laptop', 10, 3500.00, 1)")
        c.execute("INSERT INTO produkty VALUES (2, 'Myszka', 50, 120.00, 1)")
        c.execute("INSERT INTO produkty VALUES (3, 'Długopis', 200, 2.50, 2)")
    
    conn.commit()
    conn.close()

init_db()

# INTERFEJS STREAMLIT
st.title("📦 System Zarządzania Produktami")

# Pobieranie danych do wyświetlenia
conn = get_connection()
query = '''
    SELECT 
        p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria
    FROM produkty p
    JOIN kategoria k ON p.kategoria_id = k.id
'''
df = pd.read_sql_query(query, conn)
conn.close()

# Wyświetlanie danych
st.subheader("Lista produktów w bazie")
st.dataframe(df, use_container_width=True)

# Statystyki
col1, col2 = st.columns(2)
with col1:
    st.metric("Łączna liczba produktów", len(df))
with col2:
    st.metric("Wartość magazynu", f"{ (df['liczba'] * df['cena']).sum() :.2 f} PLN")
