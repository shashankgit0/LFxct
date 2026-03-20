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
div.stButton > button {
    width: 100%;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─── Role definitions ──────────────────────────────────────────────────────────
ROLE_LABELS = {
    "admin":      "♔ King",
    "bp_manager": "♕ Queen",
    "knight":     "♞ Knight",
    "bishop1":    "♗ Bishop",
    "bishop2":    "♗ Bishop",
    "bishop3":    "♗ Bishop",
    "player":     "♟ Pawn",
}
BISHOP_ROLES = ["bishop1", "bishop2", "bishop3"]
BISHOP_COLS  = {"bishop1": "panel1_score", "bishop2": "panel2_score", "bishop3": "panel3_score"}
ADMIN_ROLES  = ["admin"]
ALL_ROLES    = ["player", "bishop1", "bishop2", "bishop3", "knight", "bp_manager", "admin"]

# ─── BP Templates ──────────────────────────────────────────────────────────────
BP_TEMPLATES = [
    ("bat_30",  "🏏 {name} to score 30+ runs"),
    ("bat_50",  "🏏 {name} to score 50+ runs"),
    ("bat_duck","🏏 {name} to score a duck (0 runs)"),
    ("bat_top", "🏏 {name} to be the highest scorer"),
    ("bat_sr",  "🏏 {name} to have 200+ strike rate"),
    ("bat_out", "🏏 {name} to get out in <14 balls"),
    ("bat_b1",  "🏏 {name} to hit a boundary on ball 1"),
    ("bat_six1","🏏 {name} to hit a six on ball 1"),
    ("bowl_2w", "🎳 {name} to take 2+ wickets"),
    ("bowl_3w", "🎳 {name} to take 3+ wickets"),
    ("bowl_top","🎳 {name} to take the most wickets"),
    ("team_6s", "🔥 {name} team to hit 11+ sixes"),
    ("team_4s", "🔥 {name} team to hit 19+ fours"),
    ("team_180","🔥 {name} team to score 180+ runs"),
    ("team_200","🔥 {name} team to score 200+ runs"),
]

# ─── Helpers ───────────────────────────────────────────────────────────────────
def get_all_users():
    return db().table("users").select("*").execute().data or []

def get_playing_users():
    return [u for u in get_all_users() if u["role"] not in ADMIN_ROLES]

def get_user_display(username):
    for u in get_all_users():
        if u["username"] == username:
            return u["display_name"]
    return username

def get_user_role(username):
    for u in get_all_users():
        if u["username"] == username:
            return u["role"]
    return "player"

def caps(text):
    return text.strip().upper() if text else ""

def get_player_sp_points(username):
    total = 0
    for p in db().table("predictions").select("points_awarded").eq("player", username).execute().data or []:
        try: total += float(p.get("points_awarded") or 0)
        except: pass
    return round(total, 2)

def get_player_bp_points(username):
    total = 0
    for b in db().table("bps").select("points_awarded").eq("player", username).execute().data or []:
        try: total += float(b.get("points_awarded") or 0)
        except: pass
    return round(total, 2)

def get_player_template_bp_points(username):
    total = 0
    for b in db().table("template_bps").select("points_awarded").eq("player", username).execute().data or []:
        try: total += float(b.get("points_awarded") or 0)
        except: pass
    return round(total, 2)

def get_player_streak_points(username):
    total = 0
    for s in db().table("streaks").select("bonus_points").eq("player", username).execute().data or []:
        try: total += float(s.get("bonus_points") or 0)
        except: pass
    return round(total, 2)

def get_player_exact_count(username):
    count = 0
    for p in db().table("predictions").select("*").eq("player", username).execute().data or []:
        if p.get("actual_score") is not None:
            if int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1):
                count += 1
    return count

def get_player_season_points(username):
    total = 0
    for s in db().table("season_predictions").select("points_awarded").eq("player", username).execute().data or []:
        try: total += float(s.get("points_awarded") or 0)
        except: pass
    return round(total, 2)

def get_player_total_points(username):
    return round(
        get_player_sp_points(username) +
        get_player_bp_points(username) +
        get_player_template_bp_points(username) +
        get_player_streak_points(username) +
        get_player_season_points(username), 2)

def get_current_streak(username):
    preds = db().table("predictions").select("*").eq("player", username).execute().data or []
    done  = sorted([p for p in preds if p.get("actual_score") is not None],
                   key=lambda x: x.get("submitted_at",""), reverse=True)
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

def streak_bonus_for(streak_count):
    if streak_count < 2: return 0
    return streak_count - 1

def login(username, password):
    res = db().table("users").select("*").eq("username", username).eq("password", password).execute()
    return res.data[0] if res.data else None

def submit_panel_score(bp, col_name, score):
    update_data = {col_name: score}
    latest = db().table("bps").select("*").eq("id", bp["id"]).execute().data[0]
    p1 = latest.get("panel1_score") if col_name != "panel1_score" else score
    p2 = latest.get("panel2_score") if col_name != "panel2_score" else score
    p3 = latest.get("panel3_score") if col_name != "panel3_score" else score
    scores = [x for x in [p1, p2, p3] if x is not None]
    if len(scores) == 3:
        avg = round(sum(float(s) for s in scores) / 3, 2)
        update_data["avg_score"] = avg
        update_data["status"]    = "scored"
    db().table("bps").update(update_data).eq("id", bp["id"]).execute()

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
        pts       = 0
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


# ══════════════════════════════════════════════════════════════════════════════
# NEW TEMPLATE BP PAGE
# ══════════════════════════════════════════════════════════════════════════════

def page_template_bp():
    st.title("🎯 Bold Prediction (New)")
    st.markdown("##### Pick a template, fill in the blank, submit!")
    st.markdown("✅ Correct → **+3 pts** | ❌ Wrong → **-1 pt**")
    st.markdown("---")

    matches = [m for m in (db().table("matches").select("*").execute().data or []) if not m.get("bp_locked")]
    if not matches:
        st.warning("⏳ No open matches right now.")
        return

    match = st.selectbox("Select Match", [m["match_name"] for m in matches])

    # Check if already submitted
    existing = db().table("template_bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        b = existing[0]
        icon = "✅" if b.get("result") == "correct" else "❌" if b.get("result") == "wrong" else "⏳"
        st.warning("✅ You already submitted a BP for this match!")
        st.info(f"{icon} **{b['prediction_text']}** | Status: {b.get('result','pending')} | Pts: {b.get('points_awarded',0)}")
        return

    st.markdown("### Choose your prediction:")
    st.markdown("")

    # Template picker
    template_options = {f"{t[1].replace('{name}', '______')}": t[0] for t in BP_TEMPLATES}
    selected_label = st.radio(
        "Select a template:",
        list(template_options.keys()),
        label_visibility="collapsed"
    )
    selected_key = template_options[selected_label]
    selected_template = next(t[1] for t in BP_TEMPLATES if t[0] == selected_key)

    st.markdown("---")
    st.markdown("### Fill in the blank:")

    # Show the template with input
    if "{name}" in selected_template:
        col1, col2 = st.columns([3, 2])
        with col1:
            fill_in = st.text_input(
                "Player / Team name:",
                placeholder="e.g. Kohli, SRH, Bumrah..."
            )
        with col2:
            if fill_in:
                preview = selected_template.replace("{name}", f"**{fill_in.strip()}**")
                st.markdown(f"📋 Preview:")
                st.markdown(f"*{preview}*")

    st.markdown("---")
    if st.button("🚀 Submit BP", use_container_width=True):
        if not fill_in or not fill_in.strip():
            st.error("Please fill in the blank!")
        else:
            final_text = selected_template.replace("{name}", fill_in.strip())
            db().table("template_bps").insert({
                "match_name": match,
                "player": st.session_state.user["username"],
                "template_key": selected_key,
                "fill_in": fill_in.strip(),
                "prediction_text": final_text,
                "status": "pending",
                "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success(f"✅ Submitted: **{final_text}**")
            st.balloons()


def page_template_bp_results():
    st.title("📝 Mark Template BP Results")
    st.markdown("---")
    pending = db().table("template_bps").select("*").eq("status","pending").execute().data or []
    if not pending:
        st.info("No template BPs waiting for results.")
        return

    # Group by match
    matches = list(set(b["match_name"] for b in pending))
    selected_match = st.selectbox("Filter by Match", ["All"] + matches)
    filtered = pending if selected_match == "All" else [b for b in pending if b["match_name"] == selected_match]

    for b in filtered:
        display = get_user_display(b["player"])
        st.markdown(f"**{display}** — {b['match_name']}")
        st.markdown(f"🎯 *{b['prediction_text']}*")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Correct (+3 pts)", key=f"tc_{b['id']}"):
                db().table("template_bps").update({
                    "result": "correct", "points_awarded": 3, "status": "done"
                }).eq("id", b["id"]).execute()
                st.rerun()
        with col2:
            if st.button(f"❌ Wrong (-1 pt)", key=f"tw_{b['id']}"):
                db().table("template_bps").update({
                    "result": "wrong", "points_awarded": -1, "status": "done"
                }).eq("id", b["id"]).execute()
                st.rerun()
        st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# EXISTING PAGES
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
        sp     = get_player_sp_points(uname)
        bp     = get_player_bp_points(uname)
        tbp    = get_player_template_bp_points(uname)
        streak = get_player_streak_points(uname)
        exact  = get_player_exact_count(uname)
        total  = round(sp + bp + tbp + streak, 2)
        cur_streak = get_current_streak(uname)
        rows.append({
            "Rank":       "",
            "Player":     u["display_name"],
            "SP Pts":     sp,
            "BP Pts":     round(bp + tbp, 2),
            "Streak Pts": streak,
            "⚡ Exact":   f"{exact}x" if exact > 0 else "-",
            "🔥 Streak":  f"{cur_streak} 🔥" if cur_streak > 1 else str(cur_streak),
            "Total":      total
        })
    rows.sort(key=lambda x: x["Total"], reverse=True)
    medals = ["🥇","🥈","🥉"]
    for i, r in enumerate(rows):
        r["Rank"] = medals[i] if i < 3 else str(i+1)
    df = pd.DataFrame(rows)
    def style_df(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        styles["Total"]  = "background-color: #1e2a1e; color: #00ff88; font-weight: bold"
        styles["Player"] = "background-color: #1a1a2e; font-weight: bold"
        return styles
    st.dataframe(df.style.apply(style_df, axis=None), use_container_width=True, hide_index=True)


def page_submit_sp():
    st.title("🔮 Score Prediction")
    st.markdown("---")
    matches = [m for m in (db().table("matches").select("*").execute().data or []) if not m.get("sp_locked")]
    if not matches:
        st.warning("⏳ No open matches for Score Prediction.")
        return
    match = st.selectbox("Select Match", [m["match_name"] for m in matches])
    existing = db().table("predictions").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        p = existing[0]
        st.warning("✅ Already submitted!")
        st.info(f"**{p['predicted_score']} runs - {str(p.get('predicted_wickets',0)).zfill(2)} wkts** | Winner: {p['predicted_winner']} | Pts: {p.get('points_awarded',0)}")
        return
    col1, col2 = st.columns(2)
    with col1:
        predicted_score   = st.number_input("Predicted Score (runs)", min_value=0, max_value=400, step=1)
        predicted_wickets = st.number_input("Predicted Wickets (0-10)", min_value=0, max_value=10, step=1)
    with col2:
        predicted_winner_raw = st.text_input("Predicted Winner")
        predicted_winner     = caps(predicted_winner_raw)
        if predicted_winner:
            st.caption(f"Team: **{predicted_winner}**")
    st.caption(f"Your prediction: **{predicted_score} runs - {str(predicted_wickets).zfill(2)} wkts**")
    if st.button("🚀 Submit"):
        if not predicted_winner:
            st.error("Enter the winner!")
        else:
            db().table("predictions").insert({
                "match_name": match, "player": st.session_state.user["username"],
                "predicted_score": predicted_score, "predicted_wickets": predicted_wickets,
                "predicted_winner": predicted_winner, "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ Prediction submitted!")


def page_bp_approvals():
    st.title("✅ BP Approvals")
    st.markdown("---")
    user     = st.session_state.user
    role     = user["role"]
    username = user["username"]
    pending  = db().table("bps").select("*").eq("status","pending").execute().data or []
    if not pending:
        st.success("🎉 No pending BPs!")
        return
    shown = 0
    for bp in pending:
        bp_player      = bp["player"]
        bp_player_role = get_user_role(bp_player)
        if role == "bp_manager":
            if bp_player == username: continue
            if bp_player_role in BISHOP_ROLES + ["knight","bp_manager","admin"]: continue
        if role == "knight":
            if bp_player_role not in ["bp_manager"] + BISHOP_ROLES: continue
        shown += 1
        if role in ["bp_manager","admin"]:
            label = f"**🏏 {bp['match_name']}** — **{get_user_display(bp_player)}**: {bp['prediction']}"
        else:
            label = f"**🏏 {bp['match_name']}** — **[Hidden]**: {bp['prediction']}"
        st.markdown(label)
        st.caption(f"Submitted: {bp.get('submitted_at','')}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{bp['id']}"):
                db().table("bps").update({"status":"approved"}).eq("id",bp["id"]).execute()
                st.rerun()
        with col2:
            if st.button("❌ Reject", key=f"reject_{bp['id']}"):
                db().table("bps").update({"status":"rejected"}).eq("id",bp["id"]).execute()
                st.rerun()
        st.markdown("---")
    if shown == 0:
        st.success("🎉 Nothing to approve!")


def page_panel_scoring():
    st.title("⭐ Rate BPs")
    st.markdown("---")
    role     = st.session_state.user["role"]
    username = st.session_state.user["username"]
    approved = db().table("bps").select("*").eq("status","approved").execute().data or []
    if not approved:
        st.success("No BPs to rate!")
        return
    if role == "knight":
        to_rate = []
        for bp in approved:
            bpr  = get_user_role(bp["player"])
            slot = BISHOP_COLS.get(bpr)
            if bpr in BISHOP_ROLES and slot and bp.get(slot) is None:
                to_rate.append((bp, slot))
        if not to_rate:
            st.success("Nothing to rate!")
            return
        for bp, slot in to_rate:
            st.markdown(f"**🏏 {bp['match_name']}** — **[Hidden]**: {bp['prediction']}")
            score = st.radio("Rating:", [0,1,2,3], horizontal=True, key=f"knight_{bp['id']}")
            st.caption("0=Too easy | 1=Moderate | 2=Risky | 3=Very risky")
            if st.button("Submit Rating", key=f"knight_rate_{bp['id']}"):
                submit_panel_score(bp, slot, score)
                st.success("Rating submitted!")
                st.rerun()
            st.markdown("---")
        return
    if role in BISHOP_ROLES:
        col_name = BISHOP_COLS[role]
        unrated  = [bp for bp in approved
                    if bp["player"] != username
                    and get_user_role(bp["player"]) not in BISHOP_ROLES
                    and bp.get(col_name) is None]
        if not unrated:
            st.success("You've rated all BPs!")
            return
        for bp in unrated:
            st.markdown(f"**🏏 {bp['match_name']}** — **[Hidden]**: {bp['prediction']}")
            score = st.radio("Rating:", [0,1,2,3], horizontal=True, key=f"score_{bp['id']}")
            st.caption("0=Too easy | 1=Moderate | 2=Risky | 3=Very risky")
            if st.button("Submit Rating", key=f"rate_{bp['id']}"):
                submit_panel_score(bp, col_name, score)
                st.success("Rating submitted!")
                st.rerun()
            st.markdown("---")
        return
    if role == "admin":
        unrated = [bp for bp in approved if bp.get("panel1_score") is None]
        if not unrated:
            st.success("All BPs rated!")
            return
        for bp in unrated:
            st.markdown(f"**🏏 {bp['match_name']}** — **{get_user_display(bp['player'])}**: {bp['prediction']}")
            score = st.radio("Rating (P1):", [0,1,2,3], horizontal=True, key=f"admin_{bp['id']}")
            if st.button("Submit", key=f"admin_rate_{bp['id']}"):
                submit_panel_score(bp, "panel1_score", score)
                st.rerun()
            st.markdown("---")


def page_lock_match():
    st.title("🔒 Lock BP / SP")
    st.markdown("---")
    matches = db().table("matches").select("*").execute().data or []
    if not matches:
        st.info("No matches.")
        return
    user = st.session_state.user
    now  = datetime.now().strftime("%Y-%m-%d %H:%M")
    for m in matches:
        with st.expander(f"🏏 {m['match_name']} — {m.get('match_date','')}"):
            col1, col2 = st.columns(2)
            with col1:
                if m.get("bp_locked"):
                    st.success(f"🔒 BP locked by **{get_user_display(m.get('bp_locked_by',''))}** at {m.get('bp_locked_at','')}")
                else:
                    if st.button("🔒 Lock BP", key=f"lockbp_{m['id']}"):
                        db().table("matches").update({"bp_locked":True,"bp_locked_by":user["username"],"bp_locked_at":now}).eq("id",m["id"]).execute()
                        db().table("locklog").insert({"match_name":m["match_name"],"lock_type":"BP","locked_by":user["username"],"locked_at":now}).execute()
                        st.rerun()
            with col2:
                if m.get("sp_locked"):
                    st.success(f"🔒 SP locked by **{get_user_display(m.get('sp_locked_by',''))}** at {m.get('sp_locked_at','')}")
                else:
                    if st.button("🔒 Lock SP", key=f"locksp_{m['id']}"):
                        db().table("matches").update({"sp_locked":True,"sp_locked_by":user["username"],"sp_locked_at":now}).eq("id",m["id"]).execute()
                        db().table("locklog").insert({"match_name":m["match_name"],"lock_type":"SP","locked_by":user["username"],"locked_at":now}).execute()
                        st.rerun()


def page_enter_results():
    st.title("🏆 Enter Match Results")
    st.markdown("---")
    matches = db().table("matches").select("*").execute().data or []
    pending = [m for m in matches if m.get("sp_locked") and m.get("status") != "done"]
    if not pending:
        st.info("No matches waiting for results.")
        return
    match_sel         = st.selectbox("Select Match", [m["match_name"] for m in pending])
    actual_score      = st.number_input("Actual Score (runs)", min_value=0, max_value=500, step=1)
    actual_wickets    = st.number_input("Actual Wickets", min_value=0, max_value=10, step=1)
    actual_winner_raw = st.text_input("Actual Winner")
    actual_winner     = caps(actual_winner_raw)
    if actual_winner:
        st.caption(f"Team: **{actual_winner}**")
    if st.button("✅ Submit Result & Award Points"):
        if not actual_winner:
            st.error("Enter winner!")
        else:
            award_sp_points(match_sel, actual_score, actual_wickets, actual_winner)
            st.success(f"✅ Results submitted for {match_sel}!")
            st.rerun()


def page_bp_results():
    st.title("📝 Mark BP Results")
    st.markdown("---")
    scored = db().table("bps").select("*").eq("status","scored").execute().data or []
    if not scored:
        st.info("No scored BPs waiting for results.")
        return
    for bp in scored:
        display = get_user_display(bp["player"])
        st.markdown(f"**{display}** — {bp['match_name']}: {bp['prediction']} | Avg: **{bp.get('avg_score','?')}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Correct (+{bp.get('avg_score','?')} pts)", key=f"c_{bp['id']}"):
                db().table("bps").update({"result":"correct","points_awarded":bp.get("avg_score",0),"status":"done"}).eq("id",bp["id"]).execute()
                st.rerun()
        with col2:
            if st.button(f"❌ Wrong (-1 pt)", key=f"w_{bp['id']}"):
                db().table("bps").update({"result":"wrong","points_awarded":-1,"status":"done"}).eq("id",bp["id"]).execute()
                st.rerun()
        st.markdown("---")


def page_match_details():
    st.title("📋 Match Details")
    st.markdown("---")
    matches = db().table("matches").select("*").execute().data or []
    if not matches:
        st.info("No matches yet.")
        return
    match_options = [f"Match {i+1} — {m['match_name']}" for i, m in enumerate(matches)]
    selected_idx  = st.selectbox("Select Match", range(len(matches)), format_func=lambda i: match_options[i])
    m = matches[selected_idx]
    st.markdown(f"### 🏏 Match {selected_idx+1} — {m['match_name']} | {m.get('match_date','')}")
    col1, col2, col3 = st.columns(3)
    col1.metric("BP",     "🔒 Locked" if m.get("bp_locked") else "🟢 Open")
    col2.metric("SP",     "🔒 Locked" if m.get("sp_locked") else "🟢 Open")
    col3.metric("Status", m.get("status","open").upper())
    if m.get("actual_score"):
        st.success(f"**Result:** {m.get('actual_winner')} won | {m.get('actual_score')} runs - {str(m.get('actual_wickets',0)).zfill(2)} wkts")
    if m.get("bp_locked"):
        st.caption(f"🔒 BP locked by {get_user_display(m.get('bp_locked_by',''))} at {m.get('bp_locked_at','')}")
    if m.get("sp_locked"):
        st.caption(f"🔒 SP locked by {get_user_display(m.get('sp_locked_by',''))} at {m.get('sp_locked_at','')}")
    st.markdown("---")
    st.subheader("📝 Bold Predictions")
    bps = db().table("bps").select("*").eq("match_name", m["match_name"]).execute().data or []
    tbps = db().table("template_bps").select("*").eq("match_name", m["match_name"]).execute().data or []
    all_bps = []
    for bp in bps:
        icon = "✅" if bp.get("result")=="correct" else "❌" if bp.get("result")=="wrong" else "⏳"
        all_bps.append({"": icon, "Player": get_user_display(bp["player"]),
            "Prediction": bp["prediction"], "Type": "Custom",
            "Pts": bp.get("points_awarded",0)})
    for bp in tbps:
        icon = "✅" if bp.get("result")=="correct" else "❌" if bp.get("result")=="wrong" else "⏳"
        all_bps.append({"": icon, "Player": get_user_display(bp["player"]),
            "Prediction": bp["prediction_text"], "Type": "Template",
            "Pts": bp.get("points_awarded",0)})
    if all_bps:
        st.dataframe(pd.DataFrame(all_bps), use_container_width=True, hide_index=True)
    else:
        st.info("No BPs for this match.")
    st.markdown("---")
    st.subheader("🔮 Score Predictions")
    preds = db().table("predictions").select("*").eq("match_name", m["match_name"]).execute().data or []
    if preds:
        preds_sorted = sorted(preds, key=lambda x: x.get("points_awarded",0), reverse=True)
        sp_rows = []
        for i, p in enumerate(preds_sorted):
            rank  = "🥇" if i==0 and (p.get("points_awarded") or 0) >= 4 else ""
            exact = "⚡" if m.get("actual_score") and int(p.get("predicted_score") or 0) == m.get("actual_score") else ""
            sp_rows.append({
                "": rank, "Player": get_user_display(p["player"]),
                "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)}",
                "Winner Pick": p.get("predicted_winner","-"),
                "Actual": f"{m.get('actual_score')} - {str(m.get('actual_wickets',0)).zfill(2)}" if m.get("actual_score") else "-",
                "⚡": exact, "Pts": p.get("points_awarded",0)
            })
        st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No score predictions for this match.")


def page_stats():
    st.title("📊 Player Stats")
    st.markdown("---")
    users = get_playing_users()
    if not users:
        st.info("No players yet.")
        return
    selected = st.selectbox("Select Player", ["— Overall —"] + [u["display_name"] for u in users])
    if selected == "— Overall —":
        rows = []
        for u in users:
            uname = u["username"]
            bps   = db().table("bps").select("*").eq("player", uname).execute().data or []
            preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
            tbps  = db().table("template_bps").select("*").eq("player", uname).execute().data or []
            rows.append({
                "Player":      u["display_name"],
                "Total":       get_player_total_points(uname),
                "SP Pts":      get_player_sp_points(uname),
                "BP Pts":      round(get_player_bp_points(uname) + get_player_template_bp_points(uname), 2),
                "Streak Pts":  get_player_streak_points(uname),
                "⚡ Exacts":   get_player_exact_count(uname),
                "BPs ✅":      len([b for b in bps if b.get("result")=="correct"]) + len([b for b in tbps if b.get("result")=="correct"]),
                "BPs ❌":      len([b for b in bps if b.get("result")=="wrong"]) + len([b for b in tbps if b.get("result")=="wrong"]),
                "SP Played":   len([p for p in preds if p.get("actual_score") is not None]),
                "🔥 Streak":   get_current_streak(uname)
            })
        rows.sort(key=lambda x: x["Total"], reverse=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        u = next((u for u in users if u["display_name"] == selected), None)
        if not u: return
        uname  = u["username"]
        total  = get_player_total_points(uname)
        sp_pts = get_player_sp_points(uname)
        bp_pts = round(get_player_bp_points(uname) + get_player_template_bp_points(uname), 2)
        streak_pts = get_player_streak_points(uname)
        cur_streak = get_current_streak(uname)
        exact_count = get_player_exact_count(uname)
        col1,col2,col3,col4,col5 = st.columns(5)
        col1.metric("🏆 Total",    total)
        col2.metric("🔮 SP Pts",   sp_pts)
        col3.metric("📝 BP Pts",   bp_pts)
        col4.metric("🔥 Streak",   streak_pts)
        col5.metric("⚡ Exacts",   exact_count)
        if cur_streak > 1:
            st.success(f"🔥 Active streak: **{cur_streak} wins in a row!** (+{streak_bonus_for(cur_streak+1)} next win)")
        st.markdown("---")
        if total > 0:
            st.subheader("📊 Points Breakdown")
            chart_data = pd.DataFrame({
                "Category": ["SP Points","BP Points","Streak Points"],
                "Points":   [sp_pts, bp_pts, streak_pts]
            })
            st.bar_chart(chart_data.set_index("Category"))
        st.markdown("---")
        matches = db().table("matches").select("*").execute().data or []
        match_map = {m["match_name"]: i+1 for i, m in enumerate(matches)}
        st.subheader("🔮 Score Predictions")
        preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
        if preds:
            st.dataframe(pd.DataFrame([{
                "Match #": f"#{match_map.get(p['match_name'],'?')}",
                "Match": p["match_name"],
                "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)}",
                "Winner": p.get("predicted_winner","-"),
                "Actual": f"{p.get('actual_score')} - {str(p.get('actual_wickets',0)).zfill(2)}" if p.get("actual_score") else "Pending",
                "⚡": "Yes" if p.get("actual_score") and int(p.get("predicted_score") or 0) == int(p.get("actual_score") or -1) else "",
                "Pts": p.get("points_awarded",0)
            } for p in preds]), use_container_width=True, hide_index=True)
        else:
            st.info("No predictions yet.")
        st.markdown("---")
        st.subheader("📝 Bold Predictions")
        bps  = db().table("bps").select("*").eq("player", uname).execute().data or []
        tbps = db().table("template_bps").select("*").eq("player", uname).execute().data or []
        all_bps = []
        for b in bps:
            icon = "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "⏳"
            all_bps.append({"Match #": f"#{match_map.get(b['match_name'],'?')}", "Match": b["match_name"], "Prediction": b["prediction"], "Type": "Custom", "Result": icon, "Pts": b.get("points_awarded",0)})
        for b in tbps:
            icon = "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "⏳"
            all_bps.append({"Match #": f"#{match_map.get(b['match_name'],'?')}", "Match": b["match_name"], "Prediction": b["prediction_text"], "Type": "Template", "Result": icon, "Pts": b.get("points_awarded",0)})
        if all_bps:
            st.dataframe(pd.DataFrame(all_bps), use_container_width=True, hide_index=True)
        else:
            st.info("No BPs yet.")


def page_season_predictions():
    st.title("🌟 Season Predictions")
    st.markdown("---")
    user     = st.session_state.user
    username = user["username"]
    if user["role"] == "guest":
        results = db().table("season_predictions").select("*").execute().data or []
        if results:
            st.dataframe(pd.DataFrame([{
                "Player": get_user_display(sp["player"]),
                "🧡 Orange Cap": sp.get("orange_cap"),
                "💜 Purple Cap": sp.get("purple_cap"),
                "🌟 Emerging":   sp.get("emerging_player"),
                "Top 4": f"{sp.get('top1')}→{sp.get('top2')}→{sp.get('top3')}→{sp.get('top4')}",
                "Pts": sp.get("points_awarded",0)
            } for sp in results]), use_container_width=True, hide_index=True)
        else:
            st.info("No season predictions yet.")
        return
    existing = db().table("season_predictions").select("*").eq("player", username).execute().data or []
    if existing:
        sp = existing[0]
        st.success("✅ Your season predictions submitted!")
        st.write(f"🧡 Orange Cap: **{sp.get('orange_cap')}**")
        st.write(f"💜 Purple Cap: **{sp.get('purple_cap')}**")
        st.write(f"🌟 Emerging Player: **{sp.get('emerging_player')}**")
        st.write(f"🏏 Top 4: {sp.get('top1')} → {sp.get('top2')} → {sp.get('top3')} → {sp.get('top4')}")
        st.write(f"**Points: {sp.get('points_awarded','Pending')}**")
        return
    st.markdown("**Points:** Orange Cap=20 | Purple Cap=20 | Emerging=15 | Top4 team=6 (+4 if position correct)")
    oc = st.text_input("🧡 Orange Cap")
    pc = st.text_input("💜 Purple Cap")
    em = st.text_input("🌟 Emerging Player")
    t1 = st.text_input("1st Place")
    t2 = st.text_input("2nd Place")
    t3 = st.text_input("3rd Place")
    t4 = st.text_input("4th Place")
    if st.button("🚀 Submit"):
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
    st.subheader("🎯 Template Bold Predictions (NEW)")
    st.markdown("""
- Pick a template from the pool before BP is locked
- Fill in the player/team name
- ✅ Correct → **+3 pts**
- ❌ Wrong → **-1 pt**
""")
    st.markdown("---")
    st.subheader("📝 Custom Bold Predictions (BP)")
    st.markdown("""
- Submit **1 BP per match** before BP is locked
- ♕ Queen **approves or rejects** your BP
- ♗ Bishops rate it **0–3** for riskiness — **blind**
- BP value = **average of 3 Bishop scores**
- ✅ BP Correct → **+panel avg points**
- ❌ BP Wrong → **-1 point**
""")
    st.markdown("---")
    st.subheader("🔮 Score Predictions (SP)")
    st.markdown("""
- After 6 overs, predict **final score + wickets + match winner**
- 🏆 Closest score → **+4 pts**
- ⚡ Exact score → **+6 pts**
- ✅ Correct winner → **+2 pts**
- 🎯 Correct wickets (SP winner only) → **+1 bonus pt**
- Tie on closest score → **both get points**
""")
    st.markdown("---")
    st.subheader("🔥 Streak Points")
    st.markdown("""
- Win 2 SP in a row → **+1 bonus**
- Win 3 in a row → **+2 bonus**
- Keeps going forever! (+n-1 for n consecutive wins)
- Streak resets if you don't win
""")
    st.markdown("---")
    st.subheader("🌟 Season Predictions")
    st.markdown("""
- 🧡 Orange Cap → **20 pts** | 💜 Purple Cap → **20 pts**
- 🌟 Emerging Player → **15 pts**
- 🏏 Top 4 team correct → **6 pts** (+4 if position correct)
""")


def page_admin():
    st.title("⚙️ King's Panel")
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Matches", "👥 Players", "📝 BP Results", "🎯 Template BP Results", "🌟 Season"])

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
        role_labels_map = {r: ROLE_LABELS.get(r, r) for r in ALL_ROLES}
        nu = st.text_input("Username")
        np = st.text_input("Password")
        nr = st.selectbox("Role", ALL_ROLES, format_func=lambda x: role_labels_map[x])
        nd = st.text_input("Display Name")
        if st.button("Add Player"):
            if nu.strip() and np.strip() and nd.strip():
                db().table("users").insert({
                    "username": nu.strip(), "password": np.strip(),
                    "role": nr, "display_name": nd.strip()
                }).execute()
                st.success(f"✅ {nd} added!")
                st.rerun()
        st.markdown("---")
        st.subheader("🔁 Rotate ♕ Queen & ♞ Knight")
        users = get_all_users()
        names = [u["display_name"] for u in users if u["role"] != "admin"]
        new_queen  = st.selectbox("New ♕ Queen", names, key="nq")
        new_knight = st.selectbox("New ♞ Knight", names, key="nk")
        if st.button("Update Roles"):
            for u in users:
                if u["role"] in ["bp_manager","knight"]:
                    db().table("users").update({"role":"player"}).eq("id",u["id"]).execute()
            nq = next(u for u in users if u["display_name"] == new_queen)
            nk = next(u for u in users if u["display_name"] == new_knight)
            db().table("users").update({"role":"bp_manager"}).eq("id",nq["id"]).execute()
            db().table("users").update({"role":"knight"}).eq("id",nk["id"]).execute()
            st.success(f"✅ ♕ {new_queen} | ♞ {new_knight}")
            st.rerun()
        st.markdown("---")
        for u in (db().table("users").select("*").execute().data or []):
            st.write(f"{ROLE_LABELS.get(u['role'],'?')} **{u['display_name']}** | `{u['username']}`")

    with tab3:
        page_bp_results()

    with tab4:
        page_template_bp_results()

    with tab5:
        oc = st.text_input("🧡 Orange Cap")
        pc = st.text_input("💜 Purple Cap")
        em = st.text_input("🌟 Emerging")
        t1 = st.text_input("1st"); t2 = st.text_input("2nd")
        t3 = st.text_input("3rd"); t4 = st.text_input("4th")
        if st.button("Award Season Points"):
            actuals = {"oc":caps(oc),"pc":caps(pc),"em":caps(em),
                       "t1":caps(t1),"t2":caps(t2),"t3":caps(t3),"t4":caps(t4)}
            for sp in (db().table("season_predictions").select("*").execute().data or []):
                pts = 0
                if sp.get("orange_cap","").upper()     == actuals["oc"]: pts += 20
                if sp.get("purple_cap","").upper()     == actuals["pc"]: pts += 20
                if sp.get("emerging_player","").upper()== actuals["em"]: pts += 15
                actual_top4 = [actuals["t1"],actuals["t2"],actuals["t3"],actuals["t4"]]
                pred_top4   = [sp.get("top1","").upper(),sp.get("top2","").upper(),
                               sp.get("top3","").upper(),sp.get("top4","").upper()]
                for j, team in enumerate(pred_top4):
                    if team in actual_top4:
                        pts += 6
                        if team == actual_top4[j]: pts += 4
                db().table("season_predictions").update({"points_awarded":pts}).eq("id",sp["id"]).execute()
            st.success("✅ Done!")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(page_title="LFxCT", page_icon="🏏", layout="wide")

    if "user" not in st.session_state:
        st.session_state.user = None

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
                    st.rerun()
                else:
                    st.error("Wrong username or password!")
            st.markdown("---")
            if st.button("👁️ Continue as Guest", use_container_width=True):
                st.session_state.user = {"username":"guest","display_name":"Guest","role":"guest"}
                st.rerun()
        return

    user = st.session_state.user
    role = user["role"]

    with st.sidebar:
        role_label = ROLE_LABELS.get(role, role)
        st.markdown(f"### 👋 {user['display_name']}")
        st.markdown(f"*{role_label}*")
        st.markdown("---")

        if role == "guest":
            pages = ["🏆 Leaderboard","📊 Stats","📋 Match Details","📖 How to Score","🌟 Season Predictions"]
        else:
            pages = ["🏆 Leaderboard","📊 Stats","📋 Match Details","📖 How to Score",
                     "🌟 Season Predictions","🎯 Bold Prediction","🔮 Score Prediction"]
            if role in ["bp_manager","knight","admin"]:
                pages.append("✅ Approve BPs")
            if role in BISHOP_ROLES + ["knight","admin"]:
                pages.append("⭐ Rate BPs")
            if role in BISHOP_ROLES + ["bp_manager","admin"]:
                pages.append("🔒 Lock BP/SP")
            if role in ["bp_manager","admin"]:
                pages.append("🏆 Enter Results")
                pages.append("📝 BP Results")
            if role == "admin":
                pages.append("⚙️ King's Panel")

        page = st.radio("Navigation", pages)
        st.markdown("---")

        if role == "guest":
            if st.button("🔙 Back to Login", use_container_width=True):
                st.session_state.user = None
                st.rerun()
        else:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.rerun()

    if   page == "🏆 Leaderboard":       page_leaderboard()
    elif page == "🎯 Bold Prediction":    page_template_bp()
    elif page == "🔮 Score Prediction":   page_submit_sp()
    elif page == "✅ Approve BPs":        page_bp_approvals()
    elif page == "⭐ Rate BPs":           page_panel_scoring()
    elif page == "🔒 Lock BP/SP":         page_lock_match()
    elif page == "🏆 Enter Results":      page_enter_results()
    elif page == "📝 BP Results":         page_bp_results()
    elif page == "⚙️ King's Panel":       page_admin()
    elif page == "📊 Stats":              page_stats()
    elif page == "📋 Match Details":      page_match_details()
    elif page == "📖 How to Score":       page_how_to_score()
    elif page == "🌟 Season Predictions": page_season_predictions()


if __name__ == "__main__":
    main()
