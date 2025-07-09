from io import BytesIO
import pandas as pd

def generate_excel_file(df):
   excel_data = BytesIO()
   with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
      df.to_excel(writer, sheet_name="Tots els grups", index=False)
   return excel_data.getvalue()