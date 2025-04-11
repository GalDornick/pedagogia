import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Configurar l'accés a Google Sheets
@st.cache_resource
def setup_gsheets_connection():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'credencials.json', scope)  # Substitueix per la ruta al teu fitxer de credencials
    client = gspread.authorize(credentials)
    return client

# Funció per desar a Google Sheets
def save_to_gsheets(dataframe, spreadsheet_id, nom_professor):
    client = setup_gsheets_connection()
    
    try:
        # Obrir el full de càlcul pel seu ID
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Crear un nou full amb el nom del professor i la data
        data_actual = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        nom_full = f"{nom_professor}_{data_actual}"
        
        # Comprovar si ja existeix un full amb el mateix nom
        try:
            worksheet = spreadsheet.add_worksheet(title=nom_full, rows=len(dataframe) + 1, cols=dataframe.shape[1])
        except gspread.exceptions.APIError:
            # Si ja existeix, afegeix un número aleatori
            import random
            nom_full = f"{nom_professor}_{data_actual}_{random.randint(1, 1000)}"
            worksheet = spreadsheet.add_worksheet(title=nom_full, rows=len(dataframe) + 1, cols=dataframe.shape[1])
        
        # Afegir les capçaleres
        worksheet.update([dataframe.columns.tolist()] + dataframe.values.tolist())
        
        return True, f"Dades desades correctament al full '{nom_full}'"
    except Exception as e:
        return False, f"Error en desar les dades: {str(e)}"

# Carregar les dades de RA per matèria (simulades)
ra_data = pd.read_excel("Plantilla_RA_per_Materia_Ordenada.xlsx")
assignatures_data = pd.read_excel("Assignatures_per_Materia.xlsx")

st.title("Selecció de Resultats d'Aprenentatge per Professor/a")

# Demanar el nom del professor/a
nom_professor = st.text_input("El teu nom i cognoms:")

# ID del full de càlcul de Google Sheets
spreadsheet_id = "1ct5-tRmChvJUHU8Bjburrm2gmgS8in6b3roshjt0v1k"

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
    
    # Crear checkboxes per cada RA
    for _, ra_row in ra_materia.iterrows():
        codi_ra = ra_row["Codi RA"]
        descripcio_ra = ra_row["Resultado de aprendizaje"]
        # Retallar la descripció si és massa llarga
        descripcio_curta = descripcio_ra[:100] + "..." if len(descripcio_ra) > 100 else descripcio_ra
        
        # Crear una checkbox per aquest RA
        if st.checkbox(f"{codi_ra} – {descripcio_curta}", key=f"{assignatura}_{codi_ra}"):
            seleccions_final.append({
                "Professor/a": nom_professor,
                "Assignatura": assignatura,
                "Matèria": materia,
                "Codi RA": codi_ra,
                "Data_Selecció": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    # Afegir una línia separadora entre assignatures
    st.divider()

# Mostrar i descarregar resultat
if seleccions_final:
    df_resultat = pd.DataFrame(seleccions_final)
    st.success("Seleccions enregistrades!")
    st.dataframe(df_resultat)

    # Opció per descarregar en CSV
    csv = df_resultat.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descarrega les teves seleccions en CSV",
        data=csv,
        file_name='seleccio_RA_professor.csv',
        mime='text/csv'
    )
    
    # Botó per desar a Google Sheets
    if st.button("Desa les seleccions a Google Sheets"):
        if not nom_professor:
            st.error("Si us plau, introdueix el teu nom abans de desar.")
        else:
            success, message = save_to_gsheets(df_resultat, spreadsheet_id, nom_professor)
            if success:
                st.success(message)
            else:
                st.error(message)