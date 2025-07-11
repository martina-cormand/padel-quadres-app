import streamlit as st
import pandas as pd
from io import BytesIO
import random
from utils.file_upload import load_player_data
from utils.group_generator import assign_groups_by_category
from utils.excel_exporter import generate_excel_file
from utils.name_matcher import confirm_similar_names
from utils.constants import C_CATEGORIA
from utils.ui_helpers import display_loaded_data, select_courts_and_blocked_slots


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

         # Step 2: Select available courts
         st.header("2. Selecciona les pistes disponibles")
         num_courts, blocked_slots = select_courts_and_blocked_slots()
         st.session_state["num_courts"] = num_courts
         st.session_state["blocked_slots"] = blocked_slots

         # Step 3: Select number of groups per category
         st.header("3. Tria el nombre de grups per categoria")

         col_left, col_right = st.columns([1, 1])

         with col_left:
            categories = df[C_CATEGORIA].unique()
            category_groups = {}

            for cat in categories:
               count = df[df[C_CATEGORIA] == cat].shape[0]
               num = st.number_input(
                     f"Nombre de grups per a la categoria {cat} ({count} parelles)",
                     min_value=1,
                     max_value=count,
                     value=min(4, count),
                     key=f"num_groups_{cat}"
               )
               category_groups[cat] = int(num)

         # Step 4: Generate groups
         st.header("4. Quadres generats")
         all_groups_df = assign_groups_by_category(df, category_groups, st)

         # Step 5: Export and download
         st.header("5. Descarrega els quadres generats")
         excel_data = generate_excel_file(all_groups_df)
         st.download_button(
               label="📥 Descarrega els quadres com a Excel",
               data=excel_data,
               file_name="quadres_padel.xlsx",
               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
         )
   except Exception as e:
      st.error(f"Error reading Excel file: {e}")