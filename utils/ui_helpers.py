import streamlit as st
from utils.constants import C_CATEGORIA

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


def select_courts_and_blocked_slots():
   """
   Muestra los inputs de selección de pistas y franjas horarias bloqueadas,
   diferenciando entre fin de semana y entre semana.
   
   Retorna:
      num_courts (int): número total de pistas
      blocked_slots (dict): diccionario con bloqueos por pista
   """
   st.header("2. Selecciona les pistes disponibles")

   # Número total de pistas
   num_courts = st.number_input(
      "Nombre total de pistes disponibles",
      min_value=1,
      max_value=20,
      value=4,
      step=1
   )

   st.subheader("Bloqueig de pistes en hores determinades")

   # Horarios disponibles
   time_slots_weekend = [f"{h:02d}:00" for h in range(9, 22)]      # 9:00 - 21:00
   time_slots_weekday = [f"{h:02d}:00" for h in range(16, 23)]     # 16:00 - 22:00

   blocked_slots = {}

   for i in range(num_courts):
      court_name = f"Pista {i+1}"
      st.markdown(f"**{court_name}**")

      col1, col2 = st.columns([1, 2])
      with col1:
         days = st.radio(
               f"Selecciona el tipus de dia per bloquejar la {court_name}",
               options=["Cap de setmana", "Entre setmana"],
               key=f"day_type_{i}"
         )

      with col2:
         if days == "Cap de setmana":
               time_options = time_slots_weekend
         else:
               time_options = time_slots_weekday

         blocked = st.multiselect(
               f"Selecciona les hores en què la {court_name} estarà bloquejada",
               time_options,
               key=f"blocked_{i}"
         )
      
      blocked_slots[court_name] = blocked

   return num_courts, blocked_slots