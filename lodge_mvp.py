import streamlit as st
import sqlite3
from datetime import datetime
import os

conn = sqlite3.connect('lodge_mvp.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, phone TEXT, id_type TEXT, id_number TEXT,
    room_no TEXT, checkin DATETIME, checkout DATETIME,
    id_image_path TEXT, photo_path TEXT, status TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS rooms (
    room_no TEXT PRIMARY KEY, room_type TEXT, rate REAL, status TEXT)''')

conn.commit()

os.makedirs("uploads/id_cards", exist_ok=True)
os.makedirs("uploads/photos", exist_ok=True)

USERS = {"admin": "admin123"}

def login():
    st.title("🔐 Lodge Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if USERS.get(u) == p:
            st.session_state["auth"] = True
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

def dashboard():
    st.header("📊 Dashboard")
    total = c.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
    occ = c.execute("SELECT COUNT(*) FROM rooms WHERE status='Occupied'").fetchone()[0]
    today = c.execute("SELECT COUNT(*) FROM guests WHERE DATE(checkin)=DATE('now')").fetchone()[0]
    a,b,c1 = st.columns(3)
    a.metric("Total Rooms", total)
    b.metric("Occupied", occ)
    c1.metric("Today's Check-ins", today)

def rooms():
    st.header("🏠 Rooms")
    with st.form("room"):
        r = st.text_input("Room No")
        t = st.selectbox("Type", ["Single","Double"])
        rate = st.number_input("Rate", min_value=0)
        if st.form_submit_button("Add"):
            c.execute("INSERT OR REPLACE INTO rooms VALUES (?,?,?,?)",(r,t,rate,"Available"))
            conn.commit()
            st.success("Added")
    st.table(c.execute("SELECT * FROM rooms").fetchall())

def checkin():
    st.header("🧳 Check-In")
    avail = c.execute("SELECT room_no FROM rooms WHERE status='Available'").fetchall()
    if not avail:
        st.warning("No rooms")
        return
    with st.form("ci"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        idt = st.selectbox("ID",["Aadhaar","Passport"])
        idn = st.text_input("ID Number")
        room = st.selectbox("Room",[r[0] for r in avail])
        idimg = st.file_uploader("ID")
        photo = st.file_uploader("Photo")
        if st.form_submit_button("Check-In"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ip, pp = None, None
            if idimg:
                ip=f"uploads/id_cards/{idimg.name}"
                open(ip,"wb").write(idimg.getbuffer())
            if photo:
                pp=f"uploads/photos/{photo.name}"
                open(pp,"wb").write(photo.getbuffer())
            c.execute("INSERT INTO guests (name,phone,id_type,id_number,room_no,checkin,status,id_image_path,photo_path) VALUES (?,?,?,?,?,?,?,?,?)",
                      (name,phone,idt,idn,room,now,"Checked-In",ip,pp))
            c.execute("UPDATE rooms SET status='Occupied' WHERE room_no=?",(room,))
            conn.commit()
            st.success("Checked in")

def checkout():
    st.header("🚪 Checkout")
    g = c.execute("SELECT id,name,room_no FROM guests WHERE status='Checked-In'").fetchall()
    if not g:
        st.info("No guests")
        return
    sel = st.selectbox("Guest", g, format_func=lambda x: f"{x[1]} ({x[2]})")
    if st.button("Checkout"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE guests SET checkout=?,status='Checked-Out' WHERE id=?",(now,sel[0]))
        c.execute("UPDATE rooms SET status='Available' WHERE room_no=?",(sel[2],))
        conn.commit()
        st.success("Done")

def register():
    st.header("📘 Register")
    st.table(c.execute("SELECT name,phone,room_no,checkin,checkout,status FROM guests").fetchall())

def main():
    st.set_page_config("Lodge App", layout="wide")
    if "auth" not in st.session_state: st.session_state["auth"]=False
    if not st.session_state["auth"]:
        login(); return
    m = st.sidebar.radio("Menu",["Dashboard","Check-In","Checkout","Register","Rooms"])
    if m=="Dashboard": dashboard()
    elif m=="Check-In": checkin()
    elif m=="Checkout": checkout()
    elif m=="Register": register()
    elif m=="Rooms": rooms()

if __name__=="__main__":
    main()
