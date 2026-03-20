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

/* Make top nav buttons look clean */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 8px;
    font-size: 13px;
    padding: 4px 8px;
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

def streak_bonus_for(n):
    return max(0, n - 1)

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


# ─── Top Navigation ────────────────────────────────────────────────────────────
def top_nav(pages):
    """Renders a top navigation bar with buttons — mobile friendly"""
    if "page" not in st.session_state:
        st.session_state.page = pages[0]

    # Show user info + logout at top
    user = st.session_state.user
    role = user["role"]
    role_label = ROLE_LABELS.get(role, role)

    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.markdown(f"**👋 {user['display_name']}** · *{role_label}*")
    with col_r:
        if role == "guest":
            if st.button("🔙 Login", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = pages[0]
                st.rerun()
        else:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = pages[0]
                st.rerun()

    st.markdown("---")

    # Navigation buttons — 4 per row
    chunk_size = 4
    chunks = [pages[i:i+chunk_size] for i in range(0, len(pages), chunk_size)]
    for chunk in chunks:
        cols = st.columns(len(chunk))
        for col, p in zip(cols, chunk):
            is_active = st.session_state.page == p
            label = f"**{p}**" if is_active else p
            if col.button(label, key=f"nav_{p}", use_container_width=True):
                st.session_state.page = p
                st.rerun()

    st.markdown("---")
    return st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

def page_leaderboard():
    st.title("🏆 LFxCT Leaderboard")
    users = get_playing_users()
    if not users:
        st.info("No players yet.")
        return
    rows = []
    for u in users:
        uname  = u["username"]
        sp     = get_player_sp_points(uname)
        bp     = get_player_bp_points(uname)
        streak = get_player_streak_points(uname)
        exact  = get_player_exact_count(uname)
        total  = round(sp + bp + streak, 2)
        cur_streak = get_current_streak(uname)
        rows.append({
            "Rank":       "",
            "Player":     u["display_name"],
            "SP Pts":     sp,
            "BP Pts":     bp,
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
        s = pd.DataFrame("", index=df.index, columns=df.columns)
        s["Total"]  = "background-color: #1e2a1e; color: #00ff88; font-weight: bold"
        s["Player"] = "background-color: #1a1a2e; font-weight: bold"
        return s
    st.dataframe(df.style.apply(style_df, axis=None), use_container_width=True, hide_index=True)


def page_submit_bp():
    st.title("📝 Submit Bold Prediction")
    matches = [m for m in (db().table("matches").select("*").execute().data or []) if not m.get("bp_locked")]
    if not matches:
        st.warning("⏳ No open matches for BP submission.")
        return
    match = st.selectbox("Select Match", [m["match_name"] for m in matches])
    existing = db().table("bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        bp = existing[0]
        st.warning("✅ Already submitted!")
        st.info(f"**{bp['prediction']}** | Status: {bp['status']} | Pts: {bp.get('points_awarded',0)}")
        return
    prediction = st.text_area("Your Bold Prediction", placeholder="e.g. Kohli to score 50+ runs")
    if st.button("🚀 Submit BP"):
        if not prediction.strip():
            st.error("Enter a prediction!")
        else:
            db().table("bps").insert({
                "match_name": match, "player": st.session_state.user["username"],
                "prediction": prediction.strip(), "status": "pending",
                "points_awarded": 0, "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ BP submitted! Waiting for ♕ Queen's approval.")


def page_submit_sp():
    st.title("🔮 Score Prediction")
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
        pw_raw = st.text_input("Predicted Winner (team name)")
        pw     = caps(pw_raw)
        if pw: st.caption(f"Team: **{pw}**")
    st.caption(f"Your prediction: **{predicted_score} - {str(predicted_wickets).zfill(2)}**")
    if st.button("🚀 Submit"):
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


def page_bp_approvals():
    st.title("✅ BP Approvals")
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
        label = f"**🏏 {bp['match_name']}** — **{get_user_display(bp_player) if role in ['bp_manager','admin'] else '[Hidden]'}**: {bp['prediction']}"
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
    role     = st.session_state.user["role"]
    username = st.session_state.user["username"]
    approved = db().table("bps").select("*").eq("status","approved").execute().data or []
    if not approved:
        st.success("No BPs to rate!")
        return
    if role == "knight":
        to_rate = [(bp, BISHOP_COLS[get_user_role(bp["player"])])
                   for bp in approved
                   if get_user_role(bp["player"]) in BISHOP_ROLES
                   and BISHOP_COLS.get(get_user_role(bp["player"]))
                   and bp.get(BISHOP_COLS.get(get_user_role(bp["player"]))) is None]
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
    matches = db().table("matches").select("*").execute().data or []
    if not matches:
        st.info("No matches.")
        return
    user = st.session_state.user
    now  = datetime.now().strftime("%Y-%m-%d %H:%M")
    for m in matches:
        with st.expander(f"🏏 {m['match_name']}"):
            col1, col2 = st.columns(2)
            with col1:
                if m.get("bp_locked"):
                    st.success(f"🔒 BP: **{get_user_display(m.get('bp_locked_by',''))}** @ {m.get('bp_locked_at','')}")
                else:
                    if st.button("🔒 Lock BP", key=f"lockbp_{m['id']}"):
                        db().table("matches").update({"bp_locked":True,"bp_locked_by":user["username"],"bp_locked_at":now}).eq("id",m["id"]).execute()
                        db().table("locklog").insert({"match_name":m["match_name"],"lock_type":"BP","locked_by":user["username"],"locked_at":now}).execute()
                        st.rerun()
            with col2:
                if m.get("sp_locked"):
                    st.success(f"🔒 SP: **{get_user_display(m.get('sp_locked_by',''))}** @ {m.get('sp_locked_at','')}")
                else:
                    if st.button("🔒 Lock SP", key=f"locksp_{m['id']}"):
                        db().table("matches").update({"sp_locked":True,"sp_locked_by":user["username"],"sp_locked_at":now}).eq("id",m["id"]).execute()
                        db().table("locklog").insert({"match_name":m["match_name"],"lock_type":"SP","locked_by":user["username"],"locked_at":now}).execute()
                        st.rerun()


def page_enter_results():
    st.title("🏆 Enter Match Results")
    matches = db().table("matches").select("*").execute().data or []
    pending = [m for m in matches if m.get("sp_locked") and m.get("status") != "done"]
    if not pending:
        st.info("No matches waiting for results.")
        return
    match_sel      = st.selectbox("Select Match", [m["match_name"] for m in pending])
    actual_score   = st.number_input("Actual Score (runs)", min_value=0, max_value=500, step=1)
    actual_wickets = st.number_input("Actual Wickets", min_value=0, max_value=10, step=1)
    aw_raw         = st.text_input("Actual Winner (team name)")
    aw             = caps(aw_raw)
    if aw: st.caption(f"Team: **{aw}**")
    if st.button("✅ Submit Result & Award Points"):
        if not aw:
            st.error("Enter winner!")
        else:
            award_sp_points(match_sel, actual_score, actual_wickets, aw)
            st.success(f"✅ Results submitted for {match_sel}!")
            st.rerun()


def page_bp_results():
    st.title("📝 Mark BP Results")
    scored = db().table("bps").select("*").eq("status","scored").execute().data or []
    if not scored:
        st.info("No scored BPs waiting.")
        return
    for bp in scored:
        display = get_user_display(bp["player"])
        st.markdown(f"**{display}** — {bp['match_name']}: {bp['prediction']} | Avg: **{bp.get('avg_score','?')}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Correct (+{bp.get('avg_score','?')})", key=f"c_{bp['id']}"):
                db().table("bps").update({"result":"correct","points_awarded":bp.get("avg_score",0),"status":"done"}).eq("id",bp["id"]).execute()
                st.rerun()
        with col2:
            if st.button("❌ Wrong (-1)", key=f"w_{bp['id']}"):
                db().table("bps").update({"result":"wrong","points_awarded":-1,"status":"done"}).eq("id",bp["id"]).execute()
                st.rerun()
        st.markdown("---")


def page_match_details():
    st.title("📋 Match Details")
    matches = db().table("matches").select("*").execute().data or []
    if not matches:
        st.info("No matches yet.")
        return
    match_options = [f"Match {i+1} — {m['match_name']}" for i, m in enumerate(matches)]
    idx = st.selectbox("Select Match", range(len(matches)), format_func=lambda i: match_options[i])
    m   = matches[idx]
    st.markdown(f"### 🏏 Match {idx+1} — {m['match_name']} | {m.get('match_date','')}")
    col1, col2, col3 = st.columns(3)
    col1.metric("BP", "🔒" if m.get("bp_locked") else "🟢 Open")
    col2.metric("SP", "🔒" if m.get("sp_locked") else "🟢 Open")
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
    if bps:
        st.dataframe(pd.DataFrame([{
            "": "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "⏳",
            "Player": get_user_display(b["player"]), "Prediction": b["prediction"],
            "P1": b.get("panel1_score","-"), "P2": b.get("panel2_score","-"), "P3": b.get("panel3_score","-"),
            "Avg": b.get("avg_score","-"), "Pts": b.get("points_awarded",0)
        } for b in bps]), use_container_width=True, hide_index=True)
    else:
        st.info("No BPs.")
    st.markdown("---")
    st.subheader("🔮 Score Predictions")
    preds = sorted(db().table("predictions").select("*").eq("match_name", m["match_name"]).execute().data or [],
                   key=lambda x: x.get("points_awarded",0), reverse=True)
    if preds:
        st.dataframe(pd.DataFrame([{
            "": "🥇" if i==0 and (p.get("points_awarded") or 0)>=4 else "",
            "Player": get_user_display(p["player"]),
            "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)}",
            "Winner Pick": p.get("predicted_winner","-"),
            "Actual": f"{m.get('actual_score')} - {str(m.get('actual_wickets',0)).zfill(2)}" if m.get("actual_score") else "-",
            "⚡": "⚡" if m.get("actual_score") and int(p.get("predicted_score") or 0)==m.get("actual_score") else "",
            "Pts": p.get("points_awarded",0)
        } for i, p in enumerate(preds)]), use_container_width=True, hide_index=True)
    else:
        st.info("No SPs.")


def page_stats():
    st.title("📊 Player Stats")
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
            rows.append({
                "Player":      u["display_name"],
                "Total":       get_player_total_points(uname),
                "SP Pts":      get_player_sp_points(uname),
                "BP Pts":      get_player_bp_points(uname),
                "Streak Pts":  get_player_streak_points(uname),
                "⚡ Exacts":   get_player_exact_count(uname),
                "BPs ✅":      len([b for b in bps if b.get("result")=="correct"]),
                "BPs ❌":      len([b for b in bps if b.get("result")=="wrong"]),
                "SP Played":   len([p for p in preds if p.get("actual_score") is not None]),
                "🔥 Streak":   get_current_streak(uname)
            })
        rows.sort(key=lambda x: x["Total"], reverse=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        u = next((u for u in users if u["display_name"] == selected), None)
        if not u: return
        uname = u["username"]
        total = get_player_total_points(uname)
        sp_pts = get_player_sp_points(uname)
        bp_pts = get_player_bp_points(uname)
        streak_pts = get_player_streak_points(uname)
        cur_streak = get_current_streak(uname)
        exact_count = get_player_exact_count(uname)
        st.markdown(f"## {u['display_name']}")
        col1,col2,col3,col4,col5 = st.columns(5)
        col1.metric("🏆 Total", total)
        col2.metric("🔮 SP", sp_pts)
        col3.metric("📝 BP", bp_pts)
        col4.metric("🔥 Streak", streak_pts)
        col5.metric("⚡ Exacts", exact_count)
        if cur_streak > 1:
            st.success(f"🔥 Active streak: **{cur_streak} wins in a row!** (+{streak_bonus_for(cur_streak+1)} next win)")
        st.markdown("---")
        if total > 0:
            st.subheader("📊 Points Breakdown")
            st.bar_chart(pd.DataFrame({"Category":["SP","BP","Streak"],"Points":[sp_pts,bp_pts,streak_pts]}).set_index("Category"))
        matches = db().table("matches").select("*").execute().data or []
        match_map = {m["match_name"]: i+1 for i, m in enumerate(matches)}
        st.markdown("---")
        st.subheader("🔮 Score Prediction History")
        preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
        if preds:
            st.dataframe(pd.DataFrame([{
                "Match #": f"#{match_map.get(p['match_name'],'?')}",
                "Match": p["match_name"],
                "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)}",
                "Winner": p.get("predicted_winner","-"),
                "Actual": f"{p.get('actual_score')} - {str(p.get('actual_wickets',0)).zfill(2)}" if p.get("actual_score") else "Pending",
                "⚡": "⚡ Exact!" if p.get("actual_score") and int(p.get("predicted_score") or 0)==int(p.get("actual_score") or -1) else "",
                "Pts": p.get("points_awarded",0)
            } for p in preds]), use_container_width=True, hide_index=True)
        else:
            st.info("No predictions yet.")
        st.markdown("---")
        st.subheader("📝 Bold Prediction History")
        bps = db().table("bps").select("*").eq("player", uname).execute().data or []
        if bps:
            st.dataframe(pd.DataFrame([{
                "Match #": f"#{match_map.get(b['match_name'],'?')}",
                "Match": b["match_name"],
                "Prediction": b["prediction"],
                "Avg Panel": b.get("avg_score","Pending"),
                "Result": "✅" if b.get("result")=="correct" else "❌" if b.get("result")=="wrong" else "⏳",
                "Pts": b.get("points_awarded",0)
            } for b in bps]), use_container_width=True, hide_index=True)
        else:
            st.info("No BPs yet.")
        st.markdown("---")
        st.subheader("🔥 Streak Bonus History")
        streaks = db().table("streaks").select("*").eq("player", uname).execute().data or []
        if streaks:
            st.dataframe(pd.DataFrame([{
                "Match #": f"#{match_map.get(s['match_name'],'?')}",
                "Match": s["match_name"],
                "Streak": f"{s.get('streak_count')} in a row",
                "Bonus": s.get("bonus_points",0)
            } for s in streaks]), use_container_width=True, hide_index=True)
        else:
            st.info("No streak bonuses yet.")


def page_season_predictions():
    st.title("🌟 Season Predictions")
    user     = st.session_state.user
    username = user["username"]
    if user["role"] == "guest":
        results = db().table("season_predictions").select("*").execute().data or []
        if results:
            st.dataframe(pd.DataFrame([{
                "Player": get_user_display(sp["player"]),
                "🧡 OC": sp.get("orange_cap"), "💜 PC": sp.get("purple_cap"),
                "🌟 EP": sp.get("emerging_player"),
                "Top4": f"{sp.get('top1')}→{sp.get('top2')}→{sp.get('top3')}→{sp.get('top4')}",
                "Pts": sp.get("points_awarded",0)
            } for sp in results]), use_container_width=True, hide_index=True)
        else:
            st.info("No season predictions yet.")
        return
    existing = db().table("season_predictions").select("*").eq("player", username).execute().data or []
    if existing:
        sp = existing[0]
        st.success("✅ Submitted!")
        st.write(f"🧡 **{sp.get('orange_cap')}** | 💜 **{sp.get('purple_cap')}** | 🌟 **{sp.get('emerging_player')}**")
        st.write(f"Top 4: {sp.get('top1')} → {sp.get('top2')} → {sp.get('top3')} → {sp.get('top4')}")
        st.write(f"**Points: {sp.get('points_awarded','Pending')}**")
        return
    st.markdown("**Points:** OC=20 | PC=20 | Emerging=15 | Top4 team=6 (+4 if position correct)")
    oc=st.text_input("🧡 Orange Cap"); pc=st.text_input("💜 Purple Cap"); em=st.text_input("🌟 Emerging Player")
    t1=st.text_input("1st"); t2=st.text_input("2nd"); t3=st.text_input("3rd"); t4=st.text_input("4th")
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
    st.markdown("""
### 📝 Bold Predictions (BP)
- 1 BP per match before BP is locked
- ♕ Queen approves or rejects
- ♗ Bishops rate **0–3** (blind — name hidden)
- ✅ Correct → **+avg panel score**
- ❌ Wrong → **-1 pt**

---
### 🔮 Score Predictions (SP)
- Predict score + wickets + winner after 6 overs
- 🏆 Closest → **+4 pts**
- ⚡ Exact → **+6 pts**
- ✅ Correct winner → **+2 pts**
- 🎯 Correct wickets (SP winner only) → **+1 pt**
- Tie → both get points

---
### 🔥 Streak Points
- 2 wins in a row → **+1**
- 3 in a row → **+2**
- 4 in a row → **+3**
- 5 in a row → **+4**
- ...keeps going forever!

---
### 🌟 Season Predictions
- Orange Cap → **20 pts**
- Purple Cap → **20 pts**
- Emerging Player → **15 pts**
- Top 4 team → **6 pts each** (+4 if position correct)

---
### ♟ Roles
| | Name | Job |
|---|---|---|
| ♔ | King | Admin — not a player |
| ♕ | Queen | Approves Pawn BPs, enters results (rotates) |
| ♞ | Knight | Approves Queen+Bishop BPs blindly (rotates) |
| ♗ | Bishop x3 | Rates Pawn BPs blindly 0–3 (fixed) |
| ♟ | Pawn | Plays — submits BPs and SPs |
""")


def page_admin():
    st.title("⚙️ King's Panel")
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Matches", "👥 Players", "📝 BP Results", "🌟 Season"])
    with tab1:
        mn = st.text_input("Match Name"); md = st.date_input("Date")
        if st.button("Add Match"):
            if mn.strip():
                db().table("matches").insert({"match_name":caps(mn),"match_date":str(md),"status":"open","bp_locked":False,"sp_locked":False}).execute()
                st.success("✅ Added!"); st.rerun()
        st.markdown("---")
        for i, m in enumerate(db().table("matches").select("*").execute().data or []):
            st.write(f"**#{i+1}** 🏏 **{m['match_name']}** | BP:{'🔒' if m.get('bp_locked') else '🟢'} SP:{'🔒' if m.get('sp_locked') else '🟢'} | {m.get('status','open')}")
    with tab2:
        rlm = {r: ROLE_LABELS.get(r,r) for r in ALL_ROLES}
        nu=st.text_input("Username"); np=st.text_input("Password")
        nr=st.selectbox("Role", ALL_ROLES, format_func=lambda x: rlm[x]); nd=st.text_input("Display Name")
        if st.button("Add Player"):
            if nu.strip() and np.strip() and nd.strip():
                db().table("users").insert({"username":nu.strip(),"password":np.strip(),"role":nr,"display_name":nd.strip()}).execute()
                st.success(f"✅ {nd} added as {rlm[nr]}!"); st.rerun()
        st.markdown("---")
        st.subheader("🔁 Rotate ♕ Queen & ♞ Knight")
        users = get_all_users()
        names = [u["display_name"] for u in users if u["role"] != "admin"]
        nq = st.selectbox("New ♕ Queen", names, key="nq")
        nk = st.selectbox("New ♞ Knight", names, key="nk")
        if st.button("Update Roles"):
            for u in users:
                if u["role"] in ["bp_manager","knight"]:
                    db().table("users").update({"role":"player"}).eq("id",u["id"]).execute()
            db().table("users").update({"role":"bp_manager"}).eq("id", next(u for u in users if u["display_name"]==nq)["id"]).execute()
            db().table("users").update({"role":"knight"}).eq("id", next(u for u in users if u["display_name"]==nk)["id"]).execute()
            st.success(f"✅ ♕ {nq} | ♞ {nk}"); st.rerun()
        st.markdown("---")
        for u in db().table("users").select("*").execute().data or []:
            st.write(f"{ROLE_LABELS.get(u['role'],'?')} **{u['display_name']}** | `{u['username']}`")
    with tab3:
        page_bp_results()
    with tab4:
        oc=st.text_input("🧡 OC"); pc=st.text_input("💜 PC"); em=st.text_input("🌟 Emerging")
        t1=st.text_input("1st"); t2=st.text_input("2nd"); t3=st.text_input("3rd"); t4=st.text_input("4th")
        if st.button("Award Season Points"):
            a={"oc":caps(oc),"pc":caps(pc),"em":caps(em),"t1":caps(t1),"t2":caps(t2),"t3":caps(t3),"t4":caps(t4)}
            for sp in db().table("season_predictions").select("*").execute().data or []:
                pts=0
                if sp.get("orange_cap","").upper()==a["oc"]: pts+=20
                if sp.get("purple_cap","").upper()==a["pc"]: pts+=20
                if sp.get("emerging_player","").upper()==a["em"]: pts+=15
                at4=[a["t1"],a["t2"],a["t3"],a["t4"]]
                pt4=[sp.get(f"top{i+1}","").upper() for i in range(4)]
                for j,t in enumerate(pt4):
                    if t in at4:
                        pts+=6
                        if t==at4[j]: pts+=4
                db().table("season_predictions").update({"points_awarded":pts}).eq("id",sp["id"]).execute()
            st.success("✅ Season points awarded!")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(page_title="LFxCT", page_icon="🏏", layout="wide")

    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "🏆 Leaderboard"

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

    user = st.session_state.user
    role = user["role"]

    # ── Build page list ──
    if role == "guest":
        pages = ["🏆 Leaderboard","📊 Stats","📋 Match Details","📖 How to Score","🌟 Season Predictions"]
    else:
        pages = ["🏆 Leaderboard","📊 Stats","📋 Match Details","📖 How to Score","🌟 Season Predictions","📝 Submit BP","🔮 Score Prediction"]
        if role in ["bp_manager","knight","admin"]: pages.append("✅ Approve BPs")
        if role in BISHOP_ROLES+["knight","admin"]: pages.append("⭐ Rate BPs")
        if role in BISHOP_ROLES+["bp_manager","admin"]: pages.append("🔒 Lock BP/SP")
        if role in ["bp_manager","admin"]:
            pages.append("🏆 Enter Results")
            pages.append("📝 BP Results")
        if role == "admin": pages.append("⚙️ King's Panel")

    # Ensure current page is valid
    if st.session_state.page not in pages:
        st.session_state.page = pages[0]

    # ── Top nav (mobile friendly) ──
    page = top_nav(pages)

    # ── Routing ──
    if   page == "🏆 Leaderboard":       page_leaderboard()
    elif page == "📝 Submit BP":          page_submit_bp()
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
