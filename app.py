import streamlit as st
from PIL import Image
import pytesseract
import requests
import openai
import os

# === 설정 ===
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
DRUG_API_KEY = st.secrets.get("DRUG_API_KEY", os.getenv("DRUG_API_KEY"))

# === OCR 함수 ===
def extract_text_from_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image, lang="kor").strip()

# === 공공데이터 포털 API 호출 ===
def search_drug_info_by_name(drug_name: str, api_key: str) -> dict:
    url = "https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
    params = {
        "serviceKey": api_key,
        "itemName": drug_name,
        "type": "json",
        "numOfRows": 1,
        "pageNo": 1
    }
    res = requests.get(url, params=params)
    data = res.json()
    if data.get("body") and data["body"].get("items"):
        return data["body"]["items"][0]
    else:
        return {"error": "약 정보를 찾을 수 없습니다."}

# === GPT 요약 함수 ===
def generate_gpt_guidance(drug_info: dict) -> str:
    summary = f"""
    효능: {drug_info.get('efcyQesitm', '정보 없음')}
    복용법: {drug_info.get('useMethodQesitm', '정보 없음')}
    주의사항: {drug_info.get('atpnQesitm', '정보 없음')}
    부작용: {drug_info.get('seQesitm', '정보 없음')}
    병용금기: {drug_info.get('intrcQesitm', '정보 없음')}
    """
    messages = [
        {"role": "system", "content": "너는 약사야. 사용자가 복용할 약 정보를 친절하고 쉽게 설명해줘."},
        {"role": "user", "content": f"이 약 정보를 사용자에게 알기 쉽게 설명해줘:\n{summary}"}
    ]
    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    return response["choices"][0]["message"]["content"]

# === Streamlit UI ===
st.set_page_config(page_title="약사봇", page_icon="💊")
st.title("💊 약사봇 - 사진으로 약 분석하기")

uploaded_file = st.file_uploader("📸 약 성분이 적힌 사진을 올려주세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드한 이미지", use_column_width=True)

    with st.spinner("🧠 텍스트 인식 중..."):
        text = extract_text_from_image(image)
        st.write("🔤 인식된 텍스트:", text)

    with st.spinner("💊 의약품 정보 확인 중..."):
        drug_info = search_drug_info_by_name(text, DRUG_API_KEY)
        if "error" in drug_info:
            st.error(drug_info["error"])
        else:
            st.subheader("📋 의약품 기본 정보")
            st.write("**효능**:", drug_info["efcyQesitm"])
            st.write("**복용법**:", drug_info["useMethodQesitm"])
            st.write("**주의사항**:", drug_info["atpnQesitm"])

            with st.spinner("🤖 AI 설명 생성 중..."):
                gpt_text = generate_gpt_guidance(drug_info)
                st.subheader("👩‍⚕️ 복용 안내 (AI 설명)")
                st.write(gpt_text)
