import pandas as pd
import random

def assign_groups_by_category(df, category_groups, st=None):
   all_groups_df = pd.DataFrame()

   for cat in category_groups:
      cat_df = df[df["Categoria"] == cat]
      players = cat_df.to_dict(orient="records")
      random.shuffle(players)

      num_groups = category_groups[cat]
      groups = [[] for _ in range(num_groups)]
      for i, player in enumerate(players):
         groups[i % num_groups].append(player)

      if st:
         st.subheader(f"{cat}")
      for i, group in enumerate(groups):
         if st:
               st.markdown(f"**Grup {i+1}**")
         group_df = pd.DataFrame(group).drop(columns=["Categoria"])
         if st:
               st.table(group_df)

         group_df.insert(0, "Grup", f"Grup {i+1}")
         if "Categoria" not in group_df.columns:
               group_df.insert(1, "Categoria", cat)
         spacer = pd.DataFrame([[""] * len(group_df.columns)], columns=group_df.columns)
         all_groups_df = pd.concat([all_groups_df, group_df, spacer], ignore_index=True)

   return all_groups_df