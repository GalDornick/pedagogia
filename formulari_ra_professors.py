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
    st.write("Selecciona els RA que treballes a aquesta assignatura:")
    
    # Crear una llista per emmagatzemar els RA seleccionats per aquesta assignatura
    ras_seleccionats = []
    
    # Crear checkboxes per cada RA
    for _, ra_row in ra_materia.iterrows():
        codi_ra = ra_row["Codi RA"]
        descripcio_ra = ra_row["Resultado de aprendizaje"]
        # Retallar la descripció si és massa llarga
        descripcio_curta = descripcio_ra[:100] + "..." if len(descripcio_ra) > 100 else descripcio_ra
        
        # Crear una checkbox per aquest RA
        if st.checkbox(f"{codi_ra} – {descripcio_curta}", key=f"{assignatura}_{codi_ra}"):
            ras_seleccionats.append(codi_ra)
            seleccions_final.append({
                "Assignatura": assignatura,
                "Matèria": materia,
                "Codi RA": codi_ra
            })
    
    # Afegir una línia separadora entre assignatures
    st.divider()

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