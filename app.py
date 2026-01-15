import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

st.title("# CRC (COOL RUNNING CREW) RUNNING LOG")
st.write("- upload running log image files")

# 이미지 업로드 위젯
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 이미지 열기 및 화면 표시
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image.', use_container_width=True)
    
    st.write("")
    st.write("Extracting text...")

    # EasyOCR 리더 초기화 (한국어, 영어 지원)
    reader = easyocr.Reader(['ko', 'en'], gpu=False) 
    
    # 이미지를 numpy 배열로 변환
    image_np = np.array(image)
    
    # 텍스트 추출
    result = reader.readtext(image_np)
    
    # 결과 출력
    st.subheader("Extracted Distance (km):")
    
    # 패턴: 숫자(정수/소수) 뒤에 선택적으로 공백이 있고 'km' 또는 'k'가 오는 경우 (대소문자 무시)
    # 그룹 1: 숫자 부분 (\d+(\.\d+)?)
    # 그룹 3: 단위 부분 (km|k)
    km_pattern = re.compile(r'(\d+(\.\d+)?)\s*(km|k)', re.IGNORECASE)
    
    found_numbers = []
    print("\n--- Extraction Started ---")
    
    for (bbox, text, prob) in result:
        clean_text = text.strip()
        print(f"[DEBUG] Raw text: '{clean_text}' (Prob: {prob:.2f})")
        
        # 패턴 매칭
        for match in km_pattern.finditer(clean_text):
            num_str = match.group(1) # 첫 번째 그룹(숫자)만 추출
            found_numbers.append(num_str)
            st.write(f"Distance: {num_str} km (from '{clean_text}')")
            print(f"[LOG] Found distance: {num_str} km (from '{clean_text}')")
            
    if not found_numbers:
        st.write("No distance found.")
        print("[LOG] No distance found.")
    
    print("--- Extraction Finished ---\n")
