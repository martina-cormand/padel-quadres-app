from rapidfuzz import fuzz
import pandas as pd
import streamlit as st
import unicodedata

def normalize_name(name):
   name = str(name).strip().lower()
   name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
   return name

def find_similar_names(player_names, threshold=85):
   """Returns list of (name1, name2, score) for similar names."""
   normalized = {name: normalize_name(name) for name in player_names}
   matches = []
   checked = set()

   names = list(player_names)
   for i, name1 in enumerate(names):
      for name2 in names[i+1:]:
         pair = tuple(sorted((name1, name2)))
         if pair in checked:
               continue
         score = fuzz.ratio(normalized[name1], normalized[name2])
         if score >= threshold and name1 != name2:
               matches.append((name1, name2, score))
         checked.add(pair)
   return matches

def confirm_similar_names(df, threshold=85):
   """Handles similarity confirmation for Jugador 1 and Jugador 2."""

   all_names = pd.concat([df["Jugador 1"], df["Jugador 2"]]).dropna().unique()
   similar_pairs = find_similar_names(all_names, threshold)
   mapping = {}

   if not similar_pairs:
      st.success("✅ No s'han trobat noms similars.")
      return {name: name for name in all_names}

   for i, (n1, n2, score) in enumerate(similar_pairs):
      st.write(f"🎯 **Coincidència {i+1}:** `{n1}` ↔ `{n2}` ({score}%)")
      choice = st.radio(
         f"Es tracta de la mateixa persona?",
         ["Sí", "No"],
         key=f"match_{i}"
      )
      if choice == "Sí":
         canonical = n1
         mapping[n2] = canonical
         mapping[n1] = canonical
      else:
         mapping[n1] = n1
         mapping[n2] = n2

   # Ensure every player has a mapped name
   for name in all_names:
      if name not in mapping:
         mapping[name] = name

   return mapping