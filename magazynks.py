Aby Twoja aplikacja na Streamlit zawierała już gotowe dane zaraz po uruchomieniu, musimy zmodyfikować funkcję inicjalizującą bazę danych (init_db).

Poniżej znajduje się kod, który możesz wkleić do pliku app.py. Dodałem w nim sekcję "Dane początkowe", gdzie wpisałem przykładowe produkty. Możesz je dowolnie edytować w kodzie przed wysłaniem na GitHub.

Zaktualizowany kod app.py z gotowymi danymi:
Python
import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Magazyn z danymi", layout="wide")

def get_connection():
    return sqlite3.connect('magazyn.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tworzenie tabel
    c.execute('''CREATE TABLE IF NOT EXISTS kategoria 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT, opis TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produkty 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT, liczba INTEGER, 
                  cena REAL, kategoria_id INTEGER, 
                  FOREIGN KEY(kategoria_id) REFERENCES kategoria(id))''')
    
    # 2. Sprawdzenie czy baza jest pusta i dodanie Twoich danych
    c.execute("SELECT COUNT(*) FROM kategoria")
    if c.fetchone()[0] == 0:
        # --- TUTAJ MOŻESZ WPISAĆ SWOJE KATEGORIE ---
        kategorie = [
            (1, 'Elektronika', 'Urządzenia elektroniczne'),
            (2, 'Meble', 'Wyposażenie wnętrz')
        ]
        c.executemany("INSERT INTO kategoria (id, nazwa, opis) VALUES (?, ?, ?)", kategorie)
        
        # --- TUTAJ MOŻESZ WPISAĆ SWOJE PRODUKTY ---
        produkty = [
            ('Laptop Pro', 5, 4500.00, 1),
            ('Smartfon X', 12, 2999.99, 1),
            ('Biurko Loft', 3, 850.00, 2),
            ('Krzesło Biurowe', 10, 450.00, 2)
        ]
        c.executemany("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)", produkty)
        
    conn.commit()
    conn.close()

init_db()

# --- INTERFEJS ---
st.title("📦 Aplikacja Magazynowa z danymi")

tab1, tab2, tab3 = st.tabs(["📋 Lista produktów", "➕ Dodaj Nowy", "📂 Kategorie"])

with tab1:
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
        FROM produkty p JOIN kategoria k ON p.kategoria_id = k.id
    ''', conn)
    st.dataframe(df, use_container_width=True)
    
    # Funkcja usuwania
    st.divider()
    id_do_usuniecia = st.number_input("Wpisz ID do usunięcia", min_value=1, step=1)
    if st.button("Usuń produkt"):
        c = conn.cursor()
        c.execute("DELETE FROM produkty WHERE id = ?", (id_do_usuniecia,))
        conn.commit()
        st.rerun()
    conn.close()

with tab2:
    # Formularz dodawania (jak w poprzednim kodzie)
    st.write("Tutaj możesz dodać kolejne produkty do swojej listy.")
    # ... (reszta kodu formularza z poprzedniej wiadomości)

with tab3:
    conn = get_connection()
    df_k = pd.read_sql_query("SELECT * FROM kategoria", conn)
    st.table(df_k)
    conn.close()
