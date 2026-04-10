import streamlit as st
import psycopg2

st.set_page_config(page_title="Manage Squad", page_icon="👥")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("🇮🇹🔵 Manage Squad")

# --- Load positions for dropdown ---
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, position_name FROM positions ORDER BY position_name;")
    positions = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Error loading positions: {e}")
    positions = []

position_options = {p[1]: p[0] for p in positions}

# --- Load players for edit/delete dropdowns ---
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name, pos.position_name, p.nationality, p.age, p.wage, p.shirt_number
        FROM players p
        JOIN positions pos ON p.position_id = pos.id
        WHERE p.is_active = true
        ORDER BY p.shirt_number;
    """)
    players = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Error loading players: {e}")
    players = []

player_options = {f"#{p[6]} - {p[1]}": p for p in players}

# -----------------------------------------------
# FORM 1 — ADD PLAYER
# -----------------------------------------------
st.subheader("➕ Add New Player")
with st.form("add_player_form"):
    name = st.text_input("Full Name *")
    position = st.selectbox("Position *", options=position_options.keys())
    nationality = st.text_input("Nationality *")
    age = st.number_input("Age *", min_value=1, max_value=99, step=1)
    wage = st.number_input("Weekly Wage (£) *", min_value=0, step=1000)
    shirt_number = st.number_input("Shirt Number *", min_value=1, max_value=99, step=1)
    joined_date = st.date_input("Date Joined *")
    submitted = st.form_submit_button("Add Player")

    if submitted:
        errors = []
        if not name.strip():
            errors.append("Name is required.")
        if not nationality.strip():
            errors.append("Nationality is required.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO players (name, position_id, nationality, age, wage, shirt_number, joined_date, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, true);
                """, (name.strip(), position_options[position], nationality.strip(), age, wage, shirt_number, joined_date))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ {name} added to the squad!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")

# -----------------------------------------------
# FORM 2 — EDIT PLAYER
# -----------------------------------------------
st.subheader("✏️ Edit Player")

if not player_options:
    st.info("No players available to edit.")
else:
    with st.form("edit_player_form"):
        selected = st.selectbox("Select Player to Edit", options=player_options.keys())
        player_data = player_options[selected]
        pid, pname, ppos, pnat, page, pwage, pshirt = player_data

        new_name = st.text_input("Full Name *", value=pname)
        new_position = st.selectbox("Position *", options=position_options.keys(),
                                    index=list(position_options.keys()).index(ppos) if ppos in position_options else 0)
        new_nationality = st.text_input("Nationality *", value=pnat)
        new_age = st.number_input("Age *", min_value=1, max_value=99, value=page)
        new_wage = st.number_input("Weekly Wage (£) *", min_value=0, value=pwage, step=1000)
        new_shirt = st.number_input("Shirt Number *", min_value=1, max_value=99, value=pshirt)
        save = st.form_submit_button("Save Changes")

        if save:
            errors = []
            if not new_name.strip():
                errors.append("Name is required.")
            if not new_nationality.strip():
                errors.append("Nationality is required.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE players
                        SET name=%s, position_id=%s, nationality=%s, age=%s, wage=%s, shirt_number=%s
                        WHERE id=%s;
                    """, (new_name.strip(), position_options[new_position], new_nationality.strip(), new_age, new_wage, new_shirt, pid))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"✅ {new_name} updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

st.markdown("---")

# -----------------------------------------------
# FORM 3 — DELETE PLAYER
# -----------------------------------------------
st.subheader("🗑️ Delete Player")

if not player_options:
    st.info("No players available to delete.")
else:
    with st.form("delete_player_form"):
        selected_delete = st.selectbox("Select Player to Delete", options=player_options.keys())
        confirm = st.checkbox("I confirm I want to delete this player")
        delete = st.form_submit_button("Delete Player")

        if delete:
            if not confirm:
                st.error("Please check the confirmation box before deleting.")
            else:
                player_to_delete = player_options[selected_delete]
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM players WHERE id = %s;", (player_to_delete[0],))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"✅ {player_to_delete[1]} deleted from the squad.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

st.markdown("---")

# -----------------------------------------------
# PLAYERS TABLE
# -----------------------------------------------
st.subheader("📋 Current Squad")

search = st.text_input("Search by player name")

try:
    conn = get_connection()
    cur = conn.cursor()

    if search.strip():
        cur.execute("""
            SELECT p.name, pos.position_name, p.nationality, p.age, p.wage, p.shirt_number
            FROM players p
            JOIN positions pos ON p.position_id = pos.id
            WHERE p.is_active = true AND p.name ILIKE %s
            ORDER BY p.shirt_number;
        """, (f"%{search.strip()}%",))
    else:
        cur.execute("""
            SELECT p.name, pos.position_name, p.nationality, p.age, p.wage, p.shirt_number
            FROM players p
            JOIN positions pos ON p.position_id = pos.id
            WHERE p.is_active = true
            ORDER BY p.shirt_number;
        """)

    squad = cur.fetchall()
    cur.close()
    conn.close()

    if squad:
        st.table([{
            "Name": s[0],
            "Position": s[1],
            "Nationality": s[2],
            "Age": s[3],
            "Weekly Wage": f"£{s[4]:,}",
            "Shirt #": s[5]
        } for s in squad])
    else:
        st.info("No players found.")

except Exception as e:
    st.error(f"Error: {e}")
