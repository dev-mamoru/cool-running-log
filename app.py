import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import gspread
import re
from datetime import datetime

# --- 설정 ---
# 여기에 실제 스프레드시트 URL을 입력해주세요.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_KIl3tFbbpcqBKuxljcgxohbBnOodl1C_1tY1sQ2_PY/edit?gid=0#gid=0"

st.title("# CRC (COOL RUNNING CREW) RUNNING LOG")
st.write("- upload running log image files")

# Streamlit Secrets에서 GCP 키 로드 함수
def get_gcp_credentials():
    try:
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(key_dict)
        return creds
    except Exception as e:
        st.error(f"Secrets Load Error: {e}")
        return None

def get_vision_client(creds):
    return vision.ImageAnnotatorClient(credentials=creds)

def get_google_sheet_client(creds):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_with_scope = creds.with_scopes(scope)
    return gspread.authorize(creds_with_scope)

# GCP 인증 로드
creds = get_gcp_credentials()

# --- Google Sheets 연동 (자동 로드) ---
st.subheader("1. Select User")

selected_user = None
users = []
worksheet = None # 워크시트 객체 전역 변수처럼 사용

if creds:
    if "YOUR_SHEET_ID_HERE" in SHEET_URL:
        st.warning("⚠️ Please update the 'SHEET_URL' variable in app.py with your actual Google Sheet URL.")
    else:
        try:
            with st.spinner("Loading user list from Google Sheet..."):
                gc = get_google_sheet_client(creds)
                sh = gc.open_by_url(SHEET_URL)

                # 현재 날짜 기준 YYYY-MM 시트 선택
                current_month_sheet_name = datetime.now().strftime("%Y-%m")

                try:
                    worksheet = sh.worksheet(current_month_sheet_name)
                    st.caption(f"Connected to sheet: {current_month_sheet_name}")
                except gspread.exceptions.WorksheetNotFound:
                    st.error(f"❌ Sheet '{current_month_sheet_name}' not found. Please create a sheet named '{current_month_sheet_name}'.")
                    worksheet = None

                if worksheet:
                    # B열(2번째 열)의 데이터를 가져옴
                    all_users = worksheet.col_values(2)

                    if len(all_users) > 1:
                        # 2번째 줄부터 데이터 사용 (헤더 제외)
                        raw_users = all_users[1:]
                        users = [u for u in raw_users if u.strip()] # 빈 값 제거

                        if users:
                            selected_user = st.selectbox("Choose a user:", users)
                            st.success(f"User selected: {selected_user}")
                        else:
                            st.warning("Column B seems to be empty (excluding header).")
                    else:
                        st.warning("No data found in Column B. Please check the sheet.")

        except gspread.exceptions.SpreadsheetNotFound:
            st.error("❌ Spreadsheet not found. Please check the URL and make sure the service account has access.")
        except gspread.exceptions.APIError as e:
            st.error(f"❌ Google API Error: {e}")
            st.info("Tip: Did you enable 'Google Sheets API' and 'Google Drive API' in GCP Console?")
        except Exception as e:
            st.error(f"❌ Error loading sheet: {e}")
            st.info(f"Tip: Make sure to share the sheet with: {creds.service_account_email}")

st.divider()

# --- 이미지 업로드 및 OCR ---
st.subheader("2. Upload & Extract")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Uploaded Image.', use_container_width=True)

    st.write("")
    st.write("Extracting text...")

    if creds:
        client = get_vision_client(creds)

        content = uploaded_file.getvalue()
        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations

        if response.error.message:
            st.error(f"API Error: {response.error.message}")
        else:
            if texts:
                full_text = texts[0].description

                number_pattern = re.compile(r'\d+(\.\d+)?')
                found_numbers = []

                for match in number_pattern.finditer(full_text):
                    num_str = match.group()
                    if num_str not in found_numbers:
                        found_numbers.append(num_str)

                if found_numbers:
                    st.success(f"Found {len(found_numbers)} numbers.")
                    selected_number = st.selectbox("Select distance/time:", found_numbers)

                    if st.button("Save Log"):
                        if selected_user and worksheet:
                            try:
                                with st.spinner("Saving to Google Sheet..."):
                                    # 1. 사용자 행 찾기 (B열에서 검색)
                                    cell = worksheet.find(selected_user, in_column=2)

                                    if cell:
                                        user_row = cell.row

                                        # 2. 오늘 날짜(일)에 해당하는 열 계산
                                        # 4번째 열(D열)이 1일 -> 3 + day
                                        today = datetime.now()
                                        day = today.day
                                        target_col = 3 + day

                                        # 3. 데이터 업데이트
                                        worksheet.update_cell(user_row, target_col, selected_number)

                                        st.toast(f"Saved! {selected_user} - {today.strftime('%Y-%m-%d')}: {selected_number}", icon="✅")
                                        st.success(f"Successfully saved to row {user_row}, col {target_col} (Day {day})")
                                    else:
                                        st.error(f"Could not find user '{selected_user}' in the sheet.")
                            except Exception as e:
                                st.error(f"Save Error: {e}")
                        else:
                            st.error("Please select a user first or check sheet connection.")
                else:
                    st.warning("No numbers found.")
            else:
                st.warning("No text detected.")
    else:
        st.warning("GCP credentials not found.")
