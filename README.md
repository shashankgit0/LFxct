# 🏏 LFxCT — Fantasy Cricket League App

A full-stack fantasy cricket platform built for a private friend group to compete across IPL matches. Players submit score predictions, bold predictions (BPs), and draft league picks — all tracked live with a real-time leaderboard.

**Live App:** [lfxct3.streamlit.app](https://lfxct3.streamlit.app)

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Frontend | [Streamlit](https://streamlit.io) |
| Backend / DB | [Supabase](https://supabase.com) (PostgreSQL) |
| Language | Python |
| Auth | Username + password via Supabase `users` table |
| Assets | Supabase Storage (team logos) |

---

## 🎮 How It Works

The app has three core game modes that run in parallel across each IPL match:

### 1. 🔮 Score Prediction (SP)
Players predict the first innings score, wickets, and match winner before the 6-over mark.

| Outcome | Points |
|---|---|
| Closest score | +4 pts |
| Exact score | +6 pts |
| Correct winner | +2 pts |
| Correct wickets (SP winner only) | +1 pt |

Ties split the points. A **streak bonus** stacks if you win consecutive match predictions.

---

### 2. 🎱 Bold Predictions (BP)
Each player submits one bold prediction per match from a curated pool — or writes a custom one (cleared with admin first).

| Result | Points |
|---|---|
| ✅ Correct | +3 pts |
| ❌ Wrong | -1 pt |
| 🚫 Dismissed | 0 pts |

The BP Pool covers **60+ templates** across 4 categories: Batting, Bowling, Team, and Special events.

---

### 3. 🏏 Draft League
Each of 11 players owns a squad of 12 IPL players. The playing 11 accumulate **ESPN Cricinfo MVP points** across the season. A 12th player acts as a sub for injuries.

Admins can paste the IPL MVP leaderboard directly into the app — it auto-parses and updates all squad totals.

---

## 🏆 Leaderboard & Stats

- **Live leaderboard** with animated podium (gold/silver/bronze) and gradient rank rows
- **Overall Stats** tab: full breakdown, accuracy %, BP success rate, margin of error chart
- **Player Stats**: per-player points breakdown with bar chart + full prediction + BP history
- **Head to Head**: compare any two players across 13+ stats
- **Podium Tracker**: who finishes 1st, 2nd, 3rd most often

---

## 🏅 Hall of Fame

Tracks ~15 humorous achievement titles across all players, including:

- 👑 *"Too Good"* — Most SP wins
- 💀 *"Absolute Clown"* — Most BPs wrong
- ⚡ *"The Psychic"* — Most exact score predictions
- 🛋️ *"Checked Out"* — Most matches missed

---

## 🌟 Season Predictions

Before the season starts, players predict:
- Orange Cap & Purple Cap winners
- Emerging Player
- Top 4 IPL teams (with positional bonus)
- Fun categories (best catch, most sixes, wooden spoon, etc.)

Predictions are hidden until the admin locks and reveals them.

---

## 🔐 Roles & Access

| Role | Access |
|---|---|
| Guest | Leaderboard, stats, match details, how-to — read only |
| Player | All of the above + submit SPs, BPs, season predictions |
| Admin | All of the above + enter results, award points, manage matches, lock/cancel |

---

## 📂 Database Tables (Supabase)

| Table | Purpose |
|---|---|
| `users` | Player accounts, roles, team names |
| `matches` | Match list, dates, lock/status flags |
| `predictions` | SP submissions + awarded points |
| `pool_bps` | BP submissions + results |
| `streaks` | Streak win history + bonus points |
| `season_predictions` | Pre-season picks per player |
| `draft_player_points` | IPL MVP stats per draft player |
| `app_settings` | Feature flags (e.g. season lock) |

---

## 🚀 Running Locally

```bash
git clone https://github.com/shashankgit0/lfxct
cd lfxct
pip install -r requirements.txt
```

Add a `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-anon-key"
```

Then run:

```bash
streamlit run app.py
```
---
📸 Screenshots

<img width="408" height="716" alt="Screenshot 2026-04-27 at 21 56 04" src="https://github.com/user-attachments/assets/41332af6-3430-4094-a24b-b5d734b31dc3" />

<img width="1470" height="609" alt="Screenshot 2026-04-27 at 22 03 03" src="https://github.com/user-attachments/assets/ad8f9fa5-0c47-4c17-a96f-0cdc6e924a5f" />

<img width="1470" height="609" alt="Screenshot 2026-04-27 at 22 03 03" src="https://github.com/user-attachments/assets/ed348fd6-c9d6-40a2-9c9c-4a5e8f73de45" />

<img width="1470" height="702" alt="Screenshot 2026-04-27 at 22 05 00" src="https://github.com/user-attachments/assets/f84b5773-0fa9-475b-a4a8-0a9e88c84890" />




---


## 👤 Author

Built and maintained by [@shashankgit0](https://github.com/shashankgit0)  
Side project — started for a WhatsApp group, grew into a full product with 11 active users across an IPL season.
