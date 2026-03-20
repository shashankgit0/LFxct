import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# ─── Supabase Setup ────────────────────────────────────────────────────────────
SUPABASE_URL = "https://zfoytgcyrdqxaroctlwr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpmb3l0Z2N5cmRxeGFyb2N0bHdyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NjYyMzYsImV4cCI6MjA4OTU0MjIzNn0.pfyrH-R0Wk6S0pUcK4dB6jS7CWS8arYa26tx9of_qJI"

@st.cache_resource
def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def db():
    return get_client()


# ─── Auth ──────────────────────────────────────────────────────────────────────
def login(username, password):
    res = db().table("users").select("*").eq("username", username).eq("password", password).execute()
    if res.data:
        return res.data[0]
    return None

def get_all_users():
    res = db().table("users").select("*").execute()
    return res.data or []


# ─── Points ────────────────────────────────────────────────────────────────────
def get_player_total_points(username):
    total = 0
    bps = db().table("bps").select("points_awarded").eq("player", username).execute().data or []
    for b in bps:
        try:
            total += float(b.get("points_awarded") or 0)
        except:
            pass
    preds = db().table("predictions").select("points_awarded").eq("player", username).execute().data or []
    for p in preds:
        try:
            total += float(p.get("points_awarded") or 0)
        except:
            pass
    return round(total, 2)


# ─── Pages ─────────────────────────────────────────────────────────────────────

def page_home():
    st.title("🏏 LF x CT Fantasy Cricket")
    st.markdown("---")
    st.subheader("🏆 Leaderboard")
    users = get_all_users()
    if not users:
        st.info("No players yet.")
        return
    leaderboard = []
    for u in users:
        pts = get_player_total_points(u["username"])
        leaderboard.append({"Player": u["display_name"], "Total Points": pts})
    leaderboard.sort(key=lambda x: x["Total Points"], reverse=True)
    for i, row in enumerate(leaderboard):
        col1, col2, col3 = st.columns([1, 4, 2])
        with col1:
            if i == 0:
                st.markdown("### 🥇")
            elif i == 1:
                st.markdown("### 🥈")
            elif i == 2:
                st.markdown("### 🥉")
            else:
                st.markdown(f"### {i+1}")
        with col2:
            st.markdown(f"### {row['Player']}")
        with col3:
            st.markdown(f"### {row['Total Points']} pts")
        st.markdown("---")


def page_submit_bp():
    st.title("📝 Submit Bold Prediction")
    st.markdown("---")
    matches = db().table("matches").select("*").eq("status", "open").execute().data or []
    if not matches:
        st.warning("No open matches right now. Wait for admin to add a match.")
        return

    match_names = [m["match_name"] for m in matches]
    match = st.selectbox("Select Match", match_names)

    existing = db().table("bps").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        st.warning("You already submitted a BP for this match!")
        bp = existing[0]
        st.info(f"Your BP: **{bp['prediction']}** | Status: **{bp['status']}** | Points: **{bp['points_awarded']}**")
        return

    prediction = st.text_area("Your Bold Prediction", placeholder="e.g. Kohli to score 50+ runs")
    if st.button("🚀 Submit BP"):
        if not prediction.strip():
            st.error("Please enter a prediction!")
        else:
            db().table("bps").insert({
                "match_name": match,
                "player": st.session_state.user["username"],
                "prediction": prediction.strip(),
                "status": "pending",
                "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ BP submitted! Waiting for BP Manager approval.")


def page_submit_prediction():
    st.title("🔮 6-Over Score Prediction")
    st.markdown("---")
    matches = db().table("matches").select("*").eq("status", "open").execute().data or []
    if not matches:
        st.warning("No open matches right now.")
        return

    match_names = [m["match_name"] for m in matches]
    match = st.selectbox("Select Match", match_names)

    existing = db().table("predictions").select("*").eq("player", st.session_state.user["username"]).eq("match_name", match).execute().data or []
    if existing:
        st.warning("You already submitted a prediction for this match!")
        p = existing[0]
        st.info(f"Your prediction: **{p['predicted_score']} runs**, Winner: **{p['predicted_winner']}** | Points: **{p['points_awarded']}**")
        return

    predicted_score = st.number_input("Predicted Final Score (runs)", min_value=0, max_value=400, step=1)
    predicted_winner = st.text_input("Predicted Winner (team name)")
    if st.button("🚀 Submit Prediction"):
        if not predicted_winner.strip():
            st.error("Please enter the predicted winner!")
        else:
            db().table("predictions").insert({
                "match_name": match,
                "player": st.session_state.user["username"],
                "predicted_score": predicted_score,
                "predicted_winner": predicted_winner.strip(),
                "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }).execute()
            st.success("✅ Prediction submitted!")


def page_bp_manager():
    st.title("✅ BP Manager — Approve / Reject BPs")
    st.markdown("---")
    pending = db().table("bps").select("*").eq("status", "pending").execute().data or []
    if not pending:
        st.success("🎉 No pending BPs right now!")
        return

    for bp in pending:
        with st.expander(f"🏏 {bp['match_name']} — {bp['player']}: {bp['prediction']}"):
            st.write(f"**Submitted:** {bp.get('submitted_at', '')}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"approve_{bp['id']}"):
                    db().table("bps").update({"status": "approved"}).eq("id", bp["id"]).execute()
                    st.success("Approved!")
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{bp['id']}"):
                    db().table("bps").update({"status": "rejected"}).eq("id", bp["id"]).execute()
                    st.warning("Rejected.")
                    st.rerun()


def page_panel_scoring():
    st.title("⭐ Panel — Rate BPs (0 to 3)")
    st.markdown("---")
    role = st.session_state.user["role"]
    if role not in ["panel1", "panel2", "panel3", "admin"]:
        st.warning("You are not assigned as a panelist.")
        return

    approved = db().table("bps").select("*").eq("status", "approved").execute().data or []
    if not approved:
        st.success("No BPs waiting for panel scoring!")
        return

    col_map = {"panel1": "panel1_score", "panel2": "panel2_score", "panel3": "panel3_score", "admin": "panel1_score"}
    col_name = col_map[role]

    unrated = [bp for bp in approved if bp.get(col_name) is None]
    if not unrated:
        st.success("You've rated all pending BPs!")
        return

    for bp in unrated:
        with st.expander(f"🏏 {bp['match_name']} — {bp['player']}: {bp['prediction']}"):
            score = st.select_slider(
                "Risk Rating",
                options=[0, 1, 2, 3],
                value=1,
                key=f"score_{bp['id']}"
            )
            st.caption("0 = Too easy | 1 = Moderate | 2 = Risky | 3 = Very risky")
            if st.button("Submit Rating", key=f"rate_{bp['id']}"):
                update_data = {col_name: score}
                latest = db().table("bps").select("*").eq("id", bp["id"]).execute().data[0]
                p1 = latest.get("panel1_score")
                p2 = latest.get("panel2_score")
                p3 = latest.get("panel3_score")

                if col_name == "panel1_score": p1 = score
                elif col_name == "panel2_score": p2 = score
                else: p3 = score

                scores = [x for x in [p1, p2, p3] if x is not None]
                if len(scores) == 3:
                    avg = round(sum(float(s) for s in scores) / 3, 2)
                    update_data["avg_score"] = avg
                    update_data["status"] = "scored"

                db().table("bps").update(update_data).eq("id", bp["id"]).execute()
                st.success(f"Rating of {score} submitted!")
                st.rerun()


def page_moderator():
    st.title("🔒 Moderator — Lock Match")
    st.markdown("---")
    open_matches = db().table("matches").select("*").eq("status", "open").execute().data or []
    if not open_matches:
        st.success("No open matches to lock.")
        return

    match_names = [m["match_name"] for m in open_matches]
    match = st.selectbox("Select Match to Lock", match_names)

    if st.button("🔒 Lock This Match"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        user = st.session_state.user
        db().table("matches").update({
            "status": "locked",
            "locked_by": user["username"],
            "locked_at": now
        }).eq("match_name", match).execute()
        db().table("locklog").insert({
            "match_name": match,
            "locked_by": user["username"],
            "locked_at": now
        }).execute()
        st.success(f"✅ Match '{match}' locked by {user['display_name']} at {now}")
        st.rerun()

    st.markdown("---")
    st.subheader("📋 Lock Log")
    log = db().table("locklog").select("*").execute().data or []
    if log:
        for entry in log:
            st.write(f"🔒 **{entry['match_name']}** — locked by **{entry['locked_by']}** at {entry['locked_at']}")
    else:
        st.info("No locks recorded yet.")


def page_admin():
    st.title("⚙️ Admin Panel")
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Matches", "👥 Players", "📝 BP Results", "🏆 Prediction Results"])

    with tab1:
        st.subheader("Add New Match")
        match_name = st.text_input("Match Name (e.g. SRH vs KKR — Apr 5)")
        match_date = st.date_input("Match Date")
        if st.button("Add Match"):
            if not match_name.strip():
                st.error("Enter a match name!")
            else:
                db().table("matches").insert({
                    "match_name": match_name.strip(),
                    "match_date": str(match_date),
                    "status": "open"
                }).execute()
                st.success(f"✅ Match '{match_name}' added!")
                st.rerun()

        st.markdown("---")
        st.subheader("All Matches")
        matches = db().table("matches").select("*").execute().data or []
        for m in matches:
            st.write(f"🏏 **{m['match_name']}** | {m['match_date']} | Status: **{m['status']}**")

    with tab2:
        st.subheader("Add New Player")
        roles = ["player", "panel1", "panel2", "panel3", "moderator", "bp_manager", "admin"]
        new_username = st.text_input("Username")
        new_password = st.text_input("Password")
        new_role = st.selectbox("Role", roles)
        new_display = st.text_input("Display Name")
        if st.button("Add Player"):
            if not new_username.strip() or not new_password.strip() or not new_display.strip():
                st.error("Fill in all fields!")
            else:
                db().table("users").insert({
                    "username": new_username.strip(),
                    "password": new_password.strip(),
                    "role": new_role,
                    "display_name": new_display.strip()
                }).execute()
                st.success(f"✅ Player '{new_display}' added!")
                st.rerun()

        st.markdown("---")
        st.subheader("All Players")
        users = get_all_users()
        for u in users:
            st.write(f"👤 **{u['display_name']}** | Username: `{u['username']}` | Role: `{u['role']}`")

    with tab3:
        st.subheader("Mark BP Results After Match")
        scored = db().table("bps").select("*").eq("status", "scored").execute().data or []
        if not scored:
            st.info("No scored BPs waiting for results yet.")
        else:
            for bp in scored:
                with st.expander(f"🏏 {bp['match_name']} — {bp['player']}: {bp['prediction']} | Avg: {bp.get('avg_score', '?')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Correct (+{bp.get('avg_score', '?')} pts)", key=f"correct_{bp['id']}"):
                            db().table("bps").update({
                                "result": "correct",
                                "points_awarded": bp.get("avg_score", 0),
                                "status": "done"
                            }).eq("id", bp["id"]).execute()
                            st.success("Marked correct!")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Wrong (-1 pt)", key=f"wrong_{bp['id']}"):
                            db().table("bps").update({
                                "result": "wrong",
                                "points_awarded": -1,
                                "status": "done"
                            }).eq("id", bp["id"]).execute()
                            st.warning("Marked wrong.")
                            st.rerun()

    with tab4:
        st.subheader("Enter Match Result & Award Points")
        locked = db().table("matches").select("*").eq("status", "locked").execute().data or []
        if not locked:
            st.info("No locked matches waiting for results.")
        else:
            match_names = [m["match_name"] for m in locked]
            match_sel = st.selectbox("Select Match", match_names)
            actual_score = st.number_input("Actual Final Score (runs)", min_value=0, max_value=500, step=1)
            actual_winner = st.text_input("Actual Winner (team name)")

            if st.button("Submit Result & Award Points"):
                if not actual_winner.strip():
                    st.error("Enter the actual winner!")
                else:
                    db().table("matches").update({
                        "status": "done",
                        "actual_score": actual_score,
                        "actual_winner": actual_winner.strip()
                    }).eq("match_name", match_sel).execute()

                    preds = db().table("predictions").select("*").eq("match_name", match_sel).execute().data or []
                    if preds:
                        for p in preds:
                            p["diff"] = abs(int(p.get("predicted_score") or 0) - actual_score)
                        min_diff = min(p["diff"] for p in preds)
                        for p in preds:
                            pts = 0
                            if p["diff"] == min_diff:
                                pts += 6
                            if str(p.get("predicted_winner", "")).strip().lower() == actual_winner.strip().lower():
                                pts += 2
                            db().table("predictions").update({
                                "actual_score": actual_score,
                                "actual_winner": actual_winner.strip(),
                                "points_awarded": pts
                            }).eq("id", p["id"]).execute()

                    st.success(f"✅ Results entered and points awarded for '{match_sel}'!")
                    st.rerun()


def page_stats():
    st.title("📊 Overall Stats")
    st.markdown("---")
    users = get_all_users()
    if not users:
        st.info("No players yet.")
        return

    stats = []
    for u in users:
        uname = u["username"]
        total_pts = get_player_total_points(uname)
        bps = db().table("bps").select("*").eq("player", uname).execute().data or []
        bp_submitted = len(bps)
        bp_correct = len([b for b in bps if b.get("result") == "correct"])
        bp_wrong = len([b for b in bps if b.get("result") == "wrong"])
        scored_bps = [b for b in bps if b.get("avg_score") is not None]
        avg_panel = round(sum(float(b["avg_score"]) for b in scored_bps) / len(scored_bps), 2) if scored_bps else 0
        preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
        matches_predicted = len([p for p in preds if p.get("actual_score") is not None])
        winner_correct = len([p for p in preds if p.get("actual_winner") and str(p.get("predicted_winner", "")).strip().lower() == str(p.get("actual_winner", "")).strip().lower()])

        stats.append({
            "Player": u["display_name"],
            "Total Pts": total_pts,
            "BPs Sub": bp_submitted,
            "BPs ✅": bp_correct,
            "BPs ❌": bp_wrong,
            "Avg Panel": avg_panel,
            "Matches": matches_predicted,
            "Winners ✅": winner_correct,
        })

    stats.sort(key=lambda x: x["Total Pts"], reverse=True)
    cols = st.columns([3, 2, 2, 2, 2, 2, 2, 2])
    for col, h in zip(cols, ["Player", "Total Pts", "BPs Sub", "BPs ✅", "BPs ❌", "Avg Panel", "Matches", "Winners ✅"]):
        col.markdown(f"**{h}**")
    st.markdown("---")
    for row in stats:
        cols = st.columns([3, 2, 2, 2, 2, 2, 2, 2])
        for col, val in zip(cols, row.values()):
            col.write(val)


def page_my_stats():
    st.title(f"👤 My Stats — {st.session_state.user['display_name']}")
    st.markdown("---")
    uname = st.session_state.user["username"]
    total = get_player_total_points(uname)
    bps = db().table("bps").select("*").eq("player", uname).execute().data or []
    bp_correct = len([b for b in bps if b.get("result") == "correct"])
    bp_wrong = len([b for b in bps if b.get("result") == "wrong"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Points", total)
    col2.metric("BPs Correct ✅", bp_correct)
    col3.metric("BPs Wrong ❌", bp_wrong)

    st.markdown("---")
    st.subheader("📝 My Bold Predictions")
    if bps:
        for bp in bps:
            icon = "⏳" if bp["status"] == "pending" else "✅" if bp.get("result") == "correct" else "❌" if bp.get("result") == "wrong" else "🔍"
            st.write(f"{icon} **{bp['match_name']}** — {bp['prediction']} | Panel Avg: {bp.get('avg_score') or 'Pending'} | Points: {bp.get('points_awarded', 0)}")
    else:
        st.info("No BPs submitted yet.")

    st.markdown("---")
    st.subheader("🔮 My 6-Over Predictions")
    preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
    if preds:
        for p in preds:
            actual = f"Actual: {p.get('actual_score')} runs, {p.get('actual_winner')} won" if p.get("actual_score") else "Result pending"
            st.write(f"🏏 **{p['match_name']}** — Predicted: {p['predicted_score']} runs, {p['predicted_winner']} | {actual} | Points: {p.get('points_awarded', 0)}")
    else:
        st.info("No predictions submitted yet.")


# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="LF x CT Fantasy Cricket", page_icon="🏏", layout="wide")

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.title("🏏 LF x CT Fantasy Cricket")
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
        return

    user = st.session_state.user
    role = user["role"]

    with st.sidebar:
        st.markdown(f"### 👋 {user['display_name']}")
        st.markdown(f"*Role: {role}*")
        st.markdown("---")

        pages = ["🏠 Home", "👤 My Stats", "📊 Overall Stats", "📝 Submit BP", "🔮 6-Over Prediction"]
        if role in ["bp_manager", "admin"]:
            pages.append("✅ Approve BPs")
        if role in ["panel1", "panel2", "panel3", "admin"]:
            pages.append("⭐ Rate BPs")
        if role in ["moderator", "admin"]:
            pages.append("🔒 Lock Match")
        if role == "admin":
            pages.append("⚙️ Admin Panel")

        page = st.radio("Navigation", pages)
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    if page == "🏠 Home": page_home()
    elif page == "📝 Submit BP": page_submit_bp()
    elif page == "🔮 6-Over Prediction": page_submit_prediction()
    elif page == "✅ Approve BPs": page_bp_manager()
    elif page == "⭐ Rate BPs": page_panel_scoring()
    elif page == "🔒 Lock Match": page_moderator()
    elif page == "⚙️ Admin Panel": page_admin()
    elif page == "📊 Overall Stats": page_stats()
    elif page == "👤 My Stats": page_my_stats()


if __name__ == "__main__":
    main()
