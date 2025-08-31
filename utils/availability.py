from collections import defaultdict
import pandas as pd
from utils.constants import C_JUGADOR_1, C_JUGADOR_2
from utils.file_upload import is_day_column

# Creates a dictionary mapping each player to their available (day, hour) slots.
def build_player_availability(df):
   availability = defaultdict(set)
   day_columns = [col for col in df.columns if is_day_column(col)]

   for _, row in df.iterrows():
      for day in day_columns:
         cell = str(row[day]) if not pd.isna(row[day]) else ""
         hours = [h.strip() for h in cell.split(",") if h.strip()]
         for hour in hours:
               p1 = str(row[C_JUGADOR_1]).strip().lower()
               p2 = str(row[C_JUGADOR_2]).strip().lower()
               availability[p1].add((day, hour))
               availability[p2].add((day, hour))
   return availability