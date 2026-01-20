import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Konfiguracja strony
st.set_page_config(page_title="Zarządzanie Magazynem PRO", layout="wide", page_icon="📦")

# --- FUNKCJE BAZODANOWE ---
def get_connection():
    return sqlite3.connect('magazyn.db', check_same_thread=False)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        # Tabela kategoria
        c.execute('''CREATE TABLE IF NOT EXISTS kategoria 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      nazwa TEXT NOT NULL UNIQUE, 
                      opis TEXT)''')
        # Tabela produkty
        c.execute('''CREATE TABLE IF NOT EXISTS produkty 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      nazwa TEXT NOT NULL, 
                      liczba INTEGER, 
                      cena REAL, 
                      kategoria_id INTEGER, 
                      FOREIGN KEY(kategoria_id) REFERENCES kategoria(id))''')
        
        # Dane początkowe (jeśli baza jest pusta)
        c.execute("SELECT COUNT(*) FROM kategoria")
        if c.fetchone()[0] == 0:
            kat_start = [('Elektronika', 'Sprzęt IT'), ('Biuro', 'Artykuły biurowe'), ('Meble', 'Wyposażenie')]
            c.executemany("INSERT INTO kategoria (nazwa, opis) VALUES (?, ?)", kat_start)
            
            prod_start = [('Laptop', 3, 3500.0, 1), ('Mysz', 15, 50.0, 1), ('Biurko', 2, 1200.0, 3)]
            c.executemany("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?, ?, ?, ?)", prod_start)
            conn.commit()

init_db()

# --- INTERFEJS ---
st.title("📦 System Zarządzania Magazynem")

# Sidebar
st.sidebar.header("⚙️ Ustawienia")
prog_krytyczny = st.sidebar.slider("Próg stanu krytycznego", 0, 50, 5)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Stan Magazynu", "📈 Wykresy i Analiza", "➕ Dodaj Produkt", "📂 Kategorie"])

# TAB 1: Widok i Usuwanie
with tab1:
    with get_connection() as conn:
        df_prod = pd.read_sql_query('''
            SELECT p.id, p.nazwa, p.liczba, p.cena, k.nazwa as kategoria 
            FROM produkty p 
            LEFT JOIN kategoria k ON p.kategoria_id = k.id
        ''', conn)
        
        if not df_prod.empty:
            # Alert
            niskie = df_prod[df_prod['liczba'] < prog_krytyczny]
            if not niskie.empty:
                st.error(f"⚠️ Uwaga! {len(niskie)} produkty mają stan poniżej krytycznego.")
            
            st.subheader("Aktualna lista produktów")
            
            # Kolorowanie
            def style_row(row):
                return ['background-color: rgba(255, 75, 75, 0.3)' if row.liczba < prog_krytyczny else '' for _ in row]
            
            st.dataframe(df_prod.style.apply(style_row, axis=1), use_container_width=True, hide_index=True)

            st.divider()
            col_del1, col_del2 = st.columns([3,1])
            with col_del1:
                p_to_del = st.selectbox("Wybierz produkt do usunięcia", df_prod['id'], 
                                       format_func=lambda x: f"ID: {x} | {df_prod[df_prod['id']==x]['nazwa'].values[0]}")
            with col_del2:
                if st.button("🗑️ Usuń", use_container_width=True):
                    conn.execute("DELETE FROM produkty WHERE id = ?", (p_to_del,))
                    conn.commit()
                    st.rerun()
        else:
            st.info("Baza jest pusta.")

# TAB 2: Wykresy
with tab2:
    st.subheader("📊 Wizualizacja Danych")
    with get_connection() as conn:
        df_vis = pd.read_sql_query('''
            SELECT p.nazwa, p.liczba, p.cena, (p.liczba * p.cena) as wartosc, k.nazwa as kategoria 
            FROM produkty p 
            JOIN kategoria k ON p.kategoria_id = k.id
        ''', conn)

    if not df_vis.empty:
        col_fig1, col_fig2 = st.columns(2)
        
        with col_fig1:
            st.write("**Liczba produktów wg kategorii**")
            fig1 = px.bar(df_vis.groupby('kategoria')['liczba'].sum().reset_index(), 
                          x='kategoria', y='liczba', color='kategoria', text_auto=True)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_fig2:
            st.write("**Udział wartościowy magazynu (PLN)**")
            fig2 = px.pie(df_vis, values='wartosc', names='kategoria', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)
            
        st.metric("Całkowita wartość magazynu", f"{df_vis['wartosc'].sum():,.2f} PLN")
    else:
        st.warning("Dodaj produkty, aby zobaczyć wykresy.")

# TAB 3: Dodawanie Produktu
with tab3:
    st.subheader("➕ Nowy produkt")
    with get_connection() as conn:
        kategorie_df = pd.read_sql_query("SELECT id, nazwa FROM kategoria", conn)
        
        if kategorie_df.empty:
            st.warning("Najpierw dodaj kategorię!")
        else:
            with st.form("add_p"):
                name = st.text_input("Nazwa")
                c1, c2 = st.columns(2)
                amount = c1.number_input("Ilość", min_value=0, step=1)
                price = c2.number_input("Cena", min_value=0.0, step=0.5)
                cat = st.selectbox("Kategoria", kategorie_df['nazwa'])
                cat_id = int(kategorie_df[kategorie_df['nazwa'] == cat]['id'].values[0])
                
                if st.form_submit_button("Zapisz"):
                    if name:
                        conn.execute("INSERT INTO produkty (nazwa, liczba, cena, kategoria_id) VALUES (?,?,?,?)",
                                   (name, amount, price, cat_id))
                        conn.commit()
                        st.success("Dodano produkt!")
                        st.rerun()

# TAB 4: Kategorie
with tab4:
    st.subheader("📂 Zarządzanie kategoriami")
    with st.form("add_k"):
        k_name = st.text_input("Nazwa kategorii")
        k_desc = st.text_area("Opis")
        if st.form_submit_button("Dodaj kategorię"):
            if k_name:
                try:
                    with get_connection() as conn:
                        conn.execute("INSERT INTO kategoria (nazwa, opis) VALUES (?,?)", (k_name, k_desc))
                        conn.commit()
                    st.success("Dodano kategorię!")
                    st.rerun()
                except:
                    st.error("Kategoria o tej nazwie już istnieje!")
