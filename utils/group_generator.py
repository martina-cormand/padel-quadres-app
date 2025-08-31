"""import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from utils.constants import REQUIRED_COLUMNS, C_CATEGORIA, C_JUGADOR_1, C_JUGADOR_2, MAX_PLANNING_ATTEMPTS

# ----------------------------
# Estructura para los partidos
# ----------------------------
class Match:
   def __init__(self, pair1, pair2, category, group_id=None):
      self.pair1 = pair1
      self.pair2 = pair2
      self.category = category
      self.day = None
      self.hour = None
      self.group_id = group_id
      self.possible_slots = None
      self.current_available_slots = None

# ----------------------------
# Funciones auxiliares
# ----------------------------
def normalize(name):
   return str(name).strip().lower()

# Cast hour to string format
def normalize_hour(h):
   return str(h).strip()

def extract_players_by_category(df):
   categories = df[C_CATEGORIA].unique()
   data = {}
   for cat in categories:
      subset = df[df[C_CATEGORIA] == cat]
      data[cat] = list(zip(subset[C_JUGADOR_1], subset[C_JUGADOR_2]))
   return data

def generate_round_robin(pairs):
   return [(pairs[i], pairs[j]) for i in range(len(pairs)) for j in range(i + 1, len(pairs))]

def get_player_name_set(pair):
   return {normalize(pair[0]), normalize(pair[1])}

def has_schedule_conflict(player_matches, day, hour):
   return any((d == day and h == hour) for (d, h) in player_matches)

def played_too_much(player_matches, day):
   return sum(1 for d, _ in player_matches if d == day) >= 3

def overnight_conflict(player_matches, day, hour, all_hours):
   return False  # Placeholder para futuras reglas

def all_players_available(players, day, hour, availability):
   return all((day, hour) in availability.get(p, set()) for p in players)

def are_pairs_compatible(pair1, pair2, player_availability):
   players = [normalize(p) for p in pair1 + pair2]
   slots = [player_availability.get(p, set()) for p in players]
   return bool(set.intersection(*slots)) if slots else False

def detect_incompatibilities(pairs, player_availability):
   incompatibles = defaultdict(set)
   for i, pair1 in enumerate(pairs):
      for j in range(i + 1, len(pairs)):
         pair2 = pairs[j]
         if not are_pairs_compatible(pair1, pair2, player_availability):
            incompatibles[pair1].add(pair2)
            incompatibles[pair2].add(pair1)
   return incompatibles

# Intenta assignar un slot únic a cada partit crític sense solapaments.
def has_slot_matching(critical_matches):
   slot_to_match = {}

   def can_assign(match_idx, used_slots, assignments):
      if match_idx >= len(critical_matches):
         return True
      _, slots = critical_matches[match_idx]
      for slot in slots:
         if slot in used_slots:
            continue
         used_slots.add(slot)
         assignments.append((critical_matches[match_idx][0], slot))
         if can_assign(match_idx + 1, used_slots, assignments):
            return True
         used_slots.remove(slot)
         assignments.pop()
      return False

   return can_assign(0, set(), [])

def is_group_schedulable_advanced(group, player_availability):
   print(f"\n🔍 Comprovant si el grup és programable:")
   print(f"  ➤ Grup: {group}")

   matches = []
   for pair1, pair2 in generate_round_robin(group):
      slots = get_common_slots(pair1, pair2, player_availability)
      print(f"    - {pair1} vs {pair2}: {len(slots)} slots → {sorted(slots)}")
      matches.append(((pair1, pair2), slots))

   threshold = len(group)
   critical = [(pair, slots) for pair, slots in matches if len(slots) < threshold]

   if len(critical) <= 1:
      print("  ✅ Grup vàlid (0 o 1 partit crític)")
      return True

   print(f"  ⚠️ Hi ha {len(critical)} partits crítics (amb menys de {threshold} franges):")
   for (pair, slots) in critical:
      print(f"    - CRÍTIC: {pair[0]} vs {pair[1]} → {len(slots)} slots: {sorted(slots)}")

   if not has_slot_matching(critical):
      print("  ❌ Grup invàlid: no es poden assignar slots únics als partits crítics.")
      return False

   print("  ✅ Grup vàlid: es poden assignar slots no solapats als partits crítics.")
   return True

def assign_pairs_to_groups(pairs, incompatibles, num_groups, player_availability):
   group_size = len(pairs) // num_groups
   groupings = [[] for _ in range(num_groups)]

   for pair in sorted(pairs, key=lambda p: len(incompatibles[p]), reverse=True):
      assigned = False
      for idx, group in enumerate(groupings):
         if len(group) >= group_size:
            continue
         if all(p not in incompatibles[pair] for p in group):
            temp_group = group + [pair]
            if is_group_schedulable_advanced(temp_group, player_availability):
               group.append(pair)
               assigned = True
               break
      if not assigned:
         print(f"⚠️ Parella no assignada per problemes de compatibilitat o de franges crítiques: {pair}")
   return groupings

def create_matches_from_groups(groupings, category, player_availability):
   matches = []
   for group_index, group in enumerate(groupings):
      raw_matches = generate_round_robin(group)
      for pair1, pair2 in raw_matches:
         match = Match(pair1, pair2, category, group_id=group_index + 1)
         match.possible_slots = get_common_slots(pair1, pair2, player_availability)
         matches.append(match)
   return matches

def get_common_slots(pair1, pair2, player_availability):
   players = get_player_name_set(pair1) | get_player_name_set(pair2)
   slots = None
   for p in players:
      p_slots = player_availability.get(p, set())
      slots = p_slots if slots is None else slots & p_slots
   return slots or set()

def schedule_match(match, court_availability, player_schedule, player_availability, all_hours):
   for day in court_availability:
      for hour in court_availability[day]:
         if court_availability[day][hour] <= 0:
            continue
         all_players = get_player_name_set(match.pair1) | get_player_name_set(match.pair2)
         if (
            any(has_schedule_conflict(player_schedule[p], day, hour) for p in all_players)
            or any(played_too_much(player_schedule[p], day) for p in all_players)
            or any(overnight_conflict(player_schedule[p], day, hour, all_hours) for p in all_players)
            or not all_players_available(all_players, day, hour, player_availability)
         ):
            continue

         match.day = day
         match.hour = hour
         for p in all_players:
            player_schedule[p].append((day, hour))
         court_availability[day][hour] -= 1
         return True
   return False

# ----------------------------
# Función principal
# ----------------------------
def schedule_matches(df, category_groups, court_availability, player_availability):
   players_by_category = extract_players_by_category(df)
   all_hours = sorted({hour for day in court_availability for hour in court_availability[day]})

   for planning_attempt in range(MAX_PLANNING_ATTEMPTS):
      print(f"\n🔁 Planificació global: intent {planning_attempt + 1}")
      all_matches = []
      scheduled_matches = []
      final_non_scheduled_matches = []
      player_schedule = defaultdict(list)
      court_availability_copy = {d: court_availability[d].copy() for d in court_availability}

      for category, settings in category_groups.items():
         num_groups = settings["num_grups"]
         pairs = players_by_category[category]
         random.shuffle(pairs)

         incompatibles = detect_incompatibilities(pairs, player_availability)
         #print(f"\nIncompatibilitats per categoria {category}:")
         #for pair, conflict_set in incompatibles.items():
            #print(f"  {pair} ↔ {list(conflict_set)}")

         for grouping_attempt in range(MAX_PLANNING_ATTEMPTS):
            random.shuffle(pairs)
            groupings = assign_pairs_to_groups(pairs, incompatibles, num_groups, player_availability)
            flat_group = [pair for group in groupings for pair in group]
            if len(flat_group) == len(pairs):
               print(f"✅ Assignació de grups trobada a l'intent {grouping_attempt + 1}")
               break
            else:
               print(f"🔁 Intent {grouping_attempt + 1}: no s'han pogut assignar totes les parelles ({len(flat_group)}/{len(pairs)})")
         else:
            print(f"❌ No s'han pogut assignar totes les parelles després de {MAX_PLANNING_ATTEMPTS} intents.")

         matches = create_matches_from_groups(groupings, category, player_availability)
         all_matches.extend(matches)

      all_matches.sort(key=lambda m: len(m.possible_slots))
      print("\n📋 Partits ordenats per nombre de franges disponibles:")
      for match in all_matches:
         print(f"  {match.pair1} vs {match.pair2} ({match.category}) → {len(match.possible_slots)} slots: {sorted(match.possible_slots)}")

      
      unscheduled_matches = all_matches.copy()
      while unscheduled_matches:
         # Recalcular nombre de slots disponibles reals per cada partit
         for match in unscheduled_matches:
            available_slots = [
               (day, hour)
               for (day, hour) in match.possible_slots
               if day in court_availability_copy and normalize_hour(hour) in court_availability_copy[day] and court_availability_copy[day][normalize_hour(hour)] > 0
            ]
            match.current_available_slots = available_slots

         # Ordenar els partits que queden per menys franges reals disponibles
         unscheduled_matches.sort(key=lambda m: len(m.current_available_slots))

         # Intentar programar el primer
         match = unscheduled_matches.pop(0)
         if schedule_match(match, court_availability_copy, player_schedule, player_availability, all_hours):
            scheduled_matches.append(match)
         else:
            final_non_scheduled_matches.append(match)
            print(f"⚠️ No s'ha pogut programar el partit {match.pair1} vs {match.pair2} ({match.category}) → Tornant a començar")
            break  # Reintentem la planificació des del principi
      else:
         print(f"✅ Tots els partits s'han programat correctament a l'intent {planning_attempt + 1}")
         return scheduled_matches
   
   print(f"\n❌ No s'ha pogut trobar una combinació vàlida després de {MAX_PLANNING_ATTEMPTS} intents.")
   return [], []"""

import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from utils.constants import REQUIRED_COLUMNS, C_CATEGORIA, C_JUGADOR_1, C_JUGADOR_2, MAX_PLANNING_ATTEMPTS
from functools import lru_cache

# ----------------------------
# Estructura para los partidos
# ----------------------------
class Match:
   def __init__(self, pair1, pair2, category, group_id=None):
      self.pair1 = pair1
      self.pair2 = pair2
      self.category = category
      self.day = None
      self.hour = None
      self.group_id = group_id
      self.possible_slots = None
      self.current_available_slots = None

# ----------------------------
# Funciones auxiliares
# ----------------------------
def normalize(name):
   return str(name).strip().lower()

# Cast hour to string format
def normalize_hour(h):
   return str(h).strip()

def extract_players_by_category(df):
   categories = df[C_CATEGORIA].unique()
   data = {}
   for cat in categories:
      subset = df[df[C_CATEGORIA] == cat]
      data[cat] = list(zip(subset[C_JUGADOR_1], subset[C_JUGADOR_2]))
   return data

def generate_round_robin(pairs):
   return [(pairs[i], pairs[j]) for i in range(len(pairs)) for j in range(i + 1, len(pairs))]

def get_player_name_set(pair):
   return {normalize(pair[0]), normalize(pair[1])}

def has_schedule_conflict(player_matches, day, hour):
   return any((d == day and h == hour) for (d, h) in player_matches)

def played_too_much(player_matches, day):
   return sum(1 for d, _ in player_matches if d == day) >= 3

def overnight_conflict(player_matches, day, hour, all_hours):
   return False  # Placeholder para futuras reglas

def all_players_available(players, day, hour, availability):
   return all((day, hour) in availability.get(p, set()) for p in players)

def are_pairs_compatible(pair1, pair2, player_availability):
   players = [normalize(p) for p in pair1 + pair2]
   slots = [player_availability.get(p, set()) for p in players]
   return bool(set.intersection(*slots)) if slots else False

def detect_incompatibilities(pairs, player_availability):
   incompatibles = defaultdict(set)
   for i, pair1 in enumerate(pairs):
      for j in range(i + 1, len(pairs)):
         pair2 = pairs[j]
         if not are_pairs_compatible(pair1, pair2, player_availability):
            incompatibles[pair1].add(pair2)
            incompatibles[pair2].add(pair1)
   return incompatibles

# Intenta assignar un slot únic a cada partit crític sense solapaments.
def has_slot_matching(critical_matches):
   slot_to_match = {}

   def can_assign(match_idx, used_slots, assignments):
      if match_idx >= len(critical_matches):
         return True
      _, slots = critical_matches[match_idx]
      for slot in slots:
         if slot in used_slots:
            continue
         used_slots.add(slot)
         assignments.append((critical_matches[match_idx][0], slot))
         if can_assign(match_idx + 1, used_slots, assignments):
            return True
         used_slots.remove(slot)
         assignments.pop()
      return False

   return can_assign(0, set(), [])

def is_group_schedulable_advanced(group, player_availability):
   print(f"\n🔍 Comprovant si el grup és programable:")
   print(f"  ➤ Grup: {group}")

   matches = []
   for pair1, pair2 in generate_round_robin(group):
      slots = get_common_slots(pair1, pair2, player_availability)
      print(f"    - {pair1} vs {pair2}: {len(slots)} slots → {sorted(slots)}")
      matches.append(((pair1, pair2), slots))

   threshold = len(group)
   critical = [(pair, slots) for pair, slots in matches if len(slots) < threshold]

   if len(critical) <= 1:
      print("  ✅ Grup vàlid (0 o 1 partit crític)")
      return True

   print(f"  ⚠️ Hi ha {len(critical)} partits crítics (amb menys de {threshold} franges):")
   for (pair, slots) in critical:
      print(f"    - CRÍTIC: {pair[0]} vs {pair[1]} → {len(slots)} slots: {sorted(slots)}")

   if not has_slot_matching(critical):
      print("  ❌ Grup invàlid: no es poden assignar slots únics als partits crítics.")
      return False

   print("  ✅ Grup vàlid: es poden assignar slots no solapats als partits crítics.")
   return True

def assign_pairs_to_groups(pairs, incompatibles, num_groups, player_availability):
   group_size = len(pairs) // num_groups
   groupings = [[] for _ in range(num_groups)]

   for pair in sorted(pairs, key=lambda p: len(incompatibles[p]), reverse=True):
      assigned = False
      for idx, group in enumerate(groupings):
         if len(group) >= group_size:
            continue
         if all(p not in incompatibles[pair] for p in group):
            temp_group = group + [pair]
            if is_group_schedulable_advanced(temp_group, player_availability):
               group.append(pair)
               assigned = True
               break
      if not assigned:
         print(f"⚠️ Parella no assignada per problemes de compatibilitat o de franges crítiques: {pair}")
   return groupings

def get_common_slots(pair1, pair2, player_availability):
   players = get_player_name_set(pair1) | get_player_name_set(pair2)
   slots = None
   for p in players:
      p_slots = player_availability.get(p, set())
      slots = p_slots if slots is None else slots & p_slots
   return slots or set()

def build_slot_index(court_availability):
   """Create a stable index for every (day, hour) with its capacity."""
   # Ensure hours are normalized to avoid duplicate keys like "18" vs "18 "
   normalized = {
      d: {normalize_hour(h): cap for h, cap in hours.items()}
      for d, hours in court_availability.items()
   }

   slot_index = {}   # (day, hour) -> slot_id
   rev_slot = []     # slot_id -> (day, hour)
   cap = []          # slot_id -> remaining capacity (int)

   for d in sorted(normalized.keys()):
      for h in sorted(normalized[d].keys()):
         slot_id = len(rev_slot)
         slot_index[(d, h)] = slot_id
         rev_slot.append((d, h))
         cap.append(normalized[d][h])

   return slot_index, rev_slot, cap

def compress_player_availability(player_availability, slot_index):
   """Map each player's (day, hour) availability to slot_ids."""
   comp = {}
   for p, slots in player_availability.items():
      ids = set()
      for (d, h) in slots:
         hh = normalize_hour(h)
         if (d, hh) in slot_index:
               ids.add(slot_index[(d, hh)])
      comp[str(p).strip().lower()] = ids
   return comp

def player_set_from_pairs(pair1, pair2):
   return {
      str(pair1[0]).strip().lower(), str(pair1[1]).strip().lower(),
      str(pair2[0]).strip().lower(), str(pair2[1]).strip().lower(),
   }

def build_common_slots_getter(player_avail_ids):
   """Returns a fast, cached function that yields slot_id sets for a pair-vs-pair."""
   @lru_cache(maxsize=None)
   def get_common_slots_ids(pair1, pair2):
      players = player_set_from_pairs(pair1, pair2)
      # Intersect their slot_id sets
      it = iter(players)
      first = next(it, None)
      if first is None:
         return frozenset()
      common = set(player_avail_ids.get(first, set()))
      for p in it:
         common &= player_avail_ids.get(p, set())
         if not common:
               break
      return frozenset(common)  # frozenset so it's cacheable
   return get_common_slots_ids

def schedule_match(match, court_availability, player_schedule, player_availability, all_hours):
   for day in court_availability:
      for hour in court_availability[day]:
         if court_availability[day][hour] <= 0:
            continue
         all_players = get_player_name_set(match.pair1) | get_player_name_set(match.pair2)
         if (
            any(has_schedule_conflict(player_schedule[p], day, hour) for p in all_players)
            or any(played_too_much(player_schedule[p], day) for p in all_players)
            or any(overnight_conflict(player_schedule[p], day, hour, all_hours) for p in all_players)
            or not all_players_available(all_players, day, hour, player_availability)
         ):
            continue

         match.day = day
         match.hour = hour
         for p in all_players:
            player_schedule[p].append((day, hour))
         court_availability[day][hour] -= 1
         return True
   return False

def create_matches_from_groups(groupings, category, get_common_slots_ids):
   matches = []
   for group_index, group in enumerate(groupings):
      for pair1, pair2 in generate_round_robin(group):
         match = Match(pair1, pair2, category, group_id=group_index + 1)
         # slot_ids as a sorted list for deterministic behavior
         match.possible_slots = sorted(get_common_slots_ids(pair1, pair2))
         matches.append(match)
   return matches

def schedule_match_by_slot_id(match, cap, rev_slot, player_schedule, player_avail_ids, all_hours):
   # Try slots in the current feasible domain
   for s in match.current_available_slots:
      if cap[s] <= 0:
         continue
      day, hour = rev_slot[s]

      all_players = {
         str(match.pair1[0]).strip().lower(), str(match.pair1[1]).strip().lower(),
         str(match.pair2[0]).strip().lower(), str(match.pair2[1]).strip().lower(),
      }

      # Original constraints, but faster:
      # 1) same slot conflict
      if any(any((d == day and h == hour) for (d, h) in player_schedule[p]) for p in all_players):
         continue
      # 2) daily limit (replace with O(1) counter later if you want)
      if any(sum(1 for (d, _) in player_schedule[p] if d == day) >= 3 for p in all_players):
         continue
      # 3) overnight (you had placeholder False)
      # 4) availability (already guaranteed by domain, but keep if you want safety):
      if not all(s in player_avail_ids.get(p, set()) for p in all_players):
         continue

      # Commit
      match.day, match.hour = day, hour
      for p in all_players:
         player_schedule[p].append((day, hour))
      cap[s] -= 1
      return True

   return False

# ----------------------------
# Función principal
# ----------------------------
def schedule_matches(df, category_groups, court_availability, player_availability):
   # A1) Build slot index + capacities
   slot_index, rev_slot, cap = build_slot_index(court_availability)

   # B1) Compress player availability to slot_ids
   player_avail_ids = compress_player_availability(player_availability, slot_index)

   # C1) Cached getter for common slots
   get_common_slots_ids = build_common_slots_getter(player_avail_ids)

   players_by_category = extract_players_by_category(df)
   all_hours = sorted({hour for day in court_availability for hour in court_availability[day]})

   for planning_attempt in range(MAX_PLANNING_ATTEMPTS):
      all_matches = []
      scheduled_matches = []
      final_non_scheduled_matches = []
      player_schedule = defaultdict(list)
      cap_copy = cap[:]  # fresh capacities copy for this attempt

      for category, settings in category_groups.items():
         num_groups = settings["num_grups"]
         pairs = players_by_category[category][:]
         random.shuffle(pairs)

         incompatibles = detect_incompatibilities(pairs, player_avail_ids)  # <- you can adapt it to use ids or keep as-is if it only tests emptiness

         for grouping_attempt in range(MAX_PLANNING_ATTEMPTS):
               random.shuffle(pairs)
               groupings = assign_pairs_to_groups(pairs, incompatibles, num_groups, player_avail_ids)
               flat_group = [pair for group in groupings for pair in group]
               if len(flat_group) == len(pairs):
                  break

         # D1) Create matches with precomputed, compressed domains
         matches = create_matches_from_groups(groupings, category, get_common_slots_ids)
         all_matches.extend(matches)

      # Sort by domain size (already slot_ids) – same idea as before
      all_matches.sort(key=lambda m: len(m.possible_slots))

      # Your greedy loop but faster thanks to compressed domains + cap array
      unscheduled_matches = all_matches.copy()
      while unscheduled_matches:
         # recompute feasible domain by capacity only (quick)
         for match in unscheduled_matches:
               match.current_available_slots = [s for s in match.possible_slots if cap_copy[s] > 0]

         unscheduled_matches.sort(key=lambda m: len(m.current_available_slots))

         match = unscheduled_matches.pop(0)
         if schedule_match_by_slot_id(match, cap_copy, rev_slot, player_schedule, player_avail_ids, all_hours):
               scheduled_matches.append(match)
         else:
               final_non_scheduled_matches.append(match)
               break
      else:
         # success path
         return scheduled_matches

   return []