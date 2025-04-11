import streamlit as st
import pandas as pd

# Carregar les dades de RA per matèria (simulades)
ra_data = pd.read_excel("Plantilla_RA_per_Materia_Ordenada.xlsx")
assignatures_data = pd.read_excel("Assignatures_per_Materia.xlsx")

st.title("Selecció de Resultats d'Aprenentatge per Professor/a")

# Pas 1: Selecció de les assignatures del professor/a
st.header("1. Selecciona les assignatures que són responsabilitat teva")
assignatures_disponibles = assignatures_data["Assignatura"].unique()
assignatures_seleccionades = st.multiselect("Assignatures:", assignatures_disponibles)

# Crear un diccionari per desar les seleccions
seleccions_final = []

# Per cada assignatura seleccionada, mostrar els RA de la seva matèria
for assignatura in assignatures_seleccionades:
    materia = assignatures_data[assignatures_data["Assignatura"] == assignatura]["Matèria"].values[0]
    ra_materia = ra_data[ra_data["Matèria"] == materia][["Codi RA", "Resultado de aprendizaje"]]

    st.header(f"2. RA per a l'assignatura: {assignatura} ({materia})")
    ras_seleccionats = st.multiselect(
        f"Selecciona els RA que treballes a '{assignatura}':",
        options=ra_materia["Codi RA"] + " – " + ra_materia["Resultado de aprendizaje"].str.slice(0, 100) + "...",
        key=assignatura
    )

    for ra in ras_seleccionats:
        codi_ra = ra.split(" – ")[0]
        seleccions_final.append({
            "Assignatura": assignatura,
            "Matèria": materia,
            "Codi RA": codi_ra
        })

# Mostrar i descarregar resultat
if seleccions_final:
    df_resultat = pd.DataFrame(seleccions_final)
    st.success("Seleccions enregistrades!")
    st.dataframe(df_resultat)

    csv = df_resultat.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descarrega les teves seleccions en CSV",
        data=csv,
        file_name='seleccio_RA_professor.csv',
        mime='text/csv'
    )
