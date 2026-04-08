import streamlit as st
import psycopg2

st.set_page_config(page_title="Napoli FC Tracker", page_icon="⚽")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("⚽ Napoli FC Tracker")
st.write("Use the sidebar to navigate between pages.")
st.markdown("---")

try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM players WHERE is_active = true;")
    player_count = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(wage), 0) FROM players WHERE is_active = true;")
    total_wages = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM matches;")
    match_count = cur.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Players", player_count)
    col2.metric("Weekly Wage Bill", f"£{total_wages:,}")
    col3.metric("Matches Played", match_count)

    st.markdown("---")
    st.subheader("🕐 Recent Matches")

    cur.execute("""
        SELECT opponent, match_date, home_or_away, goals_for, goals_against, competition
        FROM matches
        ORDER BY match_date DESC
        LIMIT 5;
    """)
    rows = cur.fetchall()

    if rows:
        st.table([{
            "Opponent": r[0],
            "Date": r[1].strftime("%Y-%m-%d"),
            "H/A": r[2],
            "GF": r[3],
            "GA": r[4],
            "Competition": r[5]
        } for r in rows])
    else:
        st.info("No matches logged yet.")

    cur.close()
    conn.close()

except Exception as e:
    st.error(f"Database error: {e}")

