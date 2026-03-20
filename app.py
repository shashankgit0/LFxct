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
</style>
""", unsafe_allow_html=True)

# ─── Role definitions ──────────────────────────────────────────────────────────
ROLE_DISPLAY = {
    "admin": "♔ King",
    "bp_manager": "♕ Queen",
    "knight": "♞ Knight",
    "bishop1": "♗ Bishop",
    "bishop2": "♗ Bishop",
    "bishop3": "♗ Bishop",
    "player": "♟ Pawn",
}

BISHOP_ROLES = ["bishop1", "bishop2", "bishop3"]
BISHOP_COLS = {"bishop1": "panel1_score", "bishop2": "panel2_score", "bishop3": "panel3_score"}

# ─── Helpers ───────────────────────────────────────────────────────────────────
def get_all_users():
    return db().table("users").select("*").execute().data or []

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
    done = sorted([p for p in preds if p.get("actual_score") is not None],
                  key=lambda x: x.get("submitted_at",""), reverse=True)
    streak = 0
    for p in done:
        all_preds = db().table("predictions").select("*").eq("match_name", p["match_name"]).execute().data or []
        valid = [x for x in all_preds if x.get("actual_score") is not None]
        if not valid: break
        min_diff = min(abs(int(x.get("predicted_score") or 0) - int(x.get("actual_score") or 0)) for x in valid)
        my_diff = abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0))
        if my_diff == min_diff: streak += 1
        else: break
    return streak

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
        update_data["status"] = "scored"
    db().table("bps").update(update_data).eq("id", bp["id"]).execute()

def award_sp_points(match_sel, actual_score, actual_wickets, actual_winner):
    db().table("matches").update({
        "status": "done",
        "actual_score": actual_score,
        "actual_wickets": actual_wickets,
        "actual_winner": actual_winner.upper()
    }).eq("match_name", match_sel).execute()

    preds = db().table("predictions").select("*").eq("match_name", match_sel).execute().data or []
    if not preds:
        return

    for p in preds:
        p["diff"] = abs(int(p.get("predicted_score") or 0) - actual_score)
    min_diff = min(p["diff"] for p in preds)
    winners = [p for p in preds if p["diff"] == min_diff]

    for p in preds:
        pts = 0
        is_winner = p["diff"] == min_diff
        is_exact = int(p.get("predicted_score") or 0) == actual_score
        correct_winner = str(p.get("predicted_winner","")).upper() == actual_winner.upper()
        correct_wickets = int(p.get("predicted_wickets") or -1) == actual_wickets

        if is_exact:
            pts += 6
        elif is_winner:
            pts += 4
        if correct_winner:
            pts += 2
        if is_winner and correct_wickets:
            pts += 1

        db().table("predictions").update({
            "actual_score": actual_score,
            "actual_wickets": actual_wickets,
            "actual_winner": actual_winner.upper(),
            "points_awarded": pts
        }).eq("id", p["id"]).execute()

    # Streak bonuses
    for w in winners:
        uname = w["player"]
        streak = get_current_streak(uname)
        bonus = 3 if streak >= 4 else 2 if streak == 3 else 1 if streak == 2 else 0
        if bonus > 0:
            db().table("streaks").insert({
                "player": uname,
                "match_name": match_sel,
                "streak_count": streak,
                "bonus_points": bonus
            }).execute()


# ─── Pages ─────────────────────────────────────────────────────────────────────

def page_leaderboard():
    st.title("🏆 LFxCT Leaderboard")
    st.markdown("---")
    users = get_all_users()
    if not users:
        st.info("No players yet.")
        return

    rows = []
    for u in users:
        uname = u["username"]
        sp = get_player_sp_points(uname)
        bp = get_player_bp_points(uname)
        streak = get_player_streak_points(uname)
        total = round(sp + bp + streak, 2)
        rows.append({
            "Rank": "",
            "Player": u["display_name"],
            "SP Pts": sp,
            "BP Pts": bp,
            "Streak Pts": streak,
            "Total": total
        })

    rows.sort(key=lambda x: x["Total"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(rows):
        row["Rank"] = medals[i] if i < 3 else str(i + 1)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_submit_bp():
    st.title("📝 Submit Bold Prediction")
    st.markdown("---")
    matches = [m for m in (db().table("matches").select("*").execute().data or []) if not m.get("bp_locked")]
    if not matches:
        st.warning("⏳ No open matches for BP submission.")
        return

    match = st.selectbox("Select Match", [m["match_name"] for m in matches])
    existing = db().table("bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        bp = existing[0]
        st.warning("✅ Already submitted!")
        st.info(f"**{bp['prediction']}** | Status: {bp['status']} | Pts: {bp.get('points_awarded', 0)}")
        return

    prediction = st.text_area("Your Bold Prediction", placeholder="e.g. Kohli to score 50+ runs")
    if st.button("🚀 Submit BP"):
        if not prediction.strip():
            st.error("Enter a prediction!")
        else:
            db().table("bps").insert({
                "match_name": match,
                "player": st.session_state.user["username"],
                "prediction": prediction.strip(),
                "status": "pending",
                "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ BP submitted! Waiting for Queen's approval.")


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
        st.info(f"**{p['predicted_score']} runs - {str(p.get('predicted_wickets', 0)).zfill(2)} wkts** | Winner: {p['predicted_winner']} | Pts: {p.get('points_awarded', 0)}")
        return

    col1, col2 = st.columns(2)
    with col1:
        predicted_score = st.number_input("Predicted Score (runs)", min_value=0, max_value=400, step=1)
        predicted_wickets = st.number_input("Predicted Wickets (0-10)", min_value=0, max_value=10, step=1)
    with col2:
        predicted_winner = st.text_input("Predicted Winner (team name)").upper()

    st.caption(f"Your prediction: **{predicted_score} - {str(predicted_wickets).zfill(2)}**")

    if st.button("🚀 Submit"):
        if not predicted_winner.strip():
            st.error("Enter the winner!")
        else:
            db().table("predictions").insert({
                "match_name": match,
                "player": st.session_state.user["username"],
                "predicted_score": predicted_score,
                "predicted_wickets": predicted_wickets,
                "predicted_winner": predicted_winner.strip().upper(),
                "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ Prediction submitted!")


def page_bp_approvals():
    st.title("✅ BP Approvals")
    st.markdown("---")
    user = st.session_state.user
    role = user["role"]
    username = user["username"]

    pending = db().table("bps").select("*").eq("status", "pending").execute().data or []
    if not pending:
        st.success("🎉 No pending BPs!")
        return

    shown = 0
    for bp in pending:
        bp_player = bp["player"]
        bp_player_role = get_user_role(bp_player)

        # Queen approves only regular players' BPs
        if role == "bp_manager":
            if bp_player == username:
                continue
            if bp_player_role in BISHOP_ROLES + ["knight", "bp_manager"]:
                continue

        # Knight approves Queen's and Bishops' BPs
        if role == "knight":
            if bp_player_role not in ["bp_manager"] + BISHOP_ROLES:
                continue

        shown += 1
        # Queen sees player name, Knight sees it hidden
        if role == "bp_manager" or role == "admin":
            label = f"**🏏 {bp['match_name']}** — **{get_user_display(bp_player)}**: {bp['prediction']}"
        else:
            label = f"**🏏 {bp['match_name']}** — **[Hidden]**: {bp['prediction']}"

        st.markdown(label)
        st.caption(f"Submitted: {bp.get('submitted_at', '')}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{bp['id']}"):
                db().table("bps").update({"status": "approved"}).eq("id", bp["id"]).execute()
                st.rerun()
        with col2:
            if st.button("❌ Reject", key=f"reject_{bp['id']}"):
                db().table("bps").update({"status": "rejected"}).eq("id", bp["id"]).execute()
                st.rerun()
        st.markdown("---")

    if shown == 0:
        st.success("🎉 Nothing to approve!")


def page_panel_scoring():
    st.title("⭐ Rate BPs")
    st.markdown("---")
    role = st.session_state.user["role"]
    username = st.session_state.user["username"]

    approved = db().table("bps").select("*").eq("status", "approved").execute().data or []
    if not approved:
        st.success("No BPs to rate!")
        return

    # Knight rates Bishops' BPs (blind — no name shown)
    if role == "knight":
        to_rate = []
        for bp in approved:
            bp_player_role = get_user_role(bp["player"])
            if bp_player_role not in BISHOP_ROLES:
                continue
            slot = BISHOP_COLS.get(bp_player_role)
            if slot and bp.get(slot) is None:
                to_rate.append((bp, slot))

        if not to_rate:
            st.success("Nothing to rate!")
            return

        for bp, slot in to_rate:
            st.markdown(f"**🏏 {bp['match_name']}** — **[Hidden]**: {bp['prediction']}")
            score = st.radio("Rating:", [0, 1, 2, 3], horizontal=True, key=f"knight_{bp['id']}")
            st.caption("0=Too easy | 1=Moderate | 2=Risky | 3=Very risky")
            if st.button("Submit Rating", key=f"knight_rate_{bp['id']}"):
                submit_panel_score(bp, slot, score)
                st.success("Rating submitted!")
                st.rerun()
            st.markdown("---")
        return

    # Bishops rate regular players' BPs (blind — no name shown)
    if role in BISHOP_ROLES:
        col_name = BISHOP_COLS[role]
        # Bishops cannot rate their own BP or other bishops' BPs
        unrated = []
        for bp in approved:
            bp_player_role = get_user_role(bp["player"])
            if bp["player"] == username:
                continue
            if bp_player_role in BISHOP_ROLES:
                continue
            if bp.get(col_name) is not None:
                continue
            unrated.append(bp)

        if not unrated:
            st.success("You've rated all BPs!")
            return

        for bp in unrated:
            # Blind — no name shown to bishops
            st.markdown(f"**🏏 {bp['match_name']}** — **[Hidden]**: {bp['prediction']}")
            score = st.radio("Rating:", [0, 1, 2, 3], horizontal=True, key=f"score_{bp['id']}")
            st.caption("0=Too easy | 1=Moderate | 2=Risky | 3=Very risky")
            if st.button("Submit Rating", key=f"rate_{bp['id']}"):
                submit_panel_score(bp, col_name, score)
                st.success("Rating submitted!")
                st.rerun()
            st.markdown("---")
        return

    # Admin sees everything
    if role == "admin":
        unrated = [bp for bp in approved if bp.get("panel1_score") is None]
        if not unrated:
            st.success("All BPs rated!")
            return
        for bp in unrated:
            st.markdown(f"**🏏 {bp['match_name']}** — **{get_user_display(bp['player'])}**: {bp['prediction']}")
            score = st.radio("Rating (P1 slot):", [0, 1, 2, 3], horizontal=True, key=f"admin_score_{bp['id']}")
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for m in matches:
        with st.expander(f"🏏 {m['match_name']} — {m.get('match_date', '')}"):
            col1, col2 = st.columns(2)
            with col1:
                if m.get("bp_locked"):
                    st.success(f"🔒 BP locked by **{get_user_display(m.get('bp_locked_by', ''))}** at {m.get('bp_locked_at', '')}")
                else:
                    if st.button("🔒 Lock BP", key=f"lockbp_{m['id']}"):
                        db().table("matches").update({"bp_locked": True, "bp_locked_by": user["username"], "bp_locked_at": now}).eq("id", m["id"]).execute()
                        db().table("locklog").insert({"match_name": m["match_name"], "lock_type": "BP", "locked_by": user["username"], "locked_at": now}).execute()
                        st.rerun()
            with col2:
                if m.get("sp_locked"):
                    st.success(f"🔒 SP locked by **{get_user_display(m.get('sp_locked_by', ''))}** at {m.get('sp_locked_at', '')}")
                else:
                    if st.button("🔒 Lock SP", key=f"locksp_{m['id']}"):
                        db().table("matches").update({"sp_locked": True, "sp_locked_by": user["username"], "sp_locked_at": now}).eq("id", m["id"]).execute()
                        db().table("locklog").insert({"match_name": m["match_name"], "lock_type": "SP", "locked_by": user["username"], "locked_at": now}).execute()
                        st.rerun()


def page_enter_results():
    st.title("🏆 Enter Match Results")
    st.markdown("---")
    matches = db().table("matches").select("*").execute().data or []
    pending = [m for m in matches if m.get("sp_locked") and m.get("status") != "done"]
    if not pending:
        st.info("No matches waiting for results.")
        return

    match_sel = st.selectbox("Select Match", [m["match_name"] for m in pending])
    actual_score = st.number_input("Actual Score (runs)", min_value=0, max_value=500, step=1)
    actual_wickets = st.number_input("Actual Wickets", min_value=0, max_value=10, step=1)
    actual_winner = st.text_input("Actual Winner").upper()

    if st.button("✅ Submit Result & Award Points"):
        if not actual_winner.strip():
            st.error("Enter winner!")
        else:
            award_sp_points(match_sel, actual_score, actual_wickets, actual_winner)
            st.success(f"✅ Results submitted for {match_sel}!")
            st.rerun()


def page_bp_results():
    st.title("📝 Mark BP Results")
    st.markdown("---")
    scored = db().table("bps").select("*").eq("status", "scored").execute().data or []
    if not scored:
        st.info("No scored BPs waiting for results.")
        return

    for bp in scored:
        display = get_user_display(bp["player"])
        st.markdown(f"**{display}** — {bp['match_name']}: {bp['prediction']} | Avg: **{bp.get('avg_score', '?')}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Correct (+{bp.get('avg_score', '?')} pts)", key=f"c_{bp['id']}"):
                db().table("bps").update({"result": "correct", "points_awarded": bp.get("avg_score", 0), "status": "done"}).eq("id", bp["id"]).execute()
                st.rerun()
        with col2:
            if st.button(f"❌ Wrong (-1 pt)", key=f"w_{bp['id']}"):
                db().table("bps").update({"result": "wrong", "points_awarded": -1, "status": "done"}).eq("id", bp["id"]).execute()
                st.rerun()
        st.markdown("---")


def page_match_details():
    st.title("📋 Match Details")
    st.markdown("---")
    matches = db().table("matches").select("*").execute().data or []
    if not matches:
        st.info("No matches yet.")
        return

    selected = st.selectbox("Select Match", [m["match_name"] for m in matches])
    m = next((x for x in matches if x["match_name"] == selected), None)
    if not m: return

    st.markdown(f"### 🏏 {m['match_name']} — {m.get('match_date', '')}")
    col1, col2, col3 = st.columns(3)
    col1.metric("BP", "🔒 Locked" if m.get("bp_locked") else "🟢 Open")
    col2.metric("SP", "🔒 Locked" if m.get("sp_locked") else "🟢 Open")
    col3.metric("Status", m.get("status", "open").upper())

    if m.get("actual_score"):
        st.success(f"**Result:** {m.get('actual_winner')} won | {m.get('actual_score')} runs - {str(m.get('actual_wickets', 0)).zfill(2)} wkts")

    if m.get("bp_locked"):
        st.caption(f"🔒 BP locked by {get_user_display(m.get('bp_locked_by', ''))} at {m.get('bp_locked_at', '')}")
    if m.get("sp_locked"):
        st.caption(f"🔒 SP locked by {get_user_display(m.get('sp_locked_by', ''))} at {m.get('sp_locked_at', '')}")

    st.markdown("---")

    # BPs table
    st.subheader("📝 Bold Predictions")
    bps = db().table("bps").select("*").eq("match_name", selected).execute().data or []
    if bps:
        bp_rows = []
        for bp in bps:
            icon = "✅" if bp.get("result") == "correct" else "❌" if bp.get("result") == "wrong" else "⏳"
            bp_rows.append({
                "": icon,
                "Player": get_user_display(bp["player"]),
                "Prediction": bp["prediction"],
                "P1": bp.get("panel1_score", "-"),
                "P2": bp.get("panel2_score", "-"),
                "P3": bp.get("panel3_score", "-"),
                "Avg": bp.get("avg_score", "-"),
                "Pts": bp.get("points_awarded", 0)
            })
        st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No BPs for this match.")

    st.markdown("---")

    # SPs table
    st.subheader("🔮 Score Predictions")
    preds = db().table("predictions").select("*").eq("match_name", selected).execute().data or []
    if preds:
        preds_sorted = sorted(preds, key=lambda x: x.get("points_awarded", 0), reverse=True)
        sp_rows = []
        for i, p in enumerate(preds_sorted):
            rank = "🥇" if i == 0 and p.get("points_awarded", 0) > 0 else ""
            exact = "⚡ Exact!" if int(p.get("predicted_score") or 0) == (m.get("actual_score") or -1) else ""
            sp_rows.append({
                "": rank,
                "Player": get_user_display(p["player"]),
                "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets', 0)).zfill(2)}",
                "Winner Pick": p.get("predicted_winner", "-"),
                "Actual": f"{m.get('actual_score', '-')} - {str(m.get('actual_wickets', 0)).zfill(2)}" if m.get("actual_score") else "-",
                "Exact?": exact,
                "Pts": p.get("points_awarded", 0)
            })
        st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No score predictions for this match.")


def page_stats():
    st.title("📊 Player Stats")
    st.markdown("---")
    users = get_all_users()
    if not users:
        st.info("No players yet.")
        return

    selected = st.selectbox("Select Player", ["— Overall —"] + [u["display_name"] for u in users])

    if selected == "— Overall —":
        rows = []
        for u in users:
            uname = u["username"]
            bps = db().table("bps").select("*").eq("player", uname).execute().data or []
            preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
            rows.append({
                "Player": u["display_name"],
                "Total": get_player_total_points(uname),
                "SP Pts": get_player_sp_points(uname),
                "BP Pts": get_player_bp_points(uname),
                "Streak Pts": get_player_streak_points(uname),
                "BPs ✅": len([b for b in bps if b.get("result") == "correct"]),
                "BPs ❌": len([b for b in bps if b.get("result") == "wrong"]),
                "SP Played": len([p for p in preds if p.get("actual_score") is not None]),
                "Streak 🔥": get_current_streak(uname)
            })
        rows.sort(key=lambda x: x["Total"], reverse=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        u = next((u for u in users if u["display_name"] == selected), None)
        if not u: return
        uname = u["username"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", get_player_total_points(uname))
        col2.metric("SP Pts", get_player_sp_points(uname))
        col3.metric("BP Pts", get_player_bp_points(uname))
        col4.metric("Streak Pts", get_player_streak_points(uname))

        streak = get_current_streak(uname)
        if streak > 1:
            st.markdown(f"🔥 **Current Streak: {streak} wins in a row!**")

        st.markdown("---")
        st.subheader("📝 Bold Predictions")
        bps = db().table("bps").select("*").eq("player", uname).execute().data or []
        if bps:
            bp_rows = [{"Match": b["match_name"], "Prediction": b["prediction"],
                        "Avg Panel": b.get("avg_score", "Pending"), "Result": b.get("result", "pending"),
                        "Pts": b.get("points_awarded", 0)} for b in bps]
            st.dataframe(pd.DataFrame(bp_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No BPs yet.")

        st.markdown("---")
        st.subheader("🔮 Score Predictions")
        preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
        if preds:
            sp_rows = [{"Match": p["match_name"],
                        "Predicted": f"{p.get('predicted_score')} - {str(p.get('predicted_wickets', 0)).zfill(2)}",
                        "Winner": p.get("predicted_winner", "-"),
                        "Actual": f"{p.get('actual_score', '-')} - {str(p.get('actual_wickets', 0)).zfill(2)}" if p.get("actual_score") else "Pending",
                        "Pts": p.get("points_awarded", 0)} for p in preds]
            st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No predictions yet.")


def page_season_predictions():
    st.title("🌟 Season Predictions")
    st.markdown("---")
    user = st.session_state.user
    username = user["username"]

    if user["role"] == "guest":
        results = db().table("season_predictions").select("*").execute().data or []
        if results:
            rows = [{"Player": get_user_display(sp["player"]),
                     "🧡 Orange Cap": sp.get("orange_cap"), "💜 Purple Cap": sp.get("purple_cap"),
                     "🌟 Emerging": sp.get("emerging_player"),
                     "Top 4": f"{sp.get('top1')}→{sp.get('top2')}→{sp.get('top3')}→{sp.get('top4')}",
                     "Pts": sp.get("points_awarded", 0)} for sp in results]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
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
        st.write(f"**Points: {sp.get('points_awarded', 'Pending')}**")
        return

    st.markdown("**Points:** Orange Cap=20 | Purple Cap=20 | Emerging=15 | Top4 team=6 (+4 if position correct)")
    oc = st.text_input("🧡 Orange Cap (top run scorer)")
    pc = st.text_input("💜 Purple Cap (top wicket taker)")
    em = st.text_input("🌟 Emerging Player")
    st.markdown("**Top 4 Teams (in order):**")
    t1 = st.text_input("1st Place")
    t2 = st.text_input("2nd Place")
    t3 = st.text_input("3rd Place")
    t4 = st.text_input("4th Place")

    if st.button("🚀 Submit Season Predictions"):
        if not all([oc, pc, em, t1, t2, t3, t4]):
            st.error("Fill all fields!")
        else:
            db().table("season_predictions").insert({
                "player": username, "orange_cap": oc.upper(), "purple_cap": pc.upper(),
                "emerging_player": em.upper(), "top1": t1.upper(), "top2": t2.upper(),
                "top3": t3.upper(), "top4": t4.upper(), "points_awarded": 0
            }).execute()
            st.success("✅ Submitted!")
            st.rerun()


def page_how_to_score():
    st.title("📖 How to Score")
    st.markdown("---")

    st.subheader("📝 Bold Predictions (BP)")
    st.markdown("""
- Submit **1 BP per match** before BP is locked
- ♕ Queen **approves or rejects** your BP
- ♗ Bishops rate it **0–3** for riskiness (you cannot see who rated what)
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
    st.subheader("🔥 Streak Points (SP wins only)")
    st.markdown("""
- Win 2 in a row → **+1 bonus**
- Win 3 in a row → **+2 bonus**
- Win 4+ in a row → **+3 bonus**
- Streak resets if you don't win
""")

    st.markdown("---")
    st.subheader("🌟 Season Predictions")
    st.markdown("""
- Submit once before tournament starts
- 🧡 Orange Cap → **20 pts**
- 💜 Purple Cap → **20 pts**
- 🌟 Emerging Player → **15 pts**
- 🏏 Correct Top 4 team → **6 pts each** (+4 if position correct)
""")

    st.markdown("---")
    st.subheader("♟ Roles")
    st.markdown("""
| Role | Name | Responsibility |
|---|---|---|
| ♔ | King (Admin) | Full control |
| ♕ | Queen (BP Manager) | Approves player BPs, enters results (rotates weekly) |
| ♞ | Knight | Approves Queen's + Bishops' BPs, rates Bishops' BPs blindly (rotates weekly) |
| ♗ | Bishop x3 | Rates player BPs blindly 0–3 (fixed all tournament) |
| ♟ | Pawn (Player) | Submits BPs and SPs |
""")


def page_admin():
    st.title("⚙️ King's Panel")
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Matches", "👥 Players", "📝 BP Results", "🌟 Season Results"])

    with tab1:
        match_name = st.text_input("Match Name (e.g. SRH vs KKR)")
        match_date = st.date_input("Date")
        if st.button("Add Match"):
            if match_name.strip():
                db().table("matches").insert({
                    "match_name": match_name.strip().upper(),
                    "match_date": str(match_date),
                    "status": "open",
                    "bp_locked": False,
                    "sp_locked": False
                }).execute()
                st.success("✅ Match added!")
                st.rerun()
        st.markdown("---")
        for m in (db().table("matches").select("*").execute().data or []):
            bp = "🔒" if m.get("bp_locked") else "🟢"
            sp = "🔒" if m.get("sp_locked") else "🟢"
            st.write(f"🏏 **{m['match_name']}** | {m.get('match_date', '')} | BP:{bp} SP:{sp} | {m.get('status', 'open')}")

    with tab2:
        roles = ["player", "bishop1", "bishop2", "bishop3", "knight", "bp_manager", "admin"]
        nu = st.text_input("Username")
        np = st.text_input("Password")
        nr = st.selectbox("Role", roles)
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
        st.subheader("🔁 Rotate Queen & Knight")
        users = get_all_users()
        names = [u["display_name"] for u in users]
        new_queen = st.selectbox("New ♕ Queen (BP Manager)", names, key="nq")
        new_knight = st.selectbox("New ♞ Knight", names, key="nk")
        if st.button("Update Roles"):
            for u in users:
                if u["role"] in ["bp_manager", "knight"]:
                    db().table("users").update({"role": "player"}).eq("id", u["id"]).execute()
            nq = next(u for u in users if u["display_name"] == new_queen)
            nk = next(u for u in users if u["display_name"] == new_knight)
            db().table("users").update({"role": "bp_manager"}).eq("id", nq["id"]).execute()
            db().table("users").update({"role": "knight"}).eq("id", nk["id"]).execute()
            st.success(f"✅ Queen: {new_queen} | Knight: {new_knight}")
            st.rerun()

        st.markdown("---")
        st.subheader("All Players")
        for u in (db().table("users").select("*").execute().data or []):
            role_label = ROLE_DISPLAY.get(u["role"], u["role"])
            st.write(f"{role_label} **{u['display_name']}** | `{u['username']}`")

    with tab3:
        page_bp_results()

    with tab4:
        oc = st.text_input("🧡 Orange Cap Winner")
        pc = st.text_input("💜 Purple Cap Winner")
        em = st.text_input("🌟 Emerging Player")
        t1 = st.text_input("1st Place Team")
        t2 = st.text_input("2nd Place Team")
        t3 = st.text_input("3rd Place Team")
        t4 = st.text_input("4th Place Team")
        if st.button("Award Season Points"):
            actuals = {"oc": oc.upper(), "pc": pc.upper(), "em": em.upper(),
                       "t1": t1.upper(), "t2": t2.upper(), "t3": t3.upper(), "t4": t4.upper()}
            for sp in (db().table("season_predictions").select("*").execute().data or []):
                pts = 0
                if sp.get("orange_cap", "").upper() == actuals["oc"]: pts += 20
                if sp.get("purple_cap", "").upper() == actuals["pc"]: pts += 20
                if sp.get("emerging_player", "").upper() == actuals["em"]: pts += 15
                actual_top4 = [actuals["t1"], actuals["t2"], actuals["t3"], actuals["t4"]]
                pred_top4 = [sp.get("top1", "").upper(), sp.get("top2", "").upper(),
                             sp.get("top3", "").upper(), sp.get("top4", "").upper()]
                for j, team in enumerate(pred_top4):
                    if team in actual_top4:
                        pts += 6
                        if team == actual_top4[j]: pts += 4
                db().table("season_predictions").update({"points_awarded": pts}).eq("id", sp["id"]).execute()
            st.success("✅ Season points awarded!")


# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="LFxCT", page_icon="🏏", layout="wide")

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.title("🏏 LFxCT")
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
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
                st.session_state.user = {"username": "guest", "display_name": "Guest", "role": "guest"}
                st.rerun()
        return

    user = st.session_state.user
    role = user["role"]

    with st.sidebar:
        role_label = ROLE_DISPLAY.get(role, role)
        st.markdown(f"### 👋 {user['display_name']}")
        st.markdown(f"*{role_label}*")
        st.markdown("---")

        if role == "guest":
            pages = ["🏆 Leaderboard", "📊 Stats", "📋 Match Details", "📖 How to Score", "🌟 Season Predictions"]
        else:
            pages = ["🏆 Leaderboard", "📊 Stats", "📋 Match Details", "📖 How to Score",
                     "🌟 Season Predictions", "📝 Submit BP", "🔮 Score Prediction"]
            if role in ["bp_manager", "knight", "admin"]:
                pages.append("✅ Approve BPs")
            if role in BISHOP_ROLES + ["knight", "admin"]:
                pages.append("⭐ Rate BPs")
            if role in BISHOP_ROLES + ["bp_manager", "admin"]:
                pages.append("🔒 Lock BP/SP")
            if role in ["bp_manager", "admin"]:
                pages.append("🏆 Enter Results")
                pages.append("📝 BP Results")
            if role == "admin":
                pages.append("⚙️ King's Panel")

        page = st.radio("Navigation", pages)
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    if page == "🏆 Leaderboard": page_leaderboard()
    elif page == "📝 Submit BP": page_submit_bp()
    elif page == "🔮 Score Prediction": page_submit_sp()
    elif page == "✅ Approve BPs": page_bp_approvals()
    elif page == "⭐ Rate BPs": page_panel_scoring()
    elif page == "🔒 Lock BP/SP": page_lock_match()
    elif page == "🏆 Enter Results": page_enter_results()
    elif page == "📝 BP Results": page_bp_results()
    elif page == "⚙️ King's Panel": page_admin()
    elif page == "📊 Stats": page_stats()
    elif page == "📋 Match Details": page_match_details()
    elif page == "📖 How to Score": page_how_to_score()
    elif page == "🌟 Season Predictions": page_season_predictions()


if __name__ == "__main__":
    main()
