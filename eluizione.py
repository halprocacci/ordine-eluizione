import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations_with_replacement

st.set_page_config(page_title="TAG Elution Predictor", layout="wide")

# Dizionario interno dei FA noti per l'autocompilazione
fa_db = {
    'Bu': '4:0', 'Co': '6:0', 'Cy': '8:0', 'C': '10:0', 'La': '12:0', 
    'M': '14:0', 'P': '16:0', 'Po': '16:1', 'S': '18:0', 'O': '18:1', 
    'L': '18:2', 'Ln': '18:3', 'A': '20:0', 'G': '20:1', 'B': '22:0', 
    'E': '22:1', 'Lg': '24:0'
}

st.title("TAG Elution Predictor")
st.markdown("Inserisci le sigle degli acidi grassi (es. P, O, Ln). Se la sigla è nel database, il codice si compila da solo. Se usi un acido grasso custom, scrivilo tu.")

# --- 1. GESTIONE DINAMICA DELLE RIGHE ---
# Inizializziamo la memoria di Streamlit per partire con 3 righe vuote
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 3

def add_row():
    st.session_state.num_rows += 1

valid_fas = []

# Stampiamo gli input "uno sotto l'altro"
for i in range(st.session_state.num_rows):
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # L'utente inserisce la sigla (es. "P" o "X")
        sigla = st.text_input(f"Sigla FA {i+1}", key=f"sigla_{i}", placeholder="es. P").strip()
        
    with col2:
        if sigla in fa_db:
            # Se è nel database, auto-compiliamo e disabilitiamo il campo
            codice = st.text_input(f"Codice {i+1}", value=fa_db[sigla], key=f"codice_{i}", disabled=True)
        else:
            # Se è custom (o vuoto), l'utente può scriverci dentro
            codice = st.text_input(f"Codice {i+1}", key=f"codice_{i}", placeholder="es. 16:0")
            
    # Validazione e salvataggio dei dati inseriti
    if sigla and codice:
        if ':' in codice:
            try:
                cn, db = map(int, codice.split(':'))
                valid_fas.append({'Sigla': sigla, 'CN': cn, 'DB': db})
            except ValueError:
                with col3:
                    st.error("Formato errato. Usa CN:DB")
        else:
            with col3:
                st.warning("Usa il formato CN:DB (es. 18:1)")

# Pulsante per aggiungere nuove righe all'infinito
st.button("➕ Aggiungi riga", on_click=add_row)

st.divider()

# --- 2. MOTORE DI CALCOLO ---
# Gira solo se l'utente ha inserito correttamente almeno un Acido Grasso
if len(valid_fas) > 0:
    
    # Rimuoviamo eventuali doppioni (es. se l'utente digita due volte "P")
    unique_fas_dict = {fa['Sigla']: fa for fa in valid_fas}
    pool_fas = list(unique_fas_dict.values())
    
    # Generazione combinazioni
    tag_combinations = list(combinations_with_replacement(pool_fas, 3))
    
    results = []
    for combo in tag_combinations:
        cn_tot = sum(fa['CN'] for fa in combo)
        db_tot = sum(fa['DB'] for fa in combo)
        ecn = cn_tot - (2 * db_tot)
        
        c_lengths = [fa['CN'] for fa in combo]
        varianza_cn = np.var(c_lengths)
        
        results.append({
            'TAG': "".join([fa['Sigla'] for fa in combo]),
            'ECN': ecn,
            'CN Totale': cn_tot,
            'Doppi Legami': db_tot,
            'Asimmetria (Var)': varianza_cn
        })
        
    df_results = pd.DataFrame(results)
    
    # Sorting termodinamico
    df_results.sort_values(
        by=['ECN', 'Doppi Legami', 'Asimmetria (Var)'],
        ascending=[True, False, False],
        inplace=True
    )
    
    df_results.reset_index(drop=True, inplace=True)
    df_results.index += 1
    
    # --- 3. OUTPUT ---
    st.subheader(f"Trovati {len(df_results)} TAG possibili")
    st.dataframe(
        df_results.style.background_gradient(subset=['ECN'], cmap='viridis_r')
                        .format({'Asimmetria (Var)': "{:.2f}"}),
        use_container_width=True
    )
