import streamlit as st
import psycopg2

st.set_page_config(page_title="Manage Matches", page_icon="📅")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("📅 Manage Matches")

# --- Add Match Form ---
st.subheader("Log New Match")
with st.form("add_match_form"):
    opponent = st.text_input("Opponent *")
    match_date = st.date_input("Match Date *")
    home_or_away = st.selectbox("Home or Away *", options=["Home", "Away"])
    competition = st.selectbox("Competition *", options=["Serie A", "Coppa Italia", "Champions League"])
    goals_for = st.number_input("Goals For *", min_value=0, step=1)
    goals_against = st.number_input("Goals Against *", min_value=0, step=1)
    submitted = st.form_submit_button("Log Match")

    if submitted:
        errors = []
        if not opponent.strip():
            errors.append("Opponent is required.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO matches (opponent, match_date, home_or_away, goals_for, goals_against, competition)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (opponent.strip(), match_date, home_or_away, goals_for, goals_against, competition))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ Match vs {opponent} logged!")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")

# --- Search ---
search = st.text_input("Search by opponent name")

# --- Matches Table ---
st.subheader("All Matches")
try:
    conn = get_connection()
    cur = conn.cursor()

    if search.strip():
        cur.execute("""
            SELECT id, opponent, match_date, home_or_away, goals_for, goals_against, competition
            FROM matches
            WHERE opponent ILIKE %s
            ORDER BY match_date DESC;
        """, (f"%{search.strip()}%",))
    else:
        cur.execute("""
            SELECT id, opponent, match_date, home_or_away, goals_for, goals_against, competition
            FROM matches
            ORDER BY match_date DESC;
        """)

    matches = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Error: {e}")
    matches = []

if not matches:
    st.info("No matches logged yet.")
else:
    for match in matches:
        mid, mopp, mdate, mhoa, mgf, mga, mcomp = match
        result = "W" if mgf > mga else ("L" if mgf < mga else "D")
        result_color = "🟢" if result == "W" else ("🔴" if result == "L" else "🟡")

        col1, col2, col3, col4, col5, col6 = st.columns([2,1,1,1,1,1])
        col1.write(f"vs {mopp}")
        col2.write(mdate.strftime("%Y-%m-%d"))
        col3.write(mhoa)
        col4.write(f"{mgf} - {mga} {result_color}")
        col5.write(mcomp)

        if col6.button("Edit", key=f"edit_{mid}"):
            st.session_state[f"editing_match_{mid}"] = True

        if st.button("Delete", key=f"delete_{mid}"):
            st.session_state[f"confirm_delete_match_{mid}"] = True

        # --- Confirm Delete ---
        if st.session_state.get(f"confirm_delete_match_{mid}"):
            st.warning(f"Are you sure you want to delete the match vs {mopp}?")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"confirm_{mid}"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM matches WHERE id = %s;", (mid,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("✅ Match deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            if c2.button("Cancel", key=f"cancel_{mid}"):
                st.session_state[f"confirm_delete_match_{mid}"] = False
                st.rerun()

        # --- Edit Form ---
        if st.session_state.get(f"editing_match_{mid}"):
            with st.form(f"edit_match_{mid}"):
                st.subheader(f"Editing match vs {mopp}")
                new_opp = st.text_input("Opponent", value=mopp)
                new_date = st.date_input("Match Date", value=mdate)
                new_hoa = st.selectbox("Home or Away", options=["Home", "Away"],
                                       index=0 if mhoa == "Home" else 1)
                new_comp = st.selectbox("Competition", options=["Serie A", "Coppa Italia", "Champions League"],
                                        index=["Serie A", "Coppa Italia", "Champions League"].index(mcomp) if mcomp in ["Serie A", "Coppa Italia", "Champions League"] else 0)
                new_gf = st.number_input("Goals For", value=mgf, min_value=0)
                new_ga = st.number_input("Goals Against", value=mga, min_value=0)
                save = st.form_submit_button("Save Changes")

                if save:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE matches
                            SET opponent=%s, match_date=%s, home_or_away=%s, goals_for=%s, goals_against=%s, competition=%s
                            WHERE id=%s;
                        """, (new_opp, new_date, new_hoa, new_gf, new_ga, new_comp, mid))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("✅ Match updated!")
                        st.session_state[f"editing_match_{mid}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")