import streamlit as st
import face_recognition
import gspread
import numpy as np
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from PIL import Image

# --- CONFIGURATION (Wahi purani settings) ---
SHEET_FILE_NAME = "Student Dashboard"
TAB_NAME = "Form Responses 1"
JSON_FILE = "creds.json"
IMAGE_FOLDER = "student_images"

# Page Layout
st.set_page_config(page_title="AI Attendance", page_icon="📸")
st.title("📸 Smart AI Attendance System")
st.markdown("---")


# --- STEP 1: Google Sheets Connection ---
@st.cache_resource
def connect_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_FILE_NAME).worksheet(TAB_NAME)
    except Exception as e:
        st.error(f"Sheet Connection Error: {e}")
        return None


sheet = connect_sheet()


# --- STEP 2: Load Known Faces ---
@st.cache_data
def load_encodings():
    known_encodings = []
    known_names = []
    if not os.path.exists(IMAGE_FOLDER):
        return [], []

    for file in os.listdir(IMAGE_FOLDER):
        if file.endswith((".jpg", ".png")):
            img = face_recognition.load_image_file(f"{IMAGE_FOLDER}/{file}")
            encoding = face_recognition.face_encodings(img)
            if encoding:
                known_encodings.append(encoding[0])
                known_names.append(os.path.splitext(file)[0])
    return known_encodings, known_names


known_encodings, known_names = load_encodings()

# --- STEP 3: Camera Interface ---
st.write("### 🤳 Attendance Lagayein")
img_file = st.camera_input("Apna Chehra dikhayein")

if img_file is not None:
    with st.spinner('AI pehchan raha hai...'):
        # Image process karna
        img = Image.open(img_file)
        img_array = np.array(img)

        # Face recognition
        face_locations = face_recognition.face_locations(img_array)
        face_encodings = face_recognition.face_encodings(img_array, face_locations)

        if not face_encodings:
            st.warning("⚠️ Chehra nahi mila! Thoda piche ho kar ya light mein try karein.")
        else:
            name = "Unknown"
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_names[best_match_index]

            if name != "Unknown":
                st.success(f"✅ Welcome, {name}!")
                # Sheet update
                try:
                    cell = sheet.find(name)
                    row = cell.row
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    sheet.update_cell(row, 4, "Present")
                    sheet.update_cell(row, 5, now)

                    st.balloons()
                    st.info(f"📅 Attendance Time: {now}")
                except:
                    st.error("❌ Registration Number Sheet mein nahi mila!")
            else:
                st.error("🚫 Pehchan nahi paye! Kya aapne photo upload ki hai?")