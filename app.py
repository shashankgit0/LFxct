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

def get_all_users():
    return db().table("users").select("*").execute().data or []

def get_user_display(username):
    for u in get_all_users():
        if u["username"] == username:
            return u["display_name"]
    return username

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
    return round(get_player_sp_points(username) + get_player_bp_points(username) +
                 get_player_streak_points(username) + get_player_season_points(username), 2)

def get_current_streak(username):
    preds = db().table("predictions").select("*").eq("player", username).execute().data or []
    done = [p for p in preds if p.get("actual_score") is not None]
    done.sort(key=lambda x: x.get("submitted_at",""), reverse=True)
    streak = 0
    for p in done:
        all_preds = db().table("predictions").select("*").eq("match_name", p["match_name"]).execute().data or []
        valid = [x for x in all_preds if x.get("actual_score") is not None]
        if not valid: break
        min_diff = min(abs(int(x.get("predicted_score") or 0) - int(x.get("actual_score") or 0)) for x in valid)
        my_diff = abs(int(p.get("predicted_score") or 0) - int(p.get("actual_score") or 0))
        if my_diff == min_diff:
            streak += 1
        else:
            break
    return streak

def login(username, password):
    res = db().table("users").select("*").eq("username", username).eq("password", password).execute()
    return res.data[0] if res.data else None

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
        season = get_player_season_points(uname)
        rows.append({"Player": u["display_name"], "SP": sp, "BP": bp, "Streak": streak, "Season": season, "Total": round(sp+bp+streak+season,2)})
    rows.sort(key=lambda x: x["Total"], reverse=True)
    cols = st.columns([0.4, 2.2, 0.8, 0.8, 0.8, 0.8, 0.9])
    for col, h in zip(cols, ["#", "Player", "SP", "BP", "Streak", "Season", "Total"]):
        col.markdown(f"**{h}**")
    st.markdown("---")
    for i, row in enumerate(rows):
        cols = st.columns([0.4, 2.2, 0.8, 0.8, 0.8, 0.8, 0.9])
        medal = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else str(i+1)
        cols[0].write(medal)
        cols[1].write(row["Player"])
        cols[2].write(row["SP"])
        cols[3].write(row["BP"])
        cols[4].write(row["Streak"])
        cols[5].write(row["Season"])
        cols[6].write(f"**{row['Total']}**")

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
        st.info(f"**{bp['prediction']}** | Status: {bp['status']} | Pts: {bp.get('points_awarded',0)}")
        return
    prediction = st.text_area("Your Bold Prediction", placeholder="e.g. Kohli to score 50+ runs")
    if st.button("🚀 Submit BP"):
        if not prediction.strip():
            st.error("Enter a prediction!")
        else:
            db().table("bps").insert({"match_name": match, "player": st.session_state.user["username"],
                "prediction": prediction.strip(), "status": "pending", "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")}).execute()
            st.success("✅ BP submitted!")

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
        predicted_score = st.number_input("Predicted Score (runs)", min_value=0, max_value=400, step=1)
        predicted_wickets = st.number_input("Predicted Wickets (0-10)", min_value=0, max_value=10, step=1)
    with col2:
        predicted_winner = st.text_input("Predicted Winner").upper()
    st.caption(f"Your prediction: **{predicted_score} - {str(predicted_wickets).zfill(2)}**")
    if st.button("🚀 Submit"):
        if not predicted_winner.strip():
            st.error("Enter the winner!")
        else:
            db().table("predictions").insert({"match_name": match, "player": st.session_state.user["username"],
                "predicted_score": predicted_score, "predicted_wickets": predicted_wickets,
                "predicted_winner": predicted_winner.strip().upper(), "points_awarded": 0,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")}).execute()
            st.success("✅ Prediction submitted!")

def page_bp_manager():
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
        if role == "secondary_bp_manager":
            bp_managers = [u["username"] for u in get_all_users() if u["role"] == "bp_manager"]
            if bp_player not in bp_managers:
                continue
        if role == "bp_manager" and bp_player == username:
            continue
        shown += 1
        display = get_user_display(bp_player)
        st.markdown(f"**🏏 {bp['match_name']}** — **{display}**: {bp['prediction']}")
        st.caption(f"Submitted: {bp.get('submitted_at','')}")
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
    col_map = {"panel1": "panel1_score", "panel2": "panel2_score", "panel3": "panel3_score", "admin": "panel1_score"}
    approved = db().table("bps").select("*").eq("status", "approved").execute().data or []
    if not approved:
        st.success("No BPs to rate!")
        return

    if role == "backup_panelist":
        panel_users = {u["username"]: u["role"] for u in get_all_users() if u["role"] in ["panel1","panel2","panel3"]}
        slot_map = {"panel1": "panel1_score", "panel2": "panel2_score", "panel3": "panel3_score"}
        shown = 0
        for bp in approved:
            if bp["player"] not in panel_users:
                continue
            slot = slot_map.get(panel_users[bp["player"]])
            if not slot or bp.get(slot) is not None:
                continue
            shown += 1
            display = get_user_display(bp["player"])
            st.markdown(f"**🏏 {bp['match_name']}** — **{display}**: {bp['prediction']}")
            score = st.radio("Rating:", [0,1,2,3], horizontal=True, key=f"backup_{bp['id']}")
            st.caption("0=Too easy | 1=Moderate | 2=Risky | 3=Very risky")
            if st.button("Submit", key=f"backup_rate_{bp['id']}"):
                _submit_panel_score(bp, slot, score)
                st.rerun()
            st.markdown("---")
        if shown == 0:
            st.success("Nothing to rate!")
        return

    if role not in col_map:
        st.warning("You are not a panelist.")
        return

    col_name = col_map[role]
    unrated = [bp for bp in approved if bp.get(col_name) is None and bp["player"] != username]
    if not unrated:
        st.success("You've rated all BPs!")
        return
    for bp in unrated:
        display = get_user_display(bp["player"])
        st.markdown(f"**🏏 {bp['match_name']}** — **{display}**: {bp['prediction']}")
        score = st.radio("Rating:", [0,1,2,3], horizontal=True, key=f"score_{bp['id']}")
        st.caption("0=Too easy | 1=Moderate | 2=Risky | 3=Very risky")
        if st.button("Submit Rating", key=f"rate_{bp['id']}"):
            _submit_panel_score(bp, col_name, score)
            st.rerun()
        st.markdown("---")

def _submit_panel_score(bp, col_name, score):
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
        with st.expander(f"🏏 {m['match_name']}"):
            col1, col2 = st.columns(2)
            with col1:
                if m.get("bp_locked"):
                    st.success(f"🔒 BP locked by **{get_user_display(m.get('bp_locked_by',''))}** at {m.get('bp_locked_at','')}")
                else:
                    if st.button("🔒 Lock BP", key=f"lockbp_{m['id']}"):
                        db().table("matches").update({"bp_locked": True, "bp_locked_by": user["username"], "bp_locked_at": now}).eq("id", m["id"]).execute()
                        db().table("locklog").insert({"match_name": m["match_name"], "lock_type": "BP", "locked_by": user["username"], "locked_at": now}).execute()
                        st.rerun()
            with col2:
                if m.get("sp_locked"):
                    st.success(f"🔒 SP locked by **{get_user_display(m.get('sp_locked_by',''))}** at {m.get('sp_locked_at','')}")
                else:
                    if st.button("🔒 Lock SP", key=f"locksp_{m['id']}"):
                        db().table("matches").update({"sp_locked": True, "sp_locked_by": user["username"], "sp_locked_at": now}).eq("id", m["id"]).execute()
                        db().table("locklog").insert({"match_name": m["match_name"], "lock_type": "SP", "locked_by": user["username"], "locked_at": now}).execute()
                        st.rerun()

def page_admin():
    st.title("⚙️ Admin Panel")
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Matches", "👥 Players", "📝 BP Results", "🏆 SP Results", "🌟 Season Results"])

    with tab1:
        match_name = st.text_input("Match Name")
        match_date = st.date_input("Date")
        if st.button("Add Match"):
            if match_name.strip():
                db().table("matches").insert({"match_name": match_name.strip().upper(), "match_date": str(match_date), "status": "open", "bp_locked": False, "sp_locked": False}).execute()
                st.success("✅ Match added!")
                st.rerun()
        st.markdown("---")
        for m in (db().table("matches").select("*").execute().data or []):
            bp = "🔒" if m.get("bp_locked") else "🟢"
            sp = "🔒" if m.get("sp_locked") else "🟢"
            st.write(f"🏏 **{m['match_name']}** | {m.get('match_date','')} | BP:{bp} SP:{sp} | {m.get('status','open')}")

    with tab2:
        roles = ["player","panel1","panel2","panel3","backup_panelist","moderator","bp_manager","secondary_bp_manager","admin"]
        nu = st.text_input("Username")
        np = st.text_input("Password")
        nr = st.selectbox("Role", roles)
        nd = st.text_input("Display Name")
        if st.button("Add Player"):
            if nu.strip() and np.strip() and nd.strip():
                db().table("users").insert({"username": nu.strip(), "password": np.strip(), "role": nr, "display_name": nd.strip()}).execute()
                st.success(f"✅ {nd} added!")
                st.rerun()
        st.markdown("---")
        st.subheader("🔁 Change BP Manager")
        users = get_all_users()
        names = [u["display_name"] for u in users]
        new_bp = st.selectbox("New BP Manager", names, key="nbp")
        new_sec = st.selectbox("New Secondary BP Manager", names, key="nsec")
        if st.button("Update BP Manager"):
            for u in users:
                if u["role"] in ["bp_manager", "secondary_bp_manager"]:
                    db().table("users").update({"role": "player"}).eq("id", u["id"]).execute()
            nb = next(u for u in users if u["display_name"] == new_bp)
            ns = next(u for u in users if u["display_name"] == new_sec)
            db().table("users").update({"role": "bp_manager"}).eq("id", nb["id"]).execute()
            db().table("users").update({"role": "secondary_bp_manager"}).eq("id", ns["id"]).execute()
            st.success(f"✅ Updated!")
            st.rerun()
        st.markdown("---")
        for u in (db().table("users").select("*").execute().data or []):
            st.write(f"👤 **{u['display_name']}** | `{u['username']}` | `{u['role']}`")

    with tab3:
        scored = db().table("bps").select("*").eq("status", "scored").execute().data or []
        if not scored:
            st.info("No scored BPs waiting.")
        for bp in scored:
            display = get_user_display(bp["player"])
            st.markdown(f"**{display}** — {bp['match_name']}: {bp['prediction']} | Avg: **{bp.get('avg_score','?')}**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Correct", key=f"c_{bp['id']}"):
                    db().table("bps").update({"result": "correct", "points_awarded": bp.get("avg_score",0), "status": "done"}).eq("id", bp["id"]).execute()
                    st.rerun()
            with col2:
                if st.button(f"❌ Wrong", key=f"w_{bp['id']}"):
                    db().table("bps").update({"result": "wrong", "points_awarded": -1, "status": "done"}).eq("id", bp["id"]).execute()
                    st.rerun()
            st.markdown("---")

    with tab4:
        matches = db().table("matches").select("*").execute().data or []
        pending = [m for m in matches if m.get("sp_locked") and m.get("status") != "done"]
        if not pending:
            st.info("No matches waiting for results.")
        else:
            match_sel = st.selectbox("Select Match", [m["match_name"] for m in pending])
            actual_score = st.number_input("Actual Score (runs)", min_value=0, max_value=500, step=1)
            actual_wickets = st.number_input("Actual Wickets", min_value=0, max_value=10, step=1)
            actual_winner = st.text_input("Actual Winner").upper()
            if st.button("Submit Result & Award Points"):
                if not actual_winner.strip():
                    st.error("Enter winner!")
                else:
                    db().table("matches").update({"status": "done", "actual_score": actual_score, "actual_wickets": actual_wickets, "actual_winner": actual_winner.upper()}).eq("match_name", match_sel).execute()
                    preds = db().table("predictions").select("*").eq("match_name", match_sel).execute().data or []
                    if preds:
                        for p in preds:
                            p["diff"] = abs(int(p.get("predicted_score") or 0) - actual_score)
                        min_diff = min(p["diff"] for p in preds)
                        winners = [p for p in preds if p["diff"] == min_diff]
                        for p in preds:
                            pts = 0
                            is_winner = p["diff"] == min_diff
                            if is_winner: pts += 6
                            if str(p.get("predicted_winner","")).upper() == actual_winner.upper(): pts += 2
                            if is_winner and int(p.get("predicted_wickets") or -1) == actual_wickets: pts += 1
                            db().table("predictions").update({"actual_score": actual_score, "actual_wickets": actual_wickets, "actual_winner": actual_winner.upper(), "points_awarded": pts}).eq("id", p["id"]).execute()
                        for w in winners:
                            uname = w["player"]
                            streak = get_current_streak(uname)
                            bonus = 3 if streak >= 4 else 2 if streak == 3 else 1 if streak == 2 else 0
                            if bonus > 0:
                                db().table("streaks").insert({"player": uname, "match_name": match_sel, "streak_count": streak, "bonus_points": bonus}).execute()
                    st.success("✅ Results entered!")
                    st.rerun()

    with tab5:
        oc = st.text_input("🧡 Orange Cap Winner")
        pc = st.text_input("💜 Purple Cap Winner")
        em = st.text_input("🌟 Emerging Player")
        t1 = st.text_input("1st Place Team")
        t2 = st.text_input("2nd Place Team")
        t3 = st.text_input("3rd Place Team")
        t4 = st.text_input("4th Place Team")
        if st.button("Award Season Points"):
            actuals = {"oc": oc.upper(), "pc": pc.upper(), "em": em.upper(), "t1": t1.upper(), "t2": t2.upper(), "t3": t3.upper(), "t4": t4.upper()}
            for sp in (db().table("season_predictions").select("*").execute().data or []):
                pts = 0
                if sp.get("orange_cap","").upper() == actuals["oc"]: pts += 20
                if sp.get("purple_cap","").upper() == actuals["pc"]: pts += 20
                if sp.get("emerging_player","").upper() == actuals["em"]: pts += 15
                actual_top4 = [actuals["t1"], actuals["t2"], actuals["t3"], actuals["t4"]]
                pred_top4 = [sp.get("top1","").upper(), sp.get("top2","").upper(), sp.get("top3","").upper(), sp.get("top4","").upper()]
                for j, team in enumerate(pred_top4):
                    if team in actual_top4:
                        pts += 6
                        if team == actual_top4[j]: pts += 4
                db().table("season_predictions").update({"points_awarded": pts}).eq("id", sp["id"]).execute()
            st.success("✅ Points awarded!")

def page_season_predictions():
    st.title("🌟 Season Predictions")
    st.markdown("---")
    user = st.session_state.user
    if user["role"] == "guest":
        results = db().table("season_predictions").select("*").execute().data or []
        if results:
            st.subheader("All Season Predictions")
            for sp in results:
                st.write(f"👤 **{get_user_display(sp['player'])}** | 🧡 {sp.get('orange_cap')} | 💜 {sp.get('purple_cap')} | 🌟 {sp.get('emerging_player')} | Top4: {sp.get('top1')}→{sp.get('top2')}→{sp.get('top3')}→{sp.get('top4')} | Pts: {sp.get('points_awarded',0)}")
        else:
            st.info("No season predictions yet.")
        return

    username = user["username"]
    existing = db().table("season_predictions").select("*").eq("player", username).execute().data or []
    if existing:
        sp = existing[0]
        st.success("✅ Your season predictions:")
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
    t1 = st.text_input("1st")
    t2 = st.text_input("2nd")
    t3 = st.text_input("3rd")
    t4 = st.text_input("4th")
    if st.button("🚀 Submit Season Predictions"):
        if not all([oc,pc,em,t1,t2,t3,t4]):
            st.error("Fill all fields!")
        else:
            db().table("season_predictions").insert({"player": username, "orange_cap": oc.upper(), "purple_cap": pc.upper(), "emerging_player": em.upper(), "top1": t1.upper(), "top2": t2.upper(), "top3": t3.upper(), "top4": t4.upper(), "points_awarded": 0}).execute()
            st.success("✅ Submitted!")
            st.rerun()

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
    st.markdown(f"### 🏏 {m['match_name']} — {m.get('match_date','')}")
    col1, col2, col3 = st.columns(3)
    col1.metric("BP", "🔒 Locked" if m.get("bp_locked") else "🟢 Open")
    col2.metric("SP", "🔒 Locked" if m.get("sp_locked") else "🟢 Open")
    col3.metric("Status", m.get("status","open").upper())
    if m.get("actual_score"):
        st.markdown(f"**Result:** {m.get('actual_winner')} won | {m.get('actual_score')} runs - {str(m.get('actual_wickets',0)).zfill(2)} wkts")
    if m.get("bp_locked"):
        st.caption(f"🔒 BP locked by {get_user_display(m.get('bp_locked_by',''))} at {m.get('bp_locked_at','')}")
    if m.get("sp_locked"):
        st.caption(f"🔒 SP locked by {get_user_display(m.get('sp_locked_by',''))} at {m.get('sp_locked_at','')}")
    st.markdown("---")
    st.subheader("📝 Bold Predictions")
    for bp in (db().table("bps").select("*").eq("match_name", selected).execute().data or []):
        icon = "✅" if bp.get("result")=="correct" else "❌" if bp.get("result")=="wrong" else "⏳"
        p1 = f"P1:{bp.get('panel1_score','-')}" 
        p2 = f"P2:{bp.get('panel2_score','-')}"
        p3 = f"P3:{bp.get('panel3_score','-')}"
        st.write(f"{icon} **{get_user_display(bp['player'])}**: {bp['prediction']} | {p1} {p2} {p3} | Avg:{bp.get('avg_score','-')} | Pts:{bp.get('points_awarded',0)}")
    st.markdown("---")
    st.subheader("🔮 Score Predictions")
    for p in (db().table("predictions").select("*").eq("match_name", selected).execute().data or []):
        win_icon = "🏆" if (p.get("points_awarded") or 0) >= 6 else ""
        actual = f"→ Actual: {p.get('actual_score')} - {str(p.get('actual_wickets',0)).zfill(2)}, {p.get('actual_winner')} won" if p.get("actual_score") else ""
        st.write(f"{win_icon} **{get_user_display(p['player'])}**: {p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p.get('predicted_winner')} {actual} | Pts:{p.get('points_awarded',0)}")

def page_stats():
    st.title("📊 Player Stats")
    st.markdown("---")
    users = get_all_users()
    if not users: st.info("No players."); return
    selected = st.selectbox("Select Player", ["— Overall —"] + [u["display_name"] for u in users])
    if selected == "— Overall —":
        rows = []
        for u in users:
            uname = u["username"]
            bps = db().table("bps").select("*").eq("player", uname).execute().data or []
            preds = db().table("predictions").select("*").eq("player", uname).execute().data or []
            rows.append({"Player": u["display_name"], "Total": get_player_total_points(uname),
                "SP Pts": get_player_sp_points(uname), "BP Pts": get_player_bp_points(uname),
                "Streak Pts": get_player_streak_points(uname),
                "BPs ✅": len([b for b in bps if b.get("result")=="correct"]),
                "BPs ❌": len([b for b in bps if b.get("result")=="wrong"]),
                "SP Played": len([p for p in preds if p.get("actual_score") is not None]),
                "Streak": get_current_streak(uname)})
        rows.sort(key=lambda x: x["Total"], reverse=True)
        cols = st.columns(len(rows[0]))
        for col, h in zip(cols, rows[0].keys()): col.markdown(f"**{h}**")
        st.markdown("---")
        for row in rows:
            cols = st.columns(len(row))
            for col, val in zip(cols, row.values()): col.write(val)
    else:
        u = next((u for u in users if u["display_name"] == selected), None)
        if not u: return
        uname = u["username"]
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Total", get_player_total_points(uname))
        col2.metric("SP Pts", get_player_sp_points(uname))
        col3.metric("BP Pts", get_player_bp_points(uname))
        col4.metric("Streak Pts", get_player_streak_points(uname))
        streak = get_current_streak(uname)
        if streak > 1: st.markdown(f"🔥 **Current Streak: {streak} wins in a row!**")
        st.markdown("---")
        st.subheader("📝 BPs")
        for bp in (db().table("bps").select("*").eq("player", uname).execute().data or []):
            icon = "✅" if bp.get("result")=="correct" else "❌" if bp.get("result")=="wrong" else "⏳"
            st.write(f"{icon} **{bp['match_name']}** — {bp['prediction']} | Avg:{bp.get('avg_score','Pending')} | Pts:{bp.get('points_awarded',0)}")
        st.markdown("---")
        st.subheader("🔮 Score Predictions")
        for p in (db().table("predictions").select("*").eq("player", uname).execute().data or []):
            actual = f"→ {p.get('actual_score')} - {str(p.get('actual_wickets',0)).zfill(2)}, {p.get('actual_winner')} won" if p.get("actual_score") else "Pending"
            st.write(f"🏏 **{p['match_name']}** — {p.get('predicted_score')} - {str(p.get('predicted_wickets',0)).zfill(2)} | {p.get('predicted_winner')} | {actual} | Pts:{p.get('points_awarded',0)}")

def page_how_to_score():
    st.title("📖 How to Score")
    st.markdown("---")
    st.subheader("📝 Bold Predictions (BP)")
    st.markdown("""
- Submit **1 BP per match** before BP is locked
- BP Manager **approves or rejects** it
- Panel of 3 rates it **0–3** (riskiness)
- Your BP value = **average of 3 panel scores**
- ✅ BP Correct → **+panel avg points**
- ❌ BP Wrong → **-1 point**
- Panelists cannot rate their own BPs (backup panelist steps in)
""")
    st.markdown("---")
    st.subheader("🔮 Score Predictions (SP)")
    st.markdown("""
- After 6 overs, predict **final score + wickets + match winner**
- 🏆 Closest score → **+6 pts**
- ✅ Correct winner → **+2 pts**
- 🎯 Correct wickets (SP winner only) → **+1 bonus pt**
- Tie on closest score → **both get 6 pts**
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
    st.subheader("👥 Roles")
    st.markdown("""
| Role | Responsibility |
|---|---|
| 👤 Player | Submit BPs and SPs |
| ✅ BP Manager | Approve/reject BPs, enter match results (rotates weekly) |
| 🔁 Secondary BP Manager | Approves only the BP Manager's own BPs (rotates weekly) |
| ⭐ Panelist x3 | Rate BPs 0–3 (fixed all tournament) |
| 🔄 Backup Panelist | Rates BPs for panelists who are players (fixed) |
| 🔒 Moderator/Panelist/BP Manager | Can lock BP and SP windows |
| 👑 Admin | Full control |
""")

# ─── Main ──────────────────────────────────────────────────────────────────────
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
                st.session_state.user = {"username": "guest", "display_name": "Guest", "role": "guest"}
                st.rerun()
        return

    user = st.session_state.user
    role = user["role"]

    with st.sidebar:
        st.markdown(f"### 👋 {user['display_name']}")
        st.markdown(f"*{role}*")
        st.markdown("---")
        if role == "guest":
            pages = ["🏆 Leaderboard", "📊 Stats", "📋 Match Details", "📖 How to Score", "🌟 Season Predictions"]
        else:
            pages = ["🏆 Leaderboard", "📊 Stats", "📋 Match Details", "📖 How to Score", "🌟 Season Predictions", "📝 Submit BP", "🔮 Score Prediction"]
            if role in ["bp_manager","secondary_bp_manager","admin"]:
                pages.append("✅ Approve BPs")
            if role in ["panel1","panel2","panel3","backup_panelist","admin"]:
                pages.append("⭐ Rate BPs")
            if role in ["panel1","panel2","panel3","bp_manager","admin"]:
                pages.append("🔒 Lock BP/SP")
            if role in ["bp_manager","admin"]:
                pages.append("🏆 Enter Results")
            if role == "admin":
                pages.append("⚙️ Admin Panel")
        page = st.radio("Navigation", pages)
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    if page == "🏆 Leaderboard": page_leaderboard()
    elif page == "📝 Submit BP": page_submit_bp()
    elif page == "🔮 Score Prediction": page_submit_sp()
    elif page == "✅ Approve BPs": page_bp_manager()
    elif page == "⭐ Rate BPs": page_panel_scoring()
    elif page == "🔒 Lock BP/SP": page_lock_match()
    elif page == "⚙️ Admin Panel": page_admin()
    elif page == "🏆 Enter Results":
        # BP Manager result entry (same as admin tab4)
        st.title("🏆 Enter Match Results")
        st.markdown("---")
        matches = db().table("matches").select("*").execute().data or []
        pending = [m for m in matches if m.get("sp_locked") and m.get("status") != "done"]
        if not pending:
            st.info("No matches waiting for results.")
        else:
            match_sel = st.selectbox("Select Match", [m["match_name"] for m in pending])
            actual_score = st.number_input("Actual Score (runs)", min_value=0, max_value=500, step=1)
            actual_wickets = st.number_input("Actual Wickets", min_value=0, max_value=10, step=1)
            actual_winner = st.text_input("Actual Winner").upper()
            if st.button("Submit Result & Award Points"):
                if not actual_winner.strip():
                    st.error("Enter winner!")
                else:
                    db().table("matches").update({"status": "done", "actual_score": actual_score, "actual_wickets": actual_wickets, "actual_winner": actual_winner.upper()}).eq("match_name", match_sel).execute()
                    preds = db().table("predictions").select("*").eq("match_name", match_sel).execute().data or []
                    if preds:
                        for p in preds:
                            p["diff"] = abs(int(p.get("predicted_score") or 0) - actual_score)
                        min_diff = min(p["diff"] for p in preds)
                        winners = [p for p in preds if p["diff"] == min_diff]
                        for p in preds:
                            pts = 0
                            is_winner = p["diff"] == min_diff
                            if is_winner: pts += 6
                            if str(p.get("predicted_winner","")).upper() == actual_winner.upper(): pts += 2
                            if is_winner and int(p.get("predicted_wickets") or -1) == actual_wickets: pts += 1
                            db().table("predictions").update({"actual_score": actual_score, "actual_wickets": actual_wickets, "actual_winner": actual_winner.upper(), "points_awarded": pts}).eq("id", p["id"]).execute()
                        for w in winners:
                            uname = w["player"]
                            streak = get_current_streak(uname)
                            bonus = 3 if streak >= 4 else 2 if streak == 3 else 1 if streak == 2 else 0
                            if bonus > 0:
                                db().table("streaks").insert({"player": uname, "match_name": match_sel, "streak_count": streak, "bonus_points": bonus}).execute()
                    st.success("✅ Results submitted!")
                    st.rerun()
    elif page == "📊 Stats": page_stats()
    elif page == "📋 Match Details": page_match_details()
    elif page == "📖 How to Score": page_how_to_score()
    elif page == "🌟 Season Predictions": page_season_predictions()

if __name__ == "__main__":
    main()
