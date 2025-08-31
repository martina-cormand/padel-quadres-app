import pandas as pd
from io import BytesIO
from collections import defaultdict

# Espera una lista de objetos `match` con atributos:
# - category, group_id, pair1(str), pair2(str), day(str), hour(str)

def _pair_label(pair: tuple[str, str]) -> str:
   # Returns "Gerard Boladeras / Rachid Abougeib"
   return f"{pair[0]} / {pair[1]}"

def fill_background(ws, fmt, max_rows=300, max_cols=40):
   # Paint a big area with the page background.
   # Later writes will overwrite these blanks (both value and format).
   for r in range(max_rows + 1):
      for c in range(max_cols + 1):
         ws.write_blank(r, c, None, fmt)

def generate_excel_file(scheduled_matches):
   # Estructura: { category: { group_id: [matches...] } }
   by_cat_group = defaultdict(lambda: defaultdict(list))
   for m in scheduled_matches:
      by_cat_group[m.category][m.group_id].append(m)

   output = BytesIO()
   with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
      wb = writer.book

      # ======= PALETA Y FORMATOS =======
      COLOR_BG_PAGE   = "#F3CFCF"  # fondo hoja
      COLOR_CYAN      = "#62F6FF"  # turquesa
      COLOR_HEADER    = "#D9D9D9"  # gris cabecera
      COLOR_GRID      = "#D56F76"  # rosa salmón matriz
      COLOR_MATCH     = "#FFFFFF"  # partido

      fmt_title = wb.add_format({"bold": True, "font_size": 30,
                                 "align": "center", "valign": "vcenter"})
      fmt_subtitle = wb.add_format({"bold": True, "font_size": 18,
                                    "align": "center", "valign": "vcenter"})
      # fondo hoja
      fmt_bg_page = wb.add_format({"bg_color": COLOR_BG_PAGE})

      # cabeceras
      fmt_corner = wb.add_format({"bg_color": COLOR_CYAN, "border": 1})
      fmt_header = wb.add_format({"bg_color": COLOR_HEADER, "bold": True,
                                 "align": "center", "valign": "vcenter",
                                 "border": 1})
      fmt_name_col = wb.add_format({"bg_color": COLOR_HEADER, "bold": True,
                                    "align": "left", "valign": "vcenter",
                                    "border": 1})
      # matriz y partidos
      fmt_cell  = wb.add_format({"bg_color": COLOR_GRID, "border": 1})
      fmt_match = wb.add_format({"bg_color": COLOR_MATCH, "border": 1,
                                 "align": "center", "valign": "vcenter"})
      fmt_diag  = wb.add_format({"bg_color": COLOR_GRID, "border": 1})

      for category, groups in by_cat_group.items():
         # Una hoja por categoría
         sheet_name = str(category)[:31]  # límite Excel
         ws = wb.add_worksheet(sheet_name)

         # Fondo de página (rango amplio)
         fill_background(ws, fmt_bg_page, max_rows=300, max_cols=40)

         # Título y subtítulo
         ws.merge_range(0, 0, 2, 10, str(category).upper(), fmt_title)
         ws.merge_range(3, 0, 4, 10, "FASE PRÈVIA", fmt_subtitle)

         current_row = 6  # desde aquí empezamos a pintar grupos

         # Ordenamos por id de grupo de forma natural
         for group_id in sorted(groups.keys()):
               matches = groups[group_id]

               # 1) sacamos todas las parejas del grupo en un orden estable
               pairs = []
               seen = set()
               for m in matches:
                  for p in (m.pair1, m.pair2):
                     if p not in seen:
                           seen.add(p)
                           pairs.append(p)

               pair_labels = [_pair_label(p) for p in pairs]
               n = len(pairs)

               # 2) cabecera del bloque del grupo
               # Banda lateral turquesa con el nombre del primer equipo
               # y cabeceras horizontales de cada pareja
               # Altura y anchos agradables
               ws.set_row(current_row, 6)  # separador fino
               current_row += 1

               # Cabecera superior (columna A en turquesa vacía y luego nombres)
               ws.write(current_row, 0, "", fmt_corner)  # celda esquina turquesa
               for j, lbl in enumerate(pair_labels, start=1):
                  ws.write(current_row, j, lbl, fmt_header)
                  ws.set_column(j, j, max(20, len(lbl) + 2))
               ws.set_column(0, 0, 28)  # col de nombres
               current_row += 1

               # 3) matriz NxN. Primera columna con nombres en turquesa
               # Prellenamos con rosa
               for i, row_lbl in enumerate(pair_labels, start=0):
                  ws.write(current_row + i, 0, row_lbl, fmt_name_col)
                  for j in range(1, n + 1):
                     ws.write(current_row + i, j, "", fmt_cell)

               # 4) metemos los partidos (solo mitad superior o inferior; pintaremos simétrico)
               # Creamos un mapa rápido de índice de pareja
               idx = {pairs[k]: k for k in range(n)}

               for m in matches:
                  i = idx[m.pair1]
                  j = idx[m.pair2]
                  text = f"{m.day} - {m.hour}" if (m.day or m.hour) else ""
                  # Ponemos en [min,max] para que quede una sola celda (por si quieres triangular)
                  r = min(i, j)
                  c = max(i, j)
                  # Escribimos el encuentro
                  ws.write(current_row + r, 1 + c, text, fmt_match)

               # 5) diagonal vacía (sin partidos de sí mismo)
               for d in range(n):
                  ws.write(current_row + d, 1 + d, "", fmt_diag)

               # 6) espacio entre grupos
               current_row += n + 3

      # Guardamos
   output.seek(0)
   return output.getvalue()