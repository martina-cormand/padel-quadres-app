import streamlit as st
import pandas as pd
from io import BytesIO
import random

st.title("🏓 Padel Tournament Group Generator (Excel Upload)")

# Step 1: Upload Excel file
st.header("1. Upload Player Excel File")

uploaded_file = st.file_uploader("Upload Excel (.xlsx) with Name and Availability", type="xlsx")

if uploaded_file:
   try:
      df = pd.read_excel(uploaded_file)
      if "Name" not in df.columns or "Availability" not in df.columns:
         st.error("Excel must contain 'Name' and 'Availability' columns.")
      else:
         st.success(f"{len(df)} players loaded.")
         st.dataframe(df)

         # Step 2: Select number of groups
         st.header("2. Choose Number of Groups")
         num_groups = st.number_input("Number of groups", min_value=1, max_value=len(df), value=2)

         # Shuffle and assign to groups
         players = df.to_dict(orient="records")
         random.shuffle(players)
         groups = [[] for _ in range(int(num_groups))]
         for i, player in enumerate(players):
            groups[i % int(num_groups)].append(player)

         # Step 3: Display and export groups
         st.header("3. Group Assignments")
         excel_data = BytesIO()
         writer = pd.ExcelWriter(excel_data, engine='openpyxl')

         for i, group in enumerate(groups):
            st.subheader(f"Group {i+1}")
            group_df = pd.DataFrame(group)
            st.table(group_df)
            group_df.to_excel(writer, sheet_name=f"Group {i+1}", index=False)

         writer.save()
         st.download_button(
               label="📥 Download Groups as Excel",
               data=excel_data.getvalue(),
               file_name="padel_groups.xlsx",
               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
         )
   except Exception as e:
      st.error(f"Error reading Excel file: {e}")