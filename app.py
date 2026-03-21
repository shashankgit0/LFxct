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
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
[data-testid="stDecoration"] {visibility: hidden;}
section[data-testid="stSidebar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ─── Role definitions ──────────────────────────────────────────────────────────
ROLE_LABELS = {"admin": "♔ King", "player": "♟ Pawn"}
ADMIN_ROLES = ["admin"]
ALL_ROLES   = ["player", "admin"]

# ─── BP Pool ───────────────────────────────────────────────────────────────────
BP_POOL = {
    "🏏 Batting": [
        {"key": "bat_30",    "template": "{name} to score 30+ runs",               "note": None},
        {"key": "bat_50",    "template": "{name} to score 50+ runs",               "note": None},
        {"key": "bat_75",    "template": "{name} to score 75+ runs",               "note": None},
        {"key": "bat_100",   "template": "{name} to score a century (100+)",       "note": None},
        {"key": "bat_duck",  "template": "{name} to score a duck (0 runs)",        "note": None},
        {"key": "bat_top",   "template": "{name} to be the highest scorer",        "note": None},
        {"key": "bat_sr200", "template": "{name} to have 200+ strike rate",        "note": "Min 10 balls faced"},
        {"key": "bat_sr150", "template": "{name} to have 150+ strike rate",        "note": "Min 10 balls faced"},
        {"key": "bat_out14", "template": "{name} to get out in <14 balls",         "note": "Openers only"},
        {"key": "bat_b1",    "template": "{name} to hit a boundary on ball 1",     "note": "First ball of innings only"},
        {"key": "bat_six1",  "template": "{name} to hit a six on ball 1",          "note": "First ball of innings only"},
        {"key": "bat_6s",    "template": "{name} to hit 3+ sixes",                 "note": None},
        {"key": "bat_4s",    "template": "{name} to hit 5+ fours",                 "note": None},
        {"key": "bat_haf",   "template": "{name} to score a fifty in <20 balls",   "note": None},
    ],
    "🎳 Bowling": [
        {"key": "bowl_1w",   "template": "{name} to take 1+ wicket",               "note": None},
        {"key": "bowl_2w",   "template": "{name} to take 2+ wickets",              "note": None},
        {"key": "bowl_3w",   "template": "{name} to take 3+ wickets",              "note": None},
        {"key": "bowl_mdn",  "template": "{name} to bowl a maiden over",           "note": None},
        {"key": "bowl_top",  "template": "{name} to be the top wicket taker",      "note": None},
        {"key": "bowl_eco",  "template": "{name} to have economy under 6",         "note": "Min 2 overs bowled"},
        {"key": "bowl_dot",  "template": "{name} to bowl 10+ dot balls",           "note": None},
        {"key": "bowl_wb",   "template": "{name} to bowl 3+ wides",               "note": None},
        {"key": "bowl_hat",  "template": "{name} to take a hat-trick",             "note": "Rare but legendary 🔥"},
    ],
    "🔥 Team": [
        {"key": "team_180",  "template": "{name} team to score 180+ runs",         "note": None},
        {"key": "team_200",  "template": "{name} team to score 200+ runs",         "note": None},
        {"key": "team_140",  "template": "{name} team to score under 140",         "note": None},
        {"key": "team_6s11", "template": "{name} team to hit 11+ sixes",           "note": None},
        {"key": "team_6s15", "template": "{name} team to hit 15+ sixes",           "note": None},
        {"key": "team_4s19", "template": "{name} team to hit 19+ fours",           "note": None},
        {"key": "team_pp50", "template": "{name} team to score 50+ in powerplay",  "note": "First 6 overs"},
        {"key": "team_pp60", "template": "{name} team to score 60+ in powerplay",  "note": "First 6 overs"},
        {"key": "team_win10","template": "{name} team to win by 10+ wickets",      "note": None},
        {"key": "team_win50","template": "{name} team to win by 50+ runs",         "note": None},
        {"key": "team_allout","template": "{name} team to be all out",             "note": None},
    ],
    "⭐ Special": [
        {"key": "sp_mom",    "template": "{name} to win Man of the Match",         "note": None},
        {"key": "sp_catch",  "template": "{name} to take 2+ catches",              "note": None},
        {"key": "sp_runout", "template": "{name} to be involved in a run out",     "note": "Either as fielder or batsman"},
        {"key": "sp_6pp",    "template": "{name} to hit a six in the powerplay",   "note": "First 6 overs"},
        {"key": "sp_last",   "template": "{name} team to win off the last ball",   "note": None},
        {"key": "sp_super",  "template": "Match to go to a Super Over",            "note": "Type 'Super Over' in blank"},
        {"key": "sp_fifty6", "template": "{name} to score 50 in exactly 6 balls",  "note": "Almost impossible 🔥"},
    ],
}

# ─── Helpers ───────────────────────────────────────────────────────────────────
def get_all_users():
    return db().table("users").select("*").execute().data or []

def get_playing_users():
    return [u for u in get_all_users() if u["role"] not in ADMIN_ROLES]

def get_user_by_username(username):
    for u in get_all_users():
        if u["username"] == username:
            return u
    return {}

def get_display(username):
    u = get_user_by_username(username)
    return u.get("display_name") or username

def get_team(username):
    u = get_user_by_username(username)
    return u.get("team_name") or u.get("display_name") or username

def caps(text):
    return text.strip().upper() if text else ""

def get_matches():
    return db().table("matches").select("*").execute().data or []

def get_match_map():
    matches = get_matches()
    return {m["match_name"]: i+1 for i, m in enumerate(matches)}

def get_player_bp_points(username):
    total = 0
    for b in db().table("pool_bps").select("points_awarded").eq("player", username).execute().data or []:
        try: total += float(b.get("points_awarded") or 0)
        except: pass
    return round(total, 2)

def get_player_sp_points(username):
    total = 0
    for p in db().table("predictions").select("points_awarded").eq("player", username).execute().data or []:
        try: total += float(p.get("points_awarded") or 0)
        except: pass
    return round(total, 2)

def get_player_streak_points(username):
    total = 0
    for s in db().table("streaks").select("bonus_points").eq("player", username).execute().data or []:
        try: total += float(s.get("bonus_points") or 0)
        except: pass
    return round(total, 2)

def get_player_season_points(username):
    total = 0
    for s in db().table("season_predictions").select("points_awarded").eq("player", username).execute().data or []:
        try: total += float(s.get("points_awarded") or 0)
        except: pass
    return round(total, 2)

def get_player_total_points(username):
    return round(get_player_sp_points(username) + get_player_bp_points(username) +
                 get_player_streak_points(username) + get_player_season_points(username), 2)

def get_player_exact_count(username):
    count = 0
    for p in db().table("predictions").select("*").eq("player", username).execute().data or []:
        if p.get("actual_score") is not None:
            if int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1):
                count += 1
    return count

def get_current_streak(username):
    preds = db().table("predictions").select("*").eq("player", username).execute().data or []
    done  = sorted([p for p in preds if p.get("actual_score") is not None],
                   key=lambda x: x.get("submitted_at") or "", reverse=True)
    streak = 0
    for p in done:
        all_p = db().table("predictions").select("*").eq("match_name", p["match_name"]).execute().data or []
        valid = [x for x in all_p if x.get("actual_score") is not None]
        if not valid: break
        min_diff = min(abs(int(x.get("predicted_score") or 0) - int(x.get("actual_score") or 0)) for x in valid)
        my_diff  = abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0))
        if my_diff == min_diff: streak += 1
        else: break
    return streak

def streak_bonus_for(n):
    return max(0, n - 1)

def login(username, password):
    res = db().table("users").select("*").eq("username", username).eq("password", password).execute()
    return res.data[0] if res.data else None

def award_sp_points(match_sel, actual_score, actual_wickets, actual_winner):
    actual_winner = caps(actual_winner)
    db().table("matches").update({
        "status": "done", "actual_score": actual_score,
        "actual_wickets": actual_wickets, "actual_winner": actual_winner
    }).eq("match_name", match_sel).execute()
    preds = db().table("predictions").select("*").eq("match_name", match_sel).execute().data or []
    if not preds: return
    for p in preds:
        p["diff"] = abs(int(p.get("predicted_score") or 0) - actual_score)
    min_diff = min(p["diff"] for p in preds)
    winners  = [p for p in preds if p["diff"] == min_diff]
    for p in preds:
        pts = 0
        is_winner = p["diff"] == min_diff
        is_exact  = int(p.get("predicted_score") or 0) == actual_score
        corr_win  = caps(p.get("predicted_winner","")) == actual_winner
        corr_wkt  = int(p.get("predicted_wickets") or -1) == actual_wickets
        if is_exact:    pts += 6
        elif is_winner: pts += 4
        if corr_win:    pts += 2
        if is_winner and corr_wkt: pts += 1
        db().table("predictions").update({
            "actual_score": actual_score, "actual_wickets": actual_wickets,
            "actual_winner": actual_winner, "points_awarded": pts
        }).eq("id", p["id"]).execute()
    for w in winners:
        uname  = w["player"]
        streak = get_current_streak(uname)
        bonus  = streak_bonus_for(streak)
        if bonus > 0:
            db().table("streaks").insert({
                "player": uname, "match_name": match_sel,
                "streak_count": streak, "bonus_points": bonus
            }).execute()

def get_pages(role):
    if role == "guest":
        return ["🏆 Leaderboard","📊 Overall Stats","👤 Player Stats","🏅 Hall of Fame",
                "📋 Match Details","📖 How to Score","🌟 Season Predictions"]
    pages = ["🏆 Leaderboard","📊 Overall Stats","👤 Player Stats","🏅 Hall of Fame",
             "📋 Match Details","📖 How to Score","🌟 Season Predictions",
             "🎱 BP Pool","🔮 Score Prediction"]
    if role == "admin":
        pages += ["🏆 Enter Results","📝 BP Results","🔒 Lock / Cancel","⚙️ King's Panel"]
    return pages


# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_leaderboard():
    st.title("🏆 LFxCT Leaderboard")
    st.markdown("---")
    users = get_playing_users()
    if not users:
        st.info("No players yet.")
        return
    rows = []
    for u in users:
        uname  = u["username"]
        sp     = int(get_player_sp_points(uname))
        bp     = int(get_player_bp_points(uname))
        streak = int(get_player_streak_points(uname))
        exact  = get_player_exact_count(uname)
        cur_st = get_current_streak(uname)
        total  = sp + bp + streak
        rows.append({
            "Rank":        "",
            "Team":        u.get("team_name") or u.get("display_name") or uname,
            "SP Pts":      sp,
            "BP Pts":      bp,
            "Streak Pts":  streak,
            "⚡ Exacts":   exact,
            "🔥 Streak":   cur_st,
            "Total":       total
        })
    rows.sort(key=lambda x: x["Total"], reverse=True)
    medals = ["🥇","🥈","🥉"]
    for i, r in enumerate(rows):
        r["Rank"] = medals[i] if i < 3 else str(i+1)
    df = pd.DataFrame(rows)
    def style_df(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        styles["Total"] = "background-color: #1e2a1e; color: #00ff88; font-weight: bold"
        styles["Team"]  = "background-color: #1a1a2e; font-weight: bold"
        return styles
    st.dataframe(df.style.apply(style_df, axis=None), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# OVERALL STATS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_overall_stats():
    st.title("📊 Overall Stats")
    st.markdown("---")

    users   = get_playing_users()
    matches = get_matches()
    done_matches = [m for m in matches if m.get("status") == "done"]
    if not users or not done_matches:
        st.info("Not enough data yet.")
        return

    match_names = [m["match_name"] for m in done_matches]
    match_map   = {m["match_name"]: i+1 for i, m in enumerate(matches)}

    # ── Build full data ──
    all_preds = db().table("predictions").select("*").execute().data or []
    all_bps   = db().table("pool_bps").select("*").execute().data or []

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Points Race", "🎯 Accuracy", "🏅 Podium Tracker", "⚔️ Head to Head", "📋 Full Table"
    ])

    # ─ Tab 1: Points over time ─
    with tab1:
        st.subheader("📈 Points Race — Match by Match")
        st.caption("Who's been climbing and who's been sliding")

        # Build cumulative points per player per match
        cum_data = {}
        for u in users:
            uname = u["username"]
            team  = u.get("team_name") or uname
            cum   = 0
            cum_data[team] = []
            for mn in match_names:
                # SP points this match
                mp = next((p for p in all_preds if p["player"]==uname and p["match_name"]==mn), None)
                if mp: cum += int(float(mp.get("points_awarded") or 0))
                # BP points this match
                mb = next((b for b in all_bps if b["player"]==uname and b["match_name"]==mn), None)
                if mb: cum += int(float(mb.get("points_awarded") or 0))
                cum_data[team].append(cum)

        chart_df = pd.DataFrame(cum_data, index=[f"M{match_map[mn]}" for mn in match_names])
        st.line_chart(chart_df, use_container_width=True, height=400)

        # Match range filter
        st.markdown("---")
        st.caption("🔍 Filter match range:")
        total_matches = len(match_names)
        if total_matches > 2:
            col1, col2 = st.columns(2)
            with col1:
                start_m = st.number_input("From Match #", min_value=1, max_value=total_matches, value=1)
            with col2:
                end_m = st.number_input("To Match #", min_value=1, max_value=total_matches, value=total_matches)
            filtered_names = match_names[start_m-1:end_m]
            filtered_data = {}
            for u in users:
                uname = u["username"]
                team  = u.get("team_name") or uname
                cum   = 0
                filtered_data[team] = []
                for mn in filtered_names:
                    mp = next((p for p in all_preds if p["player"]==uname and p["match_name"]==mn), None)
                    if mp: cum += int(float(mp.get("points_awarded") or 0))
                    mb = next((b for b in all_bps if b["player"]==uname and b["match_name"]==mn), None)
                    if mb: cum += int(float(mb.get("points_awarded") or 0))
                    filtered_data[team].append(cum)
            filtered_df = pd.DataFrame(filtered_data, index=[f"M{match_map[mn]}" for mn in filtered_names])
            st.line_chart(filtered_df, use_container_width=True, height=300)

    # ─ Tab 2: Accuracy ─
    with tab2:
        st.subheader("🎯 SP Win Rate")
        sp_rows = []
        for u in users:
            uname   = u["username"]
            team    = u.get("team_name") or uname
            up      = [p for p in all_preds if p["player"]==uname and p.get("actual_score") is not None]
            wins    = len([p for p in up if p["diff"]==min((abs(int(x.get("predicted_score") or 0)-int(x.get("actual_score") or 0)) for x in [q for q in all_preds if q["match_name"]==p["match_name"] and q.get("actual_score") is not None]), default=999) if True] if up else [])
            # simpler win count
sp_wins = 0
            for p in up:
                match_preds = [x for x in all_preds if x["match_name"]==p["match_name"] and x.get("actual_score") is not None]
                if not match_preds: continue
                min_d = min(abs(int(x.get("predicted_score") or 0)-int(x.get("actual_score") or 0)) for x in match_preds)
                my_d  = abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0))
                if my_d == min_d: sp_wins += 1
            played  = len(up)
            corr_w  = len([x for x in up if caps(x.get("predicted_winner",""))==caps(x.get("actual_winner",""))])
            corr_wk = len([x for x in up if int(x.get("predicted_wickets") or -1)==int(x.get("actual_wickets") or -2)])
            margin  = sum(abs(int(x.get("predicted_score") or 0)-int(x.get("actual_score") or 0)) for x in up)
            exact   = len([x for x in up if int(x.get("predicted_score") or 0)==int(x.get("actual_score") or 0)])
            sp_rows.append({
                "Team": team, "Played": played, "SP Wins": sp_wins,
                "Win %": f"{round(sp_wins/played*100)}%" if played else "0%",
                "Correct Winners": corr_w,
                "Correct Wickets": corr_wk,
                "Exact Preds": exact,
                "Margin of Error": margin
            })
        sp_rows.sort(key=lambda x: x["SP Wins"], reverse=True)
        st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🎱 BP Success Rate")
        bp_rows = []
        for u in users:
            uname  = u["username"]
            team   = u.get("team_name") or uname
            ubps   = [b for b in all_bps if b["player"]==uname]
            correct = len([b for b in ubps if b.get("result")=="correct"])
            wrong   = len([b for b in ubps if b.get("result")=="wrong"])
            total_b = correct + wrong
            custom  = len([b for b in ubps if b.get("bp_type")=="custom"])
            bp_rows.append({
                "Team": team,
                "BP Correct": correct,
                "BP Wrong": wrong,
                "Success %": f"{round(correct/total_b*100)}%" if total_b else "0%",
                "Custom BPs": custom,
                "BP Points": int(get_player_bp_points(uname))
            })
        bp_rows.sort(key=lambda x: x["BP Correct"], reverse=True)
        st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📐 Margin of Error")
        st.caption("Total runs off across all predictions — lower is better")
        margin_rows = sorted(sp_rows, key=lambda x: x["Margin of Error"])
        margin_df = pd.DataFrame([{"Team": r["Team"], "Margin of Error": r["Margin of Error"]} for r in margin_rows])
        st.bar_chart(margin_df.set_index("Team"), use_container_width=True, height=300)

    # ─ Tab 3: Podium Tracker ─
    with tab3:
        st.subheader("🏅 Podium Tracker")
        st.caption("How many times each player finished 1st, 2nd, 3rd in SP")
        podium_rows = []
        for u in users:
            uname = u["username"]
            team  = u.get("team_name") or uname
            first = second = third = missed = 0
            for mn in match_names:
                match_preds = [p for p in all_preds if p["match_name"]==mn and p.get("actual_score") is not None]
                if not match_preds: continue
                my_pred = next((p for p in match_preds if p["player"]==uname), None)
                if not my_pred:
                    missed += 1
                    continue
                sorted_preds = sorted(match_preds, key=lambda x: abs(int(x.get("predicted_score") or 0)-int(x.get("actual_score") or 0)))
                diffs = [abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in sorted_preds]
                my_diff = abs(int(my_pred.get("predicted_score") or 0)-int(my_pred.get("actual_score") or 0))
                rank = diffs.index(my_diff) + 1 if my_diff in diffs else 99
                if rank == 1: first += 1
                elif rank == 2: second += 1
                elif rank == 3: third += 1
            podium_rows.append({
                "Team": team, "🥇 1st": first, "🥈 2nd": second,
                "🥉 3rd": third, "Missed": missed,
                "Attendance %": f"{round((len(match_names)-missed)/len(match_names)*100)}%" if match_names else "0%"
            })
        podium_rows.sort(key=lambda x: (x["🥇 1st"], x["🥈 2nd"], x["🥉 3rd"]), reverse=True)
        st.dataframe(pd.DataFrame(podium_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("😤 Most 2nd Places — Uncrowned Princes")
        second_sorted = sorted(podium_rows, key=lambda x: x["🥈 2nd"], reverse=True)[:3]
        cols = st.columns(3)
        emojis = ["🥇","🥈","🥉"]
        colors = ["#FFD700","#C0C0C0","#CD7F32"]
        for i, (col, row) in enumerate(zip(cols, second_sorted)):
            with col:
                st.markdown(f"""
<div style='background:{colors[i]};padding:15px;border-radius:10px;text-align:center;color:black'>
<b>{emojis[i]} {row['Team']}</b><br>
{row['🥈 2nd']} second places<br>
<i>😤 Uncrowned Prince</i>
</div>""", unsafe_allow_html=True)

    # ─ Tab 4: Head to Head ─
    with tab4:
        st.subheader("⚔️ Head to Head Comparison")
        player_names = [u.get("team_name") or u["username"] for u in users]
        col1, col2 = st.columns(2)
        with col1:
            p1_name = st.selectbox("Player 1", player_names, key="h2h_p1")
        with col2:
            p2_name = st.selectbox("Player 2", [n for n in player_names if n != p1_name], key="h2h_p2")

        p1 = next((u for u in users if (u.get("team_name") or u["username"]) == p1_name), None)
        p2 = next((u for u in users if (u.get("team_name") or u["username"]) == p2_name), None)

        if p1 and p2:
            u1, u2 = p1["username"], p2["username"]
            def h2h_stats(uname):
                up    = [p for p in all_preds if p["player"]==uname and p.get("actual_score") is not None]
                ubps  = [b for b in all_bps if b["player"]==uname]
                sp_wins = 0
                first = second = third = 0
                for mn in match_names:
                    match_preds = [p for p in all_preds if p["match_name"]==mn and p.get("actual_score") is not None]
                    if not match_preds: continue
                    my_pred = next((p for p in match_preds if p["player"]==uname), None)
                    if not my_pred: continue
                    my_diff = abs(int(my_pred.get("predicted_score") or 0)-int(my_pred.get("actual_score") or 0))
                    min_diff = min(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in match_preds)
                    diffs = sorted([abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in match_preds])
                    if my_diff == min_diff: sp_wins += 1
                    rank = diffs.index(my_diff)+1 if my_diff in diffs else 99
                    if rank==1: first+=1
                    elif rank==2: second+=1
                    elif rank==3: third+=1
                bp_correct = len([b for b in ubps if b.get("result")=="correct"])
                bp_wrong   = len([b for b in ubps if b.get("result")=="wrong"])
                exact      = len([p for p in up if int(p.get("predicted_score") or 0)==int(p.get("actual_score") or -1)])
                margin     = sum(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in up)
                corr_w     = len([p for p in up if caps(p.get("predicted_winner",""))==caps(p.get("actual_winner",""))])
                streak_pts = int(get_player_streak_points(uname))
                return {
                    "Total Points": int(get_player_total_points(uname)),
                    "SP Points": int(get_player_sp_points(uname)),
                    "BP Points": int(get_player_bp_points(uname)),
                    "Streak Points": streak_pts,
                    "SP Wins": sp_wins,
                    "BP Correct": bp_correct,
                    "BP Wrong": bp_wrong,
                    "Exact Predictions": exact,
                    "Correct Winners": corr_w,
                    "Margin of Error": margin,
                    "🥇 1st Place": first,
                    "🥈 2nd Place": second,
                    "🥉 3rd Place": third,
                    "Current Streak": get_current_streak(uname),
                }

            s1 = h2h_stats(u1)
            s2 = h2h_stats(u2)

            st.markdown(f"### {p1_name}  ⚔️  {p2_name}")
            h2h_rows = []
            for stat in s1.keys():
                v1, v2 = s1[stat], s2[stat]
                # For margin of error lower is better
                if stat == "Margin of Error":
                    w1 = v1 < v2
                    w2 = v2 < v1
                elif stat == "BP Wrong":
                    w1 = v1 < v2
                    w2 = v2 < v1
                else:
                    w1 = v1 > v2
                    w2 = v2 > v1
                h2h_rows.append({
                    "Stat": stat,
                    p1_name: f"✅ {v1}" if w1 else str(v1),
                    p2_name: f"✅ {v2}" if w2 else str(v2),
                })
            st.dataframe(pd.DataFrame(h2h_rows), use_container_width=True, hide_index=True)

    # ─ Tab 5: Full Table ─
    with tab5:
        st.subheader("📋 Full Stats Table")
        full_rows = []
        for u in users:
            uname  = u["username"]
            team   = u.get("team_name") or uname
            up     = [p for p in all_preds if p["player"]==uname and p.get("actual_score") is not None]
            ubps   = [b for b in all_bps if b["player"]==uname]
            sp_wins = 0
            for mn in match_names:
                match_preds = [p for p in all_preds if p["match_name"]==mn and p.get("actual_score") is not None]
                if not match_preds: continue
                my_pred = next((p for p in match_preds if p["player"]==uname), None)
                if not my_pred: continue
                my_diff  = abs(int(my_pred.get("predicted_score") or 0)-int(my_pred.get("actual_score") or 0))
                min_diff = min(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in match_preds)
                if my_diff == min_diff: sp_wins += 1
            attended = len([p for p in all_preds if p["player"]==uname])
            full_rows.append({
                "Team":           team,
                "Total":          int(get_player_total_points(uname)),
                "SP Pts":         int(get_player_sp_points(uname)),
                "BP Pts":         int(get_player_bp_points(uname)),
                "Streak Pts":     int(get_player_streak_points(uname)),
                "SP Wins":        sp_wins,
                "BP ✅":          len([b for b in ubps if b.get("result")=="correct"]),
                "BP ❌":          len([b for b in ubps if b.get("result")=="wrong"]),
                "Exacts":         get_player_exact_count(uname),
                "Correct Winners":len([p for p in up if caps(p.get("predicted_winner",""))==caps(p.get("actual_winner",""))]),
                "Margin of Error":sum(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in up),
                "Attended":       attended,
                "Missed":         len(match_names) - attended,
                "🔥 Streak":      get_current_streak(uname),
            })
        full_rows.sort(key=lambda x: x["Total"], reverse=True)
        st.dataframe(pd.DataFrame(full_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER STATS
# ══════════════════════════════════════════════════════════════════════════════
def page_player_stats():
    st.title("👤 Player Stats")
    st.markdown("---")
    users = get_playing_users()
    if not users: st.info("No players yet."); return
    selected = st.selectbox("Select Player", [u.get("team_name") or u["username"] for u in users])
    u = next((u for u in users if (u.get("team_name") or u["username"]) == selected), None)
    if not u: return
    uname   = u["username"]
    matches = get_matches()
    match_map = {m["match_name"]: i+1 for i, m in enumerate(matches)}
    total   = int(get_player_total_points(uname))
    sp_pts  = int(get_player_sp_points(uname))
    bp_pts  = int(get_player_bp_points(uname))
    str_pts = int(get_player_streak_points(uname))
    streak  = get_current_streak(uname)
    exact   = get_player_exact_count(uname)

    st.markdown(f"## {selected}")
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("🏆 Total", total)
    col2.metric("🔮 SP Pts", sp_pts)
    col3.metric("🎱 BP Pts", bp_pts)
    col4.metric("🔥 Streak Pts", str_pts)
    col5.metric("⚡ Exacts", exact)
    if streak > 1:
        st.success(f"🔥 Active streak: **{streak} wins in a row!** (+{streak_bonus_for(streak+1)} next win)")

    st.markdown("---")
    if total > 0:
        st.subheader("📊 Points Breakdown")
        chart_data = pd.DataFrame({
            "Category": ["SP Points","BP Points","Streak Points"],
            "Points":   [sp_pts, bp_pts, str_pts]
        })
        st.bar_chart(chart_data.set_index("Category"), use_container_width=True, height=250)

    st.markdown("---")
    st.subheader("🔮 Score Predictions")
    preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
    if preds:
        sp_rows = []
        for p in preds:
            exact_flag = "⚡" if p.get("actual_score") and int(p.get("predicted_score") or 0)==int(p.get("actual_score") or -1) else ""
            actual_str = f"{p.get('actual_score')} - {str(p.get('actual_wickets',0)).zfill(2)} | {p.get('actual_winner','')}" if p.get("actual_score") else "Pending"
            pred_str   = f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p.get('predicted_winner','')}"
            sp_rows.append({
                "Match #": f"#{match_map.get(p['match_name'],'?')}",
                "Match": p["match_name"],
                "Predicted": pred_str,
                "Actual": actual_str,
                "⚡": exact_flag,
                "Pts": int(float(p.get("points_awarded") or 0))
            })
        st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No predictions yet.")

    st.markdown("---")
    st.subheader("🎱 Bold Predictions")
    bps = db().table("pool_bps").select("*").eq("player", uname).execute().data or []
    if bps:
        bp_rows = []
        for b in bps:
            icon = "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "🚫" if b.get("result")=="dismissed" else "⏳"
            bp_rows.append({
                "Match #": f"#{match_map.get(b['match_name'],'?')}",
                "Match": b["match_name"],
                "Prediction": b["prediction_text"],
                "Type": "💡" if b.get("bp_type")=="custom" else "🎱",
                "Result": icon,
                "Pts": int(float(b.get("points_awarded") or 0))
            })
        st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No BPs yet.")


# ══════════════════════════════════════════════════════════════════════════════
# HALL OF FAME
# ══════════════════════════════════════════════════════════════════════════════
def render_podium(title, emoji, data, stat_label, lower_is_better=False):
    """data = list of (team_name, value) sorted best first"""
    st.markdown(f"### {emoji} {title}")
    if not data:
        st.info("Not enough data.")
        return
    colors   = ["#FFD700","#C0C0C0","#CD7F32"]
    sizes    = ["1.3em","1.1em","1em"]
    paddings = ["20px","15px","12px"]
    cols = st.columns([1,1.3,1])
    order = [1,0,2]  # silver, gold, bronze
    for col_idx, pos in enumerate(order):
        if pos >= len(data): continue
        name, val = data[pos]
        with cols[col_idx]:
            rank_emoji = ["🥇","🥈","🥉"][pos]
            st.markdown(f"""
<div style='background:{colors[pos]};padding:{paddings[pos]};border-radius:12px;text-align:center;color:#000;margin:5px'>
<div style='font-size:{sizes[pos]};font-weight:bold'>{rank_emoji}</div>
<div style='font-size:{sizes[pos]};font-weight:bold'>{name}</div>
<div style='font-size:0.85em'>{stat_label}: <b>{val}</b></div>
</div>""", unsafe_allow_html=True)
    st.markdown("---")

def page_hall_of_fame():
    st.title("🏅 Hall of Fame")
    st.markdown("---")
    users   = get_playing_users()
    matches = get_matches()
    done    = [m for m in matches if m.get("status")=="done"]
    match_names = [m["match_name"] for m in done]
    if not users or not done:
        st.info("Not enough data yet.")
        return

    all_preds = db().table("predictions").select("*").execute().data or []
    all_bps   = db().table("pool_bps").select("*").execute().data or []

    def team(uname): return get_user_by_username(uname).get("team_name") or uname

    # Build stats per player
    stats = {}
    for u in users:
        uname  = u["username"]
        up     = [p for p in all_preds if p["player"]==uname and p.get("actual_score") is not None]
        ubps   = [b for b in all_bps if b["player"]==uname]
        sp_wins = first = second = 0
        for mn in match_names:
            mp = [p for p in all_preds if p["match_name"]==mn and p.get("actual_score") is not None]
            if not mp: continue
            my = next((p for p in mp if p["player"]==uname), None)
            if not my: continue
            my_d   = abs(int(my.get("predicted_score") or 0)-int(my.get("actual_score") or 0))
            min_d  = min(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in mp)
            diffs  = sorted([abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in mp])
            rank   = diffs.index(my_d)+1 if my_d in diffs else 99
            if rank==1: sp_wins+=1; first+=1
            elif rank==2: second+=1
        bp_correct = len([b for b in ubps if b.get("result")=="correct"])
        bp_wrong   = len([b for b in ubps if b.get("result")=="wrong"])
        exact      = len([p for p in up if int(p.get("predicted_score") or 0)==int(p.get("actual_score") or -1)])
        margin     = sum(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in up)
        custom_bps = len([b for b in ubps if b.get("bp_type")=="custom"])
        attended   = len(set(p["match_name"] for p in all_preds if p["player"]==uname))
        total      = int(get_player_total_points(uname))
        corr_w     = len([p for p in up if caps(p.get("predicted_winner",""))==caps(p.get("actual_winner",""))])
        corr_wk    = len([p for p in up if int(p.get("predicted_wickets") or -1)==int(p.get("actual_wickets") or -2)])
        # Most used template
        tmpl_counts = {}
        for b in ubps:
            k = b.get("template_key","")
            if k and k != "custom":
                tmpl_counts[k] = tmpl_counts.get(k,0)+1
        top_tmpl = max(tmpl_counts, key=tmpl_counts.get) if tmpl_counts else ""
        top_tmpl_count = tmpl_counts.get(top_tmpl,0)
        # Copy cat — find most shared template with another player
        stats[uname] = {
            "total": total, "sp_wins": sp_wins, "first": first, "second": second,
            "bp_correct": bp_correct, "bp_wrong": bp_wrong, "exact": exact,
            "margin": margin, "custom_bps": custom_bps, "attended": attended,
            "corr_w": corr_w, "corr_wk": corr_wk,
            "top_tmpl": top_tmpl, "top_tmpl_count": top_tmpl_count,
            "streak_pts": int(get_player_streak_points(uname)),
            "cur_streak": get_current_streak(uname),
        }

    def top3(key, reverse=True):
        sorted_u = sorted(stats.items(), key=lambda x: x[1][key], reverse=reverse)
        return [(team(u), stats[u][key]) for u, _ in sorted_u[:3]]

    col1, col2 = st.columns(2)

    with col1:
        render_podium('"Too Good"', "👑", top3("sp_wins"), "SP Wins")
        render_podium('"The Psychic"', "⚡", top3("exact"), "Exact Predictions")
        render_podium('"Big Brain"', "🧠", top3("bp_correct"), "BPs Correct")
        render_podium('"The Uncrowned King"', "🎯", top3("margin", reverse=False), "Margin of Error", lower_is_better=True)
        render_podium('"Team Whisperer"', "🏏", top3("corr_w"), "Correct Winners")
        render_podium('"Wicket Whisperer"', "🎳", top3("corr_wk"), "Correct Wickets")
        render_podium('"Never Misses"', "🏃", top3("attended"), "Matches Attended")
        render_podium('"On Demon Time"', "🔥", top3("cur_streak"), "Current Streak")

    with col2:
        render_podium('"Absolute Clown"', "💀", top3("bp_wrong"), "BPs Wrong")
        render_podium('"Asks Nobody"', "🎲", top3("custom_bps"), "Custom BPs")
        render_podium('"Uncrowned Prince"', "😤", top3("second"), "2nd Place Finishes")
        render_podium('"What Are You Watching"', "💨", top3("margin"), "Margin of Error")
        render_podium('"Touch Grass"', "🪣", top3("total", reverse=False), "Total Points")
        render_podium('"Checked Out"', "🛋️", top3("attended", reverse=False), "Matches Attended")
        render_podium('"Boring But Elite"', "🔒", top3("first"), "1st Place Finishes")
        render_podium('"One Trick Pony"', "🃏", top3("top_tmpl_count"), "Same BP Used")


# ══════════════════════════════════════════════════════════════════════════════
# REMAINING PAGES
# ══════════════════════════════════════════════════════════════════════════════
def page_bp_pool():
    st.title("🎱 BP Pool")
    st.markdown("✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt** | 🚫 Dismissed → **0 pts**")
    st.markdown("---")
    matches = [m for m in get_matches() if not m.get("bp_locked")]
    if not matches:
        st.warning("⏳ No open matches.")
        return
    match = st.selectbox("Select Match", [m["match_name"] for m in matches])
    existing = db().table("pool_bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        b = existing[0]
        icon = "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "🚫" if b.get("result")=="dismissed" else "⏳"
        st.warning("✅ Already submitted!")
        st.info(f"{icon} **{b['prediction_text']}** | Pts: {int(float(b.get('points_awarded',0)))}")
        return
    categories = list(BP_POOL.keys())
    tabs = st.tabs(categories)
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
    if st.session_state.get("selected_bp_key"):
        tmpl = st.session_state.selected_bp_tmpl
        note = st.session_state.selected_bp_note
        st.markdown(f"#### Selected: *{tmpl.replace('{name}','______')}*")
        if note:
            st.info(f"ℹ️ **Note:** {note}")
        fill_in = st.text_input("Fill in the blank:", placeholder="e.g. Kohli, SRH...") if "{name}" in tmpl else tmpl
        if fill_in and "{name}" in tmpl:
            st.caption(f"Preview: *{tmpl.replace('{name}', fill_in.strip())}*")
        if st.button("🚀 Submit this BP", use_container_width=True):
            if not fill_in or not fill_in.strip():
                st.error("Fill in the blank!")
            else:
                final = tmpl.replace("{name}", fill_in.strip()) if "{name}" in tmpl else tmpl
                db().table("pool_bps").insert({
                    "match_name": match, "player": st.session_state.user["username"],
                    "bp_type": "pool", "template_key": st.session_state.selected_bp_key,
                    "fill_in": fill_in.strip(), "prediction_text": final,
                    "status": "pending", "points_awarded": 0,
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()
                for k in ["selected_bp_key","selected_bp_tmpl","selected_bp_note"]:
                    st.session_state[k] = None
                st.success(f"✅ Submitted: **{final}**")
                st.balloons()
    st.markdown("---")
    st.markdown("### 💡 Custom BP")
    st.caption("Clear it with admin on WhatsApp first!")
    custom_bp = st.text_area("Your custom BP:", placeholder="e.g. SRH will bowl 24 wides")
    if st.button("🚀 Submit Custom BP", use_container_width=True):
        if not custom_bp.strip():
            st.error("Enter your BP!")
        else:
            existing2 = db().table("pool_bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
            if existing2:
                st.error("Already submitted a BP for this match!")
            else:
                db().table("pool_bps").insert({
                    "match_name": match, "player": st.session_state.user["username"],
                    "bp_type": "custom", "template_key": "custom", "fill_in": "",
                    "prediction_text": custom_bp.strip(), "status": "pending",
                    "points_awarded": 0, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()
                st.success(f"✅ Custom BP submitted!")
                st.balloons()


def page_submit_sp():
    st.title("🔮 Score Prediction")
    st.markdown("---")
    matches = [m for m in get_matches() if not m.get("sp_locked")]
    if not matches:
        st.warning("⏳ No open matches.")
        return
    match = st.selectbox("Select Match", [m["match_name"] for m in matches])
    existing = db().table("predictions").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        p = existing[0]
        st.warning("✅ Already submitted!")
        st.info(f"**{p['predicted_score']} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p['predicted_winner']}** | Pts: {int(float(p.get('points_awarded',0)))}")
        return
    col1, col2 = st.columns(2)
    with col1:
        predicted_score   = st.number_input("Predicted Score (runs)", min_value=0, max_value=400, step=1)
        predicted_wickets = st.number_input("Predicted Wickets (0-10)", min_value=0, max_value=10, step=1)
    with col2:
        pw_raw = st.text_input("Predicted Winner")
        pw = caps(pw_raw)
        if pw: st.caption(f"Team: **{pw}**")
    st.caption(f"Your prediction: **{predicted_score} - {str(predicted_wickets).zfill(2)} | {pw}**")
    if st.button("🚀 Submit", use_container_width=True):
        if not pw:
            st.error("Enter the winner!")
        else:
            db().table("predictions").insert({
                "match_name": match, "player": st.session_state.user["username"],
                "predicted_score": predicted_score, "predicted_wickets": predicted_wickets,
                "predicted_winner": pw, "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ Prediction submitted!")


def page_bp_results():
    st.title("📝 BP Results")
    st.markdown("---")
    pending = db().table("pool_bps").select("*").eq("status","pending").execute().data or []
    if not pending:
        st.info("No BPs waiting.")
        return
    matches = list(set(b["match_name"] for b in pending))
    sel = st.selectbox("Filter by Match", ["All"] + matches)
    filtered = pending if sel=="All" else [b for b in pending if b["match_name"]==sel]
    for b in filtered:
        display = get_team(b["player"])
        bp_type = "💡 Custom" if b.get("bp_type")=="custom" else "🎱 Pool"
        st.markdown(f"**{display}** — {b['match_name']} {bp_type}")
        st.markdown(f"*{b['prediction_text']}*")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Correct (+3)", key=f"c_{b['id']}"):
                db().table("pool_bps").update({"result":"correct","points_awarded":3,"status":"done"}).eq("id",b["id"]).execute()
                st.rerun()
        with col2:
            if st.button("❌ Wrong (-1)", key=f"w_{b['id']}"):
                db().table("pool_bps").update({"result":"wrong","points_awarded":-1,"status":"done"}).eq("id",b["id"]).execute()
                st.rerun()
        if b.get("bp_type") == "custom":
            with col3:
                if st.button("🚫 Dismiss (0)", key=f"d_{b['id']}"):
                    db().table("pool_bps").update({"result":"dismissed","points_awarded":0,"status":"done"}).eq("id",b["id"]).execute()
                    st.rerun()
        st.markdown("---")


def page_enter_results():
    st.title("🏆 Enter Match Results")
    st.markdown("---")
    matches = get_matches()
    pending = [m for m in matches if m.get("sp_locked") and m.get("status") not in ["done","cancelled"]]
    if not pending:
        st.info("No matches waiting for results.")
        return
    match_map = {m["match_name"]: i+1 for i, m in enumerate(matches)}
    match_sel = st.selectbox("Select Match", [f"#{match_map[m['match_name']]} — {m['match_name']}" for m in pending])
    match_name = match_sel.split(" — ",1)[1]
    actual_score   = st.number_input("Actual Score (runs)", min_value=0, max_value=500, step=1)
    actual_wickets = st.number_input("Actual Wickets", min_value=0, max_value=10, step=1)
    aw_raw = st.text_input("Actual Winner")
    aw = caps(aw_raw)
    if aw: st.caption(f"Team: **{aw}**")
    if st.button("✅ Submit Result & Award Points", use_container_width=True):
        if not aw:
            st.error("Enter winner!")
        else:
            award_sp_points(match_name, actual_score, actual_wickets, aw)
            st.success(f"✅ Results submitted!")
            st.rerun()


def page_lock_cancel():
    st.title("🔒 Lock / Cancel")
    st.markdown("---")
    matches = get_matches()
    if not matches:
        st.info("No matches.")
        return
    user = st.session_state.user
    now  = datetime.now().strftime("%Y-%m-%d %H:%M")
    match_map = {m["match_name"]: i+1 for i, m in enumerate(matches)}
    for m in matches:
        with st.expander(f"Match #{match_map[m['match_name']]} — {m['match_name']} | {m.get('status','open').upper()}"):
            # Lock/Unlock BP
            col1, col2 = st.columns(2)
            with col1:
                if m.get("bp_locked"):
                    st.success(f"🔒 BP locked by **{get_team(m.get('bp_locked_by',''))}** at {m.get('bp_locked_at','')}")
                    if st.button("🔓 Unlock BP", key=f"ubp_{m['id']}"):
                        db().table("matches").update({"bp_locked":False,"bp_locked_by":None,"bp_locked_at":None}).eq("id",m["id"]).execute()
                        st.rerun()
                else:
                    if st.button("🔒 Lock BP", key=f"lbp_{m['id']}"):
                        db().table("matches").update({"bp_locked":True,"bp_locked_by":user["username"],"bp_locked_at":now}).eq("id",m["id"]).execute()
                        st.rerun()
            with col2:
                if m.get("sp_locked"):
                    st.success(f"🔒 SP locked by **{get_team(m.get('sp_locked_by',''))}** at {m.get('sp_locked_at','')}")
                    if st.button("🔓 Unlock SP", key=f"usp_{m['id']}"):
                        db().table("matches").update({"sp_locked":False,"sp_locked_by":None,"sp_locked_at":None}).eq("id",m["id"]).execute()
                        st.rerun()
                else:
                    if st.button("🔒 Lock SP", key=f"lsp_{m['id']}"):
                        db().table("matches").update({"sp_locked":True,"sp_locked_by":user["username"],"sp_locked_at":now}).eq("id",m["id"]).execute()
                        st.rerun()

            # Cancel section
            if m.get("status") != "cancelled":
                st.markdown("**🌧️ Cancel due to rain:**")
                cancel_type = st.selectbox("What to cancel?",
                    ["Select...","Cancel BP only","Cancel SP only","Cancel both BP and SP"],
                    key=f"cancel_sel_{m['id']}")
                if cancel_type != "Select...":
                    if st.button(f"🌧️ Confirm — {cancel_type}", key=f"cancel_{m['id']}"):
                        if "BP" in cancel_type:
                            db().table("pool_bps").update({"points_awarded":0,"status":"cancelled"}).eq("match_name",m["match_name"]).execute()
                        if "SP" in cancel_type:
                            db().table("predictions").update({"points_awarded":0,"status":"cancelled"}).eq("match_name",m["match_name"]).execute()
                        if cancel_type == "Cancel both BP and SP":
                            db().table("matches").update({"status":"cancelled"}).eq("id",m["id"]).execute()
                        st.success(f"✅ {cancel_type} done!")
                        st.rerun()


def page_match_details():
    st.title("📋 Match Details")
    st.markdown("---")
    matches = get_matches()
    if not matches:
        st.info("No matches yet.")
        return
    match_map = {m["match_name"]: i+1 for i, m in enumerate(matches)}
    options = [f"Match #{match_map[m['match_name']]} — {m['match_name']}" for m in matches]
    sel_idx = st.selectbox("Select Match", range(len(matches)), format_func=lambda i: options[i])
    m = matches[sel_idx]
    st.markdown(f"### 🏏 Match #{match_map[m['match_name']]} — {m['match_name']} | {m.get('match_date','')}")
    col1,col2,col3 = st.columns(3)
    col1.metric("BP", "🔒" if m.get("bp_locked") else "🟢 Open")
    col2.metric("SP", "🔒" if m.get("sp_locked") else "🟢 Open")
    col3.metric("Status", m.get("status","open").upper())
    if m.get("actual_score"):
        st.success(f"**Result:** {m.get('actual_winner')} won | {m.get('actual_score')} - {str(m.get('actual_wickets',0)).zfill(2)}")
    st.markdown("---")
    st.subheader("🎱 Bold Predictions")
    bps = db().table("pool_bps").select("*").eq("match_name",m["match_name"]).execute().data or []
    if bps:
        st.dataframe(pd.DataFrame([{
            "": "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "🚫" if b.get("result")=="dismissed" else "⏳",
            "Team": get_team(b["player"]),
            "Prediction": b["prediction_text"],
            "Type": "💡" if b.get("bp_type")=="custom" else "🎱",
            "Pts": int(float(b.get("points_awarded",0)))
        } for b in bps]), use_container_width=True, hide_index=True)
    else:
        st.info("No BPs.")
    st.markdown("---")
    st.subheader("🔮 Score Predictions")
    preds = db().table("predictions").select("*").eq("match_name",m["match_name"]).execute().data or []
    if preds:
        preds_s = sorted(preds, key=lambda x: x.get("points_awarded",0), reverse=True)
        st.dataframe(pd.DataFrame([{
            "": "🥇" if i==0 and (p.get("points_awarded") or 0)>=4 else "",
            "Team": get_team(p["player"]),
            "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p.get('predicted_winner','-')}",
            "Actual": f"{m.get('actual_score')} - {str(m.get('actual_wickets',0)).zfill(2)} | {m.get('actual_winner','')}" if m.get("actual_score") else "-",
            "⚡": "⚡" if m.get("actual_score") and int(p.get("predicted_score") or 0)==m.get("actual_score") else "",
            "Pts": int(float(p.get("points_awarded",0)))
        } for i,p in enumerate(preds_s)]), use_container_width=True, hide_index=True)
    else:
        st.info("No predictions.")


def page_season_predictions():
    st.title("🌟 Season Predictions")
    st.markdown("---")
    user = st.session_state.user
    username = user["username"]

    # Show all predictions
    all_sp = db().table("season_predictions").select("*").execute().data or []
    if all_sp:
        st.subheader("Everyone's Predictions")
        st.dataframe(pd.DataFrame([{
            "Team": get_team(sp["player"]),
            "🧡 Orange Cap": sp.get("orange_cap"),
            "💜 Purple Cap": sp.get("purple_cap"),
            "🌟 Emerging": sp.get("emerging_player"),
            "Top 4": f"{sp.get('top1')}→{sp.get('top2')}→{sp.get('top3')}→{sp.get('top4')}",
            "Pts": int(float(sp.get("points_awarded",0)))
        } for sp in all_sp]), use_container_width=True, hide_index=True)
        st.markdown("---")

    if user["role"] == "guest":
        return

    existing = db().table("season_predictions").select("*").eq("player", username).execute().data or []
    if existing:
        st.success("✅ Your season predictions already submitted!")
        return

    st.subheader("Submit Your Predictions")
    st.markdown("**Points:** Orange Cap=20 | Purple Cap=20 | Emerging=15 | Top4 team=6 (+4 if position correct)")
    oc = st.text_input("🧡 Orange Cap"); pc = st.text_input("💜 Purple Cap")
    em = st.text_input("🌟 Emerging Player")
    t1=st.text_input("1st"); t2=st.text_input("2nd"); t3=st.text_input("3rd"); t4=st.text_input("4th")
    if st.button("🚀 Submit", use_container_width=True):
        if not all([oc,pc,em,t1,t2,t3,t4]):
            st.error("Fill all fields!")
        else:
            db().table("season_predictions").insert({
                "player": username, "orange_cap": caps(oc), "purple_cap": caps(pc),
                "emerging_player": caps(em), "top1": caps(t1), "top2": caps(t2),
                "top3": caps(t3), "top4": caps(t4), "points_awarded": 0
            }).execute()
            st.success("✅ Submitted!")
            st.rerun()


def page_how_to_score():
    st.title("📖 How to Score")
    st.markdown("---")
    st.subheader("🎱 BP Pool")
    st.markdown("- Pick a template, fill in the blank\n- Custom BP: clear with admin first\n- ✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt** | 🚫 Dismissed → **0 pts**")
    st.markdown("---")
    st.subheader("🔮 Score Predictions (SP)")
    st.markdown("- Predict final score + wickets + winner after 6 overs\n- 🏆 Closest → **+4 pts** | ⚡ Exact → **+6 pts**\n- ✅ Correct winner → **+2 pts**\n- 🎯 Correct wickets (SP winner only) → **+1 pt**\n- Tie → both get points")
    st.markdown("---")
    st.subheader("🔥 Streak Points")
    st.markdown("- 2 wins in a row → **+1** | 3 → **+2** | keeps going forever!\n- Resets if you don't win")
    st.markdown("---")
    st.subheader("🌟 Season Predictions")
    st.markdown("- 🧡 Orange Cap → **20 pts** | 💜 Purple Cap → **20 pts**\n- 🌟 Emerging → **15 pts**\n- 🏏 Top 4 team → **6 pts** (+4 if position correct)")


def page_admin():
    st.title("⚙️ King's Panel")
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["➕ Matches", "👥 Players", "🌟 Season Results"])

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
        matches = get_matches()
        match_map = {m["match_name"]: i+1 for i, m in enumerate(matches)}
        for m in matches:
            bp="🔒" if m.get("bp_locked") else "🟢"
            sp="🔒" if m.get("sp_locked") else "🟢"
            st.write(f"**#{match_map[m['match_name']]}** 🏏 **{m['match_name']}** | BP:{bp} SP:{sp} | {m.get('status','open')}")

    with tab2:
        nu=st.text_input("Username"); np=st.text_input("Password")
        nr=st.selectbox("Role", ALL_ROLES, format_func=lambda x: ROLE_LABELS.get(x,x))
        nd=st.text_input("Display Name"); nt=st.text_input("Team Name")
        if st.button("Add Player"):
            if nu.strip() and np.strip() and nd.strip():
                db().table("users").insert({
                    "username": nu.strip(), "password": np.strip(),
                    "role": nr, "display_name": nd.strip(), "team_name": nt.strip()
                }).execute()
                st.success(f"✅ {nd} added!")
                st.rerun()
        st.markdown("---")
        for u in (db().table("users").select("*").execute().data or []):
            st.write(f"{ROLE_LABELS.get(u['role'],'?')} **{u.get('team_name') or u['display_name']}** | `{u['username']}`")

    with tab3:
        oc=st.text_input("🧡 Orange Cap"); pc=st.text_input("💜 Purple Cap")
        em=st.text_input("🌟 Emerging")
        t1=st.text_input("1st"); t2=st.text_input("2nd"); t3=st.text_input("3rd"); t4=st.text_input("4th")
        if st.button("Award Season Points"):
            actuals = {"oc":caps(oc),"pc":caps(pc),"em":caps(em),
                       "t1":caps(t1),"t2":caps(t2),"t3":caps(t3),"t4":caps(t4)}
            for sp in (db().table("season_predictions").select("*").execute().data or []):
                pts=0
                if sp.get("orange_cap","").upper()==actuals["oc"]: pts+=20
                if sp.get("purple_cap","").upper()==actuals["pc"]: pts+=20
                if sp.get("emerging_player","").upper()==actuals["em"]: pts+=15
                at4=[actuals["t1"],actuals["t2"],actuals["t3"],actuals["t4"]]
                pt4=[sp.get("top1","").upper(),sp.get("top2","").upper(),sp.get("top3","").upper(),sp.get("top4","").upper()]
                for j,team_name in enumerate(pt4):
                    if team_name in at4:
                        pts+=6
                        if team_name==at4[j]: pts+=4
                db().table("season_predictions").update({"points_awarded":pts}).eq("id",sp["id"]).execute()
            st.success("✅ Done!")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(page_title="LFxCT", page_icon="🏏", layout="wide")
    for k,v in [("user",None),("page","🏆 Leaderboard"),
                ("selected_bp_key",None),("selected_bp_tmpl",None),("selected_bp_note",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.user is None:
        st.title("🏏 LFxCT")
        st.markdown("---")
        col1,col2,col3 = st.columns([1,2,1])
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

    # ── Top nav ──
    col_name, col_nav, col_logout = st.columns([2,4,1])
    with col_name:
        team_display = get_team(user["username"]) if role != "guest" else "Guest"
        st.markdown(f"**🏏 LFxCT**")
        st.caption(f"{ROLE_LABELS.get(role,role)} — {team_display}")
    with col_nav:
        selected = st.selectbox("nav", pages,
            index=pages.index(st.session_state.page),
            label_visibility="collapsed", key="top_nav")
        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()
    with col_logout:
        if st.button("🔙" if role=="guest" else "🚪", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")

    page = st.session_state.page
    if   page == "🏆 Leaderboard":       page_leaderboard()
    elif page == "📊 Overall Stats":      page_overall_stats()
    elif page == "👤 Player Stats":       page_player_stats()
    elif page == "🏅 Hall of Fame":       page_hall_of_fame()
    elif page == "🎱 BP Pool":            page_bp_pool()
    elif page == "🔮 Score Prediction":   page_submit_sp()
    elif page == "🏆 Enter Results":      page_enter_results()
    elif page == "📝 BP Results":         page_bp_results()
    elif page == "🔒 Lock / Cancel":      page_lock_cancel()
    elif page == "⚙️ King's Panel":       page_admin()
    elif page == "📋 Match Details":      page_match_details()
    elif page == "📖 How to Score":       page_how_to_score()
    elif page == "🌟 Season Predictions": page_season_predictions()


if __name__ == "__main__":
    main()
