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
# 🛡️ [Security] Gemini & 키움 API 설정
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

# 키움 API 인증 정보 (Streamlit Secrets 필수 등록)
KIWOOM_APP_KEY = st.secrets.get("KIWOOM_APP_KEY", "")
KIWOOM_APP_SECRET = st.secrets.get("KIWOOM_APP_SECRET", "")

# ==========================================
# 🎨 [UI/UX] 프리미엄 대시보드 커스텀 CSS
# ==========================================
st.markdown(
    """
    <style>
    /* 웹 폰트 (Pretendard & Inter 조합으로 모던하고 전문적인 느낌) */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', 'Inter', sans-serif;
    }

    .stApp {
        background-color: #f8fafc; /* 더 부드럽고 고급스러운 배경색 */
    }

    /* 🌟 상단 타이틀 고급화 (그라데이션 및 폰트 두께 조절) */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
        letter-spacing: -0.02em;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 25px;
    }

    /* 🌟 핵심 CTA(Call To Action) 버튼 디자인 (실시간 스캔 버튼) */
    div.stButton > button:first-child {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 1.05rem;
        font-weight: 700;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2), 0 2px 4px -1px rgba(37, 99, 235, 0.1);
        transition: all 0.2s ease-in-out;
        width: 100%;
        margin-bottom: 15px;
    }
    div.stButton > button:first-child:hover {
        background-color: #1d4ed8;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3), 0 4px 6px -2px rgba(37, 99, 235, 0.15);
        transform: translateY(-2px);
    }
    div.stButton > button:first-child p {
        font-size: 1.05rem;
        font-weight: 700;
    }

    /* 🌟 시장 브리핑 박스 스타일 (전문 리포트 느낌) */
    .briefing-box {
        background: white;
        border-top: 4px solid #3b82f6;
        padding: 20px 24px;
        border-radius: 10px;
        margin-bottom: 25px;
        font-size: 1rem;
        color: #334155;
        line-height: 1.6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .briefing-title {
        font-weight: 800;
        font-size: 1.15rem;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 🌟 실시간 주도주 리스트 카드 디자인 */
    .stock-card {
        background: white;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        border-left: 5px solid #cbd5e1; /* 기본 보더 컬러 */
        transition: transform 0.1s ease;
    }
    .stock-card:hover {
        transform: translateX(2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    .left-zone { display: flex; align-items: center; gap: 10px; flex: 0 1 auto; }
    .center-zone { display: flex; align-items: center; gap: 6px; flex: 0 1 auto; margin-left: 15px; flex-wrap: wrap; }
    .right-zone { display: flex; align-items: center; gap: 18px; flex: 1; justify-content: flex-end; }

    .stock-name { font-weight: 800; font-size: 1.1rem; color: #1e293b; white-space: nowrap; letter-spacing: -0.01em; }
    
    .market-tag { 
        font-size: 0.7rem; 
        font-weight: 800; 
        padding: 3px 6px; 
        border-radius: 6px;
        white-space: nowrap;
    }
    .market-kospi { background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .market-kosdaq { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }

    .sector-badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid rgba(0,0,0,0.05);
        white-space: nowrap;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.5);
    }

    /* 🌟 지수 폰트 크기 슬림화 및 한국식 등락 색상 강제 */
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 800 !important; color: #0f172a !important; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; font-weight: 600 !important; color: #64748b !important; margin-bottom: -2px !important; }
    
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Up"] { color: #ef4444 !important; fill: #ef4444 !important; }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Up"]) > div { color: #ef4444 !important; font-weight: 700 !important; }
    
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Down"] { color: #3b82f6 !important; fill: #3b82f6 !important; }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Down"]) > div { color: #3b82f6 !important; font-weight: 700 !important; }

    /* 🌟 우측 주도 섹터 아코디언(Expander) 고급화 */
    div[data-testid="stExpander"] { 
        border: 1px solid #e2e8f0 !important; 
        border-radius: 8px !important; 
        background: white !important;
        margin-bottom: 8px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stExpander"] summary { 
        padding: 10px 15px !important; 
        background-color: #f8fafc !important; 
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary p { font-weight: 800 !important; font-size: 0.95rem !important; color: #1e293b !important; }
    
    .sector-item {
        font-size: 0.9rem;
        color: #334155;
        padding: 8px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed #e2e8f0;
        width: 100%;
    }
    .sector-item:last-child { border-bottom: none; }

    .sector-item-left { display: flex; align-items: center; flex: 1; overflow: hidden; }
    .sector-stock-name { font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .sector-item-right { display: flex; align-items: center; justify-content: flex-end; }
    
    .val-rate { width: 65px; text-align: right; font-weight: 800; margin-right: 12px; }
    .val-vol { width: 75px; text-align: right; color: #64748b; font-size: 0.8rem; font-weight: 600; }

    .leader-label {
        font-size: 0.65rem;
        background: #ef4444;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 8px;
        flex-shrink: 0;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    /* 사이드바 테마 아이템 스타일 (카드형) */
    .sidebar-theme-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 8px;
        font-weight: 700;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    /* 탭 메뉴 디자인 */
    button[data-baseweb="tab"] {
        font-family: 'Pretendard', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
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
SECTOR_COLORS = {
    '반도체': '#dbeafe', '로봇/AI': '#ede9fe', '2차전지': '#d1fae5', '배터리': '#d1fae5', 'ESS': '#d1fae5',
    '전력': '#fef3c7', '신재생에너지': '#fef3c7', '바이오': '#fee2e2', 
    '방산': '#f1f5f9', '우주항공': '#f1f5f9', '스페이스X': '#e2e8f0',
    '금융/지주': '#f3f4f6', '자동차': '#e0f2fe', '현대차그룹': '#cffafe', '철강': '#f1f5f9',
    '비만치료제': '#fce7f3', '가상화폐/블록체인': '#fef9c3', '조선': '#e0e7ff', '희토류': '#fef08a'
}

def get_sector_color(sector_name):
    for key in SECTOR_COLORS:
        if key in sector_name:
            return SECTOR_COLORS[key]
    return '#f1f5f9'

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
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url = "https://www.google.com/finance/quote/SOX:INDEXNASDAQ"
        res = requests.get(url, headers=headers, timeout=7)
        soup = BeautifulSoup(res.text, 'html.parser')
        val = soup.select_one(".YMlKec.fxKb9b").text
        rate = soup.select_one(".Jw796").text.replace('(', '').replace(')', '').replace('%', '').strip()
        if not rate.startswith('-') and not rate.startswith('+'): rate = f"+{rate}"
        return val, f"{rate}%"
    except: return None, None

def fetch_robust_finance(ticker):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(res.text, 'html.parser')
        val_tag = soup.find("fin-streamer", {"data-field": "regularMarketPrice"})
        rate_tag = soup.find("fin-streamer", {"data-field": "regularMarketChangePercent"})
        if val_tag:
            rate_text = rate_tag.text.strip().replace('(', '').replace(')', '')
            if not rate_text.startswith('-') and not rate_text.startswith('+') and rate_text != "0.00%":
                rate_text = f"+{rate_text}"
            return val_tag.text, rate_text
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
        indices.append({"name": "필라 반도체", "value": sox_v or "N/A", "delta": sox_r or "0.00%"})
        st.session_state.global_indices = indices
        st.session_state.global_briefing = f"최종 업데이트: {get_kst_time()}"
    except: pass

# --- [3] 💡 종목 정밀 분석 엔진 (Gemini) ---

def fetch_stock_news_headlines(stock_name):
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': "https://finance.naver.com/"}
    titles = []
    try:
        encoded_kw = quote(f"특징주 {stock_name}", encoding='euc-kr')
        fin_url = f"https://finance.naver.com/news/news_search.naver?q={encoded_kw}"
        res = requests.get(fin_url, headers=headers, timeout=5)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        blocks = soup.select("ul.newsList li dl, .newsList dl")
        for blk in blocks:
            t_tag = blk.select_one(".articleSubject a, .tit, dt a")
            if t_tag: titles.append(f"제목: {t_tag.text.strip()}")
    except: pass
    return titles[:10] if titles else ["[에러] 뉴스 검색 실패"]

def perform_batch_analysis(news_map):
    if not model: return "API 키 누락", []
    try:
        prompt = f"다음 주도주 뉴스 분석: {json.dumps(news_map, ensure_ascii=False)}\n순수 JSON으로 응답: {{'시장브리핑': '...', '종목분석': [{{'종목명': '...', '섹터': [], '이유': '...', '분석과정': '...'}}]}}"
        response = model.generate_content(prompt)
        raw_text = re.sub(r"^[^{]*", "", re.sub(r"[^}]*$", "", response.text.strip()))
        parsed_json = json.loads(raw_text)
        return parsed_json.get("시장브리핑"), parsed_json.get("종목분석", [])
    except: return "분석 중 오류 발생", []

# --- [4] 🚀 키움 API 기반 수급 추출 엔진 ---

def get_kiwoom_token():
    """키움증권 REST API 토큰 발급 로직"""
    if not KIWOOM_APP_KEY or not KIWOOM_APP_SECRET: return None
    try:
        url = "https://openapi.kiwoom.com/v1/auth/token"
        data = {"app_key": KIWOOM_APP_KEY, "app_secret": KIWOOM_APP_SECRET}
        res = requests.post(url, json=data, timeout=5)
        return res.json().get("access_token")
    except: return None

def fetch_kiwoom_market_data():
    """키움 API를 활용해 ETF/ETN 제외, 거래대금 상위 100위 중 4% 상승 종목 추출"""
    token = get_kiwoom_token()
    if not token: return pd.DataFrame()
    
    headers = {"Authorization": f"Bearer {token}"}
    all_stocks = []
    # 001: 코스피, 101: 코스닥 시장 순회
    for m_code in ["001", "101"]:
        try:
            # 거래대금 순위(ranking) API 호출
            url = f"https://openapi.kiwoom.com/v1/quotes/market-ranking?market_code={m_code}&sort_type=2"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json().get("output", [])
            for item in data:
                name = item.get("hname", "")
                # 🌟 [핵심 필터] ETF, ETN, 스팩, 파생상품 완전 제거 로직
                is_pure = not any(kw in name for kw in ['KODEX', 'TIGER', 'ACE', 'SOL', 'KBSTAR', '스팩', 'ETN', '선물', '인버스', '레버리지'])
                if is_pure:
                    all_stocks.append({
                        '시장': '코스피' if m_code == "001" else '코스닥',
                        '종목명': name,
                        '등락률_num': float(item.get("change_rate", 0)),
                        '거래대금_num': float(item.get("trade_amount", 0)) / 1000000  # 백만 단위 변환
                    })
        except: continue
    return pd.DataFrame(all_stocks)

def format_volume_to_jo_eok(x_million):
    val = int(x_million)
    return f"{val // 10000}조 {val % 10000}억" if val >= 10000 else f"{val}억"

# --- [5] UI 레이아웃 구성 ---

with st.sidebar:
    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 800; color: #0f172a;'>🌐 글로벌 증시</h2>", unsafe_allow_html=True)
    if st.button("🚀 실시간 스캔", use_container_width=True, key="global_btn"): get_global_market_status()
    for idx in st.session_state.global_indices: st.metric(label=idx['name'], value=idx['value'], delta=idx['delta'])
    st.info(f"📍 **상태:** {st.session_state.global_briefing}")

st.markdown("<div class='main-title'>🔑 Golden Key Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>키움 API 기반 탑티어 퀀트 & 주도주 분석 대시보드</div>", unsafe_allow_html=True)

tab_scanner, tab_analysis = st.tabs(["🚀 실시간 주도주 스캐너", "📰 종목별 상세 뉴스"])

with tab_scanner:
    col_main, col_summary = st.columns([7, 3])
    with col_summary:
        st.markdown("<h3 style='font-size: 1.3rem; font-weight: 800; color: #0f172a;'>🏆 주도 섹터 랭킹</h3>", unsafe_allow_html=True)
        summary_placeholder = st.empty()
        
    with col_main:
        if st.button("🚀 국내 실시간 스캔 및 AI 분석 실행", use_container_width=True):
            with st.spinner("1/2. 키움 API로부터 순수 기업 데이터 수집 중..."):
                # 키움 API 엔진 가동
                df = fetch_kiwoom_market_data()
                if not df.empty:
                    # 🌟 [로직 적용] 1. 거래대금 순 상위 100위 추출
                    df = df.sort_values(by='거래대금_num', ascending=False).head(100)
                    # 🌟 [로직 적용] 2. 그중 상승률 4.0% 이상인 종목만 필터링
                    df = df[df['등락률_num'] >= 4.0].sort_values(by='등락률_num', ascending=False)
                
            if not df.empty:
                with st.spinner(f"2/2. AI 트레이더의 주도장세 분석 중... ({len(df)}개 종목)"):
                    news_payload = {name: fetch_stock_news_headlines(name) for name in df['종목명'].tolist()}
                    st.session_state.news_payload = news_payload
                    market_brief, ai_results = perform_batch_analysis(news_payload)
                    st.session_state.market_briefing, st.session_state.analysis_results = market_brief, ai_results
                    sector_dict = {item.get("종목명"): force_list(item.get("섹터")) for item in ai_results if isinstance(item, dict)}
                    df['섹터'] = df['종목명'].apply(lambda x: sector_dict.get(x, ['개별주']))
                    st.session_state.domestic_df = df
            else: st.info("ℹ️ 현재 조건(상위 100위 내 +4% 이상)에 맞는 주도주가 없습니다.")

        if st.session_state.market_briefing:
            st.markdown(f'<div class="briefing-box"><div class="briefing-title">🎙️ AI 트레이더 브리핑</div>{st.session_state.market_briefing}</div>', unsafe_allow_html=True)

        for _, row in st.session_state.domestic_df.iterrows():
            badges = "".join([f'<span class="sector-badge" style="background:{get_sector_color(s)};">{s}</span>' for s in row['섹터']])
            rv = round(row['등락률_num'], 2)
            st.markdown(f'''<div class="stock-card">
                <div class="left-zone"><span class="market-tag {"market-kospi" if row["시장"]=="코스피" else "market-kosdaq"}">{row["시장"]}</span><span class="stock-name">{row["종목명"]}</span></div>
                <div class="center-zone">{badges}</div>
                <div class="right-zone"><span style="color:#ef4444; font-weight:800; font-size:1.15rem;">+{rv}%</span><span>{format_volume_to_jo_eok(row["거래대금_num"])}</span></div>
            </div>''', unsafe_allow_html=True)
            
            with summary_placeholder.container():
                theme_counts = {}
                for idx, row_d in st.session_state.domestic_df.iterrows():
                    for sec in row_d['섹터']:
                        if '(개별주)' in sec or sec == '개별주': continue 
                        if sec not in theme_counts: theme_counts[sec] = []
                        theme_counts[sec].append(row_d)
                sorted_themes = sorted(theme_counts.items(), key=lambda x: (len(x[1]), sum(r['거래대금_num'] for r in x[1])), reverse=True)
                for s_name, stocks_list in sorted_themes:
                    with st.expander(f"{s_name} ({len(stocks_list)})", expanded=True):
                        for idx_l, s_row in enumerate(pd.DataFrame(stocks_list).sort_values('등락률_num', ascending=False).iloc):
                            ldr = '<span class="leader-label">대장</span>' if idx_l == 0 else ''
                            st.markdown(f'''<div class="sector-item"><div class="sector-item-left">{ldr}{s_row["종목명"]}</div><div class="sector-item-right"><span style="color:#ef4444;font-weight:800;margin-right:12px;">+{s_row["등락률_num"]}%</span>{format_volume_to_jo_eok(s_row["거래대금_num"])}</div></div>''', unsafe_allow_html=True)

with tab_analysis:
    if st.session_state.domestic_df.empty: st.info("먼저 스캔을 실행하세요.")
    else:
        for stock, headlines in st.session_state.news_payload.items():
            res = next((i for i in st.session_state.analysis_results if i.get("종목명") == stock), {})
            st.markdown(f'''<div style="background:white; border-radius:12px; padding:22px; margin-bottom:20px; border-left:5px solid #3b82f6;">
                <h3 style="margin:0;">{stock}</h3><div style="margin-top:15px; padding:14px; background:#eff6ff; border-radius:8px; color:#1e40af; font-weight:700;">💡 핵심 재료: {res.get("이유", "분석 중")}</div>
                <div style="margin-top:8px; padding:12px; background:#f8fafc; border-radius:8px; color:#475569; font-size:0.9rem;">🧠 AI 추론: {res.get("분석과정", "-")}</div>
                <hr style="border:0; height:1px; background:#e2e8f0; margin:20px 0;">
                <ul style="margin:0; padding-left:22px;">{"".join([f"<li>{h}</li>" for h in headlines])}</ul></div>''', unsafe_allow_html=True)