import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="네이버 뉴스 텍스트 추출기", page_icon="📰", layout="centered")

def get_naver_news_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.select_one("#title_area span") or soup.select_one(".media_end_head_headline")
        title = title.get_text(strip=True) if title else "제목 없음"
        date = soup.select_one(".media_end_head_info_datestamp_time")
        date = date.get_text(strip=True) if date else "날짜 없음"
        content = soup.select_one("#dic_area") or soup.select_one("#newsct_article")
        if content:
            for useless in content.select(".img_desc, .media_end_summary"): useless.extract()
            text = content.get_text(separator="\n")
            text = re.sub(r'\n\s+\n', '\n\n', text).strip()
        else: text = "본문 없음"
        return {"title": title, "date": date, "content": text}
    except Exception as e: return {"error": str(e)}

st.title("📰 네이버 뉴스 텍스트 추출기")
url = st.text_input("URL 입력:")
if st.button("가져오기") and url:
    res = get_naver_news_content(url)
    if "error" in res: st.error(res["error"])
    else:
        st.subheader(res['title'])
        st.text_area("본문", value=res['content'], height=500)

### 2. `requirements.txt`
아래 3줄을 복사하세요.
streamlit
requests
beautifulsoup4

### 3. `README.md`
아래 내용을 복사하세요.
# 네이버 뉴스 추출기
URL을 입력하면 본문만 추출합니다.

이제 내용이 보이시나요? 만약 그래도 안 보인다면 브라우저를 새로고침 해보시는 것을 추천드립니다.
