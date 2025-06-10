import streamlit as st
from PIL import Image
import pytesseract
import requests
import openai
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# Cloud용 tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# TLS 버전 강제 설정 위한 커스텀 Adapter
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        # TLS 1.0, 1.1 비활성화하고 TLS 1.2 이상만 허용
        ctx.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx,
        )

# 사이드바 - API 키 입력
st.sidebar.title("API 키 입력")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
drug_api_key = st.sidebar.text_input("공공데이터 API Key", type="password")

if not openai_key or not drug_api_key:
    st.warning("OpenAI와 공공데이터 API 키를 모두 입력해주세요.")
    st.stop()

st.title("약사봇 - 약 사진으로 복용 정보 확인")

uploaded_file = st.file_uploader("약 사진을 업로드하세요 (jpg, jpeg, png)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 약 사진", use_container_width=True)


    text = pytesseract.image_to_string(image, lang="eng+kor")
    st.text_area("OCR 결과 (인식된 텍스트)", text, height=150)

    query = text.strip().split("\n")[0]
    st.write(f"인식된 약 이름(첫 줄): {query}")

    if st.button("약 정보 조회 및 GPT 설명"):
        api_url = f"https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList?serviceKey={drug_api_key}&itemName={query}&type=json"

        try:
            session = requests.Session()
            session.mount("https://", TLSAdapter())

            response = session.get(api_url, verify=True)
            if response.ok:
                data = response.json()
                items = data.get("body", {}).get("items", [])

                if items:
                    item = items[0]
                    st.subheader(f"약 이름: {item.get('itemName', '정보 없음')}")
                    st.write(f"효능: {item.get('efcyQesitm', '정보 없음')}")
                    st.write(f"주의사항: {item.get('useMethodQesitm', '정보 없음')}")

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
