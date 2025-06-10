import streamlit as st
from PIL import Image
import pytesseract
import requests
import openai

# Cloud용 tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# API 키 입력
st.sidebar.title("API 키 입력")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
drug_api_key = st.sidebar.text_input("공공데이터 API Key", type="password")

if not openai_key or not drug_api_key:
    st.warning("API 키를 입력하세요.")
    st.stop()

uploaded_file = st.file_uploader("약 사진 업로드", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 이미지", use_column_width=True)
    text = pytesseract.image_to_string(image, lang="eng+kor")
    st.text_area("OCR 결과", text, height=150)

    if st.button("약 정보 분석"):
        st.write("📦 약 이름으로 공공 API 조회 중...")
        # 예시: 공공 API에서 검색
        query = text.strip().split("\n")[0]
        api_url = f"https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList?serviceKey={drug_api_key}&itemName={query}&type=json"
        response = requests.get(api_url)
        if response.ok:
            items = response.json().get("body", {}).get("items", [])
            if items:
                item = items[0]
                st.subheader(item["itemName"])
                prompt = f"다음은 약 정보입니다: {item['efcyQesitm']}\n이 약의 복용 주의사항을 요약해줘."
                openai.api_key = openai_key
                chat = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.info(chat.choices[0].message["content"])
            else:
                st.error("약 정보를 찾을 수 없습니다.")
        else:
            st.error("API 요청 실패")
