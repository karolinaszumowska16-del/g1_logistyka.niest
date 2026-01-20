import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

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
                      nazwa TEXT NOT NULL UNIQUE, 
                      opis TEXT)''') # Dodano UNIQUE do nazwy kategorii
        # Tabela produkty
        c.execute('''CREATE TABLE IF NOT EXISTS produkty 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      nazwa TEXT NOT NULL, 
                      liczba INTEGER DEFAULT 0, 
                      cena REAL DEFAULT 0.0, 
                      kategoria_id INTEGER, 
                      FOREIGN KEY(kategoria_id) REFERENCES kategoria(id))''')
        
        # Dane początkowe (jeśli baza jest pusta)
        c.execute("SELECT COUNT(*) FROM kategoria")
        if c.fetchone()[0] == 0:
            kategorie_startowe = [
                ('Elektronika', 'Sprzęt komputerowy i telefony'),
