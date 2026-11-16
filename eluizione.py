import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations_with_replacement

st.set_page_config(page_title="TAG Elution Predictor", layout="wide")

# Dizionario interno
fa_db = {
    'Bu': '4:0', 'Co': '6:0', 'Cy': '8:0', 'C': '10:0', 'La': '12:0', 
    'M': '14:0', 'P': '16:0', 'Po': '16:1', 'S': '18:0', 'O': '18:1', 
    'L': '18:2', 'Ln': '18:3', 'A': '20:0', 'G': '20:1', 'B': '22:0', 
    'E': '22:1', 'Lg': '24:0'
}

st.title("TAG Elution Predictor")

# Inizializziamo le righe
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 3

def add_row():
    st.session_state.num_rows += 1

valid_fas = []

st.markdown("### 1. Inserisci gli Acidi Grassi")

# Input dinamico
for i in range(st.session_state.num_rows):
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        sigla = st.text_input(f"Sigla FA {i+1}", key=f"sigla_{i}", placeholder="es. P, O, Ln").strip()
        
    with col2:
        if sigla:
            if sigla in fa_db:
                # Se è nel database, lo mostriamo bello chiaro e salviamo il valore
                st.info(f"**{fa_db[sigla]}**")
                codice = fa_db[sigla]
            else:
                # Se non c'è, lasciamo lo spazio per scriverlo
                codice = st.text_input(f"Codice custom {i+1}", key=f"codice_{i}", placeholder="es. 16:0")
        else:
            codice = ""
            
    # Validazione silenziosa
    if sigla and codice:
        if ':' in codice:
            try:
                cn, db = map(int, codice.split(':'))
                valid_fas.append({'Sigla': sigla, 'CN': cn, 'DB': db})
            except ValueError:
                with col3:
                    st.error("Usa numeri (es. 16:0)")
        else:
            with col3:
                st.warning("Usa il formato CN:DB")

# Pulsante per aggiungere righe
st.button("➕ Aggiungi riga", on_click=add_row)

st.divider()

# --- MOTORE DI CALCOLO PROTETTO DA UN PULSANTE ---
st.markdown("### 2. Genera e Ordina")

# Adesso il calcolo parte SOLO quando premi il pulsante
if st.button("🚀 Calcola Ordine di Eluizione", type="primary"):
    if len(valid_fas) > 0:
        
        # Eliminiamo eventuali doppioni inseriti per sbaglio
        unique_fas_dict = {fa['Sigla']: fa for fa in valid_fas}
        pool_fas = list(unique_fas_dict.values())
        
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
        
        # Sorting
        df_results.sort_values(
            by=['ECN', 'Doppi Legami', 'Asimmetria (Var)'],
            ascending=[True, False, False],
            inplace=True
        )
        
        df_results.reset_index(drop=True, inplace=True)
        df_results.index += 1
        
        # Output
        st.success(f"Trovati {len(df_results)} TAG possibili!")
        st.dataframe(
            df_results.style.background_gradient(subset=['ECN'], cmap='viridis_r')
                            .format({'Asimmetria (Var)': "{:.2f}"}),
            use_container_width=True
        )
    else:
        st.error("Inserisci almeno un acido grasso valido prima di calcolare!")
