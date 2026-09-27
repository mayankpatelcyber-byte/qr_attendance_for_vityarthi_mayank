import os
import json
import time
import pandas as pd
import qrcode
import streamlit as st

# ==========================================
# 1. AUTOMATIC SETUP (DATABASE & QR CODE)
# ==========================================
CSV_FILE = "students.csv"
DATA_FILE = "latest_scan.json"
QR_FILE = "attendance_qr.png"

# Generate 100 students CSV if it doesn't exist yet
if not os.path.exists(CSV_FILE):
    students = []
    for i in range(1, 101):
        students.append({
            "reg_no": f"2026cs{1000 + i}",
            "name": f"student{i}",
            "phone_number": f"98765{i:05d}",  # Fixed column name matching
            "status": "absent"
        })
    df = pd.DataFrame(students)  # Fixed: Moved outside the for loop
    df.to_csv(CSV_FILE, index=False)
    print("Success: Generated students.csv")

# Generate QR Code if it doesn't exist yet
if not os.path.exists(QR_FILE):
    my_laptop_ip = "172.25.186.83"  # Your laptop IP address
    port = "8501"                   # Streamlit default port
    target_url = f"http://{my_laptop_ip}:{port}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(QR_FILE)  # Saved directly to root directory for easy access
    print(f"QR Code created pointing to: {target_url}")

# ==========================================
# 2. STREAMLIT APP CONFIGURATION & ROUTING
# ==========================================
st.set_page_config(page_title="Attendance System", layout="centered")

query_params = st.query_params
view_type = query_params.get("view", "mobile")

# ------------------------------------------
# VIEW A: CLASSROOM PROJECTOR DISPLAY SCREEN
# URL: http://localhost:8501/?view=screen
# ------------------------------------------
if view_type == "screen":
    st.title("Classroom Attendance System")
    st.subheader("Live Verification Display")

    if os.path.exists(QR_FILE):
        st.image(QR_FILE, caption="Scan QR with mobile phone to mark attendance", width=260)
    
    st.divider()
    screen_placeholder = st.empty()  # Fixed Streamlit placeholder object

    while True:
        with screen_placeholder.container():
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    latest_data = json.load(f)

                status = latest_data.get("status")

                if status == "success":
                    st.success("Attendance Verified Successfully!")
                    col1, col2, col3 = st.columns(3)
                    col1.metric(label="Student Name", value=latest_data.get("name"))
                    col2.metric(label="Registration No.", value=latest_data.get("reg_no"))
                    col3.metric(label="Mobile Number", value=latest_data.get("phone_number"))

                elif status == "error":
                    st.error("Access Denied: Unregistered Phone Number")
                    st.write(f"**Submitted Mobile:** {latest_data.get('phone_number')}")
                    st.warning("This number is not registered in college records.")
            else:
                st.info("System Ready — Waiting for next scan...")

        time.sleep(1)

# ------------------------------------------
# VIEW B: MOBILE PHONE STUDENT PORTAL
# URL: http://172.25.186.83:8501
# ------------------------------------------
else:
    st.title("Student Attendance Portal")
    st.write("Enter your 10-digit registered mobile number below:")

    user_phone = st.text_input("Registered Mobile Number", placeholder="e.g. 9876500001")

    if st.button("Submit Attendance", type="primary"):
        if user_phone:
            phone_str = user_phone.strip()
            df = pd.read_csv(CSV_FILE)
            df['phone_number'] = df['phone_number'].astype(str)

            match = df[df['phone_number'] == phone_str]

            if not match.empty:
                student = match.iloc[0]

                # Update live display data for projector screen
                scan_info = {
                    "status": "success",
                    "name": student['name'],
                    "reg_no": student['reg_no'],
                    "phone_number": student['phone_number']
                }
                with open(DATA_FILE, "w") as f:
                    json.dump(scan_info, f)

                # Check if student is already present or mark present
                if student['status'] == 'Present':
                    st.warning("Notice: You have already been marked Present today.")
                else:
                    df.loc[df['phone_number'] == phone_str, 'status'] = 'Present'
                    df.to_csv(CSV_FILE, index=False)
                    st.success("Attendance Marked Successfully!")
            else:
                # Number not in database -> send error state to display
                scan_info = {
                    "status": "error",
                    "name": "N/A",
                    "reg_no": "N/A",
                    "phone_number": phone_str
                }
                with open(DATA_FILE, "w") as f:
                    json.dump(scan_info, f)

                st.error("Error: This phone number is not found in college data!")
        else:
            st.warning("Please enter a valid phone number.")
