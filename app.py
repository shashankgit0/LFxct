import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def db() -> Client:
return create_client(SUPABASE_URL, SUPABASE_KEY)

st.markdown(”””

<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
[data-testid="stDecoration"] {visibility: hidden;}
section[data-testid="stSidebar"] {display: none !important;}
</style>

“””, unsafe_allow_html=True)

ROLE_LABELS = {“admin”: “♔ King”, “player”: “♟ Pawn”}
ADMIN_ROLES = [“admin”]
ALL_ROLES   = [“player”, “admin”]

# ─── BP Pool ───────────────────────────────────────────────────────────────────

# Each template has:

# key, display (shown to user), fields (list of {label, placeholder}), note

# {0}, {1}, {2} are replaced by user inputs in order

BP_POOL = {
“🏏 Batting”: [
# Single blank
{“key”:“bat_duck”,   “display”:”{0} to score a duck (0 runs)”,           “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“bat_top”,    “display”:”{0} to be the highest scorer in the team”,“fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“bat_sr200”,  “display”:”{0} to have 200+ strike rate”,            “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:“Min 10 balls faced”},
{“key”:“bat_b1”,     “display”:”{0} to hit a boundary on ball 1”,         “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:“First ball of innings”},
{“key”:“bat_six1”,   “display”:”{0} to hit a six on ball 1”,              “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:“First ball of innings”},
{“key”:“bat_5six”,   “display”:”{0} to hit 5+ sixes”,                     “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“bat_8four”,  “display”:”{0} to hit 8+ fours”,                     “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“bat_50fast”, “display”:”{0} to score a fifty in less than 20 balls”,“fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                         “note”:None},
{“key”:“bat_pp30”,   “display”:”{0} to score 30+ in the powerplay”,       “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:“First 6 overs”},
{“key”:“bat_pp40”,   “display”:”{0} to score 40+ in the powerplay”,       “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:“First 6 overs”},
{“key”:“bat_nosix”,  “display”:”{0} to not hit a single six”,             “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“bat_last”,   “display”:”{0} to be the last wicket to fall”,       “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“bat_consix”, “display”:”{0} to hit consecutive sixes”,            “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“bat_gduck”,  “display”:”{0} to be dismissed for a golden duck”,   “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”}],                                          “note”:“Out first ball”},
# Multi blank
{“key”:“bat_range”,  “display”:”{0} to score between {1} and {2} runs”,   “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”},{“label”:“Min runs”,“ph”:“e.g. 30”},{“label”:“Max runs”,“ph”:“e.g. 40”}], “note”:None},
{“key”:“bat_getout”, “display”:”{0} to get out for {1} runs”,             “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”},{“label”:“Runs”,“ph”:“e.g. 23”}],           “note”:None},
{“key”:“bat_ofballs”,“display”:”{0} to score {1}+ runs off {2} balls”,    “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”},{“label”:“Runs”,“ph”:“e.g. 30”},{“label”:“Balls”,“ph”:“e.g. 15”}], “note”:None},
{“key”:“bat_nsix”,   “display”:”{0} to hit {1} sixes in their innings”,   “fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”},{“label”:“Sixes”,“ph”:“e.g. 3”}],           “note”:None},
{“key”:“bat_50over”, “display”:”{0} to score a fifty in less than {1} balls”,“fields”:[{“label”:“Batter”,“ph”:“e.g. Kohli”},{“label”:“Balls”,“ph”:“e.g. 25”}],        “note”:None},
],
“🎳 Bowling”: [
# Single blank
{“key”:“bowl_1w”,    “display”:”{0} to take 1 wicket”,                    “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_2w”,    “display”:”{0} to take 2 wickets”,                   “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_3w”,    “display”:”{0} to take 3 wickets”,                   “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_3wp”,   “display”:”{0} to take 3+ wickets”,                  “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_mdn”,   “display”:”{0} to bowl a maiden over”,               “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_top”,   “display”:”{0} to be the top wicket taker”,          “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_eco6”,  “display”:”{0} to have economy under 6”,             “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:“Min 2 overs”},
{“key”:“bowl_eco7”,  “display”:”{0} to have economy under 7”,             “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:“Min 2 overs”},
{“key”:“bowl_dot10”, “display”:”{0} to bowl 10+ dot balls”,               “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_wide”,  “display”:”{0} to bowl 3+ wides”,                    “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_nb”,    “display”:”{0} to bowl 2+ no balls”,                 “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_fb”,    “display”:”{0} to take a wicket on their first ball”, “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                        “note”:None},
{“key”:“bowl_pp”,    “display”:”{0} to take a wicket in the powerplay”,   “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:“First 6 overs”},
{“key”:“bowl_bb”,    “display”:”{0} to take back to back wickets”,        “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_zero”,  “display”:”{0} to concede 0 runs in an over”,        “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_hat”,   “display”:”{0} to take a hat trick”,                 “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:“Rare but legendary 🔥”},
{“key”:“bowl_exp”,   “display”:”{0} to be the most expensive bowler”,     “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
{“key”:“bowl_top2”,  “display”:”{0} to dismiss the top scorer”,           “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”}],                                         “note”:None},
# Multi blank
{“key”:“bowl_wktruns”,“display”:”{0} to take {1} wicket/s for under {2} runs”,“fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”},{“label”:“Wickets”,“ph”:“e.g. 2”},{“label”:“Runs”,“ph”:“e.g. 25”}], “note”:None},
{“key”:“bowl_conc”,  “display”:”{0} to concede under {1} runs in {2} overs”,“fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”},{“label”:“Runs”,“ph”:“e.g. 20”},{“label”:“Overs”,“ph”:“e.g. 4”}], “note”:None},
{“key”:“bowl_dotn”,  “display”:”{0} to bowl {1} dot balls in their spell”,“fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”},{“label”:“Dot balls”,“ph”:“e.g. 8”}],     “note”:None},
{“key”:“bowl_overn”, “display”:”{0} to take a wicket in over {1}”,        “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”},{“label”:“Over number”,“ph”:“e.g. 6”}],   “note”:None},
{“key”:“bowl_4ovr”,  “display”:”{0} to bowl 4 overs for under {1} runs”,  “fields”:[{“label”:“Bowler”,“ph”:“e.g. Bumrah”},{“label”:“Runs”,“ph”:“e.g. 25”}],         “note”:None},
],
“🔥 Team”: [
# Single blank
{“key”:“team_200p”,  “display”:”{0} team to score 200+ runs”,             “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_u130”,  “display”:”{0} team to score under 130 runs”,        “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_6s11”,  “display”:”{0} team to hit 11+ sixes”,               “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_6s15”,  “display”:”{0} team to hit 15+ sixes”,               “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_4s19”,  “display”:”{0} team to hit 19+ fours”,               “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_win10”, “display”:”{0} team to win by 10+ wickets”,          “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_win50”, “display”:”{0} team to win by 50+ runs”,             “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_allout”,“display”:”{0} team to be all out”,                  “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_fw3”,   “display”:”{0} team to lose first wicket inside 3 overs”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                         “note”:None},
{“key”:“team_fw6”,   “display”:”{0} team to lose first wicket after 6 overs”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                          “note”:None},
{“key”:“team_100p”,  “display”:”{0} team to have a 100+ partnership”,     “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_six1”,  “display”:”{0} team to hit a six on the first ball”, “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_ext10”, “display”:”{0} team to have 10+ extras total”,       “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“team_pp50”,  “display”:”{0} team to score 50+ in powerplay”,      “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:“First 6 overs”},
{“key”:“team_pp60”,  “display”:”{0} team to score 60+ in powerplay”,      “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:“First 6 overs”},
{“key”:“team_d20”,   “display”:”{0} team to score 20+ in the last 2 overs”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                            “note”:None},
{“key”:“team_d30”,   “display”:”{0} team to score 30+ in the last 2 overs”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                            “note”:None},
# Multi blank
{“key”:“team_range”, “display”:”{0} team to score between {1} and {2} runs”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”},{“label”:“Min runs”,“ph”:“e.g. 160”},{“label”:“Max runs”,“ph”:“e.g. 180”}], “note”:None},
{“key”:“team_over”,  “display”:”{0} team to score {1} runs in over {2}”,  “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”},{“label”:“Runs”,“ph”:“e.g. 15”},{“label”:“Over number”,“ph”:“e.g. 6”}], “note”:None},
{“key”:“team_pprange”,“display”:”{0} team to score between {1} and {2} in powerplay”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”},{“label”:“Min runs”,“ph”:“e.g. 45”},{“label”:“Max runs”,“ph”:“e.g. 55”}], “note”:“First 6 overs”},
{“key”:“team_lastn”, “display”:”{0} team to score {1}+ in the last {2} overs”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”},{“label”:“Runs”,“ph”:“e.g. 40”},{“label”:“Overs”,“ph”:“e.g. 4”}], “note”:None},
{“key”:“team_wktn”,  “display”:”{0} team to lose their first wicket in over {1}”,“fields”:[{“label”:“Team”,“ph”:“e.g. SRH”},{“label”:“Over number”,“ph”:“e.g. 4”}], “note”:None},
{“key”:“team_partnr”,“display”:”{0} team to have a {1}+ partnership”,     “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”},{“label”:“Runs”,“ph”:“e.g. 50”}],             “note”:None},
],
“⭐ Special”: [
{“key”:“sp_mom”,     “display”:”{0} to win Man of the Match”,             “fields”:[{“label”:“Player”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“sp_catch2”,  “display”:”{0} to take 2+ catches”,                  “fields”:[{“label”:“Player”,“ph”:“e.g. Kohli”}],                                          “note”:None},
{“key”:“sp_runout”,  “display”:”{0} to be involved in a run out”,         “fields”:[{“label”:“Player”,“ph”:“e.g. Kohli”}],                                          “note”:“Fielder or batsman”},
{“key”:“sp_last”,    “display”:”{0} team to win off the last ball”,       “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“sp_super”,   “display”:“Match to go to a Super Over”,             “fields”:[{“label”:“Type”,“ph”:“Super Over”}],                                            “note”:None},
{“key”:“sp_toss_bat”,“display”:”{0} to win toss and choose to bat”,       “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“sp_toss_bowl”,“display”:”{0} to win toss and choose to bowl”,     “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“sp_allround”,“display”:”{0} to score 30+ and take 2+ wickets”,   “fields”:[{“label”:“Player”,“ph”:“e.g. Jadeja”}],                                         “note”:“All rounder special”},
{“key”:“sp_top3_20”, “display”:“Top 3 batters of {0} to all score 20+”,  “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“sp_six1st”,  “display”:“First ball of the match to be a six”,    “fields”:[{“label”:“Type”,“ph”:“First ball six”}],                                        “note”:None},
{“key”:“sp_wkt1st”,  “display”:“First ball of the match to be a wicket”, “fields”:[{“label”:“Type”,“ph”:“First ball wicket”}],                                     “note”:None},
{“key”:“sp_30sixes”, “display”:“Match to have 30+ sixes total”,           “fields”:[{“label”:“Type”,“ph”:“30+ sixes”}],                                            “note”:None},
{“key”:“sp_open20”,  “display”:“Both openers of {0} to score 20+”,       “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“sp_open30”,  “display”:“Both openers of {0} to score 30+”,       “fields”:[{“label”:“Team”,“ph”:“e.g. SRH”}],                                             “note”:None},
{“key”:“sp_d6six”,   “display”:“Last 5 overs to have {0}+ sixes”,        “fields”:[{“label”:“Sixes”,“ph”:“e.g. 5”}],                                              “note”:“Death overs”},
],
}

# ─── Helpers ───────────────────────────────────────────────────────────────────

def get_all_users():
return db().table(“users”).select(”*”).execute().data or []

def get_playing_users():
return [u for u in get_all_users() if u[“role”] not in ADMIN_ROLES]

def get_user_by_username(username):
for u in get_all_users():
if u[“username”] == username:
return u
return {}

def get_team(username):
u = get_user_by_username(username)
return u.get(“team_name”) or u.get(“display_name”) or username

def caps(text):
return text.strip().upper() if text else “”

def get_matches():
return db().table(“matches”).select(”*”).execute().data or []

def get_match_map():
return {m[“match_name”]: i+1 for i, m in enumerate(get_matches())}

def sp_pts(username):
total = 0
for p in db().table(“predictions”).select(“points_awarded”).eq(“player”, username).execute().data or []:
try: total += float(p.get(“points_awarded”) or 0)
except: pass
return round(total, 2)

def bp_pts(username):
total = 0
for b in db().table(“pool_bps”).select(“points_awarded”).eq(“player”, username).execute().data or []:
try: total += float(b.get(“points_awarded”) or 0)
except: pass
return round(total, 2)

def streak_pts(username):
total = 0
for s in db().table(“streaks”).select(“bonus_points”).eq(“player”, username).execute().data or []:
try: total += float(s.get(“bonus_points”) or 0)
except: pass
return round(total, 2)

def season_pts(username):
total = 0
for s in db().table(“season_predictions”).select(“points_awarded”).eq(“player”, username).execute().data or []:
try: total += float(s.get(“points_awarded”) or 0)
except: pass
return round(total, 2)

def total_pts(username):
return round(sp_pts(username) + bp_pts(username) + streak_pts(username) + season_pts(username), 2)

def exact_count(username):
count = 0
for p in db().table(“predictions”).select(”*”).eq(“player”, username).execute().data or []:
if p.get(“actual_score”) is not None:
if int(p.get(“predicted_score”) or 0) == int(p.get(“actual_score”) or -1):
count += 1
return count

def current_streak(username):
preds = db().table(“predictions”).select(”*”).eq(“player”, username).execute().data or []
done  = sorted([p for p in preds if p.get(“actual_score”) is not None],
key=lambda x: x.get(“submitted_at”) or “”, reverse=True)
streak = 0
for p in done:
all_p = db().table(“predictions”).select(”*”).eq(“match_name”, p[“match_name”]).execute().data or []
valid = [x for x in all_p if x.get(“actual_score”) is not None]
if not valid: break
min_diff = min(abs(int(x.get(“predicted_score”) or 0) - int(x.get(“actual_score”) or 0)) for x in valid)
my_diff  = abs(int(p.get(“predicted_score”) or 0) - int(p.get(“actual_score”) or 0))
if my_diff == min_diff: streak += 1
else: break
return streak

def streak_bonus(n):
return max(0, n - 1)

def login(username, password):
res = db().table(“users”).select(”*”).eq(“username”, username).eq(“password”, password).execute()
return res.data[0] if res.data else None

def calc_sp_wins(username, all_preds, match_names):
wins = 0
for mn in match_names:
mp = [p for p in all_preds if p[“match_name”]==mn and p.get(“actual_score”) is not None]
if not mp: continue
my = next((p for p in mp if p[“player”]==username), None)
if not my: continue
my_d  = abs(int(my.get(“predicted_score”) or 0) - int(my.get(“actual_score”) or 0))
min_d = min(abs(int(p.get(“predicted_score”) or 0) - int(p.get(“actual_score”) or 0)) for p in mp)
if my_d == min_d: wins += 1
return wins

def calc_rank(username, mn, all_preds):
mp = [p for p in all_preds if p[“match_name”]==mn and p.get(“actual_score”) is not None]
if not mp: return None
my = next((p for p in mp if p[“player”]==username), None)
if not my: return None
my_d  = abs(int(my.get(“predicted_score”) or 0) - int(my.get(“actual_score”) or 0))
diffs = sorted([abs(int(p.get(“predicted_score”) or 0) - int(p.get(“actual_score”) or 0)) for p in mp])
return diffs.index(my_d) + 1 if my_d in diffs else 99

def award_sp_points(match_sel, actual_score, actual_wickets, actual_winner):
actual_winner = caps(actual_winner)
db().table(“matches”).update({
“status”: “done”, “actual_score”: actual_score,
“actual_wickets”: actual_wickets, “actual_winner”: actual_winner
}).eq(“match_name”, match_sel).execute()
preds = db().table(“predictions”).select(”*”).eq(“match_name”, match_sel).execute().data or []
if not preds: return
for p in preds:
p[“diff”] = abs(int(p.get(“predicted_score”) or 0) - actual_score)
min_diff = min(p[“diff”] for p in preds)
winners  = [p for p in preds if p[“diff”] == min_diff]
for p in preds:
pts      = 0
is_win   = p[“diff”] == min_diff
is_exact = int(p.get(“predicted_score”) or 0) == actual_score
corr_win = caps(p.get(“predicted_winner”,””)) == actual_winner
corr_wkt = int(p.get(“predicted_wickets”) or -1) == actual_wickets
if is_exact:  pts += 6
elif is_win:  pts += 4
if corr_win:  pts += 2
if is_win and corr_wkt: pts += 1
db().table(“predictions”).update({
“actual_score”: actual_score, “actual_wickets”: actual_wickets,
“actual_winner”: actual_winner, “points_awarded”: pts
}).eq(“id”, p[“id”]).execute()
for w in winners:
u = w[“player”]
s = current_streak(u)
b = streak_bonus(s)
if b > 0:
db().table(“streaks”).insert({
“player”: u, “match_name”: match_sel,
“streak_count”: s, “bonus_points”: b
}).execute()

def build_prediction_text(template_display, inputs):
text = template_display
for i, val in enumerate(inputs):
text = text.replace(f”{{{i}}}”, val.strip())
return text

def get_pages(role):
if role == “guest”:
return [“🏆 Leaderboard”,“📊 Overall Stats”,“👤 Player Stats”,“🏅 Hall of Fame”,
“📋 Match Details”,“📖 How to Score”,“🌟 Season Predictions”]
pages = [“🏆 Leaderboard”,“📊 Overall Stats”,“👤 Player Stats”,“🏅 Hall of Fame”,
“📋 Match Details”,“📖 How to Score”,“🌟 Season Predictions”,
“🎱 BP Pool”,“🔮 Score Prediction”]
if role == “admin”:
pages += [“🏆 Enter Results”,“📝 BP Results”,“🔒 Lock / Cancel”,“⚙️ King’s Panel”]
return pages

# ══════════════════════════════════════════════════════════════════════════════

# LEADERBOARD

# ══════════════════════════════════════════════════════════════════════════════

def page_leaderboard():
st.title(“🏆 LFxCT Leaderboard”)
st.markdown(”—”)
users = get_playing_users()
if not users: st.info(“No players yet.”); return
rows = []
for u in users:
un = u[“username”]
rows.append({
“Rank”:       “”,
“Team”:       u.get(“team_name”) or u.get(“display_name”) or un,
“SP Pts”:     int(sp_pts(un)),
“BP Pts”:     int(bp_pts(un)),
“Streak Pts”: int(streak_pts(un)),
“⚡ Exacts”:  exact_count(un),
“🔥 Streak”:  current_streak(un),
“Total”:      int(total_pts(un)),
})
rows.sort(key=lambda x: x[“Total”], reverse=True)
for i, r in enumerate(rows):
r[“Rank”] = [“🥇”,“🥈”,“🥉”][i] if i < 3 else str(i+1)
df = pd.DataFrame(rows)
def style_df(df):
s = pd.DataFrame(””, index=df.index, columns=df.columns)
s[“Total”] = “background-color:#1e2a1e;color:#00ff88;font-weight:bold”
s[“Team”]  = “background-color:#1a1a2e;font-weight:bold”
return s
st.dataframe(df.style.apply(style_df, axis=None), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════

# OVERALL STATS

# ══════════════════════════════════════════════════════════════════════════════

def page_overall_stats():
st.title(“📊 Overall Stats”)
st.markdown(”—”)
users   = get_playing_users()
matches = get_matches()
done    = [m for m in matches if m.get(“status”) == “done”]
if not users or not done: st.info(“Not enough data yet.”); return

```
match_names = [m["match_name"] for m in done]
match_map   = {m["match_name"]: i+1 for i, m in enumerate(matches)}
all_preds   = db().table("predictions").select("*").execute().data or []
all_bps     = db().table("pool_bps").select("*").execute().data or []

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Points Race", "🎯 Accuracy", "🏅 Podium Tracker", "⚔️ Head to Head", "📋 Full Table"
])

with tab1:
    st.subheader("📈 Points Race — Match by Match")
    cum_data = {}
    for u in users:
        un = u["username"]; team = u.get("team_name") or un
        cum = 0; cum_data[team] = []
        for mn in match_names:
            mp = next((p for p in all_preds if p["player"]==un and p["match_name"]==mn), None)
            if mp: cum += int(float(mp.get("points_awarded") or 0))
            mb = next((b for b in all_bps if b["player"]==un and b["match_name"]==mn), None)
            if mb: cum += int(float(mb.get("points_awarded") or 0))
            cum_data[team].append(cum)
    st.line_chart(pd.DataFrame(cum_data, index=[f"M{match_map[mn]}" for mn in match_names]), use_container_width=True, height=400)
    st.markdown("---")
    st.caption("🔍 Filter match range:")
    total_m = len(match_names)
    if total_m > 2:
        c1,c2 = st.columns(2)
        with c1: start_m = st.number_input("From Match #", min_value=1, max_value=total_m, value=1)
        with c2: end_m   = st.number_input("To Match #",   min_value=1, max_value=total_m, value=total_m)
        f_names = match_names[start_m-1:end_m]
        f_data  = {}
        for u in users:
            un = u["username"]; team = u.get("team_name") or un
            cum = 0; f_data[team] = []
            for mn in f_names:
                mp = next((p for p in all_preds if p["player"]==un and p["match_name"]==mn), None)
                if mp: cum += int(float(mp.get("points_awarded") or 0))
                mb = next((b for b in all_bps if b["player"]==un and b["match_name"]==mn), None)
                if mb: cum += int(float(mb.get("points_awarded") or 0))
                f_data[team].append(cum)
        st.line_chart(pd.DataFrame(f_data, index=[f"M{match_map[mn]}" for mn in f_names]), use_container_width=True, height=300)

with tab2:
    st.subheader("🎯 SP Win Rate")
    sp_rows = []
    for u in users:
        un = u["username"]; team = u.get("team_name") or un
        up = [p for p in all_preds if p["player"]==un and p.get("actual_score") is not None]
        sp_w    = calc_sp_wins(un, all_preds, match_names)
        played  = len(up)
        corr_w  = sum(1 for p in up if caps(p.get("predicted_winner",""))==caps(p.get("actual_winner","")))
        corr_wk = sum(1 for p in up if int(p.get("predicted_wickets") or -1)==int(p.get("actual_wickets") or -2))
        margin  = sum(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in up)
        exacts  = sum(1 for p in up if int(p.get("predicted_score") or 0)==int(p.get("actual_score") or 0))
        sp_rows.append({"Team":team,"Played":played,"SP Wins":sp_w,
            "Win %":f"{round(sp_w/played*100)}%" if played else "0%",
            "Correct Winners":corr_w,"Correct Wickets":corr_wk,
            "Exact Preds":exacts,"Margin of Error":margin})
    sp_rows.sort(key=lambda x: x["SP Wins"], reverse=True)
    st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("🎱 BP Success Rate")
    bp_rows = []
    for u in users:
        un = u["username"]; team = u.get("team_name") or un
        ubps = [b for b in all_bps if b["player"]==un]
        correct = sum(1 for b in ubps if b.get("result")=="correct")
        wrong   = sum(1 for b in ubps if b.get("result")=="wrong")
        total_b = correct + wrong
        bp_rows.append({"Team":team,"BP Correct":correct,"BP Wrong":wrong,
            "Success %":f"{round(correct/total_b*100)}%" if total_b else "0%",
            "Custom BPs":sum(1 for b in ubps if b.get("bp_type")=="custom"),
            "BP Points":int(bp_pts(un))})
    bp_rows.sort(key=lambda x: x["BP Correct"], reverse=True)
    st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("📐 Margin of Error — lower is better")
    m_df = pd.DataFrame([{"Team":r["Team"],"Margin of Error":r["Margin of Error"]} for r in sorted(sp_rows, key=lambda x: x["Margin of Error"])])
    st.bar_chart(m_df.set_index("Team"), use_container_width=True, height=300)

with tab3:
    st.subheader("🏅 Podium Tracker")
    podium_rows = []
    for u in users:
        un = u["username"]; team = u.get("team_name") or un
        first = second = third = missed = 0
        for mn in match_names:
            r = calc_rank(un, mn, all_preds)
            if r is None: missed += 1
            elif r==1: first+=1
            elif r==2: second+=1
            elif r==3: third+=1
        attended = len(match_names) - missed
        podium_rows.append({"Team":team,"🥇 1st":first,"🥈 2nd":second,"🥉 3rd":third,
            "Missed":missed,"Attendance %":f"{round(attended/len(match_names)*100)}%" if match_names else "0%"})
    podium_rows.sort(key=lambda x: (x["🥇 1st"],x["🥈 2nd"],x["🥉 3rd"]), reverse=True)
    st.dataframe(pd.DataFrame(podium_rows), use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("😤 Most 2nd Places — Uncrowned Princes")
    top_sec = sorted(podium_rows, key=lambda x: x["🥈 2nd"], reverse=True)[:3]
    cols = st.columns(3)
    for i,(col,row) in enumerate(zip(cols, top_sec)):
        with col:
            st.markdown(f"""<div style='background:{"#FFD700" if i==0 else "#C0C0C0" if i==1 else "#CD7F32"};
```

padding:15px;border-radius:10px;text-align:center;color:black’>
<b>{“🥇🥈🥉”[i]} {row[“Team”]}</b><br>{row[“🥈 2nd”]} second places

</div>""", unsafe_allow_html=True)

```
with tab4:
    st.subheader("⚔️ Head to Head")
    names = [u.get("team_name") or u["username"] for u in users]
    c1,c2 = st.columns(2)
    with c1: p1n = st.selectbox("Player 1", names, key="h1")
    with c2: p2n = st.selectbox("Player 2", [n for n in names if n!=p1n], key="h2")
    p1 = next((u for u in users if (u.get("team_name") or u["username"])==p1n), None)
    p2 = next((u for u in users if (u.get("team_name") or u["username"])==p2n), None)
    if p1 and p2:
        def h2h(u):
            un = u["username"]
            up = [p for p in all_preds if p["player"]==un and p.get("actual_score") is not None]
            ubp= [b for b in all_bps if b["player"]==un]
            f=s=t=0
            for mn in match_names:
                r = calc_rank(un, mn, all_preds)
                if r==1: f+=1
                elif r==2: s+=1
                elif r==3: t+=1
            return {
                "Total Points":      int(total_pts(un)),
                "SP Points":         int(sp_pts(un)),
                "BP Points":         int(bp_pts(un)),
                "Streak Points":     int(streak_pts(un)),
                "SP Wins":           calc_sp_wins(un, all_preds, match_names),
                "BP Correct":        sum(1 for b in ubp if b.get("result")=="correct"),
                "BP Wrong":          sum(1 for b in ubp if b.get("result")=="wrong"),
                "Exact Predictions": exact_count(un),
                "Correct Winners":   sum(1 for p in up if caps(p.get("predicted_winner",""))==caps(p.get("actual_winner",""))),
                "Margin of Error":   sum(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in up),
                "1st Place":         f, "2nd Place": s, "3rd Place": t,
                "Current Streak":    current_streak(un),
            }
        s1 = h2h(p1); s2 = h2h(p2)
        lower = {"Margin of Error","BP Wrong"}
        rows_h = []
        for stat in s1:
            v1,v2 = s1[stat],s2[stat]
            w1 = v1<v2 if stat in lower else v1>v2
            w2 = v2<v1 if stat in lower else v2>v1
            rows_h.append({"Stat":stat, p1n:f"✅ {v1}" if w1 else str(v1), p2n:f"✅ {v2}" if w2 else str(v2)})
        st.markdown(f"### {p1n}  ⚔️  {p2n}")
        st.dataframe(pd.DataFrame(rows_h), use_container_width=True, hide_index=True)

with tab5:
    st.subheader("📋 Full Stats Table")
    full = []
    for u in users:
        un = u["username"]; team = u.get("team_name") or un
        up = [p for p in all_preds if p["player"]==un and p.get("actual_score") is not None]
        ubps = [b for b in all_bps if b["player"]==un]
        full.append({
            "Team":team,"Total":int(total_pts(un)),
            "SP Pts":int(sp_pts(un)),"BP Pts":int(bp_pts(un)),"Streak Pts":int(streak_pts(un)),
            "SP Wins":calc_sp_wins(un, all_preds, match_names),
            "BP Correct":sum(1 for b in ubps if b.get("result")=="correct"),
            "BP Wrong":sum(1 for b in ubps if b.get("result")=="wrong"),
            "Exacts":exact_count(un),
            "Correct Winners":sum(1 for p in up if caps(p.get("predicted_winner",""))==caps(p.get("actual_winner",""))),
            "Margin of Error":sum(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in up),
            "Attended":len(set(p["match_name"] for p in all_preds if p["player"]==un)),
            "Missed":len(match_names)-len(set(p["match_name"] for p in all_preds if p["player"]==un)),
            "🔥 Streak":current_streak(un),
        })
    full.sort(key=lambda x: x["Total"], reverse=True)
    st.dataframe(pd.DataFrame(full), use_container_width=True, hide_index=True)
```

# ══════════════════════════════════════════════════════════════════════════════

# PLAYER STATS

# ══════════════════════════════════════════════════════════════════════════════

def page_player_stats():
st.title(“👤 Player Stats”)
st.markdown(”—”)
users = get_playing_users()
if not users: st.info(“No players.”); return
names    = [u.get(“team_name”) or u[“username”] for u in users]
selected = st.selectbox(“Select Player”, names)
u = next((u for u in users if (u.get(“team_name”) or u[“username”])==selected), None)
if not u: return
un = u[“username”]
matches = get_matches()
mm = {m[“match_name”]: i+1 for i, m in enumerate(matches)}
s_pts=int(sp_pts(un)); b_pts=int(bp_pts(un)); st_pts=int(streak_pts(un))
tot=int(total_pts(un)); streak=current_streak(un); exacts=exact_count(un)
st.markdown(f”## {selected}”)
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric(“🏆 Total”,tot); c2.metric(“🔮 SP”,s_pts)
c3.metric(“🎱 BP”,b_pts); c4.metric(“🔥 Streak”,st_pts); c5.metric(“⚡ Exacts”,exacts)
if streak > 1: st.success(f”🔥 Active streak: **{streak} wins in a row!** (+{streak_bonus(streak+1)} next win)”)
st.markdown(”—”)
if tot > 0:
st.subheader(“📊 Points Breakdown”)
st.bar_chart(pd.DataFrame({“Category”:[“SP”,“BP”,“Streak”],“Points”:[s_pts,b_pts,st_pts]}).set_index(“Category”), use_container_width=True, height=250)
st.markdown(”—”)
st.subheader(“🔮 Score Predictions”)
preds = db().table(“predictions”).select(”*”).eq(“player”, un).execute().data or []
if preds:
st.dataframe(pd.DataFrame([{
“Match #”:f”#{mm.get(p[‘match_name’],’?’)}”,“Match”:p[“match_name”],
“Predicted”:f”{p.get(‘predicted_score’)} - {str(p.get(‘predicted_wickets’,0)).zfill(2)} | {p.get(‘predicted_winner’,’’)}”,
“Actual”:f”{p.get(‘actual_score’)} - {str(p.get(‘actual_wickets’,0)).zfill(2)} | {p.get(‘actual_winner’,’’)}” if p.get(“actual_score”) else “Pending”,
“⚡”:“⚡” if p.get(“actual_score”) and int(p.get(“predicted_score”) or 0)==int(p.get(“actual_score”) or -1) else “”,
“Pts”:int(float(p.get(“points_awarded”) or 0))
} for p in preds]), use_container_width=True, hide_index=True)
else: st.info(“No predictions yet.”)
st.markdown(”—”)
st.subheader(“🎱 Bold Predictions”)
bps = db().table(“pool_bps”).select(”*”).eq(“player”, un).execute().data or []
if bps:
st.dataframe(pd.DataFrame([{
“Match #”:f”#{mm.get(b[‘match_name’],’?’)}”,“Match”:b[“match_name”],
“Prediction”:b[“prediction_text”],
“Type”:“💡” if b.get(“bp_type”)==“custom” else “🎱”,
“Result”:“✅” if b.get(“result”)==“correct” else “❌” if b.get(“result”)==“wrong” else “🚫” if b.get(“result”)==“dismissed” else “⏳”,
“Pts”:int(float(b.get(“points_awarded”) or 0))
} for b in bps]), use_container_width=True, hide_index=True)
else: st.info(“No BPs yet.”)

# ══════════════════════════════════════════════════════════════════════════════

# HALL OF FAME

# ══════════════════════════════════════════════════════════════════════════════

def render_podium(title, data, stat_label):
st.markdown(f”### {title}”)
if not data: st.info(“Not enough data.”); st.markdown(”—”); return
colors=[”#FFD700”,”#C0C0C0”,”#CD7F32”]
sizes=[“1.3em”,“1.1em”,“1em”]
pads=[“20px”,“15px”,“12px”]
cols=st.columns([1,1.3,1])
for ci,pos in enumerate([1,0,2]):
if pos >= len(data): continue
name,val = data[pos]
with cols[ci]:
st.markdown(f”””<div style='background:{colors[pos]};padding:{pads[pos]};border-radius:12px;
text-align:center;color:#000;margin:5px'>

<div style='font-size:{sizes[pos]};font-weight:bold'>{"🥇🥈🥉"[pos]}</div>
<div style='font-weight:bold'>{name}</div>
<div style='font-size:0.85em'>{stat_label}: <b>{val}</b></div>
</div>""", unsafe_allow_html=True)
    st.markdown("---")

def page_hall_of_fame():
st.title(“🏅 Hall of Fame”)
st.markdown(”—”)
users   = get_playing_users()
matches = get_matches()
done    = [m for m in matches if m.get(“status”)==“done”]
mnames  = [m[“match_name”] for m in done]
if not users or not done: st.info(“Not enough data yet.”); return
all_preds = db().table(“predictions”).select(”*”).execute().data or []
all_bps   = db().table(“pool_bps”).select(”*”).execute().data or []
stats = {}
for u in users:
un=u[“username”]; team=u.get(“team_name”) or un
up=[p for p in all_preds if p[“player”]==un and p.get(“actual_score”) is not None]
ubps=[b for b in all_bps if b[“player”]==un]
first=second=0
for mn in mnames:
r=calc_rank(un,mn,all_preds)
if r==1: first+=1
elif r==2: second+=1
tmpl_counts={}
for b in ubps:
k=b.get(“template_key”,””)
if k and k!=“custom”: tmpl_counts[k]=tmpl_counts.get(k,0)+1
stats[un]={
“team”:team,“total”:int(total_pts(un)),
“sp_wins”:calc_sp_wins(un,all_preds,mnames),
“first”:first,“second”:second,
“bp_correct”:sum(1 for b in ubps if b.get(“result”)==“correct”),
“bp_wrong”:sum(1 for b in ubps if b.get(“result”)==“wrong”),
“exact”:exact_count(un),
“margin”:sum(abs(int(p.get(“predicted_score”) or 0)-int(p.get(“actual_score”) or 0)) for p in up),
“custom_bps”:sum(1 for b in ubps if b.get(“bp_type”)==“custom”),
“attended”:len(set(p[“match_name”] for p in all_preds if p[“player”]==un)),
“corr_w”:sum(1 for p in up if caps(p.get(“predicted_winner”,””))==caps(p.get(“actual_winner”,””))),
“corr_wk”:sum(1 for p in up if int(p.get(“predicted_wickets”) or -1)==int(p.get(“actual_wickets”) or -2)),
“top_tmpl_cnt”:max(tmpl_counts.values()) if tmpl_counts else 0,
“cur_streak”:current_streak(un),
}
def top3(key,rev=True):
s=sorted(stats.items(),key=lambda x:x[1][key],reverse=rev)
return [(stats[u][“team”],stats[u][key]) for u,_ in s[:3]]
c1,c2=st.columns(2)
with c1:
render_podium(‘👑 “Too Good”’,top3(“sp_wins”),“SP Wins”)
render_podium(‘⚡ “The Psychic”’,top3(“exact”),“Exact Predictions”)
render_podium(‘🧠 “Big Brain”’,top3(“bp_correct”),“BPs Correct”)
render_podium(‘🎯 “The Uncrowned King”’,top3(“margin”,rev=False),“Margin of Error”)
render_podium(‘🏏 “Team Whisperer”’,top3(“corr_w”),“Correct Winners”)
render_podium(‘🎳 “Wicket Whisperer”’,top3(“corr_wk”),“Correct Wickets”)
render_podium(‘🏃 “Never Misses”’,top3(“attended”),“Matches Attended”)
render_podium(‘🔥 “On Demon Time”’,top3(“cur_streak”),“Current Streak”)
with c2:
render_podium(‘💀 “Absolute Clown”’,top3(“bp_wrong”),“BPs Wrong”)
render_podium(‘🎲 “Asks Nobody”’,top3(“custom_bps”),“Custom BPs”)
render_podium(‘😤 “Uncrowned Prince”’,top3(“second”),“2nd Place Finishes”)
render_podium(‘💨 “What Are You Watching”’,top3(“margin”),“Margin of Error”)
render_podium(‘🪣 “Touch Grass”’,top3(“total”,rev=False),“Total Points”)
render_podium(‘🛋️ “Checked Out”’,top3(“attended”,rev=False),“Matches Attended”)
render_podium(‘🔒 “Boring But Elite”’,top3(“first”),“1st Place Finishes”)
render_podium(‘🃏 “One Trick Pony”’,top3(“top_tmpl_cnt”),“Same BP Used”)

# ══════════════════════════════════════════════════════════════════════════════

# BP POOL

# ══════════════════════════════════════════════════════════════════════════════

def page_bp_pool():
st.title(“🎱 BP Pool”)
st.markdown(“✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt** | 🚫 Dismissed → **0 pts**”)
st.markdown(”—”)
matches = [m for m in get_matches() if not m.get(“bp_locked”)]
if not matches: st.warning(“⏳ No open matches.”); return
mm = get_match_map()
match_sel = st.selectbox(“Select Match”, [f”#{mm.get(m[‘match_name’],’?’)} — {m[‘match_name’]}” for m in matches])
match_name = match_sel.split(” — “,1)[1]
existing = db().table(“pool_bps”).select(”*”).eq(“player”, st.session_state.user[“username”]).eq(“match_name”, match_name).execute().data or []
if existing:
b=existing[0]
icon=“✅” if b.get(“result”)==“correct” else “❌” if b.get(“result”)==“wrong” else “🚫” if b.get(“result”)==“dismissed” else “⏳”
st.warning(“✅ Already submitted!”)
st.info(f”{icon} **{b[‘prediction_text’]}** | Pts: {int(float(b.get(‘points_awarded’,0)))}”)
return

```
# Category tabs
tabs = st.tabs(list(BP_POOL.keys()))
for tab, cat in zip(tabs, BP_POOL.keys()):
    with tab:
        for bp in BP_POOL[cat]:
            if st.button(bp["display"], key=f"bp_{bp['key']}", use_container_width=True):
                st.session_state.sel_bp = bp
                st.rerun()

st.markdown("---")

# Fill in section
if st.session_state.get("sel_bp"):
    bp = st.session_state.sel_bp
    st.markdown(f"#### Selected: *{bp['display']}*")
    if bp.get("note"): st.info(f"ℹ️ **Note:** {bp['note']}")
    inputs = []
    cols_input = st.columns(len(bp["fields"]))
    for i, (col, field) in enumerate(zip(cols_input, bp["fields"])):
        with col:
            val = st.text_input(field["label"], placeholder=field["ph"], key=f"inp_{i}")
            inputs.append(val)
    if all(v.strip() for v in inputs):
        preview = build_prediction_text(bp["display"], inputs)
        st.success(f"📋 Preview: **{preview}**")
    if st.button("🚀 Submit this BP", use_container_width=True):
        if not all(v.strip() for v in inputs):
            st.error("Fill in all blanks!")
        else:
            final = build_prediction_text(bp["display"], inputs)
            db().table("pool_bps").insert({
                "match_name": match_name, "player": st.session_state.user["username"],
                "bp_type": "pool", "template_key": bp["key"],
                "fill_in": "|".join(v.strip() for v in inputs),
                "prediction_text": final, "status": "pending",
                "points_awarded": 0, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.session_state.sel_bp = None
            st.success(f"✅ Submitted: **{final}**")
            st.balloons()

st.markdown("---")
st.markdown("### 💡 Custom BP")
st.caption("Clear it with admin on WhatsApp first!")
custom = st.text_area("Your custom BP:", placeholder="e.g. SRH will bowl 24 wides")
if st.button("🚀 Submit Custom BP", use_container_width=True):
    if not custom.strip(): st.error("Enter your BP!")
    else:
        ex2 = db().table("pool_bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match_name).execute().data or []
        if ex2: st.error("Already submitted a BP for this match!")
        else:
            db().table("pool_bps").insert({
                "match_name": match_name, "player": st.session_state.user["username"],
                "bp_type": "custom", "template_key": "custom", "fill_in": "",
                "prediction_text": custom.strip(), "status": "pending",
                "points_awarded": 0, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ Custom BP submitted!")
            st.balloons()
```

# ══════════════════════════════════════════════════════════════════════════════

# SCORE PREDICTION

# ══════════════════════════════════════════════════════════════════════════════

def page_submit_sp():
st.title(“🔮 Score Prediction”)
st.markdown(”—”)
matches = [m for m in get_matches() if not m.get(“sp_locked”)]
if not matches: st.warning(“⏳ No open matches.”); return
mm = get_match_map()
match_sel = st.selectbox(“Select Match”, [f”#{mm.get(m[‘match_name’],’?’)} — {m[‘match_name’]}” for m in matches])
match_name = match_sel.split(” — “,1)[1]
existing = db().table(“predictions”).select(”*”).eq(“player”, st.session_state.user[“username”]).eq(“match_name”, match_name).execute().data or []
if existing:
p=existing[0]
st.warning(“✅ Already submitted!”)
st.info(f”**{p[‘predicted_score’]} - {str(p.get(‘predicted_wickets’,0)).zfill(2)} | {p[‘predicted_winner’]}** | Pts: {int(float(p.get(‘points_awarded’,0)))}”)
return
c1,c2 = st.columns(2)
with c1:
ps = st.number_input(“Predicted Score (runs)”, min_value=0, max_value=400, step=1)
pw = st.number_input(“Predicted Wickets (0-10)”, min_value=0, max_value=10, step=1)
with c2:
winner_raw = st.text_input(“Predicted Winner”)
winner = caps(winner_raw)
if winner: st.caption(f”Team: **{winner}**”)
st.caption(f”Your prediction: **{ps} - {str(pw).zfill(2)} | {winner}**”)
if st.button(“🚀 Submit”, use_container_width=True):
if not winner: st.error(“Enter the winner!”)
else:
db().table(“predictions”).insert({
“match_name”: match_name, “player”: st.session_state.user[“username”],
“predicted_score”: ps, “predicted_wickets”: pw,
“predicted_winner”: winner, “points_awarded”: 0,
“submitted_at”: datetime.now().strftime(”%Y-%m-%d %H:%M”)
}).execute()
st.success(“✅ Prediction submitted!”)

# ══════════════════════════════════════════════════════════════════════════════

# BP RESULTS

# ══════════════════════════════════════════════════════════════════════════════

def page_bp_results():
st.title(“📝 BP Results”)
st.markdown(”—”)
pending = db().table(“pool_bps”).select(”*”).eq(“status”,“pending”).execute().data or []
if not pending: st.info(“No BPs waiting.”); return
match_list = list(set(b[“match_name”] for b in pending))
sel = st.selectbox(“Filter by Match”, [“All”] + match_list)
filtered = pending if sel==“All” else [b for b in pending if b[“match_name”]==sel]
for b in filtered:
bp_type = “💡 Custom” if b.get(“bp_type”)==“custom” else “🎱 Pool”
st.markdown(f”**{get_team(b[‘player’])}** — {b[‘match_name’]} {bp_type}”)
st.markdown(f”*{b[‘prediction_text’]}*”)
c1,c2,c3 = st.columns(3)
with c1:
if st.button(“✅ Correct (+3)”, key=f”c_{b[‘id’]}”):
db().table(“pool_bps”).update({“result”:“correct”,“points_awarded”:3,“status”:“done”}).eq(“id”,b[“id”]).execute()
st.rerun()
with c2:
if st.button(“❌ Wrong (-1)”, key=f”w_{b[‘id’]}”):
db().table(“pool_bps”).update({“result”:“wrong”,“points_awarded”:-1,“status”:“done”}).eq(“id”,b[“id”]).execute()
st.rerun()
if b.get(“bp_type”)==“custom”:
with c3:
if st.button(“🚫 Dismiss (0)”, key=f”d_{b[‘id’]}”):
db().table(“pool_bps”).update({“result”:“dismissed”,“points_awarded”:0,“status”:“done”}).eq(“id”,b[“id”]).execute()
st.rerun()
st.markdown(”—”)

# ══════════════════════════════════════════════════════════════════════════════

# ENTER RESULTS

# ══════════════════════════════════════════════════════════════════════════════

def page_enter_results():
st.title(“🏆 Enter Match Results”)
st.markdown(”—”)
matches = get_matches()
mm = {m[“match_name”]: i+1 for i, m in enumerate(matches)}
pending = [m for m in matches if m.get(“sp_locked”) and m.get(“status”) not in [“done”,“cancelled”]]
if not pending: st.info(“No matches waiting for results.”); return
sel = st.selectbox(“Select Match”, [f”#{mm[m[‘match_name’]]} — {m[‘match_name’]}” for m in pending])
match_name = sel.split(” — “,1)[1]
actual_score   = st.number_input(“Actual Score (runs)”, min_value=0, max_value=500, step=1)
actual_wickets = st.number_input(“Actual Wickets”, min_value=0, max_value=10, step=1)
aw_raw = st.text_input(“Actual Winner”)
aw = caps(aw_raw)
if aw: st.caption(f”Team: **{aw}**”)
if st.button(“✅ Submit Result & Award Points”, use_container_width=True):
if not aw: st.error(“Enter winner!”)
else:
award_sp_points(match_name, actual_score, actual_wickets, aw)
st.success(“✅ Results submitted!”)
st.rerun()

# ══════════════════════════════════════════════════════════════════════════════

# LOCK / CANCEL

# ══════════════════════════════════════════════════════════════════════════════

def page_lock_cancel():
st.title(“🔒 Lock / Cancel”)
st.markdown(”—”)
matches = get_matches()
if not matches: st.info(“No matches.”); return
user = st.session_state.user
now  = datetime.now().strftime(”%Y-%m-%d %H:%M”)
mm   = {m[“match_name”]: i+1 for i, m in enumerate(matches)}
for m in matches:
with st.expander(f”Match #{mm[m[‘match_name’]]} — {m[‘match_name’]} | {m.get(‘status’,‘open’).upper()}”):
c1,c2 = st.columns(2)
with c1:
if m.get(“bp_locked”):
st.success(f”🔒 BP locked by **{get_team(m.get(‘bp_locked_by’,’’))}** at {m.get(‘bp_locked_at’,’’)}”)
if st.button(“🔓 Unlock BP”, key=f”ubp_{m[‘id’]}”):
db().table(“matches”).update({“bp_locked”:False,“bp_locked_by”:None,“bp_locked_at”:None}).eq(“id”,m[“id”]).execute()
st.rerun()
else:
if st.button(“🔒 Lock BP”, key=f”lbp_{m[‘id’]}”):
db().table(“matches”).update({“bp_locked”:True,“bp_locked_by”:user[“username”],“bp_locked_at”:now}).eq(“id”,m[“id”]).execute()
st.rerun()
with c2:
if m.get(“sp_locked”):
st.success(f”🔒 SP locked by **{get_team(m.get(‘sp_locked_by’,’’))}** at {m.get(‘sp_locked_at’,’’)}”)
if st.button(“🔓 Unlock SP”, key=f”usp_{m[‘id’]}”):
db().table(“matches”).update({“sp_locked”:False,“sp_locked_by”:None,“sp_locked_at”:None}).eq(“id”,m[“id”]).execute()
st.rerun()
else:
if st.button(“🔒 Lock SP”, key=f”lsp_{m[‘id’]}”):
db().table(“matches”).update({“sp_locked”:True,“sp_locked_by”:user[“username”],“sp_locked_at”:now}).eq(“id”,m[“id”]).execute()
st.rerun()
if m.get(“status”) != “cancelled”:
st.markdown(”**🌧️ Cancel due to rain:**”)
cancel_type = st.selectbox(“What to cancel?”,
[“Select…”,“Cancel BP only”,“Cancel SP only”,“Cancel both BP and SP”],
key=f”csel_{m[‘id’]}”)
if cancel_type != “Select…”:
if st.button(f”🌧️ Confirm — {cancel_type}”, key=f”cancel_{m[‘id’]}”):
if “BP” in cancel_type:
db().table(“pool_bps”).update({“points_awarded”:0,“status”:“cancelled”}).eq(“match_name”,m[“match_name”]).execute()
if “SP” in cancel_type:
db().table(“predictions”).update({“points_awarded”:0,“status”:“cancelled”}).eq(“match_name”,m[“match_name”]).execute()
if cancel_type == “Cancel both BP and SP”:
db().table(“matches”).update({“status”:“cancelled”}).eq(“id”,m[“id”]).execute()
st.success(f”✅ {cancel_type} done!”)
st.rerun()

# ══════════════════════════════════════════════════════════════════════════════

# MATCH DETAILS

# ══════════════════════════════════════════════════════════════════════════════

def page_match_details():
st.title(“📋 Match Details”)
st.markdown(”—”)
matches = get_matches()
if not matches: st.info(“No matches yet.”); return
mm = {m[“match_name”]: i+1 for i, m in enumerate(matches)}
options = [f”Match #{mm[m[‘match_name’]]} — {m[‘match_name’]}” for m in matches]
idx = st.selectbox(“Select Match”, range(len(matches)), format_func=lambda i: options[i])
m = matches[idx]
st.markdown(f”### 🏏 Match #{mm[m[‘match_name’]]} — {m[‘match_name’]} | {m.get(‘match_date’,’’)}”)
c1,c2,c3 = st.columns(3)
c1.metric(“BP”,“🔒 Locked” if m.get(“bp_locked”) else “🟢 Open”)
c2.metric(“SP”,“🔒 Locked” if m.get(“sp_locked”) else “🟢 Open”)
c3.metric(“Status”,m.get(“status”,“open”).upper())
if m.get(“actual_score”):
st.success(f”**Result:** {m.get(‘actual_winner’)} won | {m.get(‘actual_score’)} - {str(m.get(‘actual_wickets’,0)).zfill(2)}”)
st.markdown(”—”)
st.subheader(“🎱 Bold Predictions”)
bps = db().table(“pool_bps”).select(”*”).eq(“match_name”,m[“match_name”]).execute().data or []
if bps:
st.dataframe(pd.DataFrame([{
“”:“✅” if b.get(“result”)==“correct” else “❌” if b.get(“result”)==“wrong” else “🚫” if b.get(“result”)==“dismissed” else “⏳”,
“Team”:get_team(b[“player”]),“Prediction”:b[“prediction_text”],
“Type”:“💡” if b.get(“bp_type”)==“custom” else “🎱”,
“Pts”:int(float(b.get(“points_awarded”,0)))
} for b in bps]), use_container_width=True, hide_index=True)
else: st.info(“No BPs.”)
st.markdown(”—”)
st.subheader(“🔮 Score Predictions”)
preds = db().table(“predictions”).select(”*”).eq(“match_name”,m[“match_name”]).execute().data or []
if preds:
preds_s = sorted(preds, key=lambda x: x.get(“points_awarded”,0), reverse=True)
st.dataframe(pd.DataFrame([{
“”:“🥇” if i==0 and (p.get(“points_awarded”) or 0)>=4 else “”,
“Team”:get_team(p[“player”]),
“Predicted”:f”{p.get(‘predicted_score’)} - {str(p.get(‘predicted_wickets’,0)).zfill(2)} | {p.get(‘predicted_winner’,’’)}”,
“Actual”:f”{m.get(‘actual_score’)} - {str(m.get(‘actual_wickets’,0)).zfill(2)} | {m.get(‘actual_winner’,’’)}” if m.get(“actual_score”) else “-”,
“⚡”:“⚡” if m.get(“actual_score”) and int(p.get(“predicted_score”) or 0)==m.get(“actual_score”) else “”,
“Pts”:int(float(p.get(“points_awarded”,0)))
} for i,p in enumerate(preds_s)]), use_container_width=True, hide_index=True)
else: st.info(“No predictions.”)

# ══════════════════════════════════════════════════════════════════════════════

# SEASON PREDICTIONS

# ══════════════════════════════════════════════════════════════════════════════

def page_season_predictions():
st.title(“🌟 Season Predictions”)
st.markdown(”—”)
user = st.session_state.user
un   = user[“username”]
all_sp = db().table(“season_predictions”).select(”*”).execute().data or []
if all_sp:
st.subheader(“Everyone’s Predictions”)
st.dataframe(pd.DataFrame([{
“Team”:get_team(sp[“player”]),
“🧡 Orange Cap”:sp.get(“orange_cap”),“💜 Purple Cap”:sp.get(“purple_cap”),
“🌟 Emerging”:sp.get(“emerging_player”),
“Top 4”:f”{sp.get(‘top1’)}→{sp.get(‘top2’)}→{sp.get(‘top3’)}→{sp.get(‘top4’)}”,
“Pts”:int(float(sp.get(“points_awarded”,0)))
} for sp in all_sp]), use_container_width=True, hide_index=True)
st.markdown(”—”)
if user[“role”]==“guest”: return
existing = db().table(“season_predictions”).select(”*”).eq(“player”,un).execute().data or []
if existing: st.success(“✅ Your season predictions already submitted!”); return
st.subheader(“Submit Your Predictions”)
st.markdown(”**Points:** Orange Cap=20 | Purple Cap=20 | Emerging=15 | Top4 team=6 (+4 if position correct)”)
oc=st.text_input(“🧡 Orange Cap”); pc=st.text_input(“💜 Purple Cap”); em=st.text_input(“🌟 Emerging Player”)
t1=st.text_input(“1st”); t2=st.text_input(“2nd”); t3=st.text_input(“3rd”); t4=st.text_input(“4th”)
if st.button(“🚀 Submit”, use_container_width=True):
if not all([oc,pc,em,t1,t2,t3,t4]): st.error(“Fill all fields!”)
else:
db().table(“season_predictions”).insert({
“player”:un,“orange_cap”:caps(oc),“purple_cap”:caps(pc),
“emerging_player”:caps(em),“top1”:caps(t1),“top2”:caps(t2),
“top3”:caps(t3),“top4”:caps(t4),“points_awarded”:0
}).execute()
st.success(“✅ Submitted!”)
st.rerun()

# ══════════════════════════════════════════════════════════════════════════════

# HOW TO SCORE

# ══════════════════════════════════════════════════════════════════════════════

def page_how_to_score():
st.title(“📖 How to Score”)
st.markdown(”—”)
st.subheader(“🎱 BP Pool”)
st.markdown(”- Pick a template, fill in the blanks\n- Custom BP: clear with admin on WhatsApp first\n- ✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt** | 🚫 Dismissed → **0 pts**”)
st.markdown(”—”)
st.subheader(“🔮 Score Predictions (SP)”)
st.markdown(”- Predict final score + wickets + winner after 6 overs\n- 🏆 Closest → **+4 pts** | ⚡ Exact → **+6 pts**\n- ✅ Correct winner → **+2 pts**\n- 🎯 Correct wickets (SP winner only) → **+1 pt**\n- Tie → both get points”)
st.markdown(”—”)
st.subheader(“🔥 Streak Points”)
st.markdown(”- 2 SP wins in a row → **+1** | 3 → **+2** | keeps going forever!\n- Resets if you don’t win”)
st.markdown(”—”)
st.subheader(“🌟 Season Predictions”)
st.markdown(”- 🧡 Orange Cap → **20 pts** | 💜 Purple Cap → **20 pts**\n- 🌟 Emerging → **15 pts**\n- 🏏 Top 4 team → **6 pts** (+4 if position correct)”)

# ══════════════════════════════════════════════════════════════════════════════

# KING’S PANEL

# ══════════════════════════════════════════════════════════════════════════════

def page_admin():
st.title(“⚙️ King’s Panel”)
st.markdown(”—”)
tab1,tab2,tab3 = st.tabs([“➕ Matches”,“👥 Players”,“🌟 Season Results”])
with tab1:
mn=st.text_input(“Match Name”); md=st.date_input(“Date”)
if st.button(“Add Match”):
if mn.strip():
db().table(“matches”).insert({
“match_name”:caps(mn),“match_date”:str(md),
“status”:“open”,“bp_locked”:False,“sp_locked”:False
}).execute()
st.success(“✅ Match added!”)
st.rerun()
st.markdown(”—”)
matches=get_matches()
mm={m[“match_name”]:i+1 for i,m in enumerate(matches)}
for m in matches:
bp=“🔒” if m.get(“bp_locked”) else “🟢”
sp=“🔒” if m.get(“sp_locked”) else “🟢”
st.write(f”**#{mm[m[‘match_name’]]}** 🏏 **{m[‘match_name’]}** | BP:{bp} SP:{sp} | {m.get(‘status’,‘open’)}”)
with tab2:
nu=st.text_input(“Username”); np=st.text_input(“Password”)
nr=st.selectbox(“Role”,ALL_ROLES,format_func=lambda x:ROLE_LABELS.get(x,x))
nd=st.text_input(“Display Name”); nt=st.text_input(“Team Name”)
if st.button(“Add Player”):
if nu.strip() and np.strip() and nd.strip():
db().table(“users”).insert({
“username”:nu.strip(),“password”:np.strip(),
“role”:nr,“display_name”:nd.strip(),“team_name”:nt.strip()
}).execute()
st.success(f”✅ {nd} added!”)
st.rerun()
st.markdown(”—”)
for u in (db().table(“users”).select(”*”).execute().data or []):
st.write(f”{ROLE_LABELS.get(u[‘role’],’?’)} **{u.get(‘team_name’) or u[‘display_name’]}** | `{u['username']}`”)
with tab3:
oc=st.text_input(“🧡 Orange Cap”); pc=st.text_input(“💜 Purple Cap”); em=st.text_input(“🌟 Emerging”)
t1=st.text_input(“1st”); t2=st.text_input(“2nd”); t3=st.text_input(“3rd”); t4=st.text_input(“4th”)
if st.button(“Award Season Points”):
actuals={“oc”:caps(oc),“pc”:caps(pc),“em”:caps(em),“t1”:caps(t1),“t2”:caps(t2),“t3”:caps(t3),“t4”:caps(t4)}
for sp in (db().table(“season_predictions”).select(”*”).execute().data or []):
pts=0
if sp.get(“orange_cap”,””).upper()==actuals[“oc”]: pts+=20
if sp.get(“purple_cap”,””).upper()==actuals[“pc”]: pts+=20
if sp.get(“emerging_player”,””).upper()==actuals[“em”]: pts+=15
at4=[actuals[“t1”],actuals[“t2”],actuals[“t3”],actuals[“t4”]]
pt4=[sp.get(“top1”,””).upper(),sp.get(“top2”,””).upper(),sp.get(“top3”,””).upper(),sp.get(“top4”,””).upper()]
for j,tn in enumerate(pt4):
if tn in at4:
pts+=6
if tn==at4[j]: pts+=4
db().table(“season_predictions”).update({“points_awarded”:pts}).eq(“id”,sp[“id”]).execute()
st.success(“✅ Done!”)

# ══════════════════════════════════════════════════════════════════════════════

# MAIN

# ══════════════════════════════════════════════════════════════════════════════

def main():
st.set_page_config(page_title=“LFxCT”, page_icon=“🏏”, layout=“wide”)
defaults = [(“user”,None),(“page”,“🏆 Leaderboard”),(“sel_bp”,None)]
for k,v in defaults:
if k not in st.session_state: st.session_state[k]=v

```
if st.session_state.user is None:
    st.title("🏏 LFxCT")
    st.markdown("---")
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        st.subheader("Login")
        username=st.text_input("Username")
        password=st.text_input("Password",type="password")
        if st.button("Login",use_container_width=True):
            user=login(username,password)
            if user:
                st.session_state.user=user
                st.session_state.page="🏆 Leaderboard"
                st.rerun()
            else: st.error("Wrong username or password!")
        st.markdown("---")
        if st.button("👁️ Continue as Guest",use_container_width=True):
            st.session_state.user={"username":"guest","display_name":"Guest","role":"guest"}
            st.session_state.page="🏆 Leaderboard"
            st.rerun()
    return

user=st.session_state.user
role=user["role"]
pages=get_pages(role)
if st.session_state.page not in pages: st.session_state.page=pages[0]

c1,c2,c3=st.columns([2,4,1])
with c1:
    team_display=get_team(user["username"]) if role!="guest" else "Guest"
    st.markdown("**🏏 LFxCT**")
    st.caption(f"{ROLE_LABELS.get(role,role)} — {team_display}")
with c2:
    sel=st.selectbox("nav",pages,index=pages.index(st.session_state.page),
        label_visibility="collapsed",key="top_nav")
    if sel!=st.session_state.page:
        st.session_state.page=sel
        st.rerun()
with c3:
    if st.button("🔙" if role=="guest" else "🚪",use_container_width=True):
        st.session_state.user=None
        st.rerun()

st.markdown("---")

page=st.session_state.page
if   page=="🏆 Leaderboard":       page_leaderboard()
elif page=="📊 Overall Stats":      page_overall_stats()
elif page=="👤 Player Stats":       page_player_stats()
elif page=="🏅 Hall of Fame":       page_hall_of_fame()
elif page=="🎱 BP Pool":            page_bp_pool()
elif page=="🔮 Score Prediction":   page_submit_sp()
elif page=="🏆 Enter Results":      page_enter_results()
elif page=="📝 BP Results":         page_bp_results()
elif page=="🔒 Lock / Cancel":      page_lock_cancel()
elif page=="⚙️ King's Panel":       page_admin()
elif page=="📋 Match Details":      page_match_details()
elif page=="📖 How to Score":       page_how_to_score()
elif page=="🌟 Season Predictions": page_season_predictions()
```

if **name**==”**main**”:
main()
