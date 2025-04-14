import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import datetime
import random
from pytz import timezone
zona_espanya = timezone("Europe/Madrid")

# Configurar l'accés a Google Sheets
@st.cache_resource
def setup_gsheets_connection():
    """Estableix la connexió amb Google Sheets utilitzant les credencials a st.secrets"""
    try:
        # Opció 1: Les credencials estan en un diccionari anidado llamado "gcp_service_account"
        credentials_dict = st.secrets["gcp_service_account"]
    except KeyError:
        try:
            # Opció 2: Les credencials estan al nivell superior de st.secrets
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
            # Si no es poden obtenir les credencials, mostrar un missatge d'error explicatiu
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
            return None
    
    try:
        # Crear credencials amb els valors obtinguts
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Error en establir connexió amb Google: {str(e)}")
        return None

# Funció per desar a Google Sheets (tant al full individual com al resum)
def save_to_gsheets(dataframe, spreadsheet_id, nom_professor):
    """
    Desa el dataframe a un nou full al Google Sheet especificat 
    i també actualitza el full de resum (primera fulla)
    """
    client = setup_gsheets_connection()
    
    if client is None:
        return False, "No s'ha pogut establir connexió amb Google Sheets"
    
    try:
        # Obrir el full de càlcul pel seu ID
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # 1. Crear un nou full amb el nom del professor i la data
        data_actual = datetime.datetime.now(zona_espanya).strftime("%Y-%m-%d_%H-%M")
        nom_full = f"{nom_professor}_{data_actual}"
        
        # Comprovar si ja existeix un full amb el mateix nom
        try:
            worksheet = spreadsheet.add_worksheet(title=nom_full, rows=len(dataframe) + 1, cols=dataframe.shape[1])
        except gspread.exceptions.APIError:
            # Si ja existeix, afegeix un número aleatori
            nom_full = f"{nom_professor}_{data_actual}_{random.randint(1, 1000)}"
            worksheet = spreadsheet.add_worksheet(title=nom_full, rows=len(dataframe) + 1, cols=dataframe.shape[1])
        
        # Afegir les capçaleres i dades al full individual
        worksheet.update([dataframe.columns.tolist()] + dataframe.values.tolist())
        
        # 2. Actualitzar el full de resum (primera fulla)
        try:
            # Obtenir el primer full (resum)
            summary_sheet = spreadsheet.get_worksheet(0)
            
            # Obtenir les dades actuals del full de resum
            existing_data = summary_sheet.get_all_values()
            
            # Si el full està buit, afegir les capçaleres
            if not existing_data:
                summary_sheet.update([dataframe.columns.tolist()] + dataframe.values.tolist())
            else:
                # Si ja hi ha dades, afegir només les noves files (sense les capçaleres)
                # Determinar la primera fila buida
                next_row = len(existing_data) + 1
                
                # Comprovar si les capçaleres coincideixen
                headers = existing_data[0]
                df_headers = dataframe.columns.tolist()
                
                if headers != df_headers:
                    st.warning(f"Les capçaleres del full de resum no coincideixen amb les dades actuals. Es mantindran les capçaleres existents.")
                
                # Afegir les noves files a partir de la primera fila buida
                if dataframe.values.tolist():  # Comprovar si hi ha files per afegir
                    cell_range = f'A{next_row}'
                    summary_sheet.update(cell_range, dataframe.values.tolist())
                
        except Exception as e:
            return False, f"S'han desat les dades al full individual, però ha fallat l'actualització del resum: {str(e)}"
        
        return True, f"Dades desades correctament. Moltes gràcies!"
    except Exception as e:
        return False, f"Error en desar les dades: {str(e)}"

# Funció per carregar dades d'Excel
@st.cache_data
def carregar_dades():
    """Carrega les dades dels arxius Excel"""
    try:
        ra_data = pd.read_excel("Plantilla_RA_per_Materia_Ordenada.xlsx")
        assignatures_data = pd.read_excel("Assignatures_per_Materia.xlsx")
        return ra_data, assignatures_data
    except Exception as e:
        st.error(f"Error al carregar els arxius Excel: {str(e)}")
        return None, None

def main():
    """Funció principal de l'aplicació"""
    st.title("Grau de Pedagogia UIB. Selecció de Resultats d'Aprenentatge per assignatura")
    
    # Carregar les dades
    ra_data, assignatures_data = carregar_dades()
    if ra_data is None or assignatures_data is None:
        st.stop()
    
    # ID del full de càlcul de Google Sheets
    spreadsheet_id = "1ct5-tRmChvJUHU8Bjburrm2gmgS8in6b3roshjt0v1k"
    
    # Demanar el nom del professor/a
    nom_professor = st.text_input("Per favor, indica el teu nom i cognoms:")
    
    # Pas 1: Selecció de les assignatures del professor/a
    st.header("1. Selecciona les assignatures que són responsabilitat teva")
    st.info("El nom de les assignatures apareix en castellà per minimitzar inconsistències amb la memòria verificada.")
    
    # Comprovar si hi ha assignatures disponibles
    if 'Assignatura' not in assignatures_data.columns:
        st.error("El format del fitxer d'assignatures no és correcte. Revisa que tingui una columna anomenada 'Assignatura'.")
        st.stop()
        
    assignatures_disponibles = assignatures_data["Assignatura"].unique()
    assignatures_seleccionades = st.multiselect("Assignatures:", assignatures_disponibles)
    
    # Crear una llista per desar les seleccions
    seleccions_final = []
    
    # Per cada assignatura seleccionada, mostrar els RA de la seva matèria
    for assignatura in assignatures_seleccionades:
        try:
            materia = assignatures_data[assignatures_data["Assignatura"] == assignatura]["Matèria"].values[0]
            ra_materia = ra_data[ra_data["Matèria"] == materia][["Codi RA", "Resultado de aprendizaje", "Clasificación"]]
        except Exception as e:
            st.error(f"Error en recuperar la informació per a l'assignatura {assignatura}: {str(e)}")
            continue
        
        st.header(f"2. RA per a l'assignatura: {assignatura} ({materia})")
        st.write("A la llista següent apareixen els Resultats d'Aprenentatge (RA) de la matèria a la qual pertany l'assignatura seleccionada. Per favor, selecciona els RA que treballes en aquesta assignatura en concret:")
        
        # Afegir una nota sobre com veure els RA complets
        st.info("🔍 Si necessites veure la descripció completa d'un RA, fes clic a la fletxa per expandir el seu contingut (mantenim els RA en castellà per minimitzar inconsistències amb la memòria verificada).")
        
        # Per cada RA
        for _, ra_row in ra_materia.iterrows():
            codi_ra = ra_row["Codi RA"]
            descripcio_ra = ra_row["Resultado de aprendizaje"]
            classificacio = ra_row["Clasificación"]  # Correcció: Ara obtenim correctament la classificació
            
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
                        "Clasificación": classificacio,  # Ara utilitzem la variable correcta
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
    elif assignatures_seleccionades:
        st.warning("No has seleccionat cap RA. Si us plau, marca les caselles dels RA que treballes a les teves assignatures.")

if __name__ == "__main__":
    main()
