import pandas as pd
import streamlit as st
import re
import math
from utils.constants import C_CATEGORIA

DAYS_OF_WEEK = ["dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge"]

# Display player data
def display_loaded_data(df, df_waitlist):
   st.success(f"{len(df)} parelles llegides correctament.")
   categories = df[C_CATEGORIA].unique()

   for cat in categories:
      cat_df = df[df[C_CATEGORIA] == cat].drop(columns=[C_CATEGORIA])
      with st.expander(f"{cat} - {len(cat_df)} parelles"):
         st.dataframe(cat_df.reset_index(drop=True))

   if not df_waitlist.empty:
      st.warning(f"{len(df_waitlist)} parelles a la **llista d'espera**.")
      with st.expander("👀 Veure llista d'espera"):
         st.dataframe(df_waitlist)

def is_day_column(col_name):
   normalized = re.sub(r"\s+", "", col_name.lower())
   return any(day in normalized for day in DAYS_OF_WEEK)

def get_default_hours_for_day(day_name):
   day_name = day_name.lower()
   if "dissabte" in day_name or "diumenge" in day_name:
      return [f"{h:02d}:00" for h in range(9, 22)]  # 09:00 - 21:00
   else:
      return [f"{h:02d}:00" for h in range(16, 23)] # 16:00 - 22:00

# Select court availability for each day and hour
def select_court_availability(df):
   max_pistes = st.number_input("Nombre màxim de pistes disponibles al recinte", min_value=1, max_value=20, value=6)

   day_columns = [col for col in df.columns if is_day_column(col)]

   # Get all unique hours across all days
   all_hours = sorted({hour for day in day_columns for hour in get_default_hours_for_day(day)})

   # Create a DataFrame with default values
   data = {}
   for hour in all_hours:
      row = {}
      for day in day_columns:
         default_hours = get_default_hours_for_day(day)
         row[day] = max_pistes if hour in default_hours else 0
      data[hour] = row

   df_editor = pd.DataFrame.from_dict(data, orient="index")
   df_editor.index.name = "Hora"

   st.markdown("Introdueix el nombre de pistes disponibles per a cada franja horària:")

   row_height = 35
   total_height = row_height * (len(df_editor)+1) + 2

   edited_df = st.data_editor(
      df_editor,
      use_container_width=True,
      num_rows="fixed",
      height=total_height
   )

   # Convert edited DataFrame to the required format
   pistes_per_day_hour = {
      day: {
         hour: int(edited_df.loc[hour, day])
         for hour in edited_df.index
         if day in edited_df.columns
      }
      for day in edited_df.columns
   }

   return max_pistes, pistes_per_day_hour

# Select number of pairs per group for each category
def select_number_of_pairs_per_group(df):
   category_settings = {}
   categories = df[C_CATEGORIA].unique()
   error = None

   for cat in categories:
      count = df[df[C_CATEGORIA] == cat].shape[0]
      col1, col2 = st.columns([2, 3])

      # Display category header and input for pairs per group
      with col1:
         with st.container():
            st.markdown(
               f"""<div style="padding-top: 6px; padding-bottom: 2px;">
                  <strong>{cat}</strong> — {count} parelles
               </div>""",
               unsafe_allow_html=True
            )
            parelles_per_grup = st.number_input(
               "Parelles per grup:",
               min_value=2,
               max_value=count,
               value=4,
               step=1,
               key=f"ppg_{cat}"
            )

      num_grups = count // parelles_per_grup
      sobrants = count % parelles_per_grup

      # Display summary of groups and surplus pairs
      with col2:
         with st.container():
            if sobrants > 0:
               resumen = f"""<span style="color:#c20000;">
                  {num_grups} grup(s) de {parelles_per_grup} parelles
                  <span style="color:#c20000;"> + {sobrants} parella(es) sobrants</span>
               </span>"""
               error = (
                  "⚠️ No es pot continuar: hi ha categories amb parelles sobrants. Revisa les dades d'entrada o ajusta els nombres de parelles per grup."
               )
            else:
               resumen = f"""<span style="color:#1e8c3a; ">
                  {num_grups} grup(s) de {parelles_per_grup} parelles
               </span>"""
            st.markdown(
               f"""<div style="padding-top: 68px; font-size: 16px;"><strong>{resumen}</strong></div>""",
               unsafe_allow_html=True
            )

      st.markdown("""<div style="margin-top: 10px; margin-bottom: 10px; border-bottom: 1px solid #eee;"></div>""", unsafe_allow_html=True)

      # Store settings for this category
      category_settings[cat] = {
         'parelles_per_grup': parelles_per_grup,
         'num_grups': num_grups,
         'sobrants': sobrants
      }

   return category_settings, error

def show_remaining_court_availability(court_availability):
   st.subheader("📊 Disponibilitat restant de pistes per dia i hora")
   df_remaining = pd.DataFrame(court_availability).fillna(0).astype(int)
   # Ordena les hores correctament si són strings
   try:
      df_remaining.index = sorted(df_remaining.index, key=lambda x: int(str(x).split(":")[0]))
   except:
      df_remaining = df_remaining.sort_index()

   st.dataframe(df_remaining, use_container_width=True)