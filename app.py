import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(
    page_title="홍보팀 뉴스 통합 수집기",
    page_icon="📰",
    layout="wide"
)

# --- 1. 뉴스 상세 내용 가져오기 (본문 추출) ---
def get_news_content(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 제목 추출
        title = soup.select_one("#title_area span") or soup.select_one(".media_end_head_headline")
        title = title.get_text(strip=True) if title else ""
        
        # 날짜 추출
        date = soup.select_one(".media_end_head_info_datestamp_time")
        date = date.get_text(strip=True) if date else ""
        
        # 언론사 추출
        press = soup.select_one(".media_end_linked_more_point")
        press = press.get_text(strip=True) if press else ""
        
        # 본문 추출
        content = soup.select_one("#dic_area") or soup.select_one("#newsct_article")
        if content:
            # 이미지 설명, 요약 등 불필요한 태그 제거
            for tag in content.select(".img_desc, .media_end_summary, .guide_text"):
                tag.extract()
            body = content.get_text(separator="\n").strip()
        else:
            body = "본문 추출 실패"
            
        return {
            "작성일": date,
            "언론사": press,
            "제목": title,
            "본문": body,
            "링크": url
        }
    except Exception:
        return None

# --- 2. 검색 결과 리스트 크롤링 ---
def crawl_naver_news(keyword, start_date, end_date, max_pages):
    results = []
    
    # 네이버 검색 날짜 포맷 변환
    sd_dot = start_date.strftime("%Y.%m.%d")
    ed_dot = end_date.strftime("%Y.%m.%d")
    sd_raw = start_date.strftime("%Y%m%d")
    ed_raw = end_date.strftime("%Y%m%d")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 진행 상황 표시바
    bar = st.progress(0)
    status = st.empty()
    
    for i in range(max_pages):
        # 진행률 업데이트
        status.text(f"🔍 {i+1}페이지 검색 중... (현재 {len(results)}건 수집됨)")
        bar.progress((i + 1) / max_pages)
        
        # 네이버 뉴스 검색 URL 생성
        start_idx = i * 10 + 1
        url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={sd_dot}&de={ed_dot}&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so%3Ar%2Cp%3Afrom{sd_raw}to{ed_raw}&is_sug_officeid=0&office_category=0&service_area=0&start={start_idx}"
        
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 기사 리스트 가져오기
        articles = soup.select("div.news_wrap")
        
        if not articles:
            break # 기사가 더 없으면 중단
        
        for article in articles:
            # 네이버 뉴스 인링크(n.news.naver.com)만 필터링
            links = article.select("a.info")
            for link in links:
                href = link.attrs.get("href", "")
                if "n.news.naver.com" in href:
                    # 상세 내용 크롤링
                    data = get_news_content(href)
                    if data:
                        results.append(data)
                    break # 동일 기사는 한 번만 처리
        
        time.sleep(1) # 차단 방지를 위해 1초 대기
        
    bar.empty()
    status.empty()
    return pd.DataFrame(results)

# --- UI 화면 구성 ---
st.title("🗞️ 홍보팀 뉴스 통합 수집기")
st.markdown("특정 기간의 키워드 뉴스를 검색하여 **엑셀(CSV)**로 다운로드합니다.")

# 입력창 배치
col1, col2 = st.columns([3, 1])
keyword = col1.text_input("검색 키워드", placeholder="예: 삼성전자, ESG 경영")
pages = col2.number_input("검색할 페이지 수 (1페이지=10건)", min_value=1, max_value=50, value=3)

col3, col4 = st.columns(2)
s_date = col3.date_input("시작일", value=datetime.now() - timedelta(days=1))
e_date = col4.date_input("종료일", value=datetime.now())

# 실행 버튼
if st.button("뉴스 수집 및 엑셀 변환", type="primary"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("뉴스를 수집하고 있습니다..."):
            df = crawl_naver_news(keyword, s_date, e_date, pages)
            
        if df.empty:
            st.error("수집된 뉴스가 없습니다. 기간이나 키워드를 확인해주세요.")
        else:
            st.success(f"완료! 총 {len(df)}건의 기사를 수집했습니다.")
            
            # 데이터 미리보기
            st.dataframe(df)
            
            # 엑셀(CSV) 다운로드 버튼
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 엑셀(CSV) 다운로드",
                data=csv,
                file_name=f"{keyword}_뉴스모니터링.csv",
                mime="text/csv"
            )
