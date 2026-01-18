import streamlit as st
import sqlite3
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Manager Bazy Danych", layout="centered")

# --- FUNKCJE BAZODANOWE ---
def get_connection():
    return sqlite3.connect('magazyn.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kategoria 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT, opis TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produkty 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT, liczba INTEGER, 
                  cena REAL, kategoria_id INTEGER, 
                  FOREIGN KEY(kategoria_id) REFERENCES kategoria(id))''')
    conn.commit()
    conn.close()

init_db()

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("🚀 System Zarządzania Magazynem")

tab1, tab2, tab3 = st.tabs(["📋 Widok Tabel", "➕ Dodaj Produkt", "📂 Dodaj Kategorię"])

# TAB 1: Podgląd danych
with tab1:
    conn = get_connection()
    st.subheader("Produkty w bazie")
    df_prod = pd.read_sql_query('''
        SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
        FROM produkty p LEFT JOIN kategoria k ON p.kategoria_id = k.id
    ''', conn)
    st.dataframe(df_prod, use_container_width=True)
    
    st.subheader("Kategorie")
    df_kat = pd.read_sql_query("SELECT * FROM kategoria", conn)
    st.table(df_kat)
    conn.close()

# TAB 2: Dodawanie Produktu
with tab2:
    st.subheader("Nowy Produkt")
    conn = get_connection()
    kategorie = pd.read_sql_query("SELECT id, nazwa FROM kategoria", conn)
    
    with st.form("form_produkt"):
        nazwa_p = st.text_input("Nazwa produktu")
        liczba_p = st.number_input("Ilość", min_value=0, step=1)
        cena_p = st.number_input("Cena", min_value=0.0, step=0.01)
        
        # Lista rozwijana z kategoriami
        opcje_kat = {row['nazwa']: row['id'] for _, row in kategorie.iterrows()}
        wybrana_kat = st.selectbox("Wybierz kategorię", options=list(opcje_kat.keys()))
        
        submit_p = st.form_submit_button("Dodaj Produkt")
        
        if submit_p:
            if nazwa_p and wybrana_kat:
                c = conn.cursor()
                c.execute("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)",
                          (nazwa_p, liczba_p, cena_p, opcje_kat[wybrana_kat]))
                conn.commit()
                st.success(f"Dodano produkt: {nazwa_p}")
                st.rerun()
            else:
                st.error("Wypełnij wszystkie pola!")
    conn.close()

# TAB 3: Dodawanie Kategorii
with tab3:
    st.subheader("Nowa Kategoria")
    with st.form("form_kategoria"):
        nazwa_k = st.text_input("Nazwa kategorii (np. Elektronika)")
        opis_k = st.text_area("Opis")
        submit_k = st.form_submit_button("Utwórz Kategorię")
        
        if submit_k:
            if nazwa_k:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO kategoria (nazwa, opis) VALUES (?, ?)", (nazwa_k, opis_k))
                conn.commit()
                conn.close()
                st.success(f"Utworzono kategorię: {nazwa_k}")
                st.rerun()
