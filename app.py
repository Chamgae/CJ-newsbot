import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

# --- 페이지 설정 ---
st.set_page_config(
    page_title="네이버 뉴스 텍스트 추출기",
    page_icon="📰",
    layout="centered"
)

# --- 크롤링 함수 ---
def get_naver_news_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. 제목 추출
        title_element = soup.select_one("#title_area span") or soup.select_one(".media_end_head_headline")
        title = title_element.get_text(strip=True) if title_element else "제목을 찾을 수 없음"
        
        # 2. 날짜 추출
        date_element = soup.select_one(".media_end_head_info_datestamp_time")
        date = date_element.get_text(strip=True) if date_element else "날짜 정보 없음"
        
        # 3. 본문 추출
        content_element = soup.select_one("#dic_area") or soup.select_one("#newsct_article")
        
        if content_element:
            # 불필요한 요소 제거
            for useless in content_element.select(".img_desc, .media_end_summary"):
                useless.extract()
            
            # 텍스트 정리
            content = content_element.get_text(separator="\n")
            content = re.sub(r'\n\s+\n', '\n\n', content)
            content = content.strip()
        else:
            content = "본문을 찾을 수 없습니다."

        return {
            "title": title,
            "date": date,
            "content": content,
            "url": url
        }

    except Exception as e:
        return {"error": str(e)}

# --- UI 구성 ---
st.title("📰 네이버 뉴스 텍스트 추출기")
st.markdown("네이버 뉴스 링크를 입력하면 **제목, 날짜, 본문**만 깔끔하게 가져옵니다.")

url_input = st.text_input("뉴스 기사 URL을 붙여넣으세요:", placeholder="https://n.news.naver.com/...")

if st.button("내용 가져오기", type="primary"):
    if not url_input:
        st.warning("URL을 입력해주세요!")
    else:
        with st.spinner("기사 내용을 가져오는 중입니다..."):
            result = get_naver_news_content(url_input)

        if "error" in result:
            st.error(f"오류가 발생했습니다: {result['error']}")
        else:
            st.success("추출 완료!")
            st.divider()
            st.subheader(result['title'])
            st.caption(f"입력일: {result['date']}")
            st.text_area("기사 본문", value=result['content'], height=500)
            st.info("오른쪽 위의 아이콘을 누르면 복사할 수 있습니다.")
