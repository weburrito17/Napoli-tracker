import streamlit as st
import psycopg2

st.set_page_config(page_title="Manage Squad", page_icon="👥")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("👥 Manage Squad")

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

# --- Add Player Form ---
st.subheader("Add New Player")
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
        if age <= 0:
            errors.append("Age must be a positive number.")
        if wage < 0:
            errors.append("Wage cannot be negative.")
        if shirt_number < 1 or shirt_number > 99:
            errors.append("Shirt number must be between 1 and 99.")

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
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")

# --- Search Bar ---
search = st.text_input("Search players by name")

# --- Players Table ---
st.subheader("Current Squad")
try:
    conn = get_connection()
    cur = conn.cursor()

    if search.strip():
        cur.execute("""
            SELECT p.id, p.name, pos.position_name, p.nationality, p.age, p.wage, p.shirt_number
            FROM players p
            JOIN positions pos ON p.position_id = pos.id
            WHERE p.is_active = true AND p.name ILIKE %s
            ORDER BY p.shirt_number;
        """, (f"%{search.strip()}%",))
    else:
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
    st.error(f"Error: {e}")
    players = []

if not players:
    st.info("No players found.")
else:
    for player in players:
        pid, pname, ppos, pnat, page, pwage, pshirt = player
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2,2,1,1,1,2,1,1])
        col1.write(pname)
        col2.write(ppos)
        col3.write(pnat)
        col4.write(page)
        col5.write(f"£{pwage:,}")
        col6.write(f"#{pshirt}")

        if col7.button("Edit", key=f"edit_{pid}"):
            st.session_state[f"editing_{pid}"] = True

        if col8.button("Delete", key=f"delete_{pid}"):
            st.session_state[f"confirm_delete_{pid}"] = True

        # --- Confirm Delete ---
        if st.session_state.get(f"confirm_delete_{pid}"):
            st.warning(f"Are you sure you want to delete {pname}?")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"confirm_{pid}"):
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM players WHERE id = %s;", (pid,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"✅ {pname} deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            if c2.button("Cancel", key=f"cancel_{pid}"):
                st.session_state[f"confirm_delete_{pid}"] = False
                st.rerun()

        # --- Edit Form ---
        if st.session_state.get(f"editing_{pid}"):
            with st.form(f"edit_form_{pid}"):
                st.subheader(f"Editing {pname}")
                new_name = st.text_input("Name", value=pname)
                new_pos = st.selectbox("Position", options=position_options.keys(),
                                       index=list(position_options.keys()).index(ppos) if ppos in position_options else 0)
                new_nat = st.text_input("Nationality", value=pnat)
                new_age = st.number_input("Age", value=page, min_value=1, max_value=99)
                new_wage = st.number_input("Wage (£)", value=pwage, min_value=0)
                new_shirt = st.number_input("Shirt Number", value=pshirt, min_value=1, max_value=99)
                save = st.form_submit_button("Save Changes")

                if save:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE players
                            SET name=%s, position_id=%s, nationality=%s, age=%s, wage=%s, shirt_number=%s
                            WHERE id=%s;
                        """, (new_name, position_options[new_pos], new_nat, new_age, new_wage, new_shirt, pid))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("✅ Player updated!")
                        st.session_state[f"editing_{pid}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")