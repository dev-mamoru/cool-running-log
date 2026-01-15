import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import io
import re
import json

st.title("# CRC (COOL RUNNING CREW) RUNNING LOG")
st.write("- upload running log image files")

# Streamlit Secrets에서 GCP 키 로드 함수
def get_vision_client():
    try:
        # secrets.toml 파일에 gcp_service_account 섹션이 있어야 함
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(key_dict)
        client = vision.ImageAnnotatorClient(credentials=creds)
        return client
    except Exception as e:
        st.error(f"GCP Credentials Error: {e}")
        return None

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 이미지 표시
    st.image(uploaded_file, caption='Uploaded Image.', use_container_width=True)
    
    st.write("")
    st.write("Extracting text with Google Cloud Vision API...")

    client = get_vision_client()
    
    if client:
        # 이미지를 바이트로 읽기
        content = uploaded_file.getvalue()
        image = vision.Image(content=content)

        # 텍스트 감지 요청
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if response.error.message:
            st.error(f"API Error: {response.error.message}")
        else:
            # 첫 번째 요소는 전체 텍스트입니다.
            if texts:
                full_text = texts[0].description
                st.text_area("Raw Extracted Text", full_text, height=150)
                
                # km 패턴 찾기
                km_pattern = re.compile(r'(\d+(\.\d+)?)\s*(km|k)', re.IGNORECASE)
                found_numbers = []
                
                print("\n--- Extraction Started ---")
                
                # 전체 텍스트에서 검색
                for match in km_pattern.finditer(full_text):
                    num_str = match.group(1)
                    found_numbers.append(num_str)
                    st.success(f"Found Distance: {num_str} km")
                    print(f"[LOG] Found: {num_str} km")
                
                if not found_numbers:
                    st.warning("No distance (km) found in the text.")
                    print("[LOG] No distance found.")
                    
                print("--- Extraction Finished ---\n")
            else:
                st.warning("No text detected.")
    else:
        st.warning("Please configure GCP credentials in .streamlit/secrets.toml")
