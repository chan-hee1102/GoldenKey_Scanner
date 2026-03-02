import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta, timezone
import os
import re
import json
import random
import google.generativeai as genai
from urllib.parse import quote

# --- [1] 페이지 기본 설정 ---
st.set_page_config(layout="wide", page_title="Golden Key Pro | 퀀트 대시보드")

# ==========================================
# 🛡️ [Security] Gemini API 키 및 모델 엔진 설정
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
    except:
        model = None
else:
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
    model = None

# ==========================================
# 🎨 [UI/UX] 딥 차콜 다크 모드 커스텀 CSS (최고급 퀀트 터미널 룩)
# ==========================================
st.markdown(
    """
    <style>
    /* 웹 폰트 (Pretendard & Inter) */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', 'Inter', sans-serif;
    }

    /* 🌟 전체 배경 (깊이 있는 차콜 블랙) */
    .stApp {
        background-color: #0f1115 !important;
    }
    
    /* 기본 텍스트 색상 화이트로 변경 */
    p, h1, h2, h3, h4, h5, h6, span, div {
        color: #e2e8f0;
    }

    /* 🌟 상단 타이틀 고급화 (사이버틱한 네온 그라데이션) */
    .main-title {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
        letter-spacing: -0.02em;
    }
    .sub-title {
        font-size: 1rem;
        color: #94a3b8 !important;
        font-weight: 500;
        margin-bottom: 25px;
    }

    /* 🌟 핵심 CTA 버튼 디자인 (빛나는 네온 블루) */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white !important;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 1.05rem;
        font-weight: 700;
        box-shadow: 0 0 15px rgba(37, 99, 235, 0.4);
        transition: all 0.2s ease-in-out;
        width: 100%;
        margin-bottom: 15px;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.6);
        transform: translateY(-2px);
    }
    div.stButton > button:first-child p {
        font-size: 1.05rem;
        font-weight: 700;
        color: white !important;
    }

    /* 🌟 시장 브리핑 박스 (다크 글래스 느낌) */
    .briefing-box {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 4px solid #60a5fa;
        padding: 20px 24px;
        border-radius: 10px;
        margin-bottom: 25px;
        font-size: 1rem;
        color: #cbd5e1 !important;
        line-height: 1.6;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .briefing-title {
        font-weight: 800;
        font-size: 1.15rem;
        color: #f8fafc !important;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 🌟 실시간 주도주 리스트 카드 (다크 패널) */
    .stock-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(255,255,255,0.05);
        border-left: 4px solid #475569;
        transition: transform 0.1s ease, box-shadow 0.1s ease;
    }
    .stock-card:hover {
        transform: translateX(3px);
        background: #27354f;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
    }

    .left-zone { display: flex; align-items: center; gap: 10px; flex: 0 1 auto; }
    .center-zone { display: flex; align-items: center; gap: 6px; flex: 0 1 auto; margin-left: 15px; flex-wrap: wrap; }
    .right-zone { display: flex; align-items: center; gap: 18px; flex: 1; justify-content: flex-end; }

    .stock-name { font-weight: 800; font-size: 1.15rem; color: #f8fafc !important; white-space: nowrap; letter-spacing: -0.01em; }
    
    .market-tag { 
        font-size: 0.65rem; 
        font-weight: 800; 
        padding: 3px 6px; 
        border-radius: 6px;
        white-space: nowrap;
    }
    .market-kospi { background-color: rgba(59, 130, 246, 0.2); color: #93c5fd !important; border: 1px solid rgba(59, 130, 246, 0.3); }
    .market-kosdaq { background-color: rgba(239, 68, 68, 0.15); color: #fca5a5 !important; border: 1px solid rgba(239, 68, 68, 0.3); }

    /* 🌟 테마 뱃지 (글래스모피즘 네온 스타일) */
    .sector-badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.05);
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        white-space: nowrap;
    }
    
    /* 등락률에 따른 보더 하이라이트 (파이썬 코드에서 인라인 스타일로 오버라이드 됨) */

    /* 🌟 지수 폰트 슬림화 및 다크모드 전용 쨍한 등락 색상 */
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 800 !important; color: #f8fafc !important; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; font-weight: 600 !important; color: #94a3b8 !important; margin-bottom: -2px !important; }
    
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Up"] { color: #ff4d4d !important; fill: #ff4d4d !important; }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Up"]) > div { color: #ff4d4d !important; font-weight: 800 !important; text-shadow: 0 0 8px rgba(255,77,77,0.4); }
    
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Down"] { color: #3b82f6 !important; fill: #3b82f6 !important; }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Down"]) > div { color: #3b82f6 !important; font-weight: 800 !important; text-shadow: 0 0 8px rgba(59,130,246,0.4); }

    /* 🌟 우측 주도 섹터 아코디언(Expander) 다크모드화 */
    div[data-testid="stExpander"] { 
        border: 1px solid rgba(255,255,255,0.08) !important; 
        border-radius: 8px !important; 
        background: #1e293b !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stExpander"] summary { 
        padding: 10px 15px !important; 
        background-color: #161e2e !important; 
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary p { font-weight: 800 !important; font-size: 0.95rem !important; color: #e2e8f0 !important; }
    div[data-testid="stExpander"] summary svg { color: #94a3b8 !important; } /* 화살표 아이콘 색상 */
    
    .sector-item {
        font-size: 0.9rem;
        color: #cbd5e1 !important;
        padding: 8px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed rgba(255,255,255,0.1);
        width: 100%;
    }
    .sector-item:last-child { border-bottom: none; }

    .sector-item-left { display: flex; align-items: center; flex: 1; overflow: hidden; }
    .sector-stock-name { font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #f8fafc !important;}
    .sector-item-right { display: flex; align-items: center; justify-content: flex-end; }
    
    .val-rate { width: 65px; text-align: right; font-weight: 800; margin-right: 12px; }
    .val-vol { width: 75px; text-align: right; color: #64748b !important; font-size: 0.8rem; font-weight: 600; }

    .leader-label {
        font-size: 0.65rem;
        background: #ef4444;
        color: white !important;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 8px;
        flex-shrink: 0;
        font-weight: 800;
        box-shadow: 0 0 5px rgba(239, 68, 68, 0.5);
    }

    /* 사이드바 테마 아이템 스타일 (다크 카드형) */
    .sidebar-theme-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 8px;
        font-weight: 700;
        background: #1e293b;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* 탭 메뉴 디자인 및 글자색 방어 */
    button[data-baseweb="tab"] {
        font-family: 'Pretendard', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        color: #94a3b8 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #f8fafc !important;
    }
    
    /* 마크다운 내부 텍스트 색상 강제 오버라이드 방어 */
    .stMarkdown p { color: #cbd5e1; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 🌟 세션 상태(Session State) 초기화
# ==========================================
if 'global_indices' not in st.session_state: st.session_state.global_indices = []
if 'global_themes' not in st.session_state: st.session_state.global_themes = []
if 'global_briefing' not in st.session_state: st.session_state.global_briefing = "글로벌 스캔을 실행해주세요."
if 'domestic_df' not in st.session_state: st.session_state.domestic_df = pd.DataFrame()
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = []
if 'market_briefing' not in st.session_state: st.session_state.market_briefing = "" 
if 'news_payload' not in st.session_state: st.session_state.news_payload = {} 

# ==========================================
# 🌟 전역 설정 (섹터 색상 동기화 및 헬퍼 함수)
# ==========================================
# 다크모드에서는 배경을 통일하고 테두리/글자색으로 포인트를 주는 것이 예쁨
def get_sector_style(sector_name):
    # (글자색, 테두리색) 매핑
    color_map = {
        '반도체': ('#93c5fd', '#3b82f6'), '로봇/AI': ('#c4b5fd', '#8b5cf6'), 
        '2차전지': ('#6ee7b7', '#10b981'), '배터리': ('#6ee7b7', '#10b981'),
        '전력': ('#fde047', '#eab308'), '신재생에너지': ('#fde047', '#eab308'), 
        '바이오': ('#fca5a5', '#ef4444'), 
        '방산': ('#cbd5e1', '#64748b'), '우주항공': ('#cbd5e1', '#64748b'), 
        '스페이스X': ('#d8b4fe', '#a855f7'),
        '금융/지주': ('#d1d5db', '#64748b'), '자동차': ('#7dd3fc', '#3b82f6'), 
        '현대차그룹': ('#67e8f9', '#06b6d4'), '철강': ('#94a3b8', '#475569')
    }
    
    for key, (text_c, border_c) in color_map.items():
        if key in sector_name and '개별주' not in sector_name:
            return f"color: {text_c} !important; border-color: {border_c}; background: rgba({int(border_c[1:3], 16)}, {int(border_c[3:5], 16)}, {int(border_c[5:7], 16)}, 0.1);"
            
    # 개별주 및 기타 디폴트 (회색 네온)
    return "color: #94a3b8 !important; border-color: #475569; background: rgba(71, 85, 105, 0.1);"

def force_list(val):
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        if len(val) > 1 and all(len(str(x)) == 1 for x in val):
            return ["".join(str(x) for x in val)]
        return [str(x) for x in val]
    return ["개별주"]

# --- [2] 미 증시 엔진 ---

def get_kst_time():
    return datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')

def fetch_sox_stable():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = "https://" + "finance.naver.com/world/"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'tbl_exchange'})
        for row in table.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) > 3 and "필라델피아 반도체" in tds[0].text:
                rate_text = tds[3].text.strip().replace(' ', '')
                return tds[1].text.strip(), rate_text
        return None, None
    except: return None, None

def fetch_robust_finance(ticker):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        url = "https://" + f"finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(res.text, 'html.parser')
        val_tag = soup.find("fin-streamer", {"data-field": "regularMarketPrice"})
        rate_tag = soup.find("fin-streamer", {"data-field": "regularMarketChangePercent"})
        if val_tag and val_tag.text != "0.00" and val_tag.text != "":
            rate_text = rate_tag.text.strip().replace('(', '').replace(')', '')
            if not rate_text.startswith('-') and not rate_text.startswith('+') and rate_text != "0.00%":
                rate_text = f"+{rate_text}"
            return val_tag.text, rate_text
    except: pass
    try:
        google_ticker = ticker.replace('^', '.')
        mkt = "INDEXNASDAQ" if "NDX" in ticker or "SOX" in ticker else "INDEXSP"
        if "DJI" in ticker: mkt = "INDEXDJX"
        g_url = "https://" + f"www.google.com/finance/quote/{google_ticker}:{mkt}"
        g_res = requests.get(g_url, headers=headers, timeout=12)
        g_soup = BeautifulSoup(g_res.text, 'html.parser')
        g_val = g_soup.select_one(".YMlKec.fxKb9b").text
        g_rate = g_soup.select_one(".Jw796").text.replace('(', '').replace(')', '').strip()
        if not g_rate.startswith('-') and not g_rate.startswith('+') and g_rate != "0.00%":
            g_rate = f"+{g_rate}"
        if g_val: return g_val, g_rate
    except: pass
    return "N/A", "0.00%"

def get_global_market_status():
    indices = []
    themes = []
    idx_map = {"나스닥 100": "^NDX", "S&P 500": "^GSPC", "다우존스": "^DJI"}
    
    try:
        for name, tk in idx_map.items():
            v, r = fetch_robust_finance(tk)
            indices.append({"name": name, "value": v, "delta": r})
            time.sleep(0.2)
        
        sox_v, sox_r = fetch_sox_stable()
        if not sox_v: sox_v, sox_r = fetch_robust_finance("^SOX")
        indices.append({"name": "필라 반도체", "value": sox_v, "delta": sox_r})

        etf_map = [("반도체 (SOXX)", "SOXX", "반도체"), ("로봇/AI (BOTZ)", "BOTZ", "로봇/AI"), ("2차전지 (LIT)", "LIT", "2차전지"), ("전력망 (GRID)", "GRID", "전력/원전"), ("원자력 (URA)", "URA", "전력/원전"), ("바이오 (IBB)", "IBB", "바이오")]
        for name, tk, sector in etf_map:
            _, r_etf = fetch_robust_finance(tk)
            themes.append({"name": name, "delta": r_etf}) # color는 다크모드에서 html로 뺌
            time.sleep(0.2)
            
        st.session_state.global_indices = indices
        st.session_state.global_themes = themes
        st.session_state.global_briefing = f"최종 업데이트: {get_kst_time()}\n해외 지수 및 전력/원전 테마 복구가 완료되었습니다."
    except: st.session_state.global_briefing = "해외 서버 동기화 일시 지연 중"

# --- [3] 💡 종목 정밀 분석 엔진 (Gemini) ---

def fetch_stock_news_headlines(stock_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': "https://finance.naver.com/"
    }
    titles = []
    
    try:
        encoded_kw = quote(f"특징주 {stock_name}", encoding='euc-kr')
        fin_url = f"https://finance.naver.com/news/news_search.naver?q={encoded_kw}"
        res_fin = requests.get(fin_url, headers=headers, timeout=5)
        res_fin.encoding = 'euc-kr' 
        
        if res_fin.status_code == 200:
            soup_fin = BeautifulSoup(res_fin.text, 'html.parser')
            blocks = soup_fin.select("ul.newsList li dl, .newsList dl")
            if blocks:
                for blk in blocks:
                    t_tag = blk.select_one(".articleSubject a, .tit, dt a")
                    s_tag = blk.select_one(".articleSummary")
                    if t_tag:
                        title = t_tag.text.strip()
                        summary = s_tag.text.strip().replace('\n', ' ').replace('\t', '') if s_tag else ""
                        summary = re.sub(r'\|.*?$', '', summary).strip() 
                        if summary:
                            news_str = f"제목: {title} (내용: {summary})"
                        else:
                            news_str = f"제목: {title}"
                        if news_str not in titles:
                            titles.append(news_str)
            else:
                tags = soup_fin.select(".articleSubject a, .tit, dt a")
                for tag in tags:
                    text = tag.text.strip()
                    if text:
                        news_str = f"제목: {text}"
                        if news_str not in titles: titles.append(news_str)
    except: pass 

    if len(titles) < 3:
        try:
            daum_url = f"https://search.daum.net/search?w=news&q={quote('특징주 ' + stock_name)}"
            headers['Referer'] = "https://search.daum.net/"
            res_daum = requests.get(daum_url, headers=headers, timeout=5)
            if res_daum.status_code == 200:
                soup_daum = BeautifulSoup(res_daum.text, 'html.parser')
                blocks = soup_daum.select('.c-list-basic li, .wrap_cont')
                if blocks:
                    for blk in blocks:
                        t_tag = blk.select_one('.c-tit-doc, .tit_main, a.f_link_b')
                        s_tag = blk.select_one('.c-desc, .desc, .conts_desc')
                        if t_tag:
                            title = t_tag.text.strip()
                            summary = s_tag.text.strip().replace('\n', ' ').replace('\t', '') if s_tag else ""
                            if summary:
                                news_str = f"제목: {title} (내용: {summary})"
                            else:
                                news_str = f"제목: {title}"
                            if news_str not in titles:
                                titles.append(news_str)
                else:
                    for tag in soup_daum.select('.c-tit-doc, .tit_main, a.f_link_b'):
                        text = tag.text.strip()
                        if text:
                            news_str = f"제목: {text}"
                            if news_str not in titles: titles.append(news_str)
        except: pass

    if not titles:
        return ["[에러] 뉴스 검색 실패 또는 포털 서버 접근 차단됨"]
        
    return titles[:10]

def perform_batch_analysis(news_map):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return "API 키 누락", [{"종목명": "오류", "섹터": ["시스템"], "이유": "API 키가 설정되지 않았습니다.", "기사날짜": "-"}]
    
    try:
        generation_config = genai.types.GenerationConfig(temperature=0.1, top_p=0.8)
        analysis_model = genai.GenerativeModel('gemini-2.5-flash', generation_config=generation_config)
        
        prompt = f"""
        당신은 여의도 최고 수준의 프랍 트레이더이자 시장 트렌드 분석의 권위자입니다.
        아래 데이터는 오늘 시장에서 강한 수급(거래대금 상위 & 급등)이 들어온 주도주들의 뉴스 '제목'과 '본문 요약(내용)' 모음입니다.
        
        [데이터]
        {json.dumps(news_map, ensure_ascii=False)}
        
        [분석 지시사항 - 반드시 지킬 것]
        1. 대분류(Macro Theme) 강제 통일: 시장의 큰 숲을 보기 위해 동의어나 하위 테마는 반드시 아래의 '표준 테마 명칭'으로 통일하세요.
           - 태양광, 풍력, 재생에너지 -> 무조건 "신재생에너지"
           - 전력기기, 전선, 변압기 -> 무조건 "전력"
           - 전고체, LFP, 리튬, 배터리 -> 무조건 "2차전지"
           - 로봇 부품, 휴머노이드 -> 무조건 "로봇/AI"
        2. 기본 섹터 + 개별 재료 병기 룰: 종목이 근본적으로 속한 '큰 테마'가 있다면 먼저 적고, 만약 해당 기업만의 독자적인 특별 호재(신규상장, 특정 기업 계약, 편입 등)가 있다면 "호재내용(개별주)" 형태로 배열에 독립적으로 추가하세요.
           - ❌ 잘못된 예: ["신재생에너지/AI데이터센터 냉각"] (하나로 묶지 마세요)
           - ⭕ 올바른 예: ["신재생에너지", "AI 데이터센터 냉각(개별주)"]
           - ⭕ 올바른 예: ["바이오", "코스닥150 편입(개별주)"]
           - ⭕ 올바른 예: ["로봇/AI", "대규모 공급계약(개별주)"]
        3. 개별주 처리: 시장 주도 테마(섹터)에 전혀 속하지 않는 완전한 독자적 호재만 있다면 "핵심이유(개별주)" 만 적으세요. 
           - ⭕ 올바른 예: ["성수동 부지 개발(개별주)"]
        4. 시장 주도장세 브리핑 작성 (Macro 분석): 1~3번에서 추출한 40개 종목의 태그들을 종합적으로 살펴보고, 오늘 어떤 테마들에 자금이 가장 많이 쏠렸는지(교집합이 많은 태그) 분석하여 "오늘 시장은 [A] 테마와 [B] 관련주가 시장을 이끌고 있습니다." 형태의 트레이더 브리핑을 2~3줄로 작성하세요. (단, '(개별주)' 태그는 시장 주도 테마가 아니므로 브리핑에서 메인으로 언급하지 마세요)
        5. 사고의 사슬 (Chain of Thought): 종목별 태마를 결정하기 전, '분석과정' 필드에 뉴스 내용을 바탕으로 왜 이 태그들을 선정했는지 1~2줄로 먼저 추론하세요.
        6. 출력 형식: 반드시 아래 예시와 같은 구조의 순수 JSON 포맷으로만 응답하세요. (마크다운 백틱 억제)
        
        [예시 포맷]
        {{
          "시장브리핑": "오늘 시장은 현대차그룹의 모멘텀에 따른 로봇/AI 섹터와, 스페이스X 수혜를 입은 테마에 강한 매수세가 집중되고 있습니다. 그 외 개별 호재를 동반한 종목들이 각개전투 중입니다.",
          "종목분석": [
            {{
              "종목명": "현대차", 
              "분석과정": "뉴스의 핵심은 새만금 투자와 AI·로봇 거점 추진임. 그룹 차원의 모멘텀과 로봇 산업 진출이 겹치므로 독립된 두 개의 표준 태그로 분리함.",
              "섹터": ["현대차그룹", "로봇/AI"], 
              "이유": "새만금 투자 및 로봇 거점 추진 기대감"
            }},
            {{
              "종목명": "에임드바이오", 
              "분석과정": "코스닥 150 신규 편입이라는 강력한 개별 호재가 주가를 이끌고 있음. 근본 섹터가 바이오이므로 병기함.",
              "섹터": ["바이오", "코스닥150 편입(개별주)"], 
              "이유": "코스닥150 지수 신규 편입 기대감"
            }},
            {{
              "종목명": "신성이엔지", 
              "분석과정": "재생에너지 호재와 AI 데이터센터 냉각 호재가 겹침. '태양광/재생에너지'는 표준명칭인 '신재생에너지'로 통일하고 개별 호재를 병기함.",
              "섹터": ["신재생에너지", "AI 데이터센터 냉각(개별주)"], 
              "이유": "재생에너지 수혜 및 AI 데이터센터 냉각 기대감"
            }},
            {{
              "종목명": "대원전선", 
              "분석과정": "AI 열풍에 따른 전력 인프라 수요 증가가 핵심. '전선'이나 '전력기기' 대신 대분류인 '전력'으로 통일함.",
              "섹터": ["전력"], 
              "이유": "AI 전력 수요 급증 및 전력 인프라 투자 확대 기대감"
            }},
            {{
              "종목명": "삼표시멘트", 
              "분석과정": "성수동 부지 개발 기대감이 핵심 호재임. 주도 테마가 아닌 개별 호재이므로 개별주로 묶음.",
              "섹터": ["성수동 부지 개발(개별주)"], 
              "이유": "성수동 부지 개발 기대감"
            }},
            {{
              "종목명": "한미반도체", 
              "분석과정": "엔비디아 호실적 및 해외 고객사 장비 공급 이슈가 확인됨. 반도체 주도주 흐름임.",
              "섹터": ["반도체"], 
              "이유": "해외 고객사 장비 공급 및 호실적"
            }}
          ]
        }}
        """
        response = analysis_model.generate_content(prompt)
        raw_text = response.text.strip()
        raw_text = re.sub(r"^```json\n?|^```\n?", "", raw_text) 
        raw_text = re.sub(r"\n?```$", "", raw_text)
        
        parsed_json = json.loads(raw_text)
        briefing = parsed_json.get("시장브리핑", "오늘 시장의 주도 테마 브리핑을 생성하지 못했습니다.")
        stock_analysis = parsed_json.get("종목분석", [])
        
        return briefing, stock_analysis
        
    except Exception as e:
        return f"분석 중 오류 발생: {e}", [{"종목명": "시스템 에러", "분석과정": "오류 발생", "섹터": ["오류"], "이유": "AI 분석 실패", "기사날짜": "-"}]

# --- [4] 국내 데이터 크롤링 ---

def fetch_market_data(sosok, market_name):
    protocol = "https"
    host = "finance.naver.com"
    path = "sise/sise_quant.naver"
    
    url = f"{protocol}://{host}/{path}?sosok={sosok}"
    referer_url = f"{protocol}://{host}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': referer_url
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'type_2'})
        
        if not table:
            st.error(f"[에러] 네이버 금융 접근 차단됨 ({market_name})")
            return pd.DataFrame()
            
        data = []
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) > 5:
                data.append({'시장': market_name, '종목명': tds[1].text.strip(), '등락률': tds[4].text.strip(), '거래대금': tds[6].text.strip()})
        return pd.DataFrame(data)
    except Exception as e: 
        st.error(f"[에러] {market_name} 데이터 수집 중 통신 오류: {e}")
        return pd.DataFrame()

def format_volume_to_jo_eok(x_million):
    try:
        clean_val = str(x_million).replace(',', '')
        val_num = float(clean_val)
        eok = int(val_num / 100)
        return f"{eok // 10000}조 {eok % 10000}억" if eok >= 10000 else f"{eok}억"
    except: return str(x_million)

# --- [5] UI 레이아웃 구성 ---

with st.sidebar:
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin-bottom: 15px;'>🌐 글로벌 증시</h2>", unsafe_allow_html=True)
    if st.button("🚀 실시간 스캔", use_container_width=True, key="global_btn"):
        get_global_market_status()
    
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    if st.session_state.global_indices:
        for idx in st.session_state.global_indices:
            st.metric(label=idx['name'], value=idx['value'], delta=idx['delta'])
            
    st.markdown("<hr style='margin: 20px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-bottom: 15px;'>🇺🇸 미국 테마(ETF) 흐름</h3>", unsafe_allow_html=True)
    
    if st.session_state.global_themes:
        for t in st.session_state.global_themes:
            v_c = "#ff4d4d" if '+' in str(t['delta']) else "#3b82f6"
            st.markdown(f'<div class="sidebar-theme-row"><span style="color: #cbd5e1;">{t["name"]}</span><span style="color: {v_c}; text-shadow: 0 0 5px {v_c}66;">{t["delta"]}</span></div>', unsafe_allow_html=True)
            
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.info(f"📍 **시스템 상태:**\n{st.session_state.global_briefing}")

st.markdown("<div class='main-title'>🔑 Golden Key Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>탑티어 퀀트 트레이딩 & 실시간 주도주 분석 대시보드</div>", unsafe_allow_html=True)

tab_scanner, tab_analysis = st.tabs(["🚀 실시간 주도주 스캐너", "📰 종목별 상세 뉴스"])

with tab_scanner:
    col_main, col_summary = st.columns([7, 3])
    with col_summary:
        st.markdown("<h3 style='font-size: 1.3rem; font-weight: 800; margin-bottom: 15px; color: #f8fafc;'>🏆 주도 섹터 랭킹</h3>", unsafe_allow_html=True)
        summary_placeholder = st.empty()
        
    with col_main:
        if st.button("🚀 국내 실시간 스캔 및 AI 분석 실행", use_container_width=True):
            with st.spinner("1/2. 실시간 시장 수급 분석 중..."):
                df_k = fetch_market_data(0, '코스피')
                df_q = fetch_market_data(1, '코스닥')
                df = pd.concat([df_k, df_q], ignore_index=True)
                
                if df.empty:
                    st.warning("⚠️ 네이버 금융에서 데이터를 가져오지 못했습니다.")
                else:
                    df = df[~df['종목명'].str.contains('KODEX|TIGER|ACE|SOL|KBSTAR|HANARO|KOSEF|ARIRANG|스팩|ETN|선물|인버스|레버리지|VIX|옵션|마이티|히어로즈|TIMEFOLIO', na=False)]
                    df['등락률_num'] = pd.to_numeric(df['등락률'].str.replace(r'%|\+', '', regex=True), errors='coerce')
                    df['거래대금_num'] = pd.to_numeric(df['거래대금'].str.replace(',', ''), errors='coerce')
                    df = df.sort_values(by='거래대금_num', ascending=False).head(40)
                    df = df[df['등락률_num'] >= 4.0]
                    
            if not df.empty:
                with st.spinner("2/2. AI 트레이더의 주도장세 및 테마 정밀 분석 중... (약 1분 소요)"):
                    news_payload = {}
                    progress_bar = st.progress(0)
                    stocks = df['종목명'].tolist()
                    
                    for i, name in enumerate(stocks):
                        news_payload[name] = fetch_stock_news_headlines(name)
                        progress_bar.progress((i + 1) / len(stocks))
                        time.sleep(1.0) 
                    
                    st.session_state.news_payload = news_payload
                    
                    market_brief, ai_results = perform_batch_analysis(news_payload)
                    st.session_state.market_briefing = market_brief
                    st.session_state.analysis_results = ai_results
                    
                    sector_dict = {}
                    for item in ai_results:
                        if isinstance(item, dict):
                            s_name = item.get("종목명", "")
                            sectors = force_list(item.get("섹터", ["개별주"]))
                            sector_dict[s_name] = sectors
                            
                    df['섹터'] = df['종목명'].apply(lambda x: force_list(sector_dict.get(x, ['개별주'])))
                    st.session_state.domestic_df = df
            else:
                st.info("ℹ️ 현재 조건에 맞는 주도주가 없습니다.")

        if st.session_state.market_briefing:
            st.markdown(f'''
            <div class="briefing-box">
                <div class="briefing-title">🎙️ AI 트레이더의 오늘의 시장 브리핑</div>
                {st.session_state.market_briefing}
            </div>
            ''', unsafe_allow_html=True)

        if not st.session_state.domestic_df.empty:
            for _, row in st.session_state.domestic_df.iterrows():
                badges_html = ""
                safe_sectors = force_list(row['섹터'])
                for sec in safe_sectors:
                    style = get_sector_style(sec)
                    badges_html += f'<span class="sector-badge" style="{style}">{sec}</span>'
                
                rv = row['등락률_num']; rt_c = "#ff4d4d" if rv >= 20.0 else ("#10b981" if rv >= 10.0 else "#e2e8f0")
                border_c = "#ff4d4d" if rv >= 20.0 else ("#10b981" if rv >= 10.0 else "#475569")
                glow_fx = f"text-shadow: 0 0 8px {rt_c}66;" if rv >= 10.0 else ""
                
                st.markdown(f'''
                <div class="stock-card" style="border-left-color: {border_c};">
                    <div class="left-zone">
                        <span class="market-tag {"market-kospi" if row["시장"]=="코스피" else "market-kosdaq"}">{row["시장"]}</span>
                        <span class="stock-name">{row["종목명"]}</span>
                    </div>
                    <div class="center-zone">{badges_html}</div>
                    <div class="right-zone">
                        <span style="color: {rt_c}; font-weight: 800; font-size: 1.2rem; min-width: 75px; text-align: right; {glow_fx}">+{rv}%</span>
                        <span class="stock-vol">{format_volume_to_jo_eok(row["거래대금_num"])}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with summary_placeholder.container():
                theme_counts = {}
                for idx, row in st.session_state.domestic_df.iterrows():
                    safe_sectors = force_list(row['섹터'])
                    for sec in safe_sectors:
                        if '(개별주)' in sec or sec == '개별주': 
                            continue 
                        if sec not in theme_counts: theme_counts[sec] = []
                        theme_counts[sec].append(row)
                
                sorted_themes = sorted(theme_counts.items(), key=lambda x: (len(x[1]), sum(r['거래대금_num'] for r in x[1])), reverse=True)
                
                for s_name, stocks_list in sorted_themes:
                    stocks_df = pd.DataFrame(stocks_list).sort_values('등락률_num', ascending=False)
                    
                    with st.expander(f"{s_name} ({len(stocks_df)})", expanded=True):
                        for idx_l, (_, s_row) in enumerate(stocks_df.iterrows()):
                            ldr = '<span class="leader-label">대장</span>' if idx_l == 0 else ''
                            rv = s_row["등락률_num"]
                            
                            rate_color = "#ff4d4d" if rv >= 20.0 else ("#10b981" if rv >= 10.0 else "#94a3b8")
                            glow_fx = f"text-shadow: 0 0 5px {rate_color}66;" if rv >= 10.0 else ""
                            
                            st.markdown(f'''
                            <div class="sector-item">
                                <div class="sector-item-left">{ldr}<span class="sector-stock-name">{s_row["종목명"]}</span></div>
                                <div class="sector-item-right">
                                    <span class="val-rate" style="color:{rate_color}; {glow_fx}">+{rv}%</span>
                                    <span class="val-vol">{format_volume_to_jo_eok(s_row["거래대금_num"])}</span>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)

with tab_analysis:
    st.markdown("<h3 style='font-size: 1.3rem; font-weight: 800; margin-bottom: 5px; color: #f8fafc;'>📰 AI 요약 및 종목별 특징주 리스트</h3>", unsafe_allow_html=True)
    if not st.session_state.news_payload:
        st.info("👈 [실시간 주도주 스캐너] 탭에서 스캔을 먼저 실행해 주세요.")
    else:
        st.markdown("<p style='color:#94a3b8; font-size: 0.95rem; margin-bottom: 25px;'>스캔된 주도주들의 AI 상승 요약, <b>논리적 추론 과정</b>, 그리고 최근 기사(본문 포함)를 상세하게 확인합니다.</p>", unsafe_allow_html=True)
        
        for stock, headlines in st.session_state.news_payload.items():
            ai_reason = "최근 뚜렷한 재료 발견 안됨"
            ai_cot = "추론 과정 없음"
            for item in st.session_state.analysis_results:
                if isinstance(item, dict) and item.get("종목명") == stock:
                    ai_reason = item.get("이유", ai_reason)
                    ai_cot = item.get("분석과정", "추론 데이터가 없습니다.")
                    break
            
            news_li_html = ""
            if not headlines or headlines[0].startswith("[에러]"):
                news_li_html = "<li style='color: #64748b;'>수집된 관련 특징주 기사가 없습니다.</li>"
            else:
                news_li_html = "".join([f"<li style='margin-bottom: 8px; line-height: 1.5; color: #cbd5e1;'>{h}</li>" for h in headlines])
            
            card_html = f"""
            <div style="background: #1e293b; border-radius: 12px; padding: 22px; margin-bottom: 20px; border-left: 4px solid #3b82f6; border-right: 1px solid rgba(255,255,255,0.05); border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                <div style="display: flex; align-items: baseline; justify-content: space-between;">
                    <h3 style="margin: 0; color: #f8fafc; font-size: 1.4rem; font-weight: 800; letter-spacing: -0.02em;">{stock}</h3>
                </div>
                <div style="margin-top: 15px; padding: 14px 16px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 8px; color: #93c5fd; font-size: 1rem; font-weight: 700; line-height: 1.5;">
                    💡 AI 핵심 재료: {ai_reason}
                </div>
                <div style="margin-top: 8px; padding: 12px 16px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; color: #94a3b8; font-size: 0.9rem; line-height: 1.5;">
                    🧠 <b>AI 분석 추론:</b> {ai_cot}
                </div>
                <hr style="border: 0; height: 1px; background: rgba(255,255,255,0.1); margin: 20px 0;">
                <ul style="margin:0; padding-left: 22px; font-size: 0.95rem; font-weight: 500;">
                    {news_li_html}
                </ul>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)