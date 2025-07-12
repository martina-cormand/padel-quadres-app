import pandas as pd
import random
from utils.constants import REQUIRED_COLUMNS, C_CATEGORIA, C_JUGADOR_1, C_JUGADOR_2
from collections import defaultdict
import random

# ========== STRUCTURES ==========
class Match:
   def __init__(self, pair1, pair2, category, group_id=None):
      self.pair1 = pair1
      self.pair2 = pair2
      self.category = category
      self.day = None
      self.hour = None
      self.group_id = group_id

# ========== UTILS ==========

def extract_players_by_category(df):
   categories = df[C_CATEGORIA].unique()
   data = {}
   for cat in categories:
      subset = df[df[C_CATEGORIA] == cat]
      data[cat] = list(zip(subset[C_JUGADOR_1], subset[C_JUGADOR_2]))
   return data

def generate_round_robin(pairs):
   matches = []
   for i in range(len(pairs)):
      for j in range(i + 1, len(pairs)):
         matches.append((pairs[i], pairs[j]))
   return matches

def get_player_name_set(pair):
   return {pair[0].strip().lower(), pair[1].strip().lower()}

def has_schedule_conflict(player_matches, day, hour):
   return any((d == day and h == hour) for (d, h) in player_matches)

def played_too_much(player_matches, day):
   return sum(1 for d, _ in player_matches if d == day) >= 3

def overnight_conflict(player_matches, day, hour, all_hours):
   '''if hour == min(all_hours):  # first hour of the day
      prev_day_matches = [h for d, h in player_matches if d == day - 1]
      return max(prev_day_matches, default=None) == max(all_hours)
   elif hour == max(all_hours):  # last hour
      next_day_matches = [h for d, h in player_matches if d == day + 1]
      return min(next_day_matches, default=None) == min(all_hours)'''
   return False

def build_player_availability(df):
   availability = defaultdict(set)  # {player_name: set((day, hour))}
   day_columns = [col for col in df.columns if is_day_column(col)]

   for _, row in df.iterrows():
      for day in day_columns:
         hours = str(row[day]) if not pd.isna(row[day]) else ""
         split_hours = [h.strip() for h in hours.split(",") if h.strip()]
         for hour in split_hours:
            p1 = str(row[C_JUGADOR_1]).strip().lower()
            p2 = str(row[C_JUGADOR_2]).strip().lower()
            availability[p1].add((day, hour))
            availability[p2].add((day, hour))

   return availability

def all_players_available(players, day, hour, availability):
   return all((day, hour) in availability.get(player, set()) for player in players)

# ========== MAIN SCHEDULER ==========

def schedule_matches(df, category_groups, court_availability):
   players_by_category = extract_players_by_category(df)
   scheduled_matches = []
   player_schedule = defaultdict(list)
   all_hours = sorted({hour for day_hours in court_availability.values() for hour in day_hours})
   player_availability = build_player_availability(df)

   all_matches = []

   # Primero generamos todos los partidos de todos los grupos y categorías
   for category, group_settings in category_groups.items():
      num_groups = group_settings["num_grups"]
      pairs = players_by_category[category]
      group_size = len(pairs) // num_groups
      random.shuffle(pairs)
      groupings = [pairs[i:i + group_size] for i in range(0, len(pairs), group_size)]

      for group_index, group in enumerate(groupings):
         raw_matches = generate_round_robin(group)
         for pair1, pair2 in raw_matches:
               match = Match(pair1, pair2, category, group_id=group_index + 1)
               all_matches.append(match)

   # Aleatorizamos el orden de los partidos antes de asignarlos a horas
   random.shuffle(all_matches)

   # Ahora intentamos agendar todos los partidos aleatorizados
   for match in all_matches:
      scheduled = False
      for day in court_availability:
         for hour in court_availability[day]:
               courts = court_availability[day][hour]
               if courts <= 0:
                  continue

               all_players = get_player_name_set(match.pair1) | get_player_name_set(match.pair2)

               if any(has_schedule_conflict(player_schedule[p], day, hour) for p in all_players):
                  continue
               if any(played_too_much(player_schedule[p], day) for p in all_players):
                  continue
               if any(overnight_conflict(player_schedule[p], day, hour, all_hours) for p in all_players):
                  continue
               if not all_players_available(all_players, day, hour, player_availability):
                  continue

               match.day = day
               match.hour = hour
               scheduled_matches.append(match)

               for p in all_players:
                  player_schedule[p].append((day, hour))

               court_availability[day][hour] -= 1
               scheduled = True
               break
         if scheduled:
               break

      if not scheduled:
         print(f"⚠️ Couldn't schedule match: {match.pair1} vs {match.pair2} in {match.category}")

   return scheduled_matches