import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import datetime
import json
from pytz import timezone

zona_espanya = timezone("Europe/Madrid")

@st.cache_resource
def setup_gsheets_connection():
    try:
        credentials_dict = st.secrets["gcp_service_account"]
    except KeyError:
        try:
            credentials_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"]
            }
        except KeyError:
            st.error("No s'han trobat les credencials per connectar amb Google Sheets.")
            st.stop()
    
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    )
    client = gspread.authorize(credentials)
    return client

def save_to_gsheets(dataframe, spreadsheet_id, nom_professor):
    client = setup_gsheets_connection()
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        data_actual = datetime.datetime.now(zona_espanya).strftime("%Y-%m-%d_%H-%M")
        nom_full = f"{nom_professor}_{data_actual}"
        try:
            worksheet = spreadsheet.add_worksheet(title=nom_full, rows=len(dataframe) + 1, cols=dataframe.shape[1])
        except gspread.exceptions.APIError:
            import random
            nom_full = f"{nom_professor}_{data_actual}_{random.randint(1, 1000)}"
            worksheet = spreadsheet.add_worksheet(title=nom_full, rows=len(dataframe) + 1, cols=dataframe.shape[1])
        worksheet.update([dataframe.columns.tolist()] + dataframe.values.tolist())
        return True, "Dades desades correctament. Moltes gràcies!"
    except Exception as e:
        return False, f"Error en desar les dades: {str(e)}"

try:
    ra_data = pd.read_excel("Plantilla_RA_per_Materia_Ordenada.xlsx")
    assignatures_data = pd.read_excel("Assignatures_per_Materia.xlsx")
except Exception as e:
    st.error(f"Error al carregar els arxius Excel: {str(e)}")
    st.stop()

st.title("Selecció de Resultats d'Aprenentatge per Professor/a")

nom_professor = st.text_input("Per favor, indica el teu nom i cognoms:")
spreadsheet_id = "1ct5-tRmChvJUHU8Bjburrm2gmgS8in6b3roshjt0v1k"

st.header("1. Selecciona les assignatures que són responsabilitat teva")
assignatures_disponibles = assignatures_data["Assignatura"].unique()
assignatures_seleccionades = st.multiselect("Assignatures:", assignatures_disponibles)

seleccions_final = []

for assignatura in assignatures_seleccionades:
    materia = assignatures_data[assignatures_data["Assignatura"] == assignatura]["Matèria"].values[0]
    ra_materia = ra_data[ra_data["Matèria"] == materia][["Codi RA", "Resultado de aprendizaje", "Clasificación"]]
    st.header(f"2. RA per a l'assignatura: {assignatura} ({materia})")
    st.info("🔍 Si necessites veure la descripció completa d'un RA, fes clic a la fletxa per expandir el seu contingut.")

    for _, ra_row in ra_materia.iterrows():
        codi_ra = ra_row["Codi RA"]
        descripcio_ra = ra_row["Resultado de aprendizaje"]
        classificacio = ra_row["Clasificación"]

        descripcio_curta = descripcio_ra[:100] + "..." if len(descripcio_ra) > 100 else descripcio_ra
        col1, col2 = st.columns([1, 20])

        with col1:
            is_selected = st.checkbox("", key=f"{assignatura}_{codi_ra}")
            if is_selected:
                seleccions_final.append({
                    "Professor/a": nom_professor,
                    "Assignatura": assignatura,
                    "Matèria": materia,
                    "Codi RA": codi_ra,
                    "Classificació": classificacio,
                    "Data_Selecció": datetime.datetime.now(zona_espanya).strftime("%Y-%m-%d %H:%M:%S")
                })

        with col2:
            with st.expander(f"{codi_ra} – {descripcio_curta} [{classificacio}]"):
                st.write(f"**Classificació:** {classificacio}")
                st.write(f"{descripcio_ra}")
    st.divider()

if seleccions_final:
    df_resultat = pd.DataFrame(seleccions_final)
    st.warning("Revisa la teva selecció i desa-la amb el botó de davall.")
    st.dataframe(df_resultat)

    if st.button("Desa les teves respostes"):
        if not nom_professor:
            st.error("Si us plau, introdueix el teu nom abans de desar.")
        else:
            success, message = save_to_gsheets(df_resultat, spreadsheet_id, nom_professor)
            if success:
                st.success(message)
            else:
                st.error(message)
