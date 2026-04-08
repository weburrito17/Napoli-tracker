import streamlit as st
import psycopg2

st.set_page_config(page_title="Player Stats", page_icon="📊")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("📊 Player Stats")

# --- Load players and matches for dropdowns ---
try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM players WHERE is_active = true ORDER BY name;")
    players = cur.fetchall()

    cur.execute("SELECT id, opponent, match_date FROM matches ORDER BY match_date DESC;")
    matches = cur.fetchall()

    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Error loading data: {e}")
    players = []
    matches = []

player_options = {p[1]: p[0] for p in players}
match_options = {f"vs {m[1]} ({m[2].strftime('%Y-%m-%d')})": m[0] for m in matches}

# --- Log Stats Form ---
st.subheader("Log Player Stats")

if not player_options:
    st.warning("No active players found. Please add players first.")
elif not match_options:
    st.warning("No matches found. Please log a match first.")
else:
    with st.form("add_stats_form"):
        selected_player = st.selectbox("Player *", options=player_options.keys())
        selected_match = st.selectbox("Match *", options=match_options.keys())
        goals = st.number_input("Goals", min_value=0, step=1)
        assists = st.number_input("Assists", min_value=0, step=1)
        minutes_played = st.number_input("Minutes Played", min_value=0, max_value=120, step=1)
        yellow_cards = st.number_input("Yellow Cards", min_value=0, max_value=2, step=1)
        red_cards = st.number_input("Red Cards", min_value=0, max_value=1, step=1)
        rating = st.number_input("Rating (1.0 - 10.0)", min_value=1.0, max_value=10.0, step=0.1)
        submitted = st.form_submit_button("Log Stats")

        if submitted:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO player_stats (player_id, match_id, goals, assists, minutes_played, yellow_cards, red_cards, rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    player_options[selected_player],
                    match_options[selected_match],
                    goals, assists, minutes_played,
                    yellow_cards, red_cards, rating
                ))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ Stats logged for {selected_player}!")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")

# --- Search ---
search = st.text_input("Search by player name")

# --- Stats Table ---
st.subheader("All Player Stats")
try:
    conn = get_connection()
    cur = conn.cursor()

    if search.strip():
        cur.execute("""
            SELECT ps.id, p.name, m.opponent, m.match_date, ps.goals, ps.assists,
                   ps.minutes_played, ps.yellow_cards, ps.red_cards, ps.rating
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN matches m ON ps.match_id = m.id
            WHERE p.name ILIKE %s
            ORDER BY m.match_date DESC;
        """, (f"%{search.strip()}%",))
    else:
        cur.execute("""
            SELECT ps.id, p.name, m.opponent, m.match_date, ps.goals, ps.assists,
                   ps.minutes_played, ps.yellow_cards, ps.red_cards, ps.rating
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN matches m ON ps.match_id = m.id
            ORDER BY m.match_date DESC;
        """)

    stats = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Error: {e}")
    stats = []

if not stats:
    st.info("No stats logged yet.")
else:
    for stat in stats:
        sid, pname, mopp, mdate, goals, assists, mins, yc, rc, rating = stat

        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([2,2,1,1,1,1,1,1,1])
        col1.write(pname)
        col2.write(f"vs {mopp} ({mdate.strftime('%Y-%m-%d')})")
        col3.write(f"⚽ {goals}")
        col4.write(f"🅰️ {assists}")
        col5.write(f"⏱️ {mins}")
        col6.write(f"🟨 {yc}")
        col7.write(f"🟥 {rc}")
        col8.write(f"⭐ {rating}")

        if col9.button("Delete", key=f"delete_stat_{sid}"):
            st.session_state[f"confirm_delete_stat_{sid}"] = True

        if st.session_state.get(f"confirm_delete_stat_{sid}"):
            st.warning(f"Delete stats for {pname} vs {mopp}?")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"confirm_stat_{sid}"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM player_stats WHERE id = %s;", (sid,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("✅ Stat entry deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            if c2.button("Cancel", key=f"cancel_stat_{sid}"):
                st.session_state[f"confirm_delete_stat_{sid}"] = False
                st.rerun()

        # --- Edit Form ---
        if st.session_state.get(f"editing_stat_{sid}"):
            with st.form(f"edit_stat_{sid}"):
                st.subheader(f"Editing stats for {pname}")
                new_goals = st.number_input("Goals", value=goals, min_value=0)
                new_assists = st.number_input("Assists", value=assists, min_value=0)
                new_mins = st.number_input("Minutes Played", value=mins, min_value=0, max_value=120)
                new_yc = st.number_input("Yellow Cards", value=yc, min_value=0, max_value=2)
                new_rc = st.number_input("Red Cards", value=rc, min_value=0, max_value=1)
                new_rating = st.number_input("Rating", value=float(rating), min_value=1.0, max_value=10.0, step=0.1)
                save = st.form_submit_button("Save Changes")

                if save:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE player_stats
                            SET goals=%s, assists=%s, minutes_played=%s,
                                yellow_cards=%s, red_cards=%s, rating=%s
                            WHERE id=%s;
                        """, (new_goals, new_assists, new_mins, new_yc, new_rc, new_rating, sid))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("✅ Stats updated!")
                        st.session_state[f"editing_stat_{sid}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")