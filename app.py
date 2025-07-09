import streamlit as st
import pandas as pd
from io import BytesIO
import random
from utils.file_upload import load_player_data
from utils.group_generator import assign_groups_by_category
from utils.excel_exporter import generate_excel_file
from utils.name_matcher import confirm_similar_names

col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
with col3:
   st.image("logo.png", width=150)

st.title("Generador de quadres Atres Pàdel")

# Step 1: Upload Excel file
st.header("1. Penja el fitxer Excel de jugadors")

uploaded_file = st.file_uploader("Penja un Excel (.xlsx) amb la informació dels jugadors i la seva disponibiliitat", type="xlsx")

if uploaded_file:
   try:
      df, error = load_player_data(uploaded_file)
      if error:
         st.error(error)
      else:
         st.success(f"{len(df)} parelles llegides correctament.")
         categories = df["Categoria"].unique()

         #  Step 2: Detect and confirm similar names
         st.header("2. Detecta jugadors en diferents categories")
         name_mapping = confirm_similar_names(df)
         df["Jugador 1"] = df["Jugador 1"].map(name_mapping)
         df["Jugador 2"] = df["Jugador 2"].map(name_mapping)

         for cat in categories:
            cat_df = df[df["Categoria"] == cat].drop(columns=["Categoria"])
            with st.expander(f"{cat} - {len(cat_df)} parelles"):
               st.dataframe(cat_df.reset_index(drop=True))

         # Step 3: Select number of groups per category
         st.header("3. Tria el nombre de grups per categoria")

         categories = df["Categoria"].unique()
         category_groups = {}

         for cat in categories:
               count = df[df["Categoria"] == cat].shape[0]
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