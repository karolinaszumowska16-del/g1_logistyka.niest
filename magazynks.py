import streamlit as st
import sqlite3
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Zarządzanie Bazą Danych", layout="wide")

# --- FUNKCJE BAZODANOWE ---
def get_connection():
    return sqlite3.connect('magazyn.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela kategoria
    c.execute('''CREATE TABLE IF NOT EXISTS kategoria 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nazwa TEXT NOT NULL, 
                  opis TEXT)''')
    # Tabela produkty
    c.execute('''CREATE TABLE IF NOT EXISTS produkty 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nazwa TEXT NOT NULL, 
                  liczba INTEGER, 
                  cena REAL, 
                  kategoria_id INTEGER, 
                  FOREIGN KEY(kategoria_id) REFERENCES kategoria(id))''')
    
    # --- DANE POCZĄTKOWE (UZUPEŁNIJ TUTAJ SWOJE DANE) ---
    c.execute("SELECT COUNT(*) FROM kategoria")
    if c.fetchone()[0] == 0:
        # 1. Dodawanie kategorii (ID generuje się samo)
        kategorie_startowe = [
            ('Elektronika', 'Sprzęt komputerowy i telefony'),
            ('Biuro', 'Artykuły piśmiennicze i papierowe'),
            ('Meble', 'Wyposażenie biura')
        ]
        c.executemany("INSERT INTO kategoria (nazwa, opis) VALUES (?, ?)", kategorie_startowe)
        
        # 2. Dodawanie produktów (nazwa, liczba, cena, kategoria_id)
        # UWAGA: kategoria_id 1 to Elektronika, 2 to Biuro itd.
        produkty_startowe = [
            ('Laptop', 10, 3500.00, 1),
            ('Monitor 24 cale', 5, 800.00, 1),
            ('Długopis żelowy', 100, 2.50, 2),
            ('Biurko drewniane', 2, 1200.00, 3)
        ]
        c.executemany("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)", produkty_startowe)
    
    conn.commit()
    conn.close()

init_db()

# --- INTERFEJS ---
st.title("📦 System Zarządzania Produktami i Kategoriami")

tab1, tab2, tab3 = st.tabs(["📊 Przegląd i Usuwanie", "➕ Dodaj Produkt", "📂 Dodaj Kategorię"])

# TAB 1: Widok danych i usuwanie
with tab1:
    conn = get_connection()
    st.subheader("Produkty w magazynie")
    df_prod = pd.read_sql_query('''
        SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
        FROM produkty p 
        LEFT JOIN kategoria k ON p.kategoria_id = k.id
    ''', conn)
    
    if not df_prod.empty:
        st.dataframe(df_prod, use_container_width=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            prod_to_delete = st.selectbox("Wybierz produkt do usunięcia", df_prod['id'], 
                                        format_func=lambda x: f"ID: {x} - {df_prod[df_prod['id']==x]['nazwa'].values[0]}")
        with col2:
            if st.button("Usuń produkt", use_container_width=True):
                c = conn.cursor()
                c.execute("DELETE FROM produkty WHERE id = ?", (prod_to_delete,))
                conn.commit()
                st.rerun()
    else:
        st.info("Baza produktów jest pusta.")

    st.divider()
    st.subheader("Kategorie")
    df_kat = pd.read_sql_query("SELECT * FROM kategoria", conn)
    if not df_kat.empty:
        st.table(df_kat)
        kat_to_delete = st.selectbox("Wybierz kategorię do usunięcia", df_kat['id'], 
                                   format_func=lambda x: f"ID: {x} - {df_kat[df_kat['id']==x]['nazwa'].values[0]}")
        if st.button("Usuń kategorię"):
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM produkty WHERE kategoria_id = ?", (kat_to_delete,))
            if c.fetchone()[0] > 0:
                st.error("Błąd: Nie możesz usunąć kategorii, która zawiera produkty!")
            else:
                c.execute("DELETE FROM kategoria WHERE id = ?", (kat_to_delete,))
                conn.commit()
                st.rerun()
    conn.close()

# TAB 2: Dodawanie Produktu
with tab2:
    st.subheader("Dodaj nowy produkt")
    conn = get_connection()
    kategorie_df = pd.read_sql_query("SELECT id, nazwa FROM kategoria", conn)
    
    if kategorie_df.empty:
        st.warning("Najpierw musisz dodać kategorię w zakładce obok!")
    else:
        with st.form("form_dodaj_produkt"):
            nazwa_p = st.text_input("Nazwa produktu")
            col1, col2 = st.columns(2)
            with col1:
                liczba_p = st.number_input("Ilość", min_value=0, step=1)
            with col2:
                cena_p = st.number_input("Cena (PLN)", min_value=0.0, step=0.01)
            
            opcje_kat = {row['nazwa']: row['id'] for _, row in kategorie_df.iterrows()}
            wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(opcje_kat.keys()))
            
            if st.form_submit_button("Zapisz w bazie"):
                if nazwa_p:
                    c = conn.cursor()
                    c.execute("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)",
                              (nazwa_p, liczba_p, cena_p, opcje_kat[wybrana_kat_nazwa]))
                    conn.commit()
                    st.success("Dodano produkt!")
                    st.rerun()
    conn.close()

# TAB 3: Dodawanie Kategorii
with tab3:
    st.subheader("Utwórz nową kategorię")
    with st.form("form_dodaj_kategorie"):
        nazwa_k = st.text_input("Nazwa kategorii")
        opis_k = st.text_area("Opis kategorii")
        if st.form_submit_button("Dodaj kategorię"):
            if nazwa_k:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO kategoria (nazwa, opis) VALUES (?, ?)", (nazwa_k, opis_k))
                conn.commit()
                conn.close()
                st.success("Kategoria została utworzona!")
                st.rerun()
