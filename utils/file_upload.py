import pandas as pd
import re
from utils.constants import REQUIRED_COLUMNS, C_CATEGORIA

DAYS_OF_WEEK = ["dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge"]

def is_day_column(col_name):
   normalized = re.sub(r"\s+", "", col_name.lower())
   return any(day in normalized for day in DAYS_OF_WEEK)

def load_player_data(uploaded_file):
   try:
      df_full = pd.read_excel(uploaded_file, header=0)

      # Drop completely empty rows early
      df_full = df_full.dropna(how='all')

      # Filter columns: REQUIRED_COLUMNS + columns that contain days of the week
      filtered_columns = [
         col for col in df_full.columns
         if col in REQUIRED_COLUMNS or is_day_column(col)
      ]
      df = df_full[filtered_columns].copy()

      # Check if the required columns are present
      if not REQUIRED_COLUMNS.issubset(df.columns):
         return None, None, f"L'Excel ha de contenir les columnes: {', '.join(REQUIRED_COLUMNS)}"

      # Separate the waitlist from the main dataframe
      waitlist_mask = df[C_CATEGORIA].str.contains("LLISTA D'ESPERA", case=False, na=False)
      df_waitlist = df[waitlist_mask].reset_index(drop=True)
      df = df[~waitlist_mask].reset_index(drop=True)

      return df, df_waitlist, None

   except Exception as e:
      return None, None, f"Error llegint el fitxer Excel: {e}"