import streamlit as st
import pandas as pd
from io import BytesIO
import random

# ---- Logo ----
st.image("logo.png", width=150)  # local file in the same folders

st.title("Generador de quadres Atres Pàdel")

# Step 1: Upload Excel file
st.header("1. Penja el fitxer Excel de jugadors")

uploaded_file = st.file_uploader("Penja un Excel (.xlsx) amb la informació dels jugadors i la disponibiliitat", type="xlsx")

if uploaded_file:
   try:
      df = pd.read_excel(uploaded_file)
      if "Name" not in df.columns or "Availability" not in df.columns:
         st.error("L'Excel ha de contenir les columnes 'Name' i 'Availability's.")
      else:
         st.success(f"{len(df)} jugadors apuntats.")
         st.dataframe(df)

         # Step 2: Select number of groups
         st.header("2. Tria el nombre de grups per categoria")
         num_groups = st.number_input("Nombre de grups", min_value=1, max_value=len(df), value=4)

         # Shuffle and assign to groups
         players = df.to_dict(orient="records")
         random.shuffle(players)
         groups = [[] for _ in range(int(num_groups))]
         for i, player in enumerate(players):
            groups[i % int(num_groups)].append(player)

         # Step 3: Display and export groups
         st.header("3. Quadres generats")
         excel_data = BytesIO()
         writer = pd.ExcelWriter(excel_data, engine='openpyxl')

         for i, group in enumerate(groups):
            st.subheader(f"Grup {i+1}")
            group_df = pd.DataFrame(group)
            st.table(group_df)
            group_df.to_excel(writer, sheet_name=f"Group {i+1}", index=False)

         writer.save()
         st.download_button(
            label="📥 Descarrega els quadres com a Excel",
            data=excel_data.getvalue(),
            file_name="padel_groups.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
         )
   except Exception as e:
      st.error(f"Error reading Excel file: {e}")