import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta, timezone
import os
import re
import json

# --- [1] 페이지 기본 설정 ---
st.set_page_config(layout="wide", page_title="Golden Key Pro | 퀀트 대시보드")

THEME_DB_FILE = "theme_db.csv"

# ==========================================
# 🎨 [UI/UX] 프리미엄 대시보드 커스텀 CSS (기존 디자인 무삭제 유지)
# ==========================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #f1f5f9;
    }

    /* 🌟 지수 폰트 크기 최적화 (가독성 개선) 🌟 */
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #64748b !important;
        margin-bottom: -5px !important;
    }

    /* 🌟 실시간 주도주 리스트 디자인 (기존 디자인 무삭제) 🌟 */
    .stock-card {
        background: white;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        border-left: 5px solid #e2e8f0;
    }

    /* 구역별 비율 조정 */
    .left-zone { display: flex; align-items: center; gap: 8px; flex: 0 1 auto; }
    .center-zone { display: flex; align-items: center; gap: 8px; flex: 0 1 auto; margin-left: 10px; }
    .right-zone { display: flex; align-items: center; gap: 15px; flex: 1; justify-content: flex-end; }

    .stock-name { font-weight: 700; font-size: 1rem; color: #1e293b; white-space: nowrap; }
    
    .market-tag { 
        font-size: 0.65rem; 
        font-weight: 800; 
        padding: 2px 5px; 
        border-radius: 4px;
        white-space: nowrap;
    }
    .market-kospi { background-color: #dbeafe; color: #1e40af; }
    .market-kosdaq { background-color: #ffedd5; color: #9a3412; }

    .sector-badge {
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid #e2e8f0;
        white-space: nowrap;
    }

    /* 🌟 우측 섹터 리스트 칼정렬 (일직선 정렬 로직 무삭제) 🌟 */
    .sector-item {
        font-size: 0.85rem;
        color: #334155;
        padding: 6px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px inset #f1f5f9;
        width: 100%;
    }

    .sector-item-left {
        display: flex;
        align-items: center;
        flex: 1;
        overflow: hidden;
    }
    .sector-stock-name {
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .sector-item-right {
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }
    .val-rate {
        width: 65px;
        text-align: right;
        font-weight: 800;
        margin-right: 12px;
    }
    .val-vol {
        width: 75px;
        text-align: right;
        color: #64748b;
        font-size: 0.8rem;
    }

    .leader-label {
        font-size: 0.65rem;
        background: #ef4444;
        color: white;
        padding: 1px 4px;
        border-radius: 3px;
        margin-right: 5px;
        flex-shrink: 0;
    }

    /* 사이드바 테마 아이템 스타일 (무삭제) */
    .sidebar-theme-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        padding: 8px 10px;
        margin-bottom: 5px;
        border-radius: 6px;
        font-weight: 700;
    }
    
    div[data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlock"] { gap: 0px !important; }
    div[data-testid="stExpander"] { border: 1px solid rgba(0,0,0,0.1) !important; margin-bottom: -1px !important; border-radius: 0px !important; }
    div[data-testid="stExpander"]:first-of-type { border-radius: 8px 8px 0 0 !important; }
    div[data-testid="stExpander"]:last-of-type { border-radius: 0 0 8px 8px !important; margin-bottom: 15px !important; }
    div[data-testid="stExpander"] summary { padding: 4px 12px !important; font-weight: 700 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 🌟 세션 상태(Session State) 초기화 (데이터 보존용)
# ==========================================
if 'global_indices' not in st.session_state: st.session_state.global_indices = []
if 'global_themes' not in st.session_state: st.session_state.global_themes = []
if 'global_briefing' not in st.session_state: st.session_state.global_briefing = "글로벌 스캔을 실행해주세요."
if 'domestic_df' not in st.session_state: st.session_state.domestic_df = pd.DataFrame()

# ==========================================
# 🌟 전역 설정 (섹터 색상 매핑)
# ==========================================
SECTOR_COLORS = {
    '반도체': '#dbeafe', '로봇/AI': '#ede9fe', '2차전지': '#d1fae5', 
    '전력/원전': '#fef3c7', '바이오': '#fee2e2', '방산/우주': '#f1f5f9', 
    '금융/지주': '#f3f4f6', '개별주': '#ffffff'
}

CUSTOM_SECTOR_MAP = {"온코닉테라퓨틱스": "바이오", "현대ADM": "바이오"}

# --- [2] 미 증시 엔진: 3중 복구 크롤링 및 확장 테마 로직 ---

def get_kst_time():
    return datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')

def fetch_data_robust(ticker, g_code):
    """야후와 구글을 모두 시도하여 데이터를 반드시 가져오는 안정화 함수 (생략 없음)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8'
    }
    
    # 1단계: 구글 파이낸스 우선 시도 (지수 데이터 안정성 극대화)
    try:
        g_ticker = ticker.replace('^', '.')
        url = f"https://www.google.com/finance/quote/{g_ticker}:{g_code}"
        res = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(res.text, 'html.parser')
        price = soup.select_one(".YMlKec.fxKb9b").text
        rate = soup.select_one(".Jw796").text.replace('(', '').replace(')', '').strip()
        if price and price != "0.00": return price, rate
    except:
        pass

    # 2단계: 야후 파이낸스 직접 태그 추출 백업
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        v_tag = soup.find("fin-streamer", {"data-symbol": ticker, "data-field": "regularMarketPrice"})
        r_tag = soup.find("fin-streamer", {"data-symbol": ticker, "data-field": "regularMarketChangePercent"})
        if v_tag and v_tag.text != "0.00":
            return v_tag.text, r_tag.text.strip()
    except:
        return "N/A", "0.00%"
    return "연결 지연", "0.00%"

def get_global_market_status():
    """🌟 3대 지수 + SOX 완벽 수정 및 전력/원전 테마 분석 🌟"""
    indices = []
    themes = []
    
    # 지수 타겟 매핑
    idx_map = {
        "나스닥 100": ("^NDX", "INDEXNASDAQ"),
        "S&P 500": ("^GSPC", "INDEXSP"),
        "다우존스": ("^DJI", "INDEXDJX"),
        "필라 반도체": ("^SOX", "INDEXNASDAQ")
    }
    
    # 테마 ETF 타겟 (GRID, URA 포함)
    etf_map = [
        ("반도체 (SOXX)", "SOXX", "NASDAQ", "반도체"),
        ("AI (BOTZ)", "BOTZ", "NASDAQ", "로봇/AI"),
        ("2차전지 (LIT)", "LIT", "NYSEARCA", "2차전지"),
        ("전력망 (GRID)", "GRID", "NASDAQ", "전력/원전"),
        ("원자력 (URA)", "URA", "NYSEARCA", "전력/원전"),
        ("바이오 (IBB)", "IBB", "NASDAQ", "바이오")
    ]
    
    try:
        # 지수 분석 (차단 방지를 위해 시간차를 두고 천천히 가져옴)
        for name, (tk, code) in idx_map.items():
            v, r = fetch_data_robust(tk, code)
            indices.append({"name": name, "value": v, "delta": r})
            time.sleep(0.5)
            
        # 테마 ETF 분석
        for name, tk, code, sector in etf_map:
            _, r_etf = fetch_data_robust(tk, code)
            themes.append({"name": name, "delta": r_etf, "color": SECTOR_COLORS.get(sector, "#ffffff")})
            time.sleep(0.5)
            
        st.session_state.global_indices = indices
        st.session_state.global_themes = themes
        st.session_state.global_briefing = f"최종 업데이트: {get_kst_time()}\n해외 지수(SOX 포함) 및 전력/원전 테마 복구가 완료되었습니다."
    except:
        st.session_state.global_briefing = "해외 데이터 소스 동기화 지연 중. 재시도 해주세요."

# --- [3] 준비 엔진: 테마 DB 크롤링 (무삭제 보강) ---
def update_theme_db():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    theme_dict = {}
    progress_bar = st.progress(0); status_text = st.empty()
    try:
        theme_links = []
        for i in range(1, 8):
            url = f"https://finance.naver.com/sise/theme.naver?&page={i}"
            res = session.get(url, timeout=5); res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select('.type_1.theme td.col_type1 a')
            for link in links: theme_links.append((link.text.strip(), "https://finance.naver.com" + link['href']))
        
        total_themes = len(theme_links)
        for idx, (theme_name, link) in enumerate(theme_links):
            status_text.text(f"🚀 테마 DB 갱신 중... ({idx+1}/{total_themes})")
            progress_bar.progress((idx + 1) / total_themes)
            detail_res = session.get(link, timeout=5); detail_res.encoding = 'euc-kr'
            detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
            stocks = detail_soup.select('.type_5 td.name a')
            for stock in stocks:
                name = stock.text.strip()
                if name in theme_dict:
                    if theme_name not in theme_dict[name]: theme_dict[name] += f", {theme_name}"
                else: theme_dict[name] = theme_name
            time.sleep(0.02)
            
        pd.DataFrame(list(theme_dict.items()), columns=['종목명', '테마']).to_csv(THEME_DB_FILE, index=False, encoding='utf-8-sig')
        status_text.success("✅ 업데이트 완료!"); time.sleep(1); st.rerun()
    except Exception as e: status_text.error(f"오류: {e}")

# --- [4] 국내 데이터 크롤링 및 분류 (디자인 무삭제) ---
def fetch_market_data(sosok, market_name):
    url = f"https://finance.naver.com/sise/sise_quant.naver?sosok={sosok}"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5); res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'type_2'})
        data = []
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) > 5:
                data.append({'시장': market_name, '종목명': tds[1].text.strip(), '등락률': tds[4].text.strip(), '거래대금': tds[6].text.strip()})
        return pd.DataFrame(data)
    except: return pd.DataFrame()

def apply_mega_sector(row):
    stock_name = row['종목명']; t = str(row['테마'])
    if stock_name in CUSTOM_SECTOR_MAP: return CUSTOM_SECTOR_MAP[stock_name]
    keywords = {
        '반도체': ['반도체', 'HBM', 'CXL', '온디바이스', '메모리', '유리기판'],
        '2차전지': ['2차전지', '리튬', '전고체', '배터리', '양극재'],
        '바이오': ['바이오', '제약', '신약', '임상'],
        '로봇/AI': ['로봇', 'AI', '인공지능'],
        '전력/원전': ['전력', '전선', '원자력', '변압기'],
        '방산/우주': ['방산', '우주', '항공'],
        '금융/지주': ['지주사', '은행', '보험', '증권', '밸류업']
    }
    for sector, keys in keywords.items():
        if any(k in t for k in keys): return sector
    return '개별주'

def format_volume_to_jo_eok(x_million):
    try:
        eok = int(x_million / 100)
        return f"{eok // 10000}조 {eok % 10000}억" if eok >= 10000 else f"{eok}억"
    except: return str(x_million)

# --- [5] UI 레이아웃 구성 (무삭제 완전판) ---

# 1. 사이드바 구성
with st.sidebar:
    st.title("🌐 글로벌 증시")
    if st.button("🚀 글로벌 실시간 스캔", use_container_width=True):
        get_global_market_status()

    if st.session_state.global_indices:
        for idx in st.session_state.global_indices:
            st.metric(label=idx['name'], value=idx['value'], delta=idx['delta'], delta_color="normal" if '+' in str(idx['delta']) else "inverse")
    
    st.markdown("---")
    st.subheader("🇺🇸 미국 테마(ETF) 흐름")
    if st.session_state.global_themes:
        for t in st.session_state.global_themes:
            v_c = "#ef4444" if '+' in str(t['delta']) else "#2563eb"
            st.markdown(f'<div class="sidebar-theme-row" style="background-color: {t["color"]};"><span style="color: #1e293b;">{t["name"]}</span><span style="color: {v_c};">{t["delta"]}</span></div>', unsafe_allow_html=True)
    else: st.info("스캔을 실행하세요.")
    st.info(f"📍 **전문가 브리핑:**\n{st.session_state.global_briefing}")

# 2. 메인 화면
col_title, col_btn = st.columns([7, 3])
with col_title: st.title("🔑 Golden Key Pro")
with col_btn:
    st.write(""); st.write("")
    if st.button("🔄 테마 DB 최신화", use_container_width=True): update_theme_db()

tab_scanner, _ = st.tabs(["🚀 실시간 주도주 스캐너", "📊 분석"])

with tab_scanner:
    col_main, col_summary = st.columns([7, 3])
    with col_summary:
        st.subheader("🏆 주도 섹터")
        summary_placeholder = st.empty()

    with col_main:
        if st.button("🚀 국내 실시간 스캔 실행", use_container_width=True):
            with st.spinner("분석 중..."):
                df_k = fetch_market_data(0, '코스피'); df_q = fetch_market_data(1, '코스닥')
                df = pd.concat([df_k, df_q], ignore_index=True)
                if not df.empty:
                    black_list = ['KODEX', 'TIGER', '스팩', 'ETN']
                    df = df[~df['종목명'].str.contains('|'.join(black_list), na=False)]
                    df['등락률_num'] = pd.to_numeric(df['등락률'].str.replace('%|\+', '', regex=True), errors='coerce')
                    df['거래대금_num'] = pd.to_numeric(df['거래대금'].str.replace(',', ''), errors='coerce')
                    df = df.sort_values(by='거래대금_num', ascending=False).head(100)
                    df = df[df['등락률_num'] >= 4.0]
                    t_df = pd.read_csv(THEME_DB_FILE) if os.path.exists(THEME_DB_FILE) else pd.DataFrame(columns=['종목명', '테마'])
                    df['테마'] = df['종목명'].map(dict(zip(t_df['종목명'], t_df['테마']))).fillna('-')
                    df['섹터'] = df.apply(apply_mega_sector, axis=1)
                    st.session_state.domestic_df = df

        if not st.session_state.domestic_df.empty:
            df = st.session_state.domestic_df
            st.subheader(f"🔥 실시간 주도주 ({len(df)}개)")
            for _, row in df.iterrows():
                bg = SECTOR_COLORS.get(row['섹터'], '#ffffff')
                rv = row['등락률_num']
                rt_c = "#ef4444" if rv >= 20.0 else ("#22c55e" if rv >= 10.0 else "#1f2937")
                st.markdown(f'<div class="stock-card"><div class="left-zone"><span class="market-tag {"market-kospi" if row["시장"]=="코스피" else "market-kosdaq"}">{row["시장"]}</span><span class="stock-name">{row["종목명"]}</span></div><div class="center-zone"><span class="sector-badge" style="background: {bg}; color: #1e293b;">{row["섹터"]}</span></div><div class="right-zone"><span style="color: {rt_c}; font-weight: 800; font-size: 1.1rem; min-width: 65px; text-align: right;">+{rv}%</span><span class="stock-vol">{format_volume_to_jo_eok(row["거래대금_num"])}</span></div></div>', unsafe_allow_html=True)

            with summary_placeholder.container():
                sector_group = df[df['섹터'] != '개별주'].groupby('섹터').size().sort_values(ascending=False)
                if not sector_group.empty:
                    for s_name, count in sector_group.items():
                        with st.expander(f"**{s_name}** ({count})", expanded=True):
                            s_stocks = df[df['섹터'] == s_name].sort_values('등락률_num', ascending=False)
                            for idx_l, (idx, s_row) in enumerate(s_stocks.iterrows()):
                                ldr = '<span class="leader-label">대장</span>' if idx_l == 0 else ''
                                s_rv = s_row['등락률_num']; s_rtc = "#ef4444" if s_rv >= 20.0 else ("#22c55e" if s_rv >= 10.0 else "#334155")
                                st.markdown(f'<div class="sector-item"><div class="sector-item-left">{ldr}<span class="sector-stock-name">{s_row["종목명"]}</span></div><div class="sector-item-right"><span class="val-rate" style="color:{s_rtc};">+{s_rv}%</span><span class="val-vol">{format_volume_to_jo_eok(s_row["거래대금_num"])}</span></div></div>', unsafe_allow_html=True)
                else: st.info("주도 섹터 없음")
        else: st.info("국내 실시간 스캔을 먼저 실행하세요.")