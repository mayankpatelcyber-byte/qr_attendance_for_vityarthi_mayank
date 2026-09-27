import json
import os
import socket
import time
import pandas as pd
import qrcode
import streamlit as st


# Fetch active Wi-Fi IP address dynamically
def get_local_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
  except Exception:
    ip = "135.136.0.40"
  finally:
    s.close()
  return ip


st.set_page_config(
    page_title="Attendance System", page_icon="📋", layout="centered"
)

CSV_FILE = "students.csv"
DATA_FILE = "latest_scan.json"
PORT = "8501"


# Cache dataset initialization so it only runs once at startup
@st.cache_resource
def initialize_database():
  if not os.path.exists(CSV_FILE):
    students = [
        {
            "reg_no": f"2026cs{1000 + i}",
            "name": f"student{i}",
            "phone_number": f"98765{i:05d}",
            "status": "Absent",
        }
        for i in range(101)
    ]
    pd.DataFrame(students).to_csv(CSV_FILE, index=False)


initialize_database()

# Generate QR code object in memory (prevents file locking bugs)
MY_LAPTOP_IP = get_local_ip()
target_url = f"http://{MY_LAPTOP_IP}:{PORT}/?view=mobile"

qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(target_url)
qr.make(fit=True)
qr_image = qr.make_image(fill_color="black", back_color="white")

# Default view parameter set to "screen"
view_type = st.query_params.get("view", "screen")

# =========================================================
# VIEW 1: CLASSROOM SCREEN DISPLAY
# =========================================================
if view_type == "screen":
  st.title("Classroom Attendance System")
  st.write(f"**Server Address:** `{MY_LAPTOP_IP}:{PORT}`")
  st.subheader("Live Verification Display")

  # Render QR Code directly from PIL image object in RAM
  st.image(
      qr_image.get_image(),
      caption="Scan QR code with mobile phone to mark attendance",
      width=260,
  )

  st.divider()

  placeholder = st.empty()
  with placeholder.container():
    if os.path.exists(DATA_FILE):
      with open(DATA_FILE, "r") as f:
        latest_data = json.load(f)
      status = latest_data.get("status")

      if status == "success":
        st.success("Attendance Verified Successfully!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Student Name", latest_data.get("name"))
        col2.metric("Registration No.", latest_data.get("reg_no"))
        col3.metric("Mobile Number", latest_data.get("phone_number"))
      elif status == "error":
        st.error("Access Denied: Unregistered Phone Number")
        st.write(f"**Submitted Mobile:** {latest_data.get('phone_number')}")
        st.warning("This number is not registered in college records.")
    else:
      st.info("System Ready — Waiting for next scan...")

  time.sleep(2)
  st.rerun()

# =========================================================
# VIEW 2: STUDENT MOBILE PORTAL (Scan Target)
# =========================================================
else:
  st.title("Student Attendance Portal")
  st.write("Enter your 10-digit registered mobile number below:")

  user_phone = st.text_input(
      "Registered Mobile Number", placeholder="e.g. 9876500000"
  )

  if st.button("Submit Attendance", type="primary"):
    if user_phone:
      phone_str = user_phone.strip()

      if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["phone_number"] = df["phone_number"].astype(str)

        match = df[df["phone_number"] == phone_str]

        if not match.empty:
          index = match.index[0]
          student = match.iloc[0]

          if student["status"] == "Present":
            st.warning("Notice: You have already been marked Present today.")
          else:
            df.at[index, "status"] = "Present"
            df.to_csv(CSV_FILE, index=False)
            st.success("Attendance marked successfully!")

          scan_info = {
              "status": "success",
              "name": student["name"],
              "reg_no": student["reg_no"],
              "phone_number": student["phone_number"],
          }
          with open(DATA_FILE, "w") as f:
            json.dump(scan_info, f)
        else:
          scan_info = {
              "status": "error",
              "name": "N/A",
              "reg_no": "N/A",
              "phone_number": phone_str,
          }
          with open(DATA_FILE, "w") as f:
            json.dump(scan_info, f)
          st.error("Error: This phone number is not found in college data!")
      else:
        st.error("Database file missing.")
    else:
      st.warning("Please enter a valid phone number.")