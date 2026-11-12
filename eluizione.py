import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations_with_replacement

# --- 1. DATI ---
st.set_page_config(page_title="TAG Elution Predictor", layout="wide")

# Solo sigle e codici, via i nomi lunghi
fa_data = {
    'Sigla': ['Bu', 'Co', 'Cy', 'C', 'La', 'M', 'P', 'Po', 'S', 'O', 'L', 'Ln', 'A', 'G', 'B', 'E', 'Lg'],
    'Codice': ['4:0', '6:0', '8:0', '10:0', '12:0', '14:0', '16:0', '16:1', '18:0', '18:1', '18:2', '18:3', '20:0', '20:1', '22:0', '22:1', '24:0']
}
df_fa = pd.DataFrame(fa_data)

# Parsing ultrasicuro
df_fa[['CN', 'DB']] = df_fa['Codice'].str.split(':', expand=True)
df_fa['CN'] = pd.to_numeric(df_fa['CN'])
df_fa['DB'] = pd.to_numeric(df_fa['DB'])

# --- 2. INTERFACCIA ---
st.title("TAG Elution Predictor")

# Menu a tendina pulito, nudo e crudo
selected_sigle = st.multiselect(
    "Seleziona le sigle degli acidi grassi (es. P, O, La):",
    options=df_fa['Sigla'].tolist()
)

if selected_sigle:
    # Generazione combinazioni
    tag_combinations = list(combinations_with_replacement(selected_sigle, 3))
    
    results = []
    for combo in tag_combinations:
        # Recupero dati
        fa_list = [df_fa[df_fa['Sigla'] == s].iloc[0] for s in combo]
        
        cn_tot = sum(fa['CN'] for fa in fa_list)
        db_tot = sum(fa['DB'] for fa in fa_list)
        ecn = cn_tot - (2 * db_tot)
        
        # Calcolo asimmetria
        c_lengths = [fa['CN'] for fa in fa_list]
        varianza_cn = np.var(c_lengths)
        
        results.append({
            'TAG': "".join(combo),
            'ECN': ecn,
            'CN Totale': cn_tot,
            'Doppi Legami': db_tot,
            'Asimmetria (Var)': varianza_cn
        })
        
    df_results = pd.DataFrame(results)
    
    # --- 3. SORTING TERMODINAMICO ---
    df_results.sort_values(
        by=['ECN', 'Doppi Legami', 'Asimmetria (Var)'],
        ascending=[True, False, False],
        inplace=True
    )
    
    df_results.reset_index(drop=True, inplace=True)
    df_results.index += 1
    
    # --- 4. OUTPUT ---
    st.subheader(f"Trovati {len(df_results)} TAG possibili")
    st.dataframe(
        df_results.style.background_gradient(subset=['ECN'], cmap='viridis_r')
                        .format({'Asimmetria (Var)': "{:.2f}"}),
        use_container_width=True
    )
