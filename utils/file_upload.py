import pandas as pd
from constants import REQUIRED_COLUMNS

def load_player_data(uploaded_file):
   try:
      df = pd.read_excel(uploaded_file)
      if not REQUIRED_COLUMNS.issubset(df.columns):
         return None, f"L'Excel ha de contenir les columnes: {', '.join(REQUIRED_COLUMNS)}"
      return df, None
   except Exception as e:
      return None, f"Error llegint el fitxer Excel: {e}"