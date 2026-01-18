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
    # Tabela kategoria (id, nazwa, opis)
    c.execute('''CREATE TABLE IF NOT EXISTS kategoria 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nazwa TEXT NOT NULL, 
                  opis TEXT)''')
    # Tabela produkty (id, nazwa, liczba, cena, kategoria_id)
    c.execute('''CREATE TABLE IF NOT EXISTS produkty 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nazwa TEXT NOT NULL, 
                  liczba INTEGER, 
                  cena REAL, 
                  kategoria_id INTEGER, 
                  FOREIGN KEY(kategoria_id) REFERENCES kategoria(id))''')
    conn.commit()
    conn.close()

init_db()

# --- INTERFEJS ---
st.title("📦 System Zarządzania Produktami i Kategoriami")

tab1, tab2, tab3 = st.tabs(["📊 Przegląd i Usuwanie", "➕ Dodaj Produkt", "📂 Dodaj Kategorię"])

# TAB 1: Widok danych i usuwanie
with tab1:
    conn = get_connection()
    
    st.subheader("Produkty")
    df_prod = pd.read_sql_query('''
        SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
        FROM produkty p 
        LEFT JOIN kategoria k ON p.kategoria_id = k.id
    ''', conn)
    
    if not df_prod.empty:
        st.dataframe(df_prod, use_container_width=True)
        prod_to_delete = st.selectbox("Wybierz produkt do usunięcia", df_prod['id'], format_func=lambda x: f"ID: {x} - {df_prod[df_prod['id']==x]['nazwa'].values[0]}")
        if st.button("Usuń wybrany produkt"):
            c = conn.cursor()
            c.execute("DELETE FROM produkty WHERE id = ?", (prod_to_delete,))
            conn.commit()
            st.warning(f"Usunięto produkt o ID {prod_to_delete}")
            st.rerun()
    else:
        st.info("Brak produktów w bazie.")

    st.divider()

    st.subheader("Kategorie")
    df_kat = pd.read_sql_query("SELECT * FROM kategoria", conn)
    if not df_kat.empty:
        st.table(df_kat)
        kat_to_delete = st.selectbox("Wybierz kategorię do usunięcia", df_kat['id'], format_func=lambda x: f"ID: {x} - {df_kat[df_kat['id']==x]['nazwa'].values[0]}")
        if st.button("Usuń wybraną kategorię"):
            c = conn.cursor()
            # Sprawdzenie czy kategoria nie jest używana
            c.execute("SELECT COUNT(*) FROM produkty WHERE kategoria_id = ?", (kat_to_delete,))
            if c.fetchone()[0] > 0:
                st.error("Nie można usunąć kategorii, do której przypisane są produkty!")
            else:
                c.execute("DELETE FROM kategoria WHERE id = ?", (kat_to_delete,))
                conn.commit()
                st.success(f"Usunięto kategorię o ID {kat_to_delete}")
                st.rerun()
    else:
        st.info("Brak kategorii w bazie.")
    conn.close()

# TAB 2: Dodawanie Produktu
with tab2:
    st.subheader("Nowy Produkt")
    conn = get_connection()
    kategorie_df = pd.read_sql_query("SELECT id, nazwa FROM kategoria", conn)
    
    if kategorie_df.empty:
        st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
    else:
        with st.form("form_dodaj_produkt"):
            nazwa_p = st.text_input("Nazwa produktu")
            liczba_p = st.number_input("Ilość (liczba)", min_value=0, step=1)
            cena_p = st.number_input("Cena (numeric)", min_value=0.0, step=0.01)
            
            opcje_kat = {row['nazwa']: row['id'] for _, row in kategorie_df.iterrows()}
            wybrana_kat_nazwa = st.selectbox("Kategoria", options=list(opcje_kat.keys()))
            
            if st.form_submit_button("Zapisz produkt"):
                if nazwa_p:
                    c = conn.cursor()
                    c.execute("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)",
                              (nazwa_p, liczba_p, cena_p, opcje_kat[wybrana_kat_nazwa]))
                    conn.commit()
                    st.success("Produkt dodany!")
                    st.rerun()
                else:
                    st.error("Nazwa produktu jest wymagana!")
    conn.close()

# TAB 3: Dodawanie Kategorii
with tab3:
    st.subheader("Nowa Kategoria")
    with st.form("form_dodaj_kategorie"):
        nazwa_k = st.text_input("Nazwa kategorii")
        opis_k = st.text_area("Opis")
        
        if st.form_submit_button("Zapisz kategorię"):
            if nazwa_k:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO kategoria (nazwa, opis) VALUES (?, ?)", (nazwa_k, opis_k))
                conn.commit()
                conn.close()
                st.success("Kategoria dodana!")
                st.rerun()
            else:
                st.error("Nazwa kategorii jest wymagana!")
