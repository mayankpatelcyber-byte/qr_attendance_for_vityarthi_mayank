import pandas as pd
student=[]
for i in range (0,101):
    student.append({"reg_no":f"2026cs{1000 +i}",
                    "name": f"student{i}",
                    "phone_number":f"98765{i:05d}",
                    "status": "absent"})
    df = pd.DataFrame(student)
df.to_csv("students.csv", index=False)
print("Success: Created 'students.csv' with 100 records.")
import qrcode
my_laptop_ip="172.25.186.83"
port="5000"
target_url=f"http://{my_laptop_ip}:{port}"
qr=qrcode.QRCode(version=1,box_size=10,border=4)
qr.add_data(target_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
import os
os.makedirs("static", exist_ok=True)
img.save("static/attendance_qr.png")
print(f"QR Code created as  :{target_url}")
import streamlit as st
import pandas as pd
import json
import os
import time 
# Configure Streamlit page layout
st.set_page_config(page_title="Attendance System", layout="centered")
CSV_FILE = "students.csv"
DATA_FILE = "latest_scan.json"
query_params = st.query_params
view_type = query_params.get("view", "mobile")
if view_type == "screen":
    st.title("Classroom Attendance System")
    st.subheader("Live Verification Display")
    if os.path.exists("attendance_qr.png"):
        st.image("attendance_qr.png", caption="Scan QR with mobile phone to mark attendance", width=260)
        st.divider()
        while True:
            if os.path.exists(DATA_FILE):
             with open(DATA_FILE, "r") as f:
                latest_data = json.load(f)

            class screen_placeholder:
                with screen_placeholder.container():
                    status = latest_data.get("status")

                if status == "success":
                    st.success("Attendance Verified Successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric(label="Student Name", value=latest_data.get("name"))
                    col2.metric(label="Registration No.", value=latest_data.get("reg_no"))
                    col3.metric(label="Mobile Number", value=latest_data.get("phone_number"))
                elif status=="error":
                    st.error("Access Denied: Unregistered Phone Number")
                    st.write(f"**Submitted Mobile:** {latest_data.get('phone_number')}")
                    st.warning("This number is not registered in college records.")
        else:
            st.info("System Ready — Waiting for next scan...")
        time.sleep(1)
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
                scan_info = {
                    "status": "success",
                    "name": student['name'],
                    "reg_no": student['reg_no'],
                    "phone_number": student['phone_number']
                }
                with open(DATA_FILE, "w") as f:
                    json.dump(scan_info, f)
                    if student['status'] == 'Present':
                        st.warning("Notice: You have already been marked Present today.")
                    else:
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