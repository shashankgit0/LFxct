import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# ─── Supabase Setup ────────────────────────────────────────────────────────────

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_client() -> Client:
return create_client(SUPABASE_URL, SUPABASE_KEY)

def db():
return get_client()

# ─── Hide Streamlit branding ───────────────────────────────────────────────────

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

# ─── Role definitions ──────────────────────────────────────────────────────────

ROLE_LABELS = {
“admin”:  “♔ King”,
“player”: “♟ Pawn”,
}
ADMIN_ROLES = [“admin”]
ALL_ROLES   = [“player”, “admin”]

# ─── BP Pool ───────────────────────────────────────────────────────────────────

BP_POOL = {
“🏏 Batting”: [
{“key”: “bat_30”,   “template”: “{name} to score 30+ runs”,          “note”: None},
{“key”: “bat_50”,   “template”: “{name} to score 50+ runs”,          “note”: None},
{“key”: “bat_75”,   “template”: “{name} to score 75+ runs”,          “note”: None},
{“key”: “bat_100”,  “template”: “{name} to score a century (100+)”,  “note”: None},
{“key”: “bat_duck”, “template”: “{name} to score a duck (0 runs)”,   “note”: None},
{“key”: “bat_top”,  “template”: “{name} to be the highest scorer”,   “note”: None},
{“key”: “bat_sr200”,“template”: “{name} to have 200+ strike rate”,   “note”: “Min 10 balls faced”},
{“key”: “bat_sr150”,“template”: “{name} to have 150+ strike rate”,   “note”: “Min 10 balls faced”},
{“key”: “bat_out14”,“template”: “{name} to get out in <14 balls”,    “note”: “Applies to openers only”},
{“key”: “bat_b1”,   “template”: “{name} to hit a boundary on ball 1”,“note”: “First ball of innings only”},
{“key”: “bat_six1”, “template”: “{name} to hit a six on ball 1”,     “note”: “First ball of innings only”},
{“key”: “bat_6s”,   “template”: “{name} to hit 3+ sixes”,            “note”: None},
{“key”: “bat_4s”,   “template”: “{name} to hit 5+ fours”,            “note”: None},
{“key”: “bat_haf”,  “template”: “{name} to score a half century in <20 balls”, “note”: None},
],
“🎳 Bowling”: [
{“key”: “bowl_1w”,  “template”: “{name} to take 1+ wicket”,          “note”: None},
{“key”: “bowl_2w”,  “template”: “{name} to take 2+ wickets”,         “note”: None},
{“key”: “bowl_3w”,  “template”: “{name} to take 3+ wickets”,         “note”: None},
{“key”: “bowl_mdn”, “template”: “{name} to bowl a maiden over”,      “note”: None},
{“key”: “bowl_top”, “template”: “{name} to be the top wicket taker”, “note”: None},
{“key”: “bowl_eco”, “template”: “{name} to have economy <6”,         “note”: “Min 2 overs bowled”},
{“key”: “bowl_dot”, “template”: “{name} to bowl 10+ dot balls”,      “note”: None},
{“key”: “bowl_wb”,  “template”: “{name} to bowl 3+ wides”,           “note”: None},
{“key”: “bowl_nb”,  “template”: “{name} to bowl 2+ no balls”,        “note”: None},
{“key”: “bowl_hat”, “template”: “{name} to take a hat-trick”,        “note”: “Rare but legendary 🔥”},
],
“🔥 Team”: [
{“key”: “team_180”, “template”: “{name} team to score 180+ runs”,    “note”: None},
{“key”: “team_200”, “template”: “{name} team to score 200+ runs”,    “note”: None},
{“key”: “team_140”, “template”: “{name} team to score under 140”,    “note”: None},
{“key”: “team_6s11”,“template”: “{name} team to hit 11+ sixes”,      “note”: None},
{“key”: “team_6s15”,“template”: “{name} team to hit 15+ sixes”,      “note”: None},
{“key”: “team_4s19”,“template”: “{name} team to hit 19+ fours”,      “note”: None},
{“key”: “team_pp50”,“template”: “{name} team to score 50+ in powerplay”, “note”: “First 6 overs”},
{“key”: “team_pp60”,“template”: “{name} team to score 60+ in powerplay”, “note”: “First 6 overs”},
{“key”: “team_win10”,“template”: “{name} team to win by 10+ wickets”,“note”: None},
{“key”: “team_win50”,“template”: “{name} team to win by 50+ runs”,   “note”: None},
{“key”: “team_allout”,“template”: “{name} team to be all out”,       “note”: None},
],
“⭐ Special”: [
{“key”: “sp_mom”,   “template”: “{name} to win Man of the Match”,    “note”: None},
{“key”: “sp_catch”, “template”: “{name} to take 2+ catches”,         “note”: None},
{“key”: “sp_runout”,“template”: “{name} to be involved in a run out”,“note”: “Either as fielder or batsman”},
{“key”: “sp_6pp”,   “template”: “{name} to hit a six in the powerplay”, “note”: “First 6 overs”},
{“key”: “sp_lastball”,“template”: “{name} team to win off the last ball”, “note”: None},
{“key”: “sp_super”, “template”: “Match to go to a Super Over”,       “note”: “No name needed — type ‘Super Over’”},
{“key”: “sp_fifty6”,“template”: “{name} to score 50 in exactly 6 balls”, “note”: “Rare — almost impossible 🔥”},
],
}

# ─── Helpers ───────────────────────────────────────────────────────────────────

def get_all_users():
return db().table(“users”).select(”*”).execute().data or []

def get_playing_users():
return [u for u in get_all_users() if u[“role”] not in ADMIN_ROLES]

def get_user_display(username):
for u in get_all_users():
if u[“username”] == username:
return u[“display_name”]
return username

def caps(text):
return text.strip().upper() if text else “”

def get_player_bp_points(username):
total = 0
for b in db().table(“pool_bps”).select(“points_awarded”).eq(“player”, username).execute().data or []:
try: total += float(b.get(“points_awarded”) or 0)
except: pass
return round(total, 2)

def get_player_sp_points(username):
total = 0
for p in db().table(“predictions”).select(“points_awarded”).eq(“player”, username).execute().data or []:
try: total += float(p.get(“points_awarded”) or 0)
except: pass
return round(total, 2)

def get_player_streak_points(username):
total = 0
for s in db().table(“streaks”).select(“bonus_points”).eq(“player”, username).execute().data or []:
try: total += float(s.get(“bonus_points”) or 0)
except: pass
return round(total, 2)

def get_player_exact_count(username):
count = 0
for p in db().table(“predictions”).select(”*”).eq(“player”, username).execute().data or []:
if p.get(“actual_score”) is not None:
if int(p.get(“predicted_score”) or 0) == int(p.get(“actual_score”) or -1):
count += 1
return count

def get_player_season_points(username):
total = 0
for s in db().table(“season_predictions”).select(“points_awarded”).eq(“player”, username).execute().data or []:
try: total += float(s.get(“points_awarded”) or 0)
except: pass
return round(total, 2)

def get_player_total_points(username):
return round(
get_player_sp_points(username) +
get_player_bp_points(username) +
get_player_streak_points(username) +
get_player_season_points(username), 2)

def get_current_streak(username):
preds = db().table(“predictions”).select(”*”).eq(“player”, username).execute().data or []
done  = sorted([p for p in preds if p.get(“actual_score”) is not None],
key=lambda x: x.get(“submitted_at”,””), reverse=True)
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

def streak_bonus_for(n):
return max(0, n - 1)

def login(username, password):
res = db().table(“users”).select(”*”).eq(“username”, username).eq(“password”, password).execute()
return res.data[0] if res.data else None

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
pts       = 0
is_winner = p[“diff”] == min_diff
is_exact  = int(p.get(“predicted_score”) or 0) == actual_score
corr_win  = caps(p.get(“predicted_winner”,””)) == actual_winner
corr_wkt  = int(p.get(“predicted_wickets”) or -1) == actual_wickets
if is_exact:    pts += 6
elif is_winner: pts += 4
if corr_win:    pts += 2
if is_winner and corr_wkt: pts += 1
db().table(“predictions”).update({
“actual_score”: actual_score, “actual_wickets”: actual_wickets,
“actual_winner”: actual_winner, “points_awarded”: pts
}).eq(“id”, p[“id”]).execute()
for w in winners:
uname  = w[“player”]
streak = get_current_streak(uname)
bonus  = streak_bonus_for(streak)
if bonus > 0:
db().table(“streaks”).insert({
“player”: uname, “match_name”: match_sel,
“streak_count”: streak, “bonus_points”: bonus
}).execute()

def get_pages(role):
if role == “guest”:
return [“🏆 Leaderboard”,“📊 Stats”,“📋 Match Details”,“📖 How to Score”,“🌟 Season Predictions”]
pages = [“🏆 Leaderboard”,“📊 Stats”,“📋 Match Details”,“📖 How to Score”,
“🌟 Season Predictions”,“🎱 BP Pool”,“🔮 Score Prediction”]
if role == “admin”:
pages += [“🏆 Enter Results”,“📝 BP Results”,“🔒 Lock BP/SP”,“⚙️ King’s Panel”]
return pages

# ══════════════════════════════════════════════════════════════════════════════

# PAGES

# ══════════════════════════════════════════════════════════════════════════════

def page_leaderboard():
st.title(“🏆 LFxCT Leaderboard”)
st.markdown(”—”)
users = get_playing_users()
if not users:
st.info(“No players yet.”)
return
rows = []
for u in users:
uname  = u[“username”]
sp     = get_player_sp_points(uname)
bp     = get_player_bp_points(uname)
streak = get_player_streak_points(uname)
exact  = get_player_exact_count(uname)
total  = round(sp + bp + streak, 2)
cur_streak = get_current_streak(uname)
rows.append({
“Rank”:       “”,
“Player”:     u[“display_name”],
“SP Pts”:     sp,
“BP Pts”:     bp,
“Streak Pts”: streak,
“⚡ Exact”:   f”{exact}x” if exact > 0 else “-”,
“🔥 Streak”:  f”{cur_streak} 🔥” if cur_streak > 1 else str(cur_streak),
“Total”:      total
})
rows.sort(key=lambda x: x[“Total”], reverse=True)
medals = [“🥇”,“🥈”,“🥉”]
for i, r in enumerate(rows):
r[“Rank”] = medals[i] if i < 3 else str(i+1)
df = pd.DataFrame(rows)
def style_df(df):
styles = pd.DataFrame(””, index=df.index, columns=df.columns)
styles[“Total”]  = “background-color: #1e2a1e; color: #00ff88; font-weight: bold”
styles[“Player”] = “background-color: #1a1a2e; font-weight: bold”
return styles
st.dataframe(df.style.apply(style_df, axis=None), use_container_width=True, hide_index=True)

def page_bp_pool():
st.title(“🎱 BP Pool”)
st.markdown(“✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt**”)
st.markdown(”—”)

```
matches = [m for m in (db().table("matches").select("*").execute().data or []) if not m.get("bp_locked")]
if not matches:
    st.warning("⏳ No open matches for BP submission.")
    return

match = st.selectbox("Select Match", [m["match_name"] for m in matches])

# Check already submitted
existing = db().table("pool_bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
if existing:
    b = existing[0]
    icon = "✅" if b.get("result") == "correct" else "❌" if b.get("result") == "wrong" else "⏳"
    st.warning("✅ Already submitted for this match!")
    st.info(f"{icon} **{b['prediction_text']}** | Type: {b.get('bp_type','pool')} | Pts: {b.get('points_awarded',0)}")
    return

st.markdown("### Pick your BP:")
st.markdown("")

# Category tabs
categories = list(BP_POOL.keys())
tabs = st.tabs(categories)

selected_template = None
selected_key      = None
selected_note     = None

for tab, cat in zip(tabs, categories):
    with tab:
        for bp in BP_POOL[cat]:
            display_text = bp["template"].replace("{name}", "______")
            if st.button(display_text, key=f"bp_{bp['key']}", use_container_width=True):
                st.session_state.selected_bp_key  = bp["key"]
                st.session_state.selected_bp_tmpl = bp["template"]
                st.session_state.selected_bp_note = bp["note"]
                st.rerun()

st.markdown("---")

# Show fill-in section if template selected
if "selected_bp_key" in st.session_state and st.session_state.selected_bp_key:
    tmpl = st.session_state.selected_bp_tmpl
    note = st.session_state.selected_bp_note

    st.markdown(f"#### Selected: *{tmpl.replace('{name}', '______')}*")

    if note:
        st.info(f"ℹ️ **Note:** {note}")

    if "{name}" in tmpl:
        fill_in = st.text_input("Fill in the blank (player or team name):",
                                 placeholder="e.g. Kohli, SRH, Bumrah...")
        if fill_in:
            preview = tmpl.replace("{name}", f"**{fill_in.strip()}**")
            st.markdown(f"📋 Your BP: *{preview}*")
    else:
        fill_in = tmpl  # no blank needed

    if st.button("🚀 Submit this BP", use_container_width=True):
        if not fill_in or not fill_in.strip():
            st.error("Fill in the blank first!")
        else:
            final_text = tmpl.replace("{name}", fill_in.strip()) if "{name}" in tmpl else tmpl
            db().table("pool_bps").insert({
                "match_name": match,
                "player": st.session_state.user["username"],
                "bp_type": "pool",
                "template_key": st.session_state.selected_bp_key,
                "fill_in": fill_in.strip() if "{name}" in tmpl else "",
                "prediction_text": final_text,
                "status": "pending",
                "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            # Clear selection
            st.session_state.selected_bp_key  = None
            st.session_state.selected_bp_tmpl = None
            st.session_state.selected_bp_note = None
            st.success(f"✅ Submitted: **{final_text}**")
            st.balloons()

st.markdown("---")

# Custom BP section
st.markdown("### 💡 Custom BP")
st.caption("Got something creative? Clear it with admin on WhatsApp first, then submit here.")
custom_bp = st.text_area("Your custom BP:", placeholder="e.g. SRH will bowl 24 wides")
if st.button("🚀 Submit Custom BP", use_container_width=True):
    if not custom_bp.strip():
        st.error("Enter your custom BP!")
    else:
        # Check not already submitted
        existing2 = db().table("pool_bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
        if existing2:
            st.error("You already submitted a BP for this match!")
        else:
            db().table("pool_bps").insert({
                "match_name": match,
                "player": st.session_state.user["username"],
                "bp_type": "custom",
                "template_key": "custom",
                "fill_in": "",
                "prediction_text": custom_bp.strip(),
                "status": "pending",
                "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success(f"✅ Custom BP submitted: **{custom_bp.strip()}**")
            st.balloons()
```

def page_submit_sp():
st.title(“🔮 Score Prediction”)
st.markdown(”—”)
matches = [m for m in (db().table(“matches”).select(”*”).execute().data or []) if not m.get(“sp_locked”)]
if not matches:
st.warning(“⏳ No open matches for Score Prediction.”)
return
match = st.selectbox(“Select Match”, [m[“match_name”] for m in matches])
existing = db().table(“predictions”).select(”*”).eq(“player”, st.session_state.user[“username”]).eq(“match_name”, match).execute().data or []
if existing:
p = existing[0]
st.warning(“✅ Already submitted!”)
st.info(f”**{p[‘predicted_score’]} runs - {str(p.get(‘predicted_wickets’,0)).zfill(2)} wkts** | Winner: {p[‘predicted_winner’]} | Pts: {p.get(‘points_awarded’,0)}”)
return
col1, col2 = st.columns(2)
with col1:
predicted_score   = st.number_input(“Predicted Score (runs)”, min_value=0, max_value=400, step=1)
predicted_wickets = st.number_input(“Predicted Wickets (0-10)”, min_value=0, max_value=10, step=1)
with col2:
predicted_winner_raw = st.text_input(“Predicted Winner”)
predicted_winner     = caps(predicted_winner_raw)
if predicted_winner:
st.caption(f”Team: **{predicted_winner}**”)
st.caption(f”Your prediction: **{predicted_score} runs - {str(predicted_wickets).zfill(2)} wkts**”)
if st.button(“🚀 Submit”, use_container_width=True):
if not predicted_winner:
st.error(“Enter the winner!”)
else:
db().table(“predictions”).insert({
“match_name”: match, “player”: st.session_state.user[“username”],
“predicted_score”: predicted_score, “predicted_wickets”: predicted_wickets,
“predicted_winner”: predicted_winner, “points_awarded”: 0,
“submitted_at”: datetime.now().strftime(”%Y-%m-%d %H:%M”)
}).execute()
st.success(“✅ Prediction submitted!”)

def page_bp_results():
st.title(“📝 BP Results”)
st.markdown(”—”)
pending = db().table(“pool_bps”).select(”*”).eq(“status”,“pending”).execute().data or []
if not pending:
st.info(“No BPs waiting for results.”)
return
matches = list(set(b[“match_name”] for b in pending))
selected_match = st.selectbox(“Filter by Match”, [“All”] + matches)
filtered = pending if selected_match == “All” else [b for b in pending if b[“match_name”] == selected_match]
for b in filtered:
display = get_user_display(b[“player”])
bp_type = “💡 Custom” if b.get(“bp_type”) == “custom” else “🎱 Pool”
st.markdown(f”**{display}** — {b[‘match_name’]} {bp_type}”)
st.markdown(f”*{b[‘prediction_text’]}*”)
col1, col2 = st.columns(2)
with col1:
if st.button(“✅ Correct (+3 pts)”, key=f”c_{b[‘id’]}”):
db().table(“pool_bps”).update({“result”:“correct”,“points_awarded”:3,“status”:“done”}).eq(“id”,b[“id”]).execute()
st.rerun()
with col2:
if st.button(“❌ Wrong (-1 pt)”, key=f”w_{b[‘id’]}”):
db().table(“pool_bps”).update({“result”:“wrong”,“points_awarded”:-1,“status”:“done”}).eq(“id”,b[“id”]).execute()
st.rerun()
st.markdown(”—”)

def page_enter_results():
st.title(“🏆 Enter Match Results”)
st.markdown(”—”)
matches = db().table(“matches”).select(”*”).execute().data or []
pending = [m for m in matches if m.get(“sp_locked”) and m.get(“status”) != “done”]
if not pending:
st.info(“No matches waiting for results.”)
return
match_sel         = st.selectbox(“Select Match”, [m[“match_name”] for m in pending])
actual_score      = st.number_input(“Actual Score (runs)”, min_value=0, max_value=500, step=1)
actual_wickets    = st.number_input(“Actual Wickets”, min_value=0, max_value=10, step=1)
actual_winner_raw = st.text_input(“Actual Winner”)
actual_winner     = caps(actual_winner_raw)
if actual_winner:
st.caption(f”Team: **{actual_winner}**”)
if st.button(“✅ Submit Result & Award Points”, use_container_width=True):
if not actual_winner:
st.error(“Enter winner!”)
else:
award_sp_points(match_sel, actual_score, actual_wickets, actual_winner)
st.success(f”✅ Results submitted for {match_sel}!”)
st.rerun()

def page_lock_match():
st.title(“🔒 Lock / Unlock BP & SP”)
st.markdown(”—”)
matches = db().table(“matches”).select(”*”).execute().data or []
if not matches:
st.info(“No matches.”)
return
user = st.session_state.user
now  = datetime.now().strftime(”%Y-%m-%d %H:%M”)
for m in matches:
with st.expander(f”🏏 {m[‘match_name’]} — {m.get(‘match_date’,’’)}”):
col1, col2 = st.columns(2)
with col1:
if m.get(“bp_locked”):
st.success(f”🔒 BP locked by **{get_user_display(m.get(‘bp_locked_by’,’’))}** at {m.get(‘bp_locked_at’,’’)}”)
if st.button(“🔓 Unlock BP”, key=f”unlockbp_{m[‘id’]}”):
db().table(“matches”).update({“bp_locked”:False,“bp_locked_by”:None,“bp_locked_at”:None}).eq(“id”,m[“id”]).execute()
st.rerun()
else:
if st.button(“🔒 Lock BP”, key=f”lockbp_{m[‘id’]}”):
db().table(“matches”).update({“bp_locked”:True,“bp_locked_by”:user[“username”],“bp_locked_at”:now}).eq(“id”,m[“id”]).execute()
st.rerun()
with col2:
if m.get(“sp_locked”):
st.success(f”🔒 SP locked by **{get_user_display(m.get(‘sp_locked_by’,’’))}** at {m.get(‘sp_locked_at’,’’)}”)
if st.button(“🔓 Unlock SP”, key=f”unlocksp_{m[‘id’]}”):
db().table(“matches”).update({“sp_locked”:False,“sp_locked_by”:None,“sp_locked_at”:None}).eq(“id”,m[“id”]).execute()
st.rerun()
else:
if st.button(“🔒 Lock SP”, key=f”locksp_{m[‘id’]}”):
db().table(“matches”).update({“sp_locked”:True,“sp_locked_by”:user[“username”],“sp_locked_at”:now}).eq(“id”,m[“id”]).execute()
st.rerun()

def page_match_details():
st.title(“📋 Match Details”)
st.markdown(”—”)
matches = db().table(“matches”).select(”*”).execute().data or []
if not matches:
st.info(“No matches yet.”)
return
match_options = [f”Match {i+1} — {m[‘match_name’]}” for i, m in enumerate(matches)]
selected_idx  = st.selectbox(“Select Match”, range(len(matches)), format_func=lambda i: match_options[i])
m = matches[selected_idx]
st.markdown(f”### 🏏 Match {selected_idx+1} — {m[‘match_name’]} | {m.get(‘match_date’,’’)}”)
col1, col2, col3 = st.columns(3)
col1.metric(“BP”, “🔒 Locked” if m.get(“bp_locked”) else “🟢 Open”)
col2.metric(“SP”, “🔒 Locked” if m.get(“sp_locked”) else “🟢 Open”)
col3.metric(“Status”, m.get(“status”,“open”).upper())
if m.get(“actual_score”):
st.success(f”**Result:** {m.get(‘actual_winner’)} won | {m.get(‘actual_score’)} runs - {str(m.get(‘actual_wickets’,0)).zfill(2)} wkts”)
st.markdown(”—”)
st.subheader(“🎱 Bold Predictions”)
bps = db().table(“pool_bps”).select(”*”).eq(“match_name”, m[“match_name”]).execute().data or []
if bps:
bp_rows = []
for bp in bps:
icon = “✅” if bp.get(“result”)==“correct” else “❌” if bp.get(“result”)==“wrong” else “⏳”
bp_rows.append({
“”: icon,
“Player”: get_user_display(bp[“player”]),
“Prediction”: bp[“prediction_text”],
“Type”: “💡 Custom” if bp.get(“bp_type”)==“custom” else “🎱 Pool”,
“Pts”: bp.get(“points_awarded”,0)
})
st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)
else:
st.info(“No BPs for this match.”)
st.markdown(”—”)
st.subheader(“🔮 Score Predictions”)
preds = db().table(“predictions”).select(”*”).eq(“match_name”, m[“match_name”]).execute().data or []
if preds:
preds_sorted = sorted(preds, key=lambda x: x.get(“points_awarded”,0), reverse=True)
sp_rows = []
for i, p in enumerate(preds_sorted):
rank  = “🥇” if i==0 and (p.get(“points_awarded”) or 0) >= 4 else “”
exact = “⚡” if m.get(“actual_score”) and int(p.get(“predicted_score”) or 0) == m.get(“actual_score”) else “”
sp_rows.append({
“”: rank, “Player”: get_user_display(p[“player”]),
“Predicted”: f”{p.get(‘predicted_score’)} - {str(p.get(‘predicted_wickets’,0)).zfill(2)}”,
“Winner”: p.get(“predicted_winner”,”-”),
“Actual”: f”{m.get(‘actual_score’)} - {str(m.get(‘actual_wickets’,0)).zfill(2)}” if m.get(“actual_score”) else “-”,
“⚡”: exact, “Pts”: p.get(“points_awarded”,0)
})
st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
else:
st.info(“No score predictions for this match.”)

def page_stats():
st.title(“📊 Player Stats”)
st.markdown(”—”)
users = get_playing_users()
if not users:
st.info(“No players yet.”)
return
selected = st.selectbox(“Select Player”, [”— Overall —”] + [u[“display_name”] for u in users])
if selected == “— Overall —”:
rows = []
for u in users:
uname = u[“username”]
bps   = db().table(“pool_bps”).select(”*”).eq(“player”, uname).execute().data or []
preds = db().table(“predictions”).select(”*”).eq(“player”, uname).execute().data or []
rows.append({
“Player”:     u[“display_name”],
“Total”:      get_player_total_points(uname),
“SP Pts”:     get_player_sp_points(uname),
“BP Pts”:     get_player_bp_points(uname),
“Streak Pts”: get_player_streak_points(uname),
“⚡ Exacts”:  get_player_exact_count(uname),
“BPs ✅”:     len([b for b in bps if b.get(“result”)==“correct”]),
“BPs ❌”:     len([b for b in bps if b.get(“result”)==“wrong”]),
“SP Played”:  len([p for p in preds if p.get(“actual_score”) is not None]),
“🔥 Streak”:  get_current_streak(uname)
})
rows.sort(key=lambda x: x[“Total”], reverse=True)
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
u = next((u for u in users if u[“display_name”] == selected), None)
if not u: return
uname  = u[“username”]
total  = get_player_total_points(uname)
sp_pts = get_player_sp_points(uname)
bp_pts = get_player_bp_points(uname)
streak_pts  = get_player_streak_points(uname)
cur_streak  = get_current_streak(uname)
exact_count = get_player_exact_count(uname)
col1,col2,col3,col4,col5 = st.columns(5)
col1.metric(“🏆 Total”,  total)
col2.metric(“🔮 SP”,     sp_pts)
col3.metric(“🎱 BP”,     bp_pts)
col4.metric(“🔥 Streak”, streak_pts)
col5.metric(“⚡ Exacts”, exact_count)
if cur_streak > 1:
st.success(f”🔥 Active streak: **{cur_streak} wins in a row!** (+{streak_bonus_for(cur_streak+1)} next win)”)
st.markdown(”—”)
if total > 0:
st.subheader(“📊 Points Breakdown”)
chart_data = pd.DataFrame({“Category”: [“SP”,“BP”,“Streak”], “Points”: [sp_pts, bp_pts, streak_pts]})
st.bar_chart(chart_data.set_index(“Category”))
st.markdown(”—”)
matches = db().table(“matches”).select(”*”).execute().data or []
match_map = {m[“match_name”]: i+1 for i, m in enumerate(matches)}
st.subheader(“🎱 Bold Predictions”)
bps = db().table(“pool_bps”).select(”*”).eq(“player”, uname).execute().data or []
if bps:
st.dataframe(pd.DataFrame([{
“Match #”: f”#{match_map.get(b[‘match_name’],’?’)}”,
“Match”: b[“match_name”],
“Prediction”: b[“prediction_text”],
“Type”: “💡” if b.get(“bp_type”)==“custom” else “🎱”,
“Result”: “✅” if b.get(“result”)==“correct” else “❌” if b.get(“result”)==“wrong” else “⏳”,
“Pts”: b.get(“points_awarded”,0)
} for b in bps]), use_container_width=True, hide_index=True)
else:
st.info(“No BPs yet.”)
st.markdown(”—”)
st.subheader(“🔮 Score Predictions”)
preds = db().table(“predictions”).select(”*”).eq(“player”, uname).execute().data or []
if preds:
st.dataframe(pd.DataFrame([{
“Match #”: f”#{match_map.get(p[‘match_name’],’?’)}”,
“Match”: p[“match_name”],
“Predicted”: f”{p.get(‘predicted_score’)} - {str(p.get(‘predicted_wickets’,0)).zfill(2)}”,
“Winner”: p.get(“predicted_winner”,”-”),
“Actual”: f”{p.get(‘actual_score’)} - {str(p.get(‘actual_wickets’,0)).zfill(2)}” if p.get(“actual_score”) else “Pending”,
“⚡”: “Yes” if p.get(“actual_score”) and int(p.get(“predicted_score”) or 0)==int(p.get(“actual_score”) or -1) else “”,
“Pts”: p.get(“points_awarded”,0)
} for p in preds]), use_container_width=True, hide_index=True)
else:
st.info(“No predictions yet.”)

def page_season_predictions():
st.title(“🌟 Season Predictions”)
st.markdown(”—”)
user     = st.session_state.user
username = user[“username”]
if user[“role”] == “guest”:
results = db().table(“season_predictions”).select(”*”).execute().data or []
if results:
st.dataframe(pd.DataFrame([{
“Player”: get_user_display(sp[“player”]),
“🧡 Orange Cap”: sp.get(“orange_cap”),
“💜 Purple Cap”: sp.get(“purple_cap”),
“🌟 Emerging”: sp.get(“emerging_player”),
“Top 4”: f”{sp.get(‘top1’)}→{sp.get(‘top2’)}→{sp.get(‘top3’)}→{sp.get(‘top4’)}”,
“Pts”: sp.get(“points_awarded”,0)
} for sp in results]), use_container_width=True, hide_index=True)
else:
st.info(“No season predictions yet.”)
return
existing = db().table(“season_predictions”).select(”*”).eq(“player”, username).execute().data or []
if existing:
sp = existing[0]
st.success(“✅ Your season predictions submitted!”)
st.write(f”🧡 Orange Cap: **{sp.get(‘orange_cap’)}**”)
st.write(f”💜 Purple Cap: **{sp.get(‘purple_cap’)}**”)
st.write(f”🌟 Emerging: **{sp.get(‘emerging_player’)}**”)
st.write(f”🏏 Top 4: {sp.get(‘top1’)} → {sp.get(‘top2’)} → {sp.get(‘top3’)} → {sp.get(‘top4’)}”)
st.write(f”**Points: {sp.get(‘points_awarded’,‘Pending’)}**”)
return
st.markdown(”**Points:** Orange Cap=20 | Purple Cap=20 | Emerging=15 | Top4 team=6 (+4 if position correct)”)
oc = st.text_input(“🧡 Orange Cap”); pc = st.text_input(“💜 Purple Cap”)
em = st.text_input(“🌟 Emerging Player”)
t1 = st.text_input(“1st Place”); t2 = st.text_input(“2nd Place”)
t3 = st.text_input(“3rd Place”); t4 = st.text_input(“4th Place”)
if st.button(“🚀 Submit”, use_container_width=True):
if not all([oc,pc,em,t1,t2,t3,t4]):
st.error(“Fill all fields!”)
else:
db().table(“season_predictions”).insert({
“player”: username, “orange_cap”: caps(oc), “purple_cap”: caps(pc),
“emerging_player”: caps(em), “top1”: caps(t1), “top2”: caps(t2),
“top3”: caps(t3), “top4”: caps(t4), “points_awarded”: 0
}).execute()
st.success(“✅ Submitted!”)
st.rerun()

def page_how_to_score():
st.title(“📖 How to Score”)
st.markdown(”—”)
st.subheader(“🎱 BP Pool”)
st.markdown(”””

- Pick a BP from the pool before BP is locked
- Fill in the player or team name
- Or submit a **Custom BP** (clear with admin first!)
- ✅ Correct → **+3 pts**
- ❌ Wrong → **-1 pt**
  “””)
  st.markdown(”—”)
  st.subheader(“🔮 Score Predictions (SP)”)
  st.markdown(”””
- After 6 overs, predict final score + wickets + match winner
- 🏆 Closest score → **+4 pts**
- ⚡ Exact score → **+6 pts**
- ✅ Correct winner → **+2 pts**
- 🎯 Correct wickets (SP winner only) → **+1 pt**
- Tie on closest score → both get points
  “””)
  st.markdown(”—”)
  st.subheader(“🔥 Streak Points”)
  st.markdown(”””
- Consecutive SP wins keep rewarding you!
- 2 in a row → **+1** | 3 → **+2** | 4 → **+3** | keeps going forever!
- Resets if you don’t win
  “””)
  st.markdown(”—”)
  st.subheader(“🌟 Season Predictions”)
  st.markdown(”””
- Submit once before tournament starts
- 🧡 Orange Cap → **20 pts** | 💜 Purple Cap → **20 pts**
- 🌟 Emerging Player → **15 pts**
- 🏏 Top 4 team → **6 pts each** (+4 if position correct)
  “””)

def page_admin():
st.title(“⚙️ King’s Panel”)
st.markdown(”—”)
tab1, tab2, tab3, tab4 = st.tabs([“➕ Matches”, “👥 Players”, “📝 BP Results”, “🌟 Season”])

```
with tab1:
    match_name = st.text_input("Match Name")
    match_date = st.date_input("Date")
    if st.button("Add Match"):
        if match_name.strip():
            db().table("matches").insert({
                "match_name": caps(match_name), "match_date": str(match_date),
                "status": "open", "bp_locked": False, "sp_locked": False
            }).execute()
            st.success("✅ Match added!")
            st.rerun()
    st.markdown("---")
    matches = db().table("matches").select("*").execute().data or []
    for i, m in enumerate(matches):
        bp = "🔒" if m.get("bp_locked") else "🟢"
        sp = "🔒" if m.get("sp_locked") else "🟢"
        st.write(f"**#{i+1}** 🏏 **{m['match_name']}** | {m.get('match_date','')} | BP:{bp} SP:{sp} | {m.get('status','open')}")

with tab2:
    nu = st.text_input("Username"); np = st.text_input("Password")
    nr = st.selectbox("Role", ALL_ROLES, format_func=lambda x: ROLE_LABELS.get(x, x))
    nd = st.text_input("Display Name")
    if st.button("Add Player"):
        if nu.strip() and np.strip() and nd.strip():
            db().table("users").insert({"username": nu.strip(), "password": np.strip(), "role": nr, "display_name": nd.strip()}).execute()
            st.success(f"✅ {nd} added!")
            st.rerun()
    st.markdown("---")
    for u in (db().table("users").select("*").execute().data or []):
        st.write(f"{ROLE_LABELS.get(u['role'],'?')} **{u['display_name']}** | `{u['username']}`")

with tab3:
    page_bp_results()

with tab4:
    oc = st.text_input("🧡 Orange Cap"); pc = st.text_input("💜 Purple Cap")
    em = st.text_input("🌟 Emerging")
    t1 = st.text_input("1st"); t2 = st.text_input("2nd")
    t3 = st.text_input("3rd"); t4 = st.text_input("4th")
    if st.button("Award Season Points"):
        actuals = {"oc":caps(oc),"pc":caps(pc),"em":caps(em),"t1":caps(t1),"t2":caps(t2),"t3":caps(t3),"t4":caps(t4)}
        for sp in (db().table("season_predictions").select("*").execute().data or []):
            pts = 0
            if sp.get("orange_cap","").upper()     == actuals["oc"]: pts += 20
            if sp.get("purple_cap","").upper()     == actuals["pc"]: pts += 20
            if sp.get("emerging_player","").upper()== actuals["em"]: pts += 15
            actual_top4 = [actuals["t1"],actuals["t2"],actuals["t3"],actuals["t4"]]
            pred_top4   = [sp.get("top1","").upper(),sp.get("top2","").upper(),sp.get("top3","").upper(),sp.get("top4","").upper()]
            for j, team in enumerate(pred_top4):
                if team in actual_top4:
                    pts += 6
                    if team == actual_top4[j]: pts += 4
            db().table("season_predictions").update({"points_awarded":pts}).eq("id",sp["id"]).execute()
        st.success("✅ Done!")
```

# ══════════════════════════════════════════════════════════════════════════════

# MAIN

# ══════════════════════════════════════════════════════════════════════════════

def main():
st.set_page_config(page_title=“LFxCT”, page_icon=“🏏”, layout=“wide”)

```
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "🏆 Leaderboard"
if "selected_bp_key" not in st.session_state:
    st.session_state.selected_bp_key = None
if "selected_bp_tmpl" not in st.session_state:
    st.session_state.selected_bp_tmpl = None
if "selected_bp_note" not in st.session_state:
    st.session_state.selected_bp_note = None

# ── Login ──
if st.session_state.user is None:
    st.title("🏏 LFxCT")
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "🏆 Leaderboard"
                st.rerun()
            else:
                st.error("Wrong username or password!")
        st.markdown("---")
        if st.button("👁️ Continue as Guest", use_container_width=True):
            st.session_state.user = {"username":"guest","display_name":"Guest","role":"guest"}
            st.session_state.page = "🏆 Leaderboard"
            st.rerun()
    return

user  = st.session_state.user
role  = user["role"]
pages = get_pages(role)

if st.session_state.page not in pages:
    st.session_state.page = pages[0]

# ── Top nav (mobile + desktop) ──
col_name, col_nav, col_logout = st.columns([2, 4, 1])
with col_name:
    st.markdown(f"**🏏 LFxCT** &nbsp; *{ROLE_LABELS.get(role, role)}*")
    st.caption(user["display_name"])
with col_nav:
    selected = st.selectbox(
        "nav", pages,
        index=pages.index(st.session_state.page),
        label_visibility="collapsed",
        key="top_nav"
    )
    if selected != st.session_state.page:
        st.session_state.page = selected
        st.rerun()
with col_logout:
    btn_label = "🔙" if role == "guest" else "🚪"
    if st.button(btn_label, use_container_width=True):
        st.session_state.user = None
        st.rerun()

st.markdown("---")

# ── Page routing ──
page = st.session_state.page
if   page == "🏆 Leaderboard":       page_leaderboard()
elif page == "🎱 BP Pool":            page_bp_pool()
elif page == "🔮 Score Prediction":   page_submit_sp()
elif page == "🏆 Enter Results":      page_enter_results()
elif page == "📝 BP Results":         page_bp_results()
elif page == "🔒 Lock BP/SP":         page_lock_match()
elif page == "⚙️ King's Panel":       page_admin()
elif page == "📊 Stats":              page_stats()
elif page == "📋 Match Details":      page_match_details()
elif page == "📖 How to Score":       page_how_to_score()
elif page == "🌟 Season Predictions": page_season_predictions()
```

if **name** == “**main**”:
main()
