import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations_with_replacement

# --- 1. CONFIGURAZIONE PAGINA E DATI ---
st.set_page_config(page_title="TAG Elution Predictor", layout="wide")

# Database integrato per evitare dipendenze da file CSV esterni
fa_data = {
    'Nome': ['Butirrico', 'Caproico', 'Caprilico', 'Caprico', 'Laurico', 'Miristico', 'Palmitico', 'Palmitoleico', 'Stearico', 'Oleico', 'Linoleico', 'Linolenico', 'Arachidico', 'Gadoleico', 'Behenico', 'Erucico', 'Lignocerico'],
    'Sigla': ['Bu', 'Co', 'Cy', 'C', 'La', 'M', 'P', 'Po', 'S', 'O', 'L', 'Ln', 'A', 'G', 'B', 'E', 'Lg'],
    'Codice': ['4:0', '6:0', '8:0', '10:0', '12:0', '14:0', '16:0', '16:1', '18:0', '18:1', '18:2', '18:3', '20:0', '20:1', '22:0', '22:1', '24:0']
}
df_fa = pd.DataFrame(fa_data)

# Splittiamo il codice per ricavare numero di carboni (CN) e doppi legami (DB) numerici
df_fa[['CN', 'DB']] = df_fa['Codice'].str.split(':', expand=True).astype(int)

# --- 2. INTERFACCIA STREAMLIT ---
st.title("Triglyceride Elution Order (RP-HPLC)")
st.markdown("Calcolatore dell'ordine di eluizione in fase inversa basato su ECN, grado di insaturazione e ingombro sterico (asimmetria della molecola).")

# Selettore multiplo per scegliere gli acidi grassi con cui costruire i TAG
selected_sigle = st.multiselect(
    "Seleziona gli acidi grassi di partenza per generare i TAG:",
    options=df_fa['Sigla'].tolist(),
    format_func=lambda x: f"{x} ({df_fa[df_fa['Sigla'] == x]['Nome'].values[0]})"
)

# --- 3. MOTORE DI CALCOLO ---
if selected_sigle:
    # Generiamo tutte le combinazioni con ripetizione a gruppi di 3 (ignora l'ordine dei regioisomeri)
    tag_combinations = list(combinations_with_replacement(selected_sigle, 3))
    
    results = []
    for combo in tag_combinations:
        # Recuperiamo le righe del dataframe corrispondenti alle sigle della combinazione
        fa_list = [df_fa[df_fa['Sigla'] == sigla].iloc[0] for sigla in combo]
        
        # Somme lineari
        cn_tot = sum(fa['CN'] for fa in fa_list)
        db_tot = sum(fa['DB'] for fa in fa_list)
        ecn = cn_tot - (2 * db_tot)
        
        # Calcolo dell'asimmetria (varianza della lunghezza delle tre catene)
        c_lengths = [fa['CN'] for fa in fa_list]
        varianza_cn = np.var(c_lengths)
        
        # Nome combinato (es. "POO")
        nome_tag = "".join(combo)
        
        results.append({
            'TAG (Regioisomeri collassati)': nome_tag,
            'ECN': ecn,
            'CN Totale': cn_tot,
            'Doppi Legami (DB)': db_tot,
            'Indice Asimmetria (Var)': varianza_cn
        })
        
    df_results = pd.DataFrame(results)
    
    # --- 4. LOGICA DI ORDINAMENTO (IL CUORE DEL MODELLO) ---
    # In Pandas, ascending accetta una lista booleana per ogni colonna:
    # 1. ECN: True (Crescente)
    # 2. DB: False (Decrescente, chi ha più DB eluisce prima)
    # 3. Asimmetria: False (Decrescente, chi è più asimmetrico eluisce prima)
    df_results.sort_values(
        by=['ECN', 'Doppi Legami (DB)', 'Indice Asimmetria (Var)'],
        ascending=[True, False, False],
        inplace=True
    )
    
    # Pulizia dell'indice per mostrare il Rank di eluizione puro (1 = esce per primo)
    df_results.reset_index(drop=True, inplace=True)
    df_results.index += 1
    df_results.index.name = "Ordine di Eluizione"

    # --- 5. OUTPUT ---
    st.subheader(f"TAG Generati: {len(df_results)}")
    
    # Applichiamo una sfumatura di colore all'ECN per renderlo visivamente intuitivo
    st.dataframe(
        df_results.style.background_gradient(subset=['ECN'], cmap='viridis_r')
                        .format({'Indice Asimmetria (Var)': "{:.2f}"}),
        use_container_width=True
    )
    
    st.info("""
    **💡 Regole applicate in sequenza per il sorting:**
    1. **ECN:** Ordine strettamente crescente.
    2. **Risoluzione spalla:** A parità di ECN, eluisce prima il TAG con il maggior numero totale di doppi legami.
    3. **Risoluzione sterica:** A parità di atomi e insaturazioni (es. *MPS* vs *PPP*), eluisce prima il TAG con la geometria più irregolare (misurata tramite la varianza statistica della lunghezza delle tre catene alchiliche).
    """)

else:
    st.warning("Seleziona almeno un acido grasso dal menu a tendina per calcolare l'ordine di eluizione.")