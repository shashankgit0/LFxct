import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="LFxCT", page_icon="🏏", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

LOGO_BASE = "https://zfoytgcyrdqxaroctlwr.supabase.co/storage/v1/object/public/logos"

def logo_url(username):
    return f"{LOGO_BASE}/{username}.PNG"

def player_logo_html(username, size=28):
    url = logo_url(username)
    return f'<img src="{url}" width="{size}" height="{size}" style="border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:6px;" onerror="this.style.display=\'none\'">'

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

ADMIN_ROLES = ["admin"]
ALL_ROLES   = ["player", "admin"]

# ── Draft League Teams ─────────────────────────────────────────────────────────
DRAFT_TEAMS = {
    "dinu":   {"name": "Dinesh Chargers",          "players": ["Abhishek Sharma","Finn Allen","Mayank Yadav","Romario Shepard","Avesh Khan","Mitchell Marsh","Pathum Nissanka","Aquib Nabi","Karthik Tyagi","Naman Dhir","Prashant Veer","Urvil Patel"]},
    "yash":   {"name": "Yash Swaggers",            "players": ["Shubman Gill","Mohammed Siraj","Travis Head","Prabhsimran Singh","Rashid Khan","T Natarajan","Mohammed Shami","Rohit Sharma","Tim David","Wanindu Hasaranga","Rahul Tripathi","Abdul Samad"]},
    "sou":    {"name": "Sou Godfathers",           "players": ["Virat Kohli","Vaibhav Suryavanshi","Nicholas Pooran","Riyan Parag","Kuldeep Yadav","Ravindra Jadeja","Krunal Pandya","Jofra Archer","Kartik Sharma","Sherfane Rutherford","Jaydev Unadkat","Matt Henry"]},
    "vamshi": {"name": "Vamshi Hurricanes",        "players": ["Shreyas Iyer","Angkrish Raghuvanshi","Yuzvendra Chahal","Harshal Patel","Jacob Bethell","Khaleel Ahmed","Aiden Markram","Ryan Rickleton","Ramandeep Singh","Zeeshan Ansari","Suyash Sharma","Sameer Rizvi"]},
    "minto":  {"name": "Minato Maniacs",           "players": ["Sanju Samson","Heinrich Klaasen","Sunil Narine","Dewald Brevis","Liam Livingstone","MS Dhoni","Venky Iyer","Deepak Chahar","Mukesh Kumar","Devdutt Padikkal","Karun Nair","Ashwani Kumar"]},
    "snehit": {"name": "Snehit Synergy",           "players": ["Yashasvi Jaiswal","Bhuvneshwar Kumar","Phil Salt","Jitesh Sharma","Aniket Sharma","Josh Hazelwood","Will Jacks","Marco Jansen","Shashank Singh","Umesh Yadav","Salil Arora","Mangesh Yadav"]},
    "shank":  {"name": "Shank Tacticos",           "players": ["Hardik Pandya","Noor Ahmad","Tilak Varma","Priyansh Arya","Varun Chakravarthy","Dhruv Jurel","Pat Cummins","Marcus Stoinis","Anukul Roy","Nitish Rana","Vaibhav Arora","Matheesha Pathirana"]},
    "visu":   {"name": "Visu Vijayasena",          "players": ["Sai Sudharsan","Rishabh Pant","Shivam Dube","Washington Sundar","Nihal Wadhera","Prasidh Krishna","R Sai Kishore","Jos Buttler","Nandre Burger","Sarfaraz Khan","Matthew Breetzke","Azmatullah Omarzai"]},
    "kartik": {"name": "Kartik Kryptonites",       "players": ["Jasprit Bumrah","Ishan Kishan","Tristan Stubbs","Rajat Patidar","Connolly Cooper","Kagiso Rabada","Nitish Kumar Reddy","Glenn Phillips","Ajinkya Rahane","Abhishek Porel","Harpreet Brar","Mayank Markande"]},
    "vvs":    {"name": "Satwik Quantum Crusaders", "players": ["Axar Patel","Cameron Green","Arshdeep Singh","Shimron Hetmyer","Josh Inglis","Ayush Badoni","Sandeep Sharma","Mitchell Santner","Digvesh Rathi","Vipraj Nigam","Shivang Kumar","Ruturaj Gaikwad"]},
    "hari":   {"name": "Ruthvenger Legends",       "players": ["KL Rahul","Suryakumar Yadav","Quinton de Kock","Trent Boult","David Miller","Ravi Bishnoi","Rinku Singh","Lungi Ngidi","Ashutosh Sharma","Rahul Chahar","Shardul Thakur","Rahul Tewatia"]},
}

SEASON_FIELDS = [
    {"key": "ipl_winner",      "label": "🏆 IPL Winner (Team)",       "fun": True},
    {"key": "orange_cap",      "label": "🧡 Orange Cap (Player)",      "fun": False},
    {"key": "purple_cap",      "label": "💜 Purple Cap (Player)",      "fun": False},
    {"key": "emerging_player", "label": "🌟 Emerging Player",          "fun": False},
    {"key": "top1",            "label": "🏏 1st Place Team",           "fun": False},
    {"key": "top2",            "label": "🏏 2nd Place Team",           "fun": False},
    {"key": "top3",            "label": "🏏 3rd Place Team",           "fun": False},
    {"key": "top4",            "label": "🏏 4th Place Team",           "fun": False},
    {"key": "best_catch",      "label": "🤿 Best Catch (Player)",      "fun": True},
    {"key": "most_sixes",      "label": "💥 Most Sixes (Player)",      "fun": True},
    {"key": "most_fours",      "label": "4️⃣ Most Fours (Player)",      "fun": True},
    {"key": "wooden_spoon",    "label": "🥄 Wooden Spoon (Last Team)", "fun": True},
    {"key": "fairplay",        "label": "🤝 Fairplay Award (Team)",    "fun": True},
    {"key": "super_striker",   "label": "⚡ Super Striker (Player)",   "fun": True},
]

BP_POOL = {
    "🏏 Batting": [
        {"key": "bat_10_20",  "template": "{name} to score between 10 and 20 runs",        "note": None},
        {"key": "bat_20_30",  "template": "{name} to score between 20 and 30 runs",        "note": None},
        {"key": "bat_30_40",  "template": "{name} to score between 30 and 40 runs",        "note": None},
        {"key": "bat_40_50",  "template": "{name} to score between 40 and 50 runs",        "note": None},
        {"key": "bat_50",     "template": "{name} to score 50+ runs",                      "note": None},
        {"key": "bat_100",    "template": "{name} to score a century",                     "note": None},
        {"key": "bat_duck",   "template": "{name} to score a duck",                        "note": None},
        {"key": "bat_top",    "template": "{name} to be the highest scorer in the team",   "note": None},
        {"key": "bat_sr200",  "template": "{name} to have 200+ strike rate",               "note": "Min 10 balls faced"},
        {"key": "bat_b1",     "template": "{name} to hit a boundary on ball 1",            "note": "First ball of innings"},
        {"key": "bat_5six",   "template": "{name} to hit 5+ sixes",                        "note": None},
        {"key": "bat_8four",  "template": "{name} to hit 9+ fours",                        "note": None},
        {"key": "bat_pp40",   "template": "{name} to score 40+ in the powerplay",          "note": "First 6 overs"},
        {"key": "bat_last",   "template": "{name} to be the last wicket to fall",          "note": None},
        {"key": "bat_consec", "template": "{name} to hit consecutive sixes",               "note": None},
    ],
    "🎳 Bowling": [
        {"key": "bowl_1w",    "template": "{name} to take 1 wicket",                       "note": "Min 3 overs bowled"},
        {"key": "bowl_2w",    "template": "{name} to take 2 wickets",                      "note": "Min 3 overs bowled"},
        {"key": "bowl_3w",    "template": "{name} to take 3 wickets",                      "note": "Min 3 overs bowled"},
        {"key": "bowl_3plus", "template": "{name} to take 3+ wickets",                     "note": "Min 3 overs bowled"},
        {"key": "bowl_mdn",   "template": "{name} to bowl a maiden over",                  "note": None},
        {"key": "bowl_top",   "template": "{name} to be the top wicket taker",             "note": None},
        {"key": "bowl_eco6",  "template": "{name} to have economy under 6",                "note": "Min 3 overs bowled"},
        {"key": "bowl_dot15", "template": "{name} to bowl 11+ dot balls",                  "note": None},
        {"key": "bowl_3wide", "template": "{name} to bowl 4+ wides",                       "note": None},
        {"key": "bowl_2nb",   "template": "{name} to bowl 2+ no balls",                    "note": None},
        {"key": "bowl_1stb",  "template": "{name} to take a wicket on their first ball",   "note": None},
        {"key": "bowl_pp",    "template": "{name} to take 2 wickets in the powerplay",     "note": "First 6 overs"},
        {"key": "bowl_last",  "template": "{name} to take a wicket with their last ball",  "note": None},
        {"key": "bowl_back",  "template": "{name} to take back to back wickets",           "note": None},
        {"key": "bowl_hat",   "template": "{name} to take a hat trick",                    "note": "Rare but legendary"},
        {"key": "bowl_top_s", "template": "{name} to dismiss the top scorer",              "note": None},
        {"key": "bowl_exp",   "template": "{name} to be the most expensive bowler",        "note": None},
        {"key": "bowl_b2b",   "template": "{name} to take 2 wickets in 1 over",            "note": None},
    ],
    "🔥 Team": [
        {"key": "team_6s11",   "template": "{name} team to hit 11+ sixes",                 "note": None},
        {"key": "team_4s19",   "template": "{name} team to hit 18+ fours",                 "note": None},
        {"key": "team_pp60",   "template": "{name} team to score 69+ in powerplay",        "note": "First 6 overs"},
        {"key": "team_ppu40",  "template": "{name} team to score under 40 in powerplay",   "note": "First 6 overs"},
        {"key": "team_10wk",   "template": "{name} team to win by 10 wickets",             "note": None},
        {"key": "team_50run",  "template": "{name} team to win by 50+ runs",               "note": None},
        {"key": "team_allout", "template": "{name} team to be all out",                    "note": None},
        {"key": "team_1w3ov",  "template": "{name} team to lose 3+ wickets inside 3 overs","note": None},
        {"key": "team_100p",   "template": "{name} team to have a 100+ partnership",       "note": None},
        {"key": "team_10ext",  "template": "{name} team to have 15+ extras total",         "note": None},
    ],
    "⭐ Special": [
        {"key": "sp_mom",      "template": "{name} to win Man of the Match",               "note": None},
        {"key": "sp_catch2",   "template": "{name} to take 2+ catches (Keeper excluded)",  "note": None},
        {"key": "sp_runout",   "template": "{name} to be involved in a run out",           "note": "Fielder or batsman"},
        {"key": "sp_lastb",    "template": "{name} team to win off the last ball",         "note": None},
        {"key": "sp_super",    "template": "Match to go to a Super Over",                  "note": "Type any name in blank"},
        {"key": "sp_openers2", "template": "Both openers of {name} to score 30+ runs",    "note": None},
        {"key": "sp_allround", "template": "{name} to score 30+ and take 2+ wickets",     "note": "All rounder special"},
        {"key": "sp_30six",    "template": "Match to have 30+ sixes total",                "note": "Type any name in blank"},
        {"key": "sp_first6",   "template": "First ball of the match to be a boundary",     "note": "Type any name in blank"},
        {"key": "sp_firstwk",  "template": "First ball of the match to be a wicket",       "note": "Type any name in blank"},
        {"key": "sp_top3_20",  "template": "Top 3 batters of {name} to all score 20+",    "note": None},
    ],
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_all_users():
    return db().table("users").select("*").execute().data or []

def get_playing_users():
    return [u for u in get_all_users() if u["role"] not in ADMIN_ROLES]

def get_user_by_username(username):
    for u in get_all_users():
        if u["username"] == username:
            return u
    return {}

def get_team(username):
    u = get_user_by_username(username)
    return u.get("team_name") or u.get("display_name") or username

def caps(text):
    return text.strip().upper() if text else ""

def get_matches():
    # Always ordered by match_number for consistency
    return db().table("matches").select("*").order("match_number").execute().data or []

def get_open_matches():
    return [m for m in get_matches() if m.get("status") not in ["done", "cancelled"]]

def is_season_locked():
    try:
        res = db().table("app_settings").select("value").eq("key", "season_locked").execute().data or []
        return res[0]["value"] == "true" if res else False
    except:
        return False

def login(username, password):
    res = db().table("users").select("*").eq("username", username).eq("password", password).execute()
    return res.data[0] if res.data else None

def streak_bonus(n):
    return max(0, n - 1)

def get_match_teams(match_name):
    if " VS " in match_name:
        parts = match_name.split(" VS ")
        return [parts[0].strip(), parts[1].strip()]
    return []

def calc_streak_from_preds(username, all_preds):
    my_preds = [p for p in all_preds if p.get("player") == username and p.get("actual_score") is not None]
    done = sorted(my_preds, key=lambda x: x.get("submitted_at") or "", reverse=True)
    streak = 0
    for p in done:
        match_preds = [x for x in all_preds if x.get("match_name") == p["match_name"] and x.get("actual_score") is not None]
        if not match_preds: break
        min_diff = min(abs(int(x.get("predicted_score") or 0) - int(x.get("actual_score") or 0)) for x in match_preds)
        my_diff  = abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0))
        if my_diff == min_diff: streak += 1
        else: break
    return streak

def calc_sp_wins(username, all_preds, match_names):
    wins = 0
    for mn in match_names:
        mp = [p for p in all_preds if p["match_name"] == mn and p.get("actual_score") is not None]
        if not mp: continue
        my = next((p for p in mp if p["player"] == username), None)
        if not my: continue
        my_d  = abs(int(my.get("predicted_score") or 0) - int(my.get("actual_score") or 0))
        min_d = min(abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0)) for p in mp)
        if my_d == min_d: wins += 1
    return wins

def calc_rank(username, mn, all_preds):
    mp = [p for p in all_preds if p["match_name"] == mn and p.get("actual_score") is not None]
    if not mp: return None
    my = next((p for p in mp if p["player"] == username), None)
    if not my: return None
    my_d  = abs(int(my.get("predicted_score") or 0) - int(my.get("actual_score") or 0))
    diffs = sorted([abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0)) for p in mp])
    return diffs.index(my_d) + 1 if my_d in diffs else 99

def breakdown_sp_from_pred(p, all_match_preds):
    act_score  = p.get("actual_score")
    act_winner = p.get("actual_winner", "")
    act_wkt    = p.get("actual_wickets")
    pred_score = int(p.get("predicted_score") or 0)
    pred_winner= p.get("predicted_winner", "")
    pred_wkt   = int(p.get("predicted_wickets") or 0)
    if act_score is None:
        return 0, 0, 0
    my_diff  = abs(pred_score - int(act_score))
    min_diff = min(abs(int(x.get("predicted_score") or 0) - int(act_score)) for x in all_match_preds if x.get("actual_score") is not None)
    is_win   = my_diff == min_diff
    is_exact = pred_score == int(act_score)
    corr_win = caps(pred_winner) == caps(act_winner)
    corr_wkt = is_win and pred_wkt == int(act_wkt or -1)
    return (6 if is_exact else 4 if is_win else 0), (2 if corr_win else 0), (1 if corr_wkt else 0)

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
    for p in preds:
        is_win   = p["diff"] == min_diff
        is_exact = int(p.get("predicted_score") or 0) == actual_score
        corr_win = caps(p.get("predicted_winner", "")) == actual_winner
        corr_wkt = is_win and int(p.get("predicted_wickets") or -1) == actual_wickets
        score_pts  = 6 if is_exact else (4 if is_win else 0)
        winner_pts = 2 if corr_win else 0
        wicket_pts = 1 if corr_wkt else 0
        db().table("predictions").update({
            "actual_score": actual_score, "actual_wickets": actual_wickets,
            "actual_winner": actual_winner, "points_awarded": score_pts + winner_pts + wicket_pts
        }).eq("id", p["id"]).execute()
    winners = [p for p in preds if p["diff"] == min_diff]
    all_preds_full = db().table("predictions").select("*").execute().data or []
    for w in winners:
        u = w["player"]
        prev_preds = [p for p in all_preds_full if p.get("match_name") != match_sel]
        streak = calc_streak_from_preds(u, prev_preds)
        new_streak = streak + 1
        bonus = streak_bonus(new_streak)
        if bonus > 0:
            db().table("streaks").insert({
                "player": u, "match_name": match_sel,
                "streak_count": new_streak, "bonus_points": bonus
            }).execute()

def get_pages(role):
    if role == "guest":
        return ["🏆 Leaderboard", "📊 Overall Stats", "👤 Player Stats", "🏅 Hall of Fame",
                "🏏 Draft League", "📋 Match Details", "📖 How to Score", "🌟 Season Predictions"]
    pages = ["🏆 Leaderboard", "📊 Overall Stats", "👤 Player Stats", "🏅 Hall of Fame",
             "🏏 Draft League", "📋 Match Details", "📖 How to Score", "🌟 Season Predictions",
             "🎱 BP Pool", "🔮 Score Prediction"]
    if role == "admin":
        pages += ["🏆 Enter Results", "📝 BP Results", "🔒 Lock / Cancel", "⚙️ Admin Panel"]
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

    all_preds   = db().table("predictions").select("*").execute().data or []
    all_bps     = db().table("pool_bps").select("player,points_awarded").execute().data or []
    all_streaks = db().table("streaks").select("player,bonus_points").execute().data or []

    rows = []
    for u in users:
        un   = u["username"]
        team = u.get("team_name") or u.get("display_name") or un
        my_preds = [p for p in all_preds if p["player"] == un]

        score_pts = winner_pts = wicket_pts = 0
        for p in my_preds:
            if p.get("actual_score") is not None:
                match_preds = [x for x in all_preds if x["match_name"] == p["match_name"] and x.get("actual_score") is not None]
                sp, wp, wkp = breakdown_sp_from_pred(p, match_preds)
                score_pts += sp; winner_pts += wp; wicket_pts += wkp

        bp_pts     = int(sum(float(b.get("points_awarded") or 0) for b in all_bps     if b["player"] == un))
        streak_pts = int(sum(float(s.get("bonus_points")   or 0) for s in all_streaks if s["player"] == un))
        total      = score_pts + winner_pts + wicket_pts + bp_pts + streak_pts
        exacts     = sum(1 for p in my_preds if p.get("actual_score") is not None
                        and int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1))

        rows.append({
            "_un":        un,
            "Rank":       "",
            "Team":       team,
            "Score Pts":  score_pts,
            "Winner Pts": winner_pts,
            "Wicket Pts": wicket_pts,
            "BP Pts":     bp_pts,
            "Streak Pts": streak_pts,
            "⚡ Exacts":  exacts,
            "Total":      total,
        })

    rows.sort(key=lambda x: x["Total"], reverse=True)
    for i, r in enumerate(rows):
        r["Rank"] = ["🥇", "🥈", "🥉"][i] if i < 3 else str(i + 1)

    # HTML table with light background on Total and Team columns
    header  = "| Rank | Team | Score Pts | Winner Pts | Wicket Pts | BP Pts | Streak Pts | ⚡ Exacts | Total |"
    divider = "|---|---|---|---|---|---|---|---|---|"
    lines   = [header, divider]
    for r in rows:
        logo = player_logo_html(r["_un"], 24)
        lines.append(
            f"| {r['Rank']} | {logo} **{r['Team']}** | {r['Score Pts']} | {r['Winner Pts']} | "
            f"{r['Wicket Pts']} | {r['BP Pts']} | {r['Streak Pts']} | {r['⚡ Exacts']} | **{r['Total']}** |"
        )
    st.markdown("\n".join(lines), unsafe_allow_html=True)

    # Dataframe version with styling for better mobile view
    st.markdown("---")
    df_rows = [{k: v for k, v in r.items() if k != "_un"} for r in rows]
    df = pd.DataFrame(df_rows)
    def style_lb(df):
        s = pd.DataFrame("", index=df.index, columns=df.columns)
        s["Total"] = "background-color:#1a3a1a;color:#90ee90;font-weight:bold"
        s["Team"]  = "background-color:#1a1a2e;font-weight:bold"
        return s
    st.dataframe(df.style.apply(style_lb, axis=None), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# DRAFT LEAGUE
# ══════════════════════════════════════════════════════════════════════════════
def page_draft_league():
    st.title("🏏 Draft League")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🏆 Draft Leaderboard", "👥 Team Squads"])

    with tab1:
        st.subheader("🏆 Draft League Standings")
        st.caption("Based on ESPNcricinfo MVP points for each player in your squad")

        # Get all player points from DB
        all_player_pts = db().table("draft_player_points").select("*").execute().data or []
        pts_map = {row["player_name"].lower(): float(row.get("mvp_points") or 0) for row in all_player_pts}

        if not pts_map:
            st.info("No MVP points loaded yet. Admin needs to update player points.")
        
        # Calculate team totals
        team_rows = []
        for username, team_data in DRAFT_TEAMS.items():
            team_name = team_data["name"]
            players   = team_data["players"]
            total     = sum(pts_map.get(p.lower(), 0) for p in players)
            scored    = sum(1 for p in players if pts_map.get(p.lower(), 0) > 0)
            team_rows.append({
                "_username": username,
                "Team":      team_name,
                "MVP Total": round(total, 2),
                "Players Scored": f"{scored}/{len(players)}",
            })

        team_rows.sort(key=lambda x: x["MVP Total"], reverse=True)
        for i, r in enumerate(team_rows):
            r["Rank"] = ["🥇","🥈","🥉"][i] if i < 3 else str(i+1)

        header  = "| Rank | Team | MVP Total | Players Scored |"
        divider = "|---|---|---|---|"
        lines   = [header, divider]
        for r in team_rows:
            logo = player_logo_html(r["_username"], 24)
            lines.append(f"| {r['Rank']} | {logo} **{r['Team']}** | **{r['MVP Total']}** | {r['Players Scored']} |")
        st.markdown("\n".join(lines), unsafe_allow_html=True)

        st.markdown("")
        if st.session_state.user.get("role") == "admin":
            st.markdown("---")
            st.caption("Last updated: " + (all_player_pts[0].get("updated_at","Never") if all_player_pts else "Never"))

    with tab2:
        st.subheader("👥 Team Squads & Points")
        all_player_pts = db().table("draft_player_points").select("*").execute().data or []
        pts_map = {row["player_name"].lower(): float(row.get("mvp_points") or 0) for row in all_player_pts}

        selected_team = st.selectbox("Select Team", [v["name"] for v in DRAFT_TEAMS.values()])
        team_username = next((k for k, v in DRAFT_TEAMS.items() if v["name"] == selected_team), None)

        if team_username:
            team_data = DRAFT_TEAMS[team_username]
            players   = team_data["players"]
            total_mvp = sum(pts_map.get(p.lower(), 0) for p in players)

            st.markdown(f'<div style="display:flex;align-items:center;gap:12px">{player_logo_html(team_username, 48)}<h3 style="margin:0">{selected_team}</h3></div>', unsafe_allow_html=True)
            st.metric("Total MVP Points", round(total_mvp, 2))
            st.markdown("---")

            player_rows = []
            for p in players:
                pts = pts_map.get(p.lower(), 0)
                player_rows.append({
                    "Player": p,
                    "MVP Points": round(pts, 2),
                    "Status": "✅ Scored" if pts > 0 else "⏳ Yet to play"
                })
            player_rows.sort(key=lambda x: x["MVP Points"], reverse=True)

            def style_players(df):
                s = pd.DataFrame("", index=df.index, columns=df.columns)
                s["MVP Points"] = "background-color:#1a3a1a;color:#90ee90;font-weight:bold"
                return s
            st.dataframe(pd.DataFrame(player_rows).style.apply(style_players, axis=None),
                        use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# OVERALL STATS
# ══════════════════════════════════════════════════════════════════════════════
def page_overall_stats():
    st.title("📊 Overall Stats")
    st.markdown("---")
    users   = get_playing_users()
    matches = get_matches()
    done    = [m for m in matches if m.get("status") == "done"]
    if not users or not done:
        st.info("Not enough data yet.")
        return
    match_names = [m["match_name"] for m in done]
    all_preds   = db().table("predictions").select("*").execute().data or []
    all_bps     = db().table("pool_bps").select("*").execute().data or []

    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Accuracy", "🏅 Podium Tracker", "⚔️ Head to Head", "📋 Full Table"])

    with tab1:
        st.subheader("🎯 SP Breakdown")
        sp_rows = []
        for u in users:
            un   = u["username"]
            team = u.get("team_name") or un
            up   = [p for p in all_preds if p["player"] == un and p.get("actual_score") is not None]
            sp_wins = calc_sp_wins(un, all_preds, match_names)
            played  = len(up)
            score_pts = winner_pts = wicket_pts = 0
            for p in up:
                match_preds = [x for x in all_preds if x["match_name"] == p["match_name"] and x.get("actual_score") is not None]
                sp, wp, wkp = breakdown_sp_from_pred(p, match_preds)
                score_pts += sp; winner_pts += wp; wicket_pts += wkp
            corr_w  = sum(1 for p in up if caps(p.get("predicted_winner","")) == caps(p.get("actual_winner","")))
            margin  = sum(abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0)) for p in up)
            exacts  = sum(1 for p in up if int(p.get("predicted_score") or 0) == int(p.get("actual_score") or 0))
            sp_rows.append({
                "Team": team, "Played": played, "SP Wins": sp_wins,
                "Win %": f"{round(sp_wins/played*100)}%" if played else "0%",
                "Score Pts": score_pts, "Winner Pts": winner_pts, "Wicket Pts": wicket_pts,
                "Correct Winners": corr_w, "Exact Preds": exacts, "Margin of Error": margin,
            })
        sp_rows.sort(key=lambda x: x["SP Wins"], reverse=True)
        st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("🎱 BP Success Rate")
        bp_rows = []
        for u in users:
            un   = u["username"]
            team = u.get("team_name") or un
            ubps = [b for b in all_bps if b["player"] == un]
            correct = sum(1 for b in ubps if b.get("result") == "correct")
            wrong   = sum(1 for b in ubps if b.get("result") == "wrong")
            total_b = correct + wrong
            bp_rows.append({
                "Team": team, "BP Correct": correct, "BP Wrong": wrong,
                "Success %": f"{round(correct/total_b*100)}%" if total_b else "0%",
                "Custom BPs": sum(1 for b in ubps if b.get("bp_type") == "custom"),
                "BP Points": int(sum(float(b.get("points_awarded") or 0) for b in ubps)),
            })
        bp_rows.sort(key=lambda x: x["BP Correct"], reverse=True)
        st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("📐 Margin of Error — lower is better")
        m_df = pd.DataFrame([{"Team": r["Team"], "Margin": r["Margin of Error"]}
                              for r in sorted(sp_rows, key=lambda x: x["Margin of Error"])])
        st.bar_chart(m_df.set_index("Team"), use_container_width=True, height=300)

    with tab2:
        st.subheader("🏅 Podium Tracker")
        podium_rows = []
        for u in users:
            un   = u["username"]
            team = u.get("team_name") or un
            first = second = third = missed = 0
            for mn in match_names:
                rank = calc_rank(un, mn, all_preds)
                if rank is None: missed += 1
                elif rank == 1: first  += 1
                elif rank == 2: second += 1
                elif rank == 3: third  += 1
            attended = len(match_names) - missed
            podium_rows.append({
                "Team": team, "🥇 1st": first, "🥈 2nd": second, "🥉 3rd": third,
                "Missed": missed,
                "Attendance %": f"{round(attended/len(match_names)*100)}%" if match_names else "0%",
            })
        podium_rows.sort(key=lambda x: (x["🥇 1st"], x["🥈 2nd"], x["🥉 3rd"]), reverse=True)
        st.dataframe(pd.DataFrame(podium_rows), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("⚔️ Head to Head")
        names = [u.get("team_name") or u["username"] for u in users]
        c1, c2 = st.columns(2)
        with c1: p1_name = st.selectbox("Player 1", names, key="h2h1")
        with c2: p2_name = st.selectbox("Player 2", [n for n in names if n != p1_name], key="h2h2")
        p1 = next((u for u in users if (u.get("team_name") or u["username"]) == p1_name), None)
        p2 = next((u for u in users if (u.get("team_name") or u["username"]) == p2_name), None)
        if p1 and p2:
            def get_h2h(u):
                un  = u["username"]
                up  = [p for p in all_preds if p["player"] == un and p.get("actual_score") is not None]
                ubp = [b for b in all_bps if b["player"] == un]
                f = s = t = 0
                for mn in match_names:
                    r = calc_rank(un, mn, all_preds)
                    if r == 1: f += 1
                    elif r == 2: s += 1
                    elif r == 3: t += 1
                score_pts = winner_pts = wicket_pts = 0
                for p in up:
                    mp = [x for x in all_preds if x["match_name"] == p["match_name"] and x.get("actual_score") is not None]
                    sp, wp, wkp = breakdown_sp_from_pred(p, mp)
                    score_pts += sp; winner_pts += wp; wicket_pts += wkp
                bp_total  = int(sum(float(b.get("points_awarded") or 0) for b in ubp))
                str_total = int(sum(float(s2.get("bonus_points") or 0) for s2 in (db().table("streaks").select("bonus_points").eq("player", un).execute().data or [])))
                return {
                    "Total Points": score_pts + winner_pts + wicket_pts + bp_total + str_total,
                    "Score Points": score_pts, "Winner Points": winner_pts, "Wicket Points": wicket_pts,
                    "BP Points": bp_total, "Streak Points": str_total,
                    "SP Wins": calc_sp_wins(un, all_preds, match_names),
                    "BP Correct": sum(1 for b in ubp if b.get("result") == "correct"),
                    "BP Wrong": sum(1 for b in ubp if b.get("result") == "wrong"),
                    "Exact Predictions": sum(1 for p in up if int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1)),
                    "Correct Winners": sum(1 for p in up if caps(p.get("predicted_winner","")) == caps(p.get("actual_winner",""))),
                    "Margin of Error": sum(abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0)) for p in up),
                    "1st Place Finishes": f, "2nd Place Finishes": s, "3rd Place Finishes": t,
                    "Current Streak": calc_streak_from_preds(un, all_preds),
                }
            s1, s2 = get_h2h(p1), get_h2h(p2)
            lower_better = {"Margin of Error", "BP Wrong"}
            h2h_rows = []
            for stat in s1:
                v1, v2 = s1[stat], s2[stat]
                w1 = (v1 < v2) if stat in lower_better else (v1 > v2)
                w2 = (v2 < v1) if stat in lower_better else (v2 > v1)
                h2h_rows.append({"Stat": stat,
                    p1_name: f"✅ {v1}" if w1 else str(v1),
                    p2_name: f"✅ {v2}" if w2 else str(v2)})
            st.markdown(f"### {p1_name}  ⚔️  {p2_name}")
            st.dataframe(pd.DataFrame(h2h_rows), use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("📋 Full Stats Table")
        full = []
        for u in users:
            un   = u["username"]
            team = u.get("team_name") or un
            up   = [p for p in all_preds if p["player"] == un and p.get("actual_score") is not None]
            ubps = [b for b in all_bps if b["player"] == un]
            score_pts = winner_pts = wicket_pts = 0
            for p in up:
                mp = [x for x in all_preds if x["match_name"] == p["match_name"] and x.get("actual_score") is not None]
                sp, wp, wkp = breakdown_sp_from_pred(p, mp)
                score_pts += sp; winner_pts += wp; wicket_pts += wkp
            bp_total  = int(sum(float(b.get("points_awarded") or 0) for b in ubps))
            str_total = int(sum(float(s.get("bonus_points") or 0) for s in (db().table("streaks").select("bonus_points").eq("player", un).execute().data or [])))
            full.append({
                "Team": team,
                "Total": score_pts + winner_pts + wicket_pts + bp_total + str_total,
                "Score Pts": score_pts, "Winner Pts": winner_pts, "Wicket Pts": wicket_pts,
                "BP Pts": bp_total, "Streak Pts": str_total,
                "SP Wins": calc_sp_wins(un, all_preds, match_names),
                "BP Correct": sum(1 for b in ubps if b.get("result") == "correct"),
                "BP Wrong": sum(1 for b in ubps if b.get("result") == "wrong"),
                "Exacts": sum(1 for p in up if int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1)),
                "Margin of Error": sum(abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0)) for p in up),
                "Attended": len(set(p["match_name"] for p in all_preds if p["player"] == un)),
                "Streak": calc_streak_from_preds(un, all_preds),
            })
        full.sort(key=lambda x: x["Total"], reverse=True)
        st.dataframe(pd.DataFrame(full), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER STATS
# ══════════════════════════════════════════════════════════════════════════════
def page_player_stats():
    st.title("👤 Player Stats")
    st.markdown("---")
    users = get_playing_users()
    if not users: st.info("No players."); return
    names    = [u.get("team_name") or u["username"] for u in users]
    selected = st.selectbox("Select Player", names)
    u = next((u for u in users if (u.get("team_name") or u["username"]) == selected), None)
    if not u: return
    un      = u["username"]
    matches = get_matches()
    mm      = {m["match_name"]: m.get("match_number", i+1) for i, m in enumerate(matches)}
    all_preds_full = db().table("predictions").select("*").execute().data or []
    my_preds = db().table("predictions").select("*").eq("player", un).execute().data or []
    my_bps   = db().table("pool_bps").select("*").eq("player", un).execute().data or []
    my_str   = db().table("streaks").select("bonus_points").eq("player", un).execute().data or []

    score_pts = winner_pts = wicket_pts = 0
    for p in my_preds:
        if p.get("actual_score") is not None:
            mp = [x for x in all_preds_full if x["match_name"] == p["match_name"] and x.get("actual_score") is not None]
            sp, wp, wkp = breakdown_sp_from_pred(p, mp)
            score_pts += sp; winner_pts += wp; wicket_pts += wkp

    b_pts  = int(sum(float(b.get("points_awarded") or 0) for b in my_bps))
    st_pts = int(sum(float(s.get("bonus_points")   or 0) for s in my_str))
    tot    = score_pts + winner_pts + wicket_pts + b_pts + st_pts
    streak = calc_streak_from_preds(un, all_preds_full)
    exacts = sum(1 for p in my_preds if p.get("actual_score") is not None
                 and int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1))

    st.markdown(f'<div style="display:flex;align-items:center;gap:12px">{player_logo_html(un, 52)}<h2 style="margin:0">{selected}</h2></div>', unsafe_allow_html=True)
    st.markdown("")

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("🏆 Total", tot)
    c2.metric("🎯 Score Pts", score_pts)
    c3.metric("🏆 Winner Pts", winner_pts)
    c4.metric("🎳 Wicket Pts", wicket_pts)
    c5.metric("🎱 BP Pts", b_pts)
    c6.metric("🔥 Streak Pts", st_pts)

    if streak > 1:
        st.success(f"🔥 Active streak: **{streak} wins in a row!** (+{streak_bonus(streak+1)} next win)")
    elif streak == 1:
        st.info("✅ Won last match! Win again to start earning streak bonus.")

    st.markdown("---")
    if tot > 0:
        st.subheader("📊 Points Breakdown")
        st.bar_chart(pd.DataFrame({
            "Category": ["Score","Winner","Wicket","BP","Streak"],
            "Points":   [score_pts, winner_pts, wicket_pts, b_pts, st_pts]
        }).set_index("Category"), use_container_width=True, height=250)

    st.markdown("---")
    st.subheader("🔮 Score Predictions")
    if my_preds:
        rows = []
        for p in my_preds:
            sp = wp = wkp = 0
            if p.get("actual_score") is not None:
                mp = [x for x in all_preds_full if x["match_name"] == p["match_name"] and x.get("actual_score") is not None]
                sp, wp, wkp = breakdown_sp_from_pred(p, mp)
            ex  = "⚡" if p.get("actual_score") and int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1) else ""
            act = f"{p.get('actual_score')} - {str(p.get('actual_wickets',0)).zfill(2)} | {p.get('actual_winner','')}" if p.get("actual_score") else "Pending"
            rows.append({
                "Match #":    f"#{mm.get(p['match_name'],'?')}",
                "Match":      p["match_name"],
                "Predicted":  f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p.get('predicted_winner','')}",
                "Actual":     act, "⚡": ex,
                "Score Pts":  sp, "Winner Pts": wp, "Wicket Pts": wkp,
                "Total Pts":  sp + wp + wkp,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No predictions yet.")

    st.markdown("---")
    st.subheader("🎱 Bold Predictions")
    if my_bps:
        rows = []
        for b in my_bps:
            icon = "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "🚫" if b.get("result")=="dismissed" else "⏳"
            rows.append({
                "Match #":    f"#{mm.get(b['match_name'],'?')}",
                "Match":      b["match_name"],
                "Prediction": b["prediction_text"],
                "Type":       "💡" if b.get("bp_type")=="custom" else "🎱",
                "Result":     icon,
                "Pts":        int(float(b.get("points_awarded") or 0)),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No BPs yet.")


# ══════════════════════════════════════════════════════════════════════════════
# HALL OF FAME
# ══════════════════════════════════════════════════════════════════════════════
def render_podium(title, description, data, stat_label):
    st.markdown(f"### {title}")
    st.caption(description)
    if not data:
        st.info("Not enough data.")
        st.markdown("---")
        return
    colors = ["#FFD700","#C0C0C0","#CD7F32"]
    for pos in range(min(3, len(data))):
        name, val, username = data[pos]
        medal = ["🥇","🥈","🥉"][pos]
        size  = ["1.3em","1.1em","1em"][pos]
        logo  = player_logo_html(username, 32)
        st.markdown(f"""
<div style='background:{colors[pos]};padding:12px 16px;border-radius:10px;
color:#000;margin:4px 0;display:flex;justify-content:space-between;align-items:center'>
<span style='display:flex;align-items:center;gap:8px;font-size:{size};font-weight:bold'>{logo}{medal} {name}</span>
<span style='font-size:0.9em'>{stat_label}: <b>{val}</b></span>
</div>""", unsafe_allow_html=True)
    st.markdown("---")

def page_hall_of_fame():
    st.title("🏅 Hall of Fame")
    st.markdown("---")
    users   = get_playing_users()
    matches = get_matches()
    done    = [m for m in matches if m.get("status") == "done"]
    mnames  = [m["match_name"] for m in done]
    if not users or not done:
        st.info("Not enough data yet.")
        return
    all_preds = db().table("predictions").select("*").execute().data or []
    all_bps   = db().table("pool_bps").select("*").execute().data or []
    stats = {}
    for u in users:
        un   = u["username"]
        team = u.get("team_name") or un
        up   = [p for p in all_preds if p["player"] == un and p.get("actual_score") is not None]
        ubps = [b for b in all_bps if b["player"] == un]
        first = second = 0
        for mn in mnames:
            r = calc_rank(un, mn, all_preds)
            if r == 1: first  += 1
            elif r == 2: second += 1
        tmpl_counts = {}
        for b in ubps:
            k = b.get("template_key","")
            if k and k not in ["custom","admin_behalf"]:
                tmpl_counts[k] = tmpl_counts.get(k,0)+1
        score_pts = winner_pts = wicket_pts = 0
        for p in up:
            mp = [x for x in all_preds if x["match_name"] == p["match_name"] and x.get("actual_score") is not None]
            sp, wp, wkp = breakdown_sp_from_pred(p, mp)
            score_pts += sp; winner_pts += wp; wicket_pts += wkp
        bp_total  = int(sum(float(b.get("points_awarded") or 0) for b in ubps))
        str_total = int(sum(float(s.get("bonus_points") or 0) for s in (db().table("streaks").select("bonus_points").eq("player",un).execute().data or [])))
        stats[un] = {
            "team": team, "username": un,
            "total": score_pts+winner_pts+wicket_pts+bp_total+str_total,
            "sp_wins": calc_sp_wins(un,all_preds,mnames),
            "first": first, "second": second,
            "bp_correct": sum(1 for b in ubps if b.get("result")=="correct"),
            "bp_wrong":   sum(1 for b in ubps if b.get("result")=="wrong"),
            "exact": sum(1 for p in up if int(p.get("predicted_score") or 0)==int(p.get("actual_score") or -1)),
            "margin": sum(abs(int(p.get("predicted_score") or 0)-int(p.get("actual_score") or 0)) for p in up),
            "custom_bps": sum(1 for b in ubps if b.get("bp_type")=="custom"),
            "attended": len(set(p["match_name"] for p in all_preds if p["player"]==un)),
            "corr_w": sum(1 for p in up if caps(p.get("predicted_winner",""))==caps(p.get("actual_winner",""))),
            "corr_wk": sum(1 for p in up if int(p.get("predicted_wickets") or -1)==int(p.get("actual_wickets") or -2)),
            "top_tmpl_cnt": max(tmpl_counts.values()) if tmpl_counts else 0,
            "cur_streak": calc_streak_from_preds(un, all_preds),
        }
    def top3(key, rev=True):
        s = sorted(stats.items(), key=lambda x: x[1][key], reverse=rev)
        return [(stats[u]["team"], stats[u][key], stats[u]["username"]) for u,_ in s[:3]]
    col1, col2 = st.columns(2)
    with col1:
        render_podium('👑 "Too Good"',              "Most SP wins. Consistent. Clinical. Probably cheating.",                top3("sp_wins"),           "SP Wins")
        render_podium('⚡ "The Psychic"',           "Most exact predictions. Basically has a crystal ball.",                 top3("exact"),             "Exact Preds")
        render_podium('🧠 "Big Brain"',             "Most BPs correct. Actually knows cricket. Shocking.",                   top3("bp_correct"),        "BPs Correct")
        render_podium('🎯 "The Uncrowned King"',    "Lowest margin of error. Always closest, never wins.",                   top3("margin",rev=False),  "Margin of Error")
        render_podium('🏏 "Team Whisperer"',        "Most correct match winner predictions.",                                top3("corr_w"),            "Correct Winners")
        render_podium('🎳 "Wicket Whisperer"',      "Most correct wicket predictions.",                                      top3("corr_wk"),           "Correct Wickets")
        render_podium('🏃 "Never Misses"',          "Best attendance. Always there, no excuses.",                            top3("attended"),          "Matches Attended")
        render_podium('🔥 "On Demon Time"',         "Longest active winning streak.",                                        top3("cur_streak"),        "Current Streak")
    with col2:
        render_podium('💀 "Absolute Clown"',        "Most BPs wrong. Boldly wrong every single time.",                       top3("bp_wrong"),          "BPs Wrong")
        render_podium('🎲 "Asks Nobody"',           "Most custom BPs. Didn't ask admin. Just vibes.",                        top3("custom_bps"),        "Custom BPs")
        render_podium('😤 "Uncrowned Prince"',      "Most 2nd places. So close, so often, so painful.",                      top3("second"),            "2nd Places")
        render_podium('💨 "What Are You Watching"', "Highest margin of error. Predicted 200, score was 156. Every time.",    top3("margin"),            "Margin of Error")
        render_podium('🪣 "Touch Grass"',           "Least total points. Might need a different hobby.",                     top3("total",rev=False),   "Total Points")
        render_podium('🛋️ "Checked Out"',           "Most matches missed. Drought so long it has its own Wikipedia page.",   top3("attended",rev=False),"Matches Attended")
        render_podium('🔒 "Boring But Elite"',      "Most 1st place finishes. Consistent. Boring. Winning.",                 top3("first"),             "1st Places")
        render_podium('🃏 "One Trick Pony"',        "Same BP every match. Found one move and never looked back.",            top3("top_tmpl_cnt"),      "Same BP Used")


# ══════════════════════════════════════════════════════════════════════════════
# BP POOL
# ══════════════════════════════════════════════════════════════════════════════
def page_bp_pool():
    st.title("🎱 BP Pool")
    st.markdown("✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt** | 🚫 Dismissed → **0 pts**")
    st.markdown("---")
    matches = [m for m in get_open_matches() if not m.get("bp_locked")]
    if not matches:
        st.warning("⏳ No open matches for BP submission.")
        return
    mm    = {m["match_name"]: m.get("match_number", i+1) for i, m in enumerate(get_matches())}
    match = st.selectbox("Select Match", [f"#{mm.get(m['match_name'],'?')} — {m['match_name']}" for m in matches])
    match_name = match.split(" — ",1)[1]
    existing = db().table("pool_bps").select("*").eq("player",st.session_state.user["username"]).eq("match_name",match_name).execute().data or []
    if existing:
        b = existing[0]
        icon = "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "🚫" if b.get("result")=="dismissed" else "⏳"
        st.warning("✅ Already submitted!")
        st.info(f"{icon} **{b['prediction_text']}** | Pts: {int(float(b.get('points_awarded',0)))}")
        return
    tabs = st.tabs(list(BP_POOL.keys()))
    for tab, cat in zip(tabs, BP_POOL.keys()):
        with tab:
            for bp in BP_POOL[cat]:
                disp = bp["template"].replace("{name}","______")
                if st.button(disp, key=f"bp_{bp['key']}", use_container_width=True):
                    st.session_state.sel_key  = bp["key"]
                    st.session_state.sel_tmpl = bp["template"]
                    st.session_state.sel_note = bp["note"]
                    st.rerun()
    st.markdown("---")
    if st.session_state.get("sel_key"):
        tmpl = st.session_state.sel_tmpl
        note = st.session_state.sel_note
        st.markdown(f"#### Selected: *{tmpl.replace('{name}','______')}*")
        if note: st.info(f"ℹ️ **Note:** {note}")
        fill_in = st.text_input("Fill in the blank:", placeholder="e.g. Kohli, SRH...") if "{name}" in tmpl else tmpl
        if fill_in and "{name}" in tmpl:
            st.caption(f"Preview: *{tmpl.replace('{name}', fill_in.strip())}*")
        if st.button("🚀 Submit this BP", use_container_width=True):
            if not fill_in or not fill_in.strip():
                st.error("Fill in the blank!")
            else:
                final = tmpl.replace("{name}", fill_in.strip()) if "{name}" in tmpl else tmpl
                db().table("pool_bps").insert({
                    "match_name": match_name, "player": st.session_state.user["username"],
                    "bp_type": "pool", "template_key": st.session_state.sel_key,
                    "fill_in": fill_in.strip(), "prediction_text": final,
                    "status": "pending", "points_awarded": 0,
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()
                for k in ["sel_key","sel_tmpl","sel_note"]:
                    st.session_state[k] = None
                st.success(f"✅ Submitted: **{final}**")
                st.balloons()
    st.markdown("---")
    st.markdown("### 💡 Custom BP")
    st.caption("Clear it with admin on WhatsApp first!")
    custom = st.text_area("Your custom BP:", placeholder="e.g. SRH will bowl 24 wides")
    if st.button("🚀 Submit Custom BP", use_container_width=True):
        if not custom.strip():
            st.error("Enter your BP!")
        else:
            ex2 = db().table("pool_bps").select("*").eq("player",st.session_state.user["username"]).eq("match_name",match_name).execute().data or []
            if ex2:
                st.error("Already submitted a BP for this match!")
            else:
                db().table("pool_bps").insert({
                    "match_name": match_name, "player": st.session_state.user["username"],
                    "bp_type": "custom", "template_key": "custom", "fill_in": "",
                    "prediction_text": custom.strip(), "status": "pending",
                    "points_awarded": 0, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()
                st.success("✅ Custom BP submitted!")
                st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# SCORE PREDICTION
# ══════════════════════════════════════════════════════════════════════════════
def page_submit_sp():
    st.title("🔮 Score Prediction")
    st.markdown("---")
    matches = [m for m in get_open_matches() if not m.get("sp_locked")]
    if not matches:
        st.warning("⏳ No open matches.")
        return
    mm    = {m["match_name"]: m.get("match_number", i+1) for i, m in enumerate(get_matches())}
    match = st.selectbox("Select Match", [f"#{mm.get(m['match_name'],'?')} — {m['match_name']}" for m in matches])
    match_name = match.split(" — ",1)[1]
    existing = db().table("predictions").select("*").eq("player",st.session_state.user["username"]).eq("match_name",match_name).execute().data or []
    if existing:
        p = existing[0]
        st.warning("✅ Already submitted!")
        st.info(f"**{p['predicted_score']} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p['predicted_winner']}** | Pts: {int(float(p.get('points_awarded',0)))}")
        return
    c1, c2 = st.columns(2)
    with c1:
        ps = st.number_input("Predicted Score (runs)", min_value=0, max_value=400, step=1)
        pw = st.number_input("Predicted Wickets (0-10)", min_value=0, max_value=10, step=1)
    with c2:
        teams = get_match_teams(match_name)
        winner = st.selectbox("Predicted Winner", teams) if teams else caps(st.text_input("Predicted Winner"))
        if winner: st.caption(f"Team: **{winner}**")
    st.caption(f"Your prediction: **{ps} - {str(pw).zfill(2)} | {winner}**")
    if st.button("🚀 Submit", use_container_width=True):
        if not winner:
            st.error("Select the winner!")
        else:
            db().table("predictions").insert({
                "match_name": match_name, "player": st.session_state.user["username"],
                "predicted_score": ps, "predicted_wickets": pw,
                "predicted_winner": caps(winner), "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ Prediction submitted!")


# ══════════════════════════════════════════════════════════════════════════════
# BP RESULTS
# ══════════════════════════════════════════════════════════════════════════════
def page_bp_results():
    st.title("📝 BP Results")
    st.markdown("---")
    pending = db().table("pool_bps").select("*").eq("status","pending").execute().data or []
    if not pending:
        st.info("No BPs waiting.")
        return
    match_list = list(set(b["match_name"] for b in pending))
    sel = st.selectbox("Filter by Match", ["All"] + match_list)
    filtered = pending if sel=="All" else [b for b in pending if b["match_name"]==sel]
    for b in filtered:
        bp_type = "💡 Custom" if b.get("bp_type")=="custom" else "🎱 Pool"
        st.markdown(f"**{get_team(b['player'])}** — {b['match_name']} {bp_type}")
        st.markdown(f"*{b['prediction_text']}*")
        c1,c2,c3 = st.columns(3)
        with c1:
            if st.button("✅ Correct (+3)", key=f"c_{b['id']}"):
                db().table("pool_bps").update({"result":"correct","points_awarded":3,"status":"done"}).eq("id",b["id"]).execute()
                st.rerun()
        with c2:
            if st.button("❌ Wrong (-1)", key=f"w_{b['id']}"):
                db().table("pool_bps").update({"result":"wrong","points_awarded":-1,"status":"done"}).eq("id",b["id"]).execute()
                st.rerun()
        with c3:
            if st.button("🚫 Dismiss (0)", key=f"d_{b['id']}"):
                db().table("pool_bps").update({"result":"dismissed","points_awarded":0,"status":"done"}).eq("id",b["id"]).execute()
                st.rerun()
        st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# ENTER RESULTS
# ══════════════════════════════════════════════════════════════════════════════
def page_enter_results():
    st.title("🏆 Enter Match Results")
    st.markdown("---")
    matches = get_matches()
    mm = {m["match_name"]: m.get("match_number", i+1) for i, m in enumerate(matches)}
    pending = [m for m in matches if m.get("sp_locked") and m.get("status") not in ["done","cancelled"]]
    if not pending:
        st.info("No matches waiting for results.")
        return
    sel = st.selectbox("Select Match", [f"#{mm[m['match_name']]} — {m['match_name']}" for m in pending])
    match_name     = sel.split(" — ",1)[1]
    actual_score   = st.number_input("Actual Score (runs)", min_value=0, max_value=500, step=1)
    actual_wickets = st.number_input("Actual Wickets", min_value=0, max_value=10, step=1)
    teams = get_match_teams(match_name)
    aw = st.selectbox("Actual Winner", teams) if teams else caps(st.text_input("Actual Winner"))
    if aw: st.caption(f"Team: **{aw}**")
    if st.button("✅ Submit Result & Award Points", use_container_width=True):
        if not aw:
            st.error("Enter winner!")
        else:
            award_sp_points(match_name, actual_score, actual_wickets, aw)
            st.success("✅ Results submitted!")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LOCK / CANCEL
# ══════════════════════════════════════════════════════════════════════════════
def page_lock_cancel():
    st.title("🔒 Lock / Cancel")
    st.markdown("---")
    matches = get_matches()
    if not matches: st.info("No matches."); return
    user = st.session_state.user
    now  = datetime.now().strftime("%Y-%m-%d %H:%M")
    mm   = {m["match_name"]: m.get("match_number", i+1) for i, m in enumerate(matches)}
    for m in matches:
        with st.expander(f"Match #{mm[m['match_name']]} — {m['match_name']} | {m.get('status','open').upper()}"):
            c1,c2 = st.columns(2)
            with c1:
                if m.get("bp_locked"):
                    st.success(f"🔒 BP locked at {m.get('bp_locked_at','')}")
                    if st.button("🔓 Unlock BP", key=f"ubp_{m['id']}"):
                        db().table("matches").update({"bp_locked":False,"bp_locked_by":None,"bp_locked_at":None}).eq("id",m["id"]).execute()
                        st.rerun()
                else:
                    if st.button("🔒 Lock BP", key=f"lbp_{m['id']}"):
                        db().table("matches").update({"bp_locked":True,"bp_locked_by":user["username"],"bp_locked_at":now}).eq("id",m["id"]).execute()
                        st.rerun()
            with c2:
                if m.get("sp_locked"):
                    st.success(f"🔒 SP locked at {m.get('sp_locked_at','')}")
                    if st.button("🔓 Unlock SP", key=f"usp_{m['id']}"):
                        db().table("matches").update({"sp_locked":False,"sp_locked_by":None,"sp_locked_at":None}).eq("id",m["id"]).execute()
                        st.rerun()
                else:
                    if st.button("🔒 Lock SP", key=f"lsp_{m['id']}"):
                        db().table("matches").update({"sp_locked":True,"sp_locked_by":user["username"],"sp_locked_at":now}).eq("id",m["id"]).execute()
                        st.rerun()
            if m.get("status") != "cancelled":
                st.markdown("**🌧️ Cancel due to rain:**")
                cancel_type = st.selectbox("What to cancel?",
                    ["Select...","Cancel BP only","Cancel SP only","Cancel both BP and SP"],
                    key=f"csel_{m['id']}")
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


# ══════════════════════════════════════════════════════════════════════════════
# MATCH DETAILS
# ══════════════════════════════════════════════════════════════════════════════
def page_match_details():
    st.title("📋 Match Details")
    st.markdown("---")
    matches = get_matches()
    if not matches: st.info("No matches yet."); return
    mm      = {m["match_name"]: m.get("match_number", i+1) for i, m in enumerate(matches)}
    options = [f"Match #{mm[m['match_name']]} — {m['match_name']}" for m in matches]
    idx     = st.selectbox("Select Match", range(len(matches)), format_func=lambda i: options[i])
    m       = matches[idx]
    st.markdown(f"### 🏏 Match #{mm[m['match_name']]} — {m['match_name']} | {m.get('match_date','')}")
    c1,c2,c3 = st.columns(3)
    c1.metric("BP", "🔒 Locked" if m.get("bp_locked") else "🟢 Open")
    c2.metric("SP", "🔒 Locked" if m.get("sp_locked") else "🟢 Open")
    c3.metric("Status", m.get("status","open").upper())
    if m.get("actual_score"):
        st.success(f"**Result:** {m.get('actual_winner')} won | {m.get('actual_score')} - {str(m.get('actual_wickets',0)).zfill(2)}")

    if m.get("status") == "done":
        st.markdown("---")
        st.subheader("🏆 Points of the Day")
        users = get_playing_users()
        all_preds_match = db().table("predictions").select("*").eq("match_name",m["match_name"]).execute().data or []
        day_rows = []
        for u in users:
            p = next((x for x in all_preds_match if x["player"]==u["username"]), None)
            b = db().table("pool_bps").select("points_awarded").eq("player",u["username"]).eq("match_name",m["match_name"]).execute().data or []
            sp_today = wn_today = wk_today = bp_today = 0
            if p and p.get("actual_score") is not None:
                sp_today, wn_today, wk_today = breakdown_sp_from_pred(p, all_preds_match)
            if b: bp_today = int(float(b[0].get("points_awarded") or 0))
            day_rows.append({
                "Team": u.get("team_name") or u["username"],
                "Score Pts": sp_today, "Winner Pts": wn_today,
                "Wicket Pts": wk_today, "BP Pts": bp_today,
                "Total Today": sp_today+wn_today+wk_today+bp_today
            })
        day_rows.sort(key=lambda x: x["Total Today"], reverse=True)
        st.dataframe(pd.DataFrame(day_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🎱 Bold Predictions")
    bps = db().table("pool_bps").select("*").eq("match_name",m["match_name"]).execute().data or []
    if bps:
        if not m.get("bp_locked") and m.get("status") != "done":
            st.info("🔒 Hidden until BP is locked.")
        else:
            st.dataframe(pd.DataFrame([{
                "": "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "🚫" if b.get("result")=="dismissed" else "⏳",
                "Team": get_team(b["player"]),
                "Prediction": b["prediction_text"],
                "Type": "💡" if b.get("bp_type")=="custom" else "🎱",
                "Pts": int(float(b.get("points_awarded",0))),
            } for b in bps]), use_container_width=True, hide_index=True)
    else:
        st.info("No BPs yet.")

    st.markdown("---")
    st.subheader("🔮 Score Predictions")
    preds = db().table("predictions").select("*").eq("match_name",m["match_name"]).execute().data or []
    if preds:
        if not m.get("sp_locked") and m.get("status") != "done":
            st.info("🔒 Hidden until SP is locked.")
        else:
            preds_s = sorted(preds, key=lambda x: x.get("points_awarded",0), reverse=True)
            rows = []
            for i, p in enumerate(preds_s):
                sp = wp = wkp = 0
                if p.get("actual_score") is not None:
                    sp, wp, wkp = breakdown_sp_from_pred(p, preds)
                rows.append({
                    "": "🥇" if i==0 and (p.get("points_awarded") or 0)>=4 else "",
                    "Team": get_team(p["player"]),
                    "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p.get('predicted_winner','')}",
                    "Actual": f"{m.get('actual_score')} - {str(m.get('actual_wickets',0)).zfill(2)} | {m.get('actual_winner','')}" if m.get("actual_score") else "-",
                    "⚡": "⚡" if m.get("actual_score") and int(p.get("predicted_score") or 0)==m.get("actual_score") else "",
                    "Score Pts": sp, "Winner Pts": wp, "Wicket Pts": wkp, "Total": sp+wp+wkp,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No predictions yet.")


# ══════════════════════════════════════════════════════════════════════════════
# SEASON PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
def page_season_predictions():
    st.title("🌟 Season Predictions")
    st.markdown("---")
    user   = st.session_state.user
    un     = user["username"]
    locked = is_season_locked()
    all_sp = db().table("season_predictions").select("*").execute().data or []
    if locked and all_sp:
        st.subheader("📊 Everyone's Answers")
        for field in SEASON_FIELDS:
            st.markdown(f"**{field['label']}** {'*(just for fun)*' if field['fun'] else ''}")
            field_rows = [{"Team": get_team(sp["player"]), "Answer": sp.get(field["key"],"-") or "-"} for sp in all_sp]
            st.dataframe(pd.DataFrame(field_rows), use_container_width=True, hide_index=True)
            st.markdown("")
        st.markdown("---")
    elif not locked and all_sp:
        st.info("🔒 Season predictions will be revealed once admin locks them.")
        st.markdown("---")
    if user["role"] == "guest": return
    existing = db().table("season_predictions").select("*").eq("player",un).execute().data or []
    if existing:
        st.success("✅ Your season predictions are submitted!")
        return
    if locked:
        st.info("Season predictions are now locked. Submission closed.")
        return
    st.subheader("Submit Your Predictions")
    st.markdown("**Points:** 🧡 Orange Cap=10 | 💜 Purple Cap=10 | 🌟 Emerging=15 | 🏏 Top4=5pts each (+2 if correct position) | Rest = just for fun!")
    answers = {}
    for field in SEASON_FIELDS:
        label = f"{field['label']} {'🎉 just for fun' if field['fun'] else ''}"
        answers[field["key"]] = st.text_input(label, key=f"sp_{field['key']}")
    if st.button("🚀 Submit Season Predictions", use_container_width=True):
        if not all(answers[f["key"]].strip() for f in SEASON_FIELDS):
            st.error("Please fill all fields!")
        else:
            row = {"player": un, "points_awarded": 0}
            for field in SEASON_FIELDS:
                row[field["key"]] = caps(answers[field["key"]])
            db().table("season_predictions").insert(row).execute()
            st.success("✅ Submitted!")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HOW TO SCORE
# ══════════════════════════════════════════════════════════════════════════════
def page_how_to_score():
    st.title("📖 How to Score")
    st.markdown("---")
    st.subheader("🎱 BP Pool")
    st.markdown("- Submit 1 BP per match before BP is locked\n- Custom BP: clear with admin on WhatsApp first\n- ✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt** | 🚫 Dismissed → **0 pts**")
    st.markdown("---")
    st.subheader("🔮 Score Prediction (SP)")
    st.markdown("- Predict final score + wickets + winner after 6 overs\n- 🎯 Closest score → **+4 pts** | ⚡ Exact score → **+6 pts**\n- 🏆 Correct winner → **+2 pts** (everyone who picks correctly)\n- 🎳 Correct wickets → **+1 pt** (SP score winner only)\n- Tie → both get full points")
    st.markdown("---")
    st.subheader("🔥 Streak Bonus")
    st.markdown("- 1 win = **0 streak bonus**\n- 2 wins in a row → **+1 pt**\n- 3 in a row → **+2 pts** | 4 → **+3 pts** | keeps going!\n- Resets when you don't win SP")
    st.markdown("---")
    st.subheader("🌟 Season Predictions")
    st.markdown("- 🧡 Orange Cap → **10 pts** | 💜 Purple Cap → **10 pts**\n- 🌟 Emerging → **15 pts**\n- 🏏 Top 4 → **5 pts each** (+2 if correct position)\n- Rest → just for fun, 0 pts")
    st.markdown("---")
    st.subheader("👁️ Visibility Rules")
    st.markdown("- BPs hidden until admin locks BP\n- SPs hidden until admin locks SP\n- Season predictions hidden until admin reveals them")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
def page_admin():
    st.title("⚙️ Admin Panel")
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Matches", "👥 Players", "📝 Submit on Behalf", "🌟 Season", "🏏 Draft MVP"])

    with tab1:
        mn = st.text_input("Match Name (e.g. RCB VS SRH)")
        md = st.date_input("Date")
        if st.button("Add Match"):
            if mn.strip():
                # Auto assign match number
                existing_matches = get_matches()
                next_num = max((m.get("match_number") or 0 for m in existing_matches), default=0) + 1
                db().table("matches").insert({
                    "match_name": caps(mn), "match_date": str(md),
                    "status": "open", "bp_locked": False, "sp_locked": False,
                    "match_number": next_num
                }).execute()
                st.success(f"✅ Match #{next_num} added!")
                st.rerun()
        st.markdown("---")
        matches = get_matches()
        for m in matches:
            bp = "🔒" if m.get("bp_locked") else "🟢"
            sp = "🔒" if m.get("sp_locked") else "🟢"
            st.write(f"**#{m.get('match_number','?')}** 🏏 **{m['match_name']}** | BP:{bp} SP:{sp} | {m.get('status','open')}")

    with tab2:
        nu=st.text_input("Username"); np=st.text_input("Password")
        nr=st.selectbox("Role", ALL_ROLES)
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
            st.write(f"{'Admin' if u['role']=='admin' else 'Player'} — **{u.get('team_name') or u['display_name']}** | `{u['username']}`")

    with tab3:
        st.subheader("Submit on Behalf of a Player")
        users   = get_playing_users()
        matches = get_matches()
        open_m  = get_open_matches()
        mm      = {m["match_name"]: m.get("match_number",i+1) for i,m in enumerate(matches)}
        p_names = [u.get("team_name") or u["username"] for u in users]
        sel_player = st.selectbox("Select Player", p_names, key="behalf_player")
        sel_u = next((u for u in users if (u.get("team_name") or u["username"]) == sel_player), None)

        st.markdown("#### 🎱 Submit BP on Behalf")
        bp_matches = [m for m in open_m if not m.get("bp_locked")]
        if bp_matches and sel_u:
            bp_match = st.selectbox("Match", [f"#{mm.get(m['match_name'],'?')} — {m['match_name']}" for m in bp_matches], key="behalf_bp_match")
            bp_match_name = bp_match.split(" — ",1)[1]
            ex_bp = db().table("pool_bps").select("*").eq("player",sel_u["username"]).eq("match_name",bp_match_name).execute().data or []
            if ex_bp:
                st.warning(f"⚠️ {sel_player} already submitted a BP!")
            else:
                bp_text = st.text_area("BP Prediction Text", key="behalf_bp_text")
                if st.button("🚀 Submit BP on Behalf", key="behalf_bp_submit"):
                    if bp_text.strip():
                        db().table("pool_bps").insert({
                            "match_name": bp_match_name, "player": sel_u["username"],
                            "bp_type": "custom", "template_key": "admin_behalf", "fill_in": "",
                            "prediction_text": bp_text.strip(), "status": "pending",
                            "points_awarded": 0, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }).execute()
                        st.success(f"✅ BP submitted for {sel_player}!")
                    else:
                        st.error("Enter BP text!")
        else:
            st.info("No open matches for BP.")

        st.markdown("---")
        st.markdown("#### 🔮 Submit SP on Behalf")
        sp_matches = [m for m in open_m if not m.get("sp_locked")]
        if sp_matches and sel_u:
            sp_match = st.selectbox("Match", [f"#{mm.get(m['match_name'],'?')} — {m['match_name']}" for m in sp_matches], key="behalf_sp_match")
            sp_match_name = sp_match.split(" — ",1)[1]
            ex_sp = db().table("predictions").select("*").eq("player",sel_u["username"]).eq("match_name",sp_match_name).execute().data or []
            if ex_sp:
                st.warning(f"⚠️ {sel_player} already submitted an SP!")
            else:
                c1,c2 = st.columns(2)
                with c1:
                    behalf_score = st.number_input("Predicted Score", min_value=0, max_value=400, step=1, key="behalf_score")
                    behalf_wkt   = st.number_input("Predicted Wickets", min_value=0, max_value=10, step=1, key="behalf_wkt")
                with c2:
                    teams = get_match_teams(sp_match_name)
                    behalf_winner = st.selectbox("Predicted Winner", teams, key="behalf_winner") if teams else caps(st.text_input("Predicted Winner", key="behalf_winner_text"))
                if st.button("🚀 Submit SP on Behalf", key="behalf_sp_submit"):
                    if behalf_winner:
                        db().table("predictions").insert({
                            "match_name": sp_match_name, "player": sel_u["username"],
                            "predicted_score": behalf_score, "predicted_wickets": behalf_wkt,
                            "predicted_winner": caps(behalf_winner), "points_awarded": 0,
                            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }).execute()
                        st.success(f"✅ SP submitted for {sel_player}!")
                    else:
                        st.error("Enter winner!")
        else:
            st.info("No open matches for SP.")

    with tab4:
        st.subheader("🌟 Season Predictions")
        locked = is_season_locked()
        if locked:
            st.success("✅ Season predictions are LOCKED — everyone can see them.")
            if st.button("🔓 Unlock Season Predictions"):
                try:
                    db().table("app_settings").update({"value":"false"}).eq("key","season_locked").execute()
                except:
                    db().table("app_settings").insert({"key":"season_locked","value":"false"}).execute()
                st.rerun()
        else:
            st.warning("🔒 Season predictions are hidden from everyone.")
            if st.button("🔒 Lock & Reveal Season Predictions"):
                try:
                    existing = db().table("app_settings").select("*").eq("key","season_locked").execute().data or []
                    if existing:
                        db().table("app_settings").update({"value":"true"}).eq("key","season_locked").execute()
                    else:
                        db().table("app_settings").insert({"key":"season_locked","value":"true"}).execute()
                except:
                    pass
                st.success("✅ Locked and revealed!")
                st.rerun()
        st.markdown("---")
        st.subheader("Award Season Points")
        actuals = {}
        for field in [f for f in SEASON_FIELDS if not f["fun"]]:
            actuals[field["key"]] = st.text_input(f"Actual — {field['label']}", key=f"act_{field['key']}")
        if st.button("Award Season Points"):
            for sp in (db().table("season_predictions").select("*").execute().data or []):
                pts = 0
                if caps(actuals.get("orange_cap","")) and sp.get("orange_cap","").upper()==caps(actuals["orange_cap"]): pts+=10
                if caps(actuals.get("purple_cap","")) and sp.get("purple_cap","").upper()==caps(actuals["purple_cap"]): pts+=10
                if caps(actuals.get("emerging_player","")) and sp.get("emerging_player","").upper()==caps(actuals["emerging_player"]): pts+=15
                actual_top4 = [caps(actuals.get(f"top{i}","")) for i in range(1,5)]
                for i in range(1,5):
                    pred_val = sp.get(f"top{i}","").upper()
                    if pred_val and pred_val in actual_top4:
                        pts+=5
                        if pred_val==actual_top4[i-1]: pts+=2
                db().table("season_predictions").update({"points_awarded":pts}).eq("id",sp["id"]).execute()
            st.success("✅ Season points awarded!")

    with tab5:
        st.subheader("🏏 Update Draft MVP Points")
        st.caption("Paste player names and their current ESPN MVP points. Updates the draft leaderboard.")

        all_player_pts = db().table("draft_player_points").select("*").execute().data or []
        pts_map = {row["player_name"]: float(row.get("mvp_points") or 0) for row in all_player_pts}

        # Show all players across all teams with editable points
        st.markdown("**Update points for players who played today:**")

        # Collect all unique players
        all_players = []
        for team_data in DRAFT_TEAMS.values():
            for p in team_data["players"]:
                if p not in all_players:
                    all_players.append(p)
        all_players.sort()

        st.markdown("---")
        search = st.text_input("🔍 Search player", placeholder="Type player name...")
        filtered_players = [p for p in all_players if search.lower() in p.lower()] if search else all_players

        updates = {}
        cols = st.columns(2)
        for i, player in enumerate(filtered_players):
            with cols[i % 2]:
                current = pts_map.get(player, 0)
                new_val = st.number_input(player, min_value=0.0, max_value=1000.0,
                                          value=float(current), step=0.5, key=f"mvp_{player}")
                updates[player] = new_val

        if st.button("💾 Save MVP Points", use_container_width=True):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            for player, pts in updates.items():
                existing = db().table("draft_player_points").select("*").eq("player_name", player).execute().data or []
                if existing:
                    db().table("draft_player_points").update({"mvp_points": pts, "updated_at": now_str}).eq("player_name", player).execute()
                else:
                    db().table("draft_player_points").insert({"player_name": player, "mvp_points": pts, "updated_at": now_str}).execute()
            st.success("✅ MVP points updated!")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    for k,v in [("user",None),("page","🏆 Leaderboard"),
                ("sel_key",None),("sel_tmpl",None),("sel_note",None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.user is None:
        st.title("🏏 LFxCT")
        st.markdown("---")
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
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

    c1,c2,c3 = st.columns([2,4,1])
    with c1:
        team_display = get_team(user["username"]) if role != "guest" else "Guest"
        st.markdown("**🏏 LFxCT**")
        st.caption(team_display)
    with c2:
        sel = st.selectbox("nav", pages,
            index=pages.index(st.session_state.page),
            label_visibility="collapsed", key="top_nav")
        if sel != st.session_state.page:
            st.session_state.page = sel
            st.rerun()
    with c3:
        if st.button("🔙" if role=="guest" else "🚪", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")

    page = st.session_state.page
    if   page == "🏆 Leaderboard":       page_leaderboard()
    elif page == "📊 Overall Stats":      page_overall_stats()
    elif page == "👤 Player Stats":       page_player_stats()
    elif page == "🏅 Hall of Fame":       page_hall_of_fame()
    elif page == "🏏 Draft League":       page_draft_league()
    elif page == "🎱 BP Pool":            page_bp_pool()
    elif page == "🔮 Score Prediction":   page_submit_sp()
    elif page == "🏆 Enter Results":      page_enter_results()
    elif page == "📝 BP Results":         page_bp_results()
    elif page == "🔒 Lock / Cancel":      page_lock_cancel()
    elif page == "⚙️ Admin Panel":        page_admin()
    elif page == "📋 Match Details":      page_match_details()
    elif page == "📖 How to Score":       page_how_to_score()
    elif page == "🌟 Season Predictions": page_season_predictions()


if __name__ == "__main__":
    main()
