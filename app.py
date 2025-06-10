import streamlit as st
from PIL import Image
import pytesseract
import requests
import openai
import urllib3

# SSL 경고 무시 (verify=False 쓸 때 필요)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cloud 환경 tesseract 경로 설정 (Streamlit Cloud 기준)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# 사이드바 - API 키 입력
st.sidebar.title("API 키 입력")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
drug_api_key = st.sidebar.text_input("공공데이터 API Key", type="password")

# API 키 없으면 경고 후 실행 중단
if not openai_key or not drug_api_key:
    st.warning("OpenAI와 공공데이터 API 키를 모두 입력해주세요.")
    st.stop()

st.title("약사봇 - 약 사진으로 복용 정보 확인")

# 이미지 업로드 UI
uploaded_file = st.file_uploader("약 사진을 업로드하세요 (jpg, jpeg, png)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 이미지 보여주기
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 약 사진", use_column_width=True)

    # OCR 처리
    text = pytesseract.image_to_string(image, lang="eng+kor")
    st.text_area("OCR 결과 (인식된 텍스트)", text, height=150)

    # 약 이름 추출 (간단히 첫 줄)
    query = text.strip().split("\n")[0]
    st.write(f"인식된 약 이름(첫 줄): {query}")

    if st.button("약 정보 조회 및 GPT 설명"):
        # 공공데이터 API URL 구성
        api_url = f"https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList?serviceKey={drug_api_key}&itemName={query}&type=json"

        try:
            # 공공데이터 API 호출 (SSL 검증 끔)
            response = requests.get(api_url, verify=False)
            if response.ok:
                data = response.json()
                items = data.get("body", {}).get("items", [])

                if items:
                    item = items[0]  # 첫 번째 약 정보 사용
                    st.subheader(f"약 이름: {item.get('itemName', '정보 없음')}")
                    st.write(f"효능: {item.get('efcyQesitm', '정보 없음')}")
                    st.write(f"주의사항: {item.get('useMethodQesitm', '정보 없음')}")

                    # GPT에게 효능 설명 요청
                    openai.api_key = openai_key
                    prompt = f"다음 약 효능에 대해 쉽게 설명해줘:\n{item.get('efcyQesitm', '')}"

                    completion = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=300,
                        temperature=0.7,
                    )

                    explanation = completion.choices[0].message["content"]
                    st.info(f"GPT 설명:\n{explanation}")

                else:
                    st.error("약 정보를 찾을 수 없습니다. 약 이름을 다시 확인해주세요.")
            else:
                st.error(f"공공데이터 API 요청 실패: 상태 코드 {response.status_code}")
        except Exception as e:
            st.error(f"API 호출 중 오류 발생: {e}")
