import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Configuració segura via secrets de Streamlit Cloud
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Seleccions_RA_professors").sheet1

# Carregar dades locals
ra_data = pd.read_excel("Plantilla_RA_per_Materia_Ordenada.xlsx")
assignatures_data = pd.read_excel("Assignatures_per_Materia.xlsx")

st.title("Selecció de Resultats d'Aprenentatge per Professor/a")

# Selecció d'assignatures
st.header("1. Selecciona les assignatures que són responsabilitat teva")
assignatures_disponibles = assignatures_data["Assignatura"].unique()
assignatures_seleccionades = st.multiselect("Assignatures:", assignatures_disponibles)

# Processar seleccions
if assignatures_seleccionades:
    seleccions_final = []

    for assignatura in assignatures_seleccionades:
        materia = assignatures_data[assignatures_data["Assignatura"] == assignatura]["Matèria"].values[0]
        ra_materia = ra_data[ra_data["Matèria"] == materia][["Codi RA", "Resultado de aprendizaje"]]

        st.subheader(f"RA per a '{assignatura}' ({materia})")

        for index, row in ra_materia.iterrows():
            checked = st.checkbox(f"[{row['Codi RA']}] {row['Resultado de aprendizaje']}", key=f"{assignatura}_{row['Codi RA']}")
            if checked:
                seleccions_final.append({
                    "Assignatura": assignatura,
                    "Matèria": materia,
                    "Codi RA": row["Codi RA"]
                })

    if seleccions_final:
        df_resultat = pd.DataFrame(seleccions_final)
        st.success("Seleccions enregistrades correctament!")

        # Mostrar dades
        st.dataframe(df_resultat)

        # Escriure a Google Sheets
        for _, fila in df_resultat.iterrows():
            sheet.append_row([fila["Assignatura"], fila["Matèria"], fila["Codi RA"]])

        st.info("Les teves seleccions s'han desat al full de càlcul de Google.")
