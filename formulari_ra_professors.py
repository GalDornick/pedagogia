import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import datetime
import json
from pytz import timezone
zona_espanya = timezone("Europe/Madrid")

# Configurar l'accés a Google Sheets
@st.cache_resource
def setup_gsheets_connection():
    # Intentar diferentes formas de acceder a las credenciales
    try:
        # Opción 1: Las credenciales están en un diccionario anidado llamado "gcp_service_account"
        credentials_dict = st.secrets["gcp_service_account"]
    except KeyError:
        try:
            # Opción 2: Las credenciales están en el nivel superior de st.secrets
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
            # Si no se pueden obtener las credenciales, mostrar un mensaje de error explicativo
            st.error("""
            No s'han trobat les credencials per connectar amb Google Sheets. 
            Si us plau, configura els secrets a Streamlit Cloud amb les credencials del compte de servei de Google.
            """)
            st.info("""
            Per a fer-ho:
            1. Vés a "Manage app" a la cantonada inferior dreta
            2. Selecciona "Secrets"
            3. Afegeix les credencials del teu compte de servei
            """)
            st.stop()
    
    # Crear credenciales con los valores obtenidos
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
    )
    client = gspread.authorize(credentials)
    return client

# Funció per desar a Google Sheets
def save_to_gsheets(dataframe, spreadsheet_id, nom_professor):
    client = setup_gsheets_connection()
    
    try:
        # Obrir el full de càlcul pel seu ID
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Crear un nou full amb el nom del professor i la data
        data_actual = datetime.datetime.now(zona_espanya).strftime("%Y-%m-%d_%H-%M")
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
        
        return True, f"Dades desades correctament. Moltes gràcies!"
    except Exception as e:
        return False, f"Error en desar les dades: {str(e)}"

# Carregar les dades de RA per matèria (simulades)
try:
    ra_data = pd.read_excel("Plantilla_RA_per_Materia_Ordenada.xlsx")
    assignatures_data = pd.read_excel("Assignatures_per_Materia.xlsx")
except Exception as e:
    st.error(f"Error al carregar els arxius Excel: {str(e)}")
    st.stop()

st.title("Grau de Pedagogia UIB. Selecció de Resultats d'Aprenentatge per assignatura")

# Demanar el nom del professor/a
nom_professor = st.text_input("Per favor, indica el teu nom i cognoms:")

# ID del full de càlcul de Google Sheets
spreadsheet_id = "1ct5-tRmChvJUHU8Bjburrm2gmgS8in6b3roshjt0v1k"

# Pas 1: Selecció de les assignatures del professor/a
st.header("1. Selecciona les assignatures que són responsabilitat teva")
st.info("El nom de les assignatures apareix en castellà per minimitzar inconsistències amb la memòria verificada.")
assignatures_disponibles = assignatures_data["Assignatura"].unique()
assignatures_seleccionades = st.multiselect("Assignatures:", assignatures_disponibles)

# Crear un diccionari per desar les seleccions
seleccions_final = []

# Per cada assignatura seleccionada, mostrar els RA de la seva matèria
for assignatura in assignatures_seleccionades:
    materia = assignatures_data[assignatures_data["Assignatura"] == assignatura]["Matèria"].values[0]
    ra_materia = ra_data[ra_data["Matèria"] == materia][["Codi RA", "Resultado de aprendizaje", "Clasificación"]]

    st.header(f"2. RA per a l'assignatura: {assignatura} ({materia})")
    st.write("A la llista següent apareixen els Resultats d'Aprenentatge (RA) de la matèria a la qual pertany l'assignatura seleccionada. Per favor, selecciona els RA que treballes en aquesta assignatura en concret:")
    
    # Afegir una nota sobre com veure els RA complets
    st.info("🔍 Si necessites veure la descripció completa d'un RA, fes clic a la fletxa per expandir el seu contingut (mantenim els RA en castellà per minimitzar inconsistències amb la memòria verificada).")
    
    # Per cada RA
    for _, ra_row in ra_materia.iterrows():
        codi_ra = ra_row["Codi RA"]
        descripcio_ra = ra_row["Resultado de aprendizaje"]
        
        # Retallar la descripció si és massa llarga
        descripcio_curta = descripcio_ra[:100] + "..." if len(descripcio_ra) > 100 else descripcio_ra
        
        # Columnes per la checkbox i l'expander
        col1, col2 = st.columns([1, 20])
        
        # Checkbox a la primera columna
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
        
        # Expander a la segona columna
        with col2:
            with st.expander(f"{codi_ra} – {descripcio_curta} [{classificacio}]"):
                st.write(f"**Classificació:** {classificacio}")
                st.write(f"{descripcio_ra}")
    
    # Afegir una línia separadora entre assignatures
    st.divider()

# Mostrar i descarregar resultat
if seleccions_final:
    df_resultat = pd.DataFrame(seleccions_final)
    st.warning("Per favor, revisa la teva selecció i no oblidis desar-la amb el botó de davall de tot")
    st.dataframe(df_resultat)
    
    # Botó per desar a Google Sheets
    if st.button("Desa les teves respostes"):
        if not nom_professor:
            st.error("Si us plau, introdueix el teu nom abans de desar.")
        else:
            success, message = save_to_gsheets(df_resultat, spreadsheet_id, nom_professor)
            if success:
                st.success(message)
            else:
                st.error(message)
