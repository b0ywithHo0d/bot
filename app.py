import streamlit as st
from PIL import Image
import pytesseract
import requests
from openai import OpenAI
import urllib.parse

# Tesseract 경로 (Streamlit Cloud에서는 주석처리 가능)
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# 🔐 API 키 입력
st.sidebar.title("API 키 입력")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
drug_api_key = st.sidebar.text_input("공공데이터 API Key", type="password")

st.title("💊 약사봇: 사진 한 장으로 약 정보 확인")

uploaded_file = st.file_uploader("약 사진을 업로드하세요", type=["png", "jpg", "jpeg"])

if uploaded_file and openai_key and drug_api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드한 이미지", use_container_width=True)

    with st.spinner("이미지에서 텍스트 추출 중..."):
        extracted_text = pytesseract.image_to_string(image)
        st.subheader("📝 OCR 추출 결과")
        st.write(extracted_text)

    # 약 이름 추출 시도 (단순히 첫 단어 기준으로)
    drug_name = extracted_text.strip().split()[0]
    st.info(f"인식된 약 이름: `{drug_name}`")

    # 공공데이터포털 API 호출
    encoded_drug_name = urllib.parse.quote(drug_name)
    api_url = f"http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
    params = {
        "serviceKey": drug_api_key,
        "itemName": encoded_drug_name,
        "type": "json"
    }

    try:
        with st.spinner("약 정보를 조회 중..."):
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            if 'body' in data['response'] and 'items' in data['response']['body']:
                item = data['response']['body']['items'][0]
                efcy = item.get('efcyQesitm', '효능 정보 없음')
                use_method = item.get('useMethodQesitm', '복용법 정보 없음')
                interact = item.get('intrcQesitm', '상호작용 정보 없음')
                st.subheader("📦 기본 약 정보")
                st.write(f"**효능:** {efcy}")
                st.write(f"**복용 방법:** {use_method}")
                st.write(f"**상호작용:** {interact}")
            else:
                st.warning("약 정보를 찾을 수 없습니다.")

            # GPT 요약
            client = OpenAI(api_key=openai_key)
            prompt = f"이 약의 이름은 {drug_name}이며, 효능은 {efcy}, 복용 방법은 {use_method}, 상호작용은 {interact}입니다. 이 정보를 일반 사용자가 이해하기 쉽게 요약해주세요."

            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            summary = chat_completion.choices[0].message.content
            st.subheader("🧠 요약 설명 (GPT)")
            st.write(summary)

    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 중 오류 발생: {e}")

else:
    st.warning("API 키와 이미지를 모두 입력하세요.")
