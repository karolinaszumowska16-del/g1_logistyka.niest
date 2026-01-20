import streamlit as st
import sqlite3
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide", page_icon="📦")

# --- FUNKCJE BAZODANOWE ---
def get_connection():
    return sqlite3.connect('magazyn.db', check_same_thread=False)

def init_db():
    with get_connection() as conn:
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
        
        # Dane początkowe
        c.execute("SELECT COUNT(*) FROM kategoria")
        if c.fetchone()[0] == 0:
            kategorie_startowe = [
                ('Elektronika', 'Sprzęt komputerowy i telefony'),
                ('Biuro', 'Artykuły piśmiennicze i papierowe'),
                ('Meble', 'Wyposażenie biura')
            ]
            c.executemany("INSERT INTO kategoria (nazwa, opis) VALUES (?, ?)", kategorie_startowe)
            
            produkty_startowe = [
                ('Laptop', 3, 3500.00, 1), # Stan krytyczny (<5)
                ('Monitor 24 cale', 12, 800.00, 1),
                ('Długopis żelowy', 100, 2.50, 2),
                ('Biurko drewniane', 1, 1200.00, 3) # Stan krytyczny (<5)
            ]
            c.executemany("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)", produkty_startowe)
            conn.commit()

init_db()

# --- INTERFEJS ---
st.title("📦 System Zarządzania Magazynem")

# Sidebar - Ustawienia progu krytycznego
st.sidebar.header("⚙️ Ustawienia")
prog_krytyczny = st.sidebar.slider("Próg stanu krytycznego", 0, 50, 5)

tab1, tab2, tab3 = st.tabs(["📊 Przegląd i Usuwanie", "➕ Dodaj Produkt", "📂 Dodaj Kategorię"])

# TAB 1: Widok danych i usuwanie
with tab1:
    with get_connection() as conn:
        st.subheader("Aktualny stan magazynowy")
        
        df_prod = pd.read_sql_query('''
            SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
            FROM produkty p 
            LEFT JOIN kategoria k ON p.kategoria_id = k.id
        ''', conn)
        
        if not df_prod.empty:
            # Sekcja alertów
            niskie_stany = df_prod[df_prod['liczba'] < prog_krytyczny]
            
            if not niskie_stany.empty:
                st.error(f"⚠️ **KRYTYCZNY STAN:** Masz {len(niskie_stany)} produkty wymagające zamówienia!")
                with st.expander("Zobacz listę braków"):
                    st.dataframe(niskie_stany[['nazwa', 'liczba', 'kategoria']], use_container_width=True)
            
            # Funkcja kolorująca wiersze
            def highlight_low_stock(row):
                color = 'background-color: #ff4b4b; color: white' if row.liczba < prog_krytyczny else ''
                return [color] * len(row)

            # Wyświetlanie tabeli głównej
            st.write("Wszystkie produkty:")
            st.dataframe(
                df_prod.style.apply(highlight_low_stock, axis=1), 
                use_container_width=True,
                hide_index=True
            )

            # Usuwanie produktu
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                prod_to_delete = st.selectbox("Wybierz produkt do usunięcia", df_prod['id'], 
                                            format_func=lambda x: f"ID: {x} - {df_prod[df_prod['id']==x]['nazwa'].values[0]}")
            with col2:
                if st.button("🗑️ Usuń produkt", use_container_width=True):
                    c = conn.cursor()
                    c.execute("DELETE FROM produkty WHERE id = ?", (prod_to_delete,))
                    conn.commit()
                    st.success("Produkt usunięty!")
                    st.rerun()
        else:
            st.info("Baza produktów jest pusta.")

        # Sekcja Kategorii (pod linią)
        st.divider()
        st.subheader("📂 Zarządzanie Kategoriami")
        df_kat = pd.read_sql_query("SELECT * FROM kategoria", conn)
        if not df_kat.empty:
            st.table(df_kat)
            kat_to_delete = st.selectbox("Wybierz kategorię do usunięcia", df_kat['id'], 
                                       format_func=lambda x: f"ID: {x} - {df_kat[df_kat['id']==x]['nazwa'].values[0]}")
            if st.button("Usuń kategorię"):
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM produkty WHERE kategoria_id = ?", (kat_to_delete,))
                if c.fetchone()[0] > 0:
                    st.error("Nie można usunąć kategorii, która zawiera produkty!")
                else:
                    c.execute("DELETE FROM kategoria WHERE id = ?", (kat_to_delete,))
                    conn.commit()
                    st.rerun()

# TAB 2: Dodawanie Produktu
with tab2:
    st.subheader("➕ Dodaj nowy produkt")
    with get_connection() as conn:
        kategorie_df = pd.read_sql_query("SELECT id, nazwa FROM kategoria", conn)
        
        if kategorie_df.empty:
            st.warning("Najpierw dodaj kategorię w zakładce obok!")
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
                
                if st.form_submit_button("Zapisz produkt"):
                    if nazwa_p:
                        c = conn.cursor()
                        c.execute("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)",
                                  (nazwa_p, liczba_p, cena_p, opcje_kat[wybrana_kat_nazwa]))
                        conn.commit()
                        st.success(f"Dodano: {nazwa_p}")
                        st.rerun()
                    else:
                        st.error("Nazwa produktu nie może być pusta!")

# TAB 3: Dodawanie Kategorii
with tab3:
    st.subheader("📂 Nowa kategoria")
    with st.form("form_dodaj_kategorie"):
        nazwa_k = st.text_input("Nazwa kategorii (np. Narzędzia)")
        opis_k = st.text_area("Krótki opis")
        if st.form_submit_button("Utwórz kategorię"):
            if nazwa_k:
                with get_connection() as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO kategoria (nazwa, opis) VALUES (?, ?)", (nazwa_k, opis_k))
                    conn.commit()
                st.success(f"Kategoria '{nazwa_k}' dodana!")
                st.rerun()
            else:
                st.error("Podaj nazwę kategorii!")
