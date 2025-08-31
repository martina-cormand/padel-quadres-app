import streamlit as st
import pandas as pd
from io import BytesIO
import random
from utils.file_upload import load_player_data
from utils.group_generator import schedule_matches
from utils.excel_exporter import generate_excel_file
from utils.name_matcher import confirm_similar_names
from utils.constants import C_CATEGORIA
from utils.ui_helpers import display_loaded_data, select_court_availability, select_number_of_pairs_per_group, show_remaining_court_availability
from utils.availability import build_player_availability

st.set_page_config(page_title="Generador de quadres", layout="wide")

col1, col5 = st.columns([12, 1])
with col5:
   st.image("logo.png", width=100)

with col1:
   st.title("Generador de quadres Atres Pàdel")

# Step 1: Upload Excel file
st.header("1. Penja el fitxer Excel de jugadors")

uploaded_file = st.file_uploader("Penja un Excel (.xlsx) amb la informació dels jugadors i la seva disponibiliitat", type="xlsx")

if uploaded_file:
   try:
      df, df_waitlist, error = load_player_data(uploaded_file)
      if error:
         st.error(error)
      else:
         display_loaded_data(df, df_waitlist)

         # Step 2: Select number of pairs per group for each category
         st.header("2. Tria la mida dels grups per categoria")
         category_groups, error = select_number_of_pairs_per_group(df)

         if error:
            st.error(error)
         else:
            # Step 3: Select available courts
            st.header("3. Disponibilitat de pistes per dia i hora")
            max_pistes, pistes_per_day_hour = select_court_availability(df)
            st.session_state["max_pistes"] = max_pistes
            st.session_state["pistes_per_day_hour"] = pistes_per_day_hour

            # Step 4: Generate groups
            st.header("3. Genera els quadres de partits")
            if st.button("Genera els quadres"):
               with st.spinner("Generant quadres..."):
                  court_availability = st.session_state["pistes_per_day_hour"]
                  player_availability = build_player_availability(df)
                  scheduled_matches = schedule_matches(df, category_groups, court_availability, player_availability)

                  if not scheduled_matches:
                     st.warning("No s'han pogut generar partits amb la configuració actual.")
                  else:
                     st.success("Quadres generats correctament!")

                     # Mostrar els quadres
                     st.subheader("Quadres generats")
                     match_data = [{
                           "Categoria": match.category,
                           "Grup": match.group_id,
                           "Jugador/a 1": match.pair1[0],
                           "Jugador/a 2": match.pair1[1],
                           "Contrincant 1": match.pair2[0],
                           "Contrincant 2": match.pair2[1],
                           "Dia": match.day,
                           "Hora": match.hour,
                     } for match in scheduled_matches]

                     df_matches = pd.DataFrame(match_data)
                     st.dataframe(df_matches)

                     # show_remaining_court_availability(court_availability)

                     # Botó per descarregar l'Excel
                     try:
                        excel_bytes = generate_excel_file(scheduled_matches)
                        st.download_button(
                           label="📥 Descarrega l'Excel dels quadres",
                           data=excel_bytes,
                           file_name="quadres_atres_padel.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True
                        )
                     except Exception as e:
                        st.warning(f"No s'ha pogut generar l'Excel: {e}")
                     
   except Exception as e:
      st.error(f"Error reading Excel file: {e}")