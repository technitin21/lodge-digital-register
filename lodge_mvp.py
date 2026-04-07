import streamlit as st
import sqlite3
from datetime import datetime
import os

# ------------------ DB Setup ------------------
conn = sqlite3.connect('lodge_mvp.db')
c = conn.cursor()

# Guest register table
c.execute('''
CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    address TEXT,
    id_type TEXT,
    id_number TEXT,
    room_no TEXT,
    checkin DATETIME,
    checkout DATETIME,
    id_image_path TEXT,
    photo_path TEXT,
    status TEXT
)
''')

# Room setup table
c.execute('''
CREATE TABLE IF NOT EXISTS rooms (
    room_no TEXT PRIMARY KEY,
    room_type TEXT,
    rate REAL,
    status TEXT
)
''')

conn.commit()

# Create uploads directory
os.makedirs("uploads/id_cards", exist_ok=True)
os.makedirs("uploads/photos", exist_ok=True)

# ------------------ Authentication ------------------
USERS = {"admin": "admin123", "staff": "guest123"}

def login():
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if USERS.get(username) == password:
            st.session_state["auth"] = True
            st.session_state["user"] = username
            st.sidebar.success("Login successful!")
        else:
            st.sidebar.error("Invalid credentials")

def logout():
    st.session_state["auth"] = False
    st.session_state.pop("user", None)

# ------------------ Room Management ------------------
def room_management():
    st.header("🏠 Room Management")
    with st.form("add_room"):
        col1, col2, col3 = st.columns(3)
        room_no = col1.text_input("Room No")
        room_type = col2.selectbox("Room Type", ["Single", "Double", "Deluxe"])
        rate = col3.number_input("Rate (₹)", min_value=0.0)
        if st.form_submit_button("Add Room"):
            c.execute("INSERT OR REPLACE INTO rooms VALUES (?, ?, ?, ?)", 
                      (room_no, room_type, rate, "Available"))
            conn.commit()
            st.success(f"Room {room_no} added/updated successfully")

    st.subheader("All Rooms")
    rooms = c.execute("SELECT * FROM rooms").fetchall()
    if rooms:
        st.table(rooms)
    else:
        st.info("No rooms found.")

# ------------------ Guest Check-In ------------------
def guest_checkin():
    st.header("🧳 Guest Check-In")

    with st.form("checkin_form"):
        name = st.text_input("Guest Name")
        phone = st.text_input("Phone Number")
        address = st.text_area("Address")
        id_type = st.selectbox("ID Type", ["Aadhaar", "Passport", "Driving License", "Other"])
        id_number = st.text_input("ID Number")
        room_no = st.selectbox("Room No", [r[0] for r in c.execute("SELECT room_no FROM rooms WHERE status='Available'").fetchall()])
        id_image = st.file_uploader("Upload ID Image", type=["jpg", "png", "jpeg"])
        photo = st.file_uploader("Upload Guest Photo", type=["jpg", "png", "jpeg"])
        submit = st.form_submit_button("Check-In Guest")

        if submit:
            if not all([name, phone, id_type, room_no]):
                st.error("Please fill in all required fields.")
            else:
                id_image_path, photo_path = None, None
                if id_image:
                    id_image_path = f"uploads/id_cards/{name}_{id_image.name}"
                    with open(id_image_path, "wb") as f:
                        f.write(id_image.getbuffer())

                if photo:
                    photo_path = f"uploads/photos/{name}_{photo.name}"
                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())

                checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute('''INSERT INTO guests 
                             (name, phone, address, id_type, id_number, room_no, checkin, status, id_image_path, photo_path)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (name, phone, address, id_type, id_number, room_no, checkin_time, "Checked-In", id_image_path, photo_path))
                c.execute("UPDATE rooms SET status='Occupied' WHERE room_no=?", (room_no,))
                conn.commit()
                st.success(f"{name} checked in successfully!")

# ------------------ Guest Register ------------------
def guest_register():
    st.header("📘 Digital Guest Register")
    guests = c.execute("SELECT name, phone, room_no, checkin, checkout, status FROM guests ORDER BY checkin DESC").fetchall()
    if guests:
        st.table(guests)
    else:
        st.info("No guest records found.")

# ------------------ Checkout ------------------
def guest_checkout():
    st.header("🚪 Guest Checkout")
    checked_in_guests = c.execute("SELECT id, name, room_no FROM guests WHERE status='Checked-In'").fetchall()
    if not checked_in_guests:
        st.info("No guests currently checked-in.")
        return

    guest = st.selectbox("Select Guest", checked_in_guests, format_func=lambda x: f"{x[1]} (Room {x[2]})")
    if st.button("Mark Checkout"):
        checkout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE guests SET checkout=?, status='Checked-Out' WHERE id=?", (checkout_time, guest[0]))
        c.execute("UPDATE rooms SET status='Available' WHERE room_no=?", (guest[2],))
        conn.commit()
        st.success(f"{guest[1]} checked out successfully!")

# ------------------ Main App ------------------
def main():
    st.set_page_config(page_title="Lodge Digital Register", layout="wide")
    st.title("🏨 Lodge & Guesthouse Digital Register")

    if "auth" not in st.session_state or not st.session_state["auth"]:
        login()
        return
    else:
        st.sidebar.success(f"Logged in as {st.session_state['user']}")
        if st.sidebar.button("Logout"):
            logout()
            st.experimental_rerun()

    menu = st.sidebar.radio("Menu", ["Guest Check-In", "Guest Checkout", "Guest Register", "Room Management"])
    if menu == "Guest Check-In":
        guest_checkin()
    elif menu == "Guest Checkout":
        guest_checkout()
    elif menu == "Guest Register":
        guest_register()
    elif menu == "Room Management":
        room_management()

if __name__ == "__main__":
    main()
