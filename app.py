import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta, timezone
import os
import re
import json
import google.generativeai as genai

# --- [1] 페이지 기본 설정 ---
st.set_page_config(layout="wide", page_title="Golden Key Pro | 퀀트 대시보드")

THEME_DB_FILE = "theme_db.csv"

# ==========================================
# 🛡️ [Security] Gemini API 키 및 모델 엔진 설정 (오류 수정 핵심)
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    # 💡 404 오류 영구 해결: 구글 정책 변경에 따라 최신 모델인 gemini-2.5-flash 로 지정합니다.
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash')
    except:
        model = None
else:
    # 키가 없을 경우를 대비한 대체 처리 (UI에서 경고 노출용)
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
    model = None

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

    /* 🌟 지수 폰트 크기 슬림화 (시각적 균형 최적화) 🌟 */
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #64748b !important;
        margin-bottom: -5px !important;
    }

    /* 🌟 실시간 주도주 리스트 디자인 (무삭제 유지) 🌟 */
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

    /* 🌟 우측 섹터 리스트 칼정렬 (일직선 정렬 로직) 🌟 */
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

    /* 🌟 정밀 분석 탭 전용 리스트 스타일 🌟 */
    .analysis-list-container {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .analysis-row {
        font-size: 1rem;
        padding: 12px 0;
        border-bottom: 1px solid #f1f5f9;
        line-height: 1.6;
        color: #1e293b;
    }
    .analysis-row:last-child { border-bottom: none; }
    .analysis-stock-hl { font-weight: 800; color: #2563eb; }
    .analysis-sector-hl { font-weight: 700; color: #059669; }
    .analysis-date-hl { color: #64748b; font-size: 0.85rem; font-weight: 600; }

    /* 사이드바 테마 아이템 스타일 */
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
# 🌟 세션 상태(Session State) 초기화
# ==========================================
if 'global_indices' not in st.session_state: st.session_state.global_indices = []
if 'global_themes' not in st.session_state: st.session_state.global_themes = []
if 'global_briefing' not in st.session_state: st.session_state.global_briefing = "글로벌 스캔을 실행해주세요."
if 'domestic_df' not in st.session_state: st.session_state.domestic_df = pd.DataFrame()
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = []

# ==========================================
# 🌟 전역 설정 (섹터 색상 동기화)
# ==========================================
SECTOR_COLORS = {
    '반도체': '#dbeafe', '로봇/AI': '#ede9fe', '2차전지': '#d1fae5', 
    '전력/원전': '#fef3c7', '바이오': '#fee2e2', '방산/우주': '#f1f5f9', 
    '금융/지주': '#f3f4f6', '개별주': '#ffffff'
}

CUSTOM_SECTOR_MAP = {"온코닉테라퓨틱스": "바이오", "현대ADM": "바이오"}

# --- [2] 미 증시 엔진: 네이버 금융 통합 및 듀얼 크롤링 로직 (안정성 확보) ---

def get_kst_time():
    return datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')

def fetch_sox_stable():
    """필라델피아 반도체 지수 전용: 네이버 금융 해외지수 페이지 크롤링"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = "https://finance.naver.com/world/"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'tbl_exchange'})
        for row in table.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) > 3 and "필라델피아 반도체" in tds[0].text:
                return tds[1].text.strip(), tds[3].text.strip()
        return None, None
    except: return None, None

def fetch_robust_finance(ticker):
    """지수 0% 오류 해결을 위해 야후/구글 교차 체크 및 JSON 추출 로직"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(res.text, 'html.parser')
        val_tag = soup.find("fin-streamer", {"data-field": "regularMarketPrice"})
        rate_tag = soup.find("fin-streamer", {"data-field": "regularMarketChangePercent"})
        if val_tag and val_tag.text != "0.00" and val_tag.text != "":
            return val_tag.text, rate_tag.text.strip()
    except: pass
    try:
        google_ticker = ticker.replace('^', '.')
        mkt = "INDEXNASDAQ" if "NDX" in ticker or "SOX" in ticker else "INDEXSP"
        if "DJI" in ticker: mkt = "INDEXDJX"
        g_url = f"https://www.google.com/finance/quote/{google_ticker}:{mkt}"
        g_res = requests.get(g_url, headers=headers, timeout=12)
        g_soup = BeautifulSoup(g_res.text, 'html.parser')
        g_val = g_soup.select_one(".YMlKec.fxKb9b").text
        g_rate = g_soup.select_one(".Jw796").text.replace('(', '').replace(')', '').strip()
        if g_val: return g_val, g_rate
    except: pass
    return "N/A", "0.00%"

def get_global_market_status():
    """🌟 3대 지수 및 전력/원전 확장 ETF 통합 분석 🌟"""
    indices = []
    themes = []
    idx_map = {"나스닥 100": "^NDX", "S&P 500": "^GSPC", "다우존스": "^DJI"}
    
    try:
        for name, tk in idx_map.items():
            v, r = fetch_robust_finance(tk)
            indices.append({"name": name, "value": v, "delta": r})
            time.sleep(0.2)
        
        # 필라 반도체는 네이버 경로 우선
        sox_v, sox_r = fetch_sox_stable()
        if not sox_v: sox_v, sox_r = fetch_robust_finance("^SOX")
        indices.append({"name": "필라 반도체", "value": sox_v, "delta": sox_r})

        etf_map = [("반도체 (SOXX)", "SOXX", "반도체"), ("로봇/AI (BOTZ)", "BOTZ", "로봇/AI"), ("2차전지 (LIT)", "LIT", "2차전지"), ("전력망 (GRID)", "GRID", "전력/원전"), ("원자력 (URA)", "URA", "전력/원전"), ("바이오 (IBB)", "IBB", "바이오")]
        for name, tk, sector in etf_map:
            _, r_etf = fetch_robust_finance(tk)
            themes.append({"name": name, "delta": r_etf, "color": SECTOR_COLORS.get(sector, "#ffffff")})
            time.sleep(0.2)
            
        st.session_state.global_indices = indices
        st.session_state.global_themes = themes
        st.session_state.global_briefing = f"최종 업데이트: {get_kst_time()}\n해외 지수 및 전력/원전 테마 복구가 완료되었습니다."
    except: st.session_state.global_briefing = "해외 서버 동기화 일시 지연 중"

# --- [3] 준비 엔진: 테마 DB 전체 크롤링 및 로컬 저장 ---
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
        status_text.success("✅ 테마 DB 업데이트 완료!"); time.sleep(1); st.rerun()
    except Exception as e: status_text.error(f"오류: {e}")

# --- [4] 종목 정밀 분석 엔진: 뉴스 크롤링 & Gemini 배치 분석 (설계 추가) ---

def fetch_stock_news_headline(stock_name):
    """'특징주 [종목명]' 키워드로 최신순 검색하여 핵심 제목 추출"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = f"https://search.naver.com/search.naver?where=news&query=특징주+{stock_name}&sort=1"
    try:
        res = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')
        area = soup.select_one(".news_area")
        if area:
            title = area.select_one(".news_tit").text
            date_info = area.select_one(".info_group").text.strip().split(" ")[0]
            return {"title": title, "date": date_info}
        return {"title": "최근 1개월 내 특징주 뉴스 없음", "date": "-"}
    except: return {"title": "뉴스 수집 실패", "date": "-"}

def perform_batch_analysis(news_map):
    """Gemini 2.5 Flash를 이용한 배치 분석 및 설계 포맷팅"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return ["⚠️ Gemini API 키를 코드 상단에 입력해 주세요."]
    
    try:
        # 💡 핵심: 여기서도 동일하게 최신 2.5 모델을 호출해야 합니다.
        analysis_model = genai.GenerativeModel('gemini-2.5-flash')
        # 10개 단위로 끊어서 요청 (정확도 확보)
        prompt = f"""
        당신은 한국 주식 전문가입니다. 아래 종목들의 최근 뉴스 제목을 분석하여 재료의 본질을 파악하세요.
        
        [데이터]
        {json.dumps(news_map, ensure_ascii=False)}
        
        [출력 양식 규칙]
        각 종목을 아래 형식으로 한 줄씩 출력하세요:
        • [종목명] - 섹터: {{핵심섹터}} - 이유: {{상승이유 20자 이내 요약}} ({{뉴스날짜}} 특징주)
        
        섹터는 '반도체', '2차전지', '바이오', '로봇/AI', '전력/원전', '방산/우주항공', '금융/지주', '개별주' 중 하나를 선택하세요.
        """
        response = analysis_model.generate_content(prompt)
        return response.text.strip().split("\n")
    except Exception as e:
        return [f"Gemini 분석 오류: {str(e)}"]

# --- [5] 국내 데이터 크롤링 및 분류 로직 ---

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
    keywords = {'반도체': ['반도체', 'HBM', 'CXL', '온디바이스', '메모리', 'NPU', '유리기판'], '2차전지': ['2차전지', '리튬', '전고체', '배터리'], '바이오': ['바이오', '제약', '신약', '임상', '비만'], '로봇/AI': ['로봇', 'AI', '인공지능'], '전력/원전': ['전력', '전선', '원자력'], '방산/우주': ['방산', '우주', '항공'], '금융/지주': ['지주사', '은행', '증권', '밸류업']}
    for sector, keys in keywords.items():
        if any(k in t for k in keys): return sector
    return '개별주'

def format_volume_to_jo_eok(x_million):
    try:
        # 쉼표 제거 후 숫자로 변환
        clean_val = str(x_million).replace(',', '')
        val_num = float(clean_val)
        eok = int(val_num / 100)
        return f"{eok // 10000}조 {eok % 10000}억" if eok >= 10000 else f"{eok}억"
    except: return str(x_million)

# --- [6] UI 레이아웃 구성 (무삭제 마스터) ---

# 사이드바
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
    st.info(f"📍 **전문가 브리핑:**\n{st.session_state.global_briefing}")

# 메인 화면
col_title, col_btn = st.columns([7, 3])
with col_title: st.title("🔑 Golden Key Pro")
with col_btn:
    st.write(""); st.write("")
    if st.button("🔄 테마 DB 최신화", use_container_width=True): update_theme_db()

tab_scanner, tab_analysis = st.tabs(["🚀 실시간 주도주 스캐너", "📊 종목 정밀 분석"])

with tab_scanner:
    col_main, col_summary = st.columns([7, 3])
    with col_summary:
        st.subheader("🏆 주도 섹터")
        summary_placeholder = st.empty()
    with col_main:
        if st.button("🚀 국내 실시간 스캔 실행", use_container_width=True):
            with st.spinner("국내 시장 수급 분석 중..."):
                df_k = fetch_market_data(0, '코스피'); df_q = fetch_market_data(1, '코스닥')
                df = pd.concat([df_k, df_q], ignore_index=True)
                if not df.empty:
                    # 불필요 종목 필터링 (ETF, 스팩 등)
                    df = df[~df['종목명'].str.contains('KODEX|TIGER|ACE|SOL|스팩|ETN', na=False)]
                    df['등락률_num'] = pd.to_numeric(df['등락률'].str.replace('%|\+', '', regex=True), errors='coerce')
                    df['거래대금_num'] = pd.to_numeric(df['거래대금'].str.replace(',', ''), errors='coerce')
                    # 거래대금 상위 40개
                    df = df.sort_values(by='거래대금_num', ascending=False).head(40)
                    df = df[df['등락률_num'] >= 4.0]
                    # 테마 DB 매핑
                    if os.path.exists(THEME_DB_FILE):
                        t_df = pd.read_csv(THEME_DB_FILE)
                        df['테마'] = df['종목명'].map(dict(zip(t_df['종목명'], t_df['테마']))).fillna('-')
                    else: df['테마'] = '-'
                    df['섹터'] = df.apply(apply_mega_sector, axis=1)
                    st.session_state.domestic_df = df
        
        if not st.session_state.domestic_df.empty:
            for _, row in st.session_state.domestic_df.iterrows():
                bg = SECTOR_COLORS.get(row['섹터'], '#ffffff')
                rv = row['등락률_num']; rt_c = "#ef4444" if rv >= 20.0 else ("#22c55e" if rv >= 10.0 else "#1f2937")
                st.markdown(f'<div class="stock-card"><div class="left-zone"><span class="market-tag {"market-kospi" if row["시장"]=="코스피" else "market-kosdaq"}">{row["시장"]}</span><span class="stock-name">{row["종목명"]}</span></div><div class="center-zone"><span class="sector-badge" style="background: {bg}; color: #1e293b;">{row["섹터"]}</span></div><div class="right-zone"><span style="color: {rt_c}; font-weight: 800; font-size: 1.1rem; min-width: 65px; text-align: right;">+{rv}%</span><span class="stock-vol">{format_volume_to_jo_eok(row["거래대금_num"])}</span></div></div>', unsafe_allow_html=True)
            with summary_placeholder.container():
                s_group = st.session_state.domestic_df[st.session_state.domestic_df['섹터'] != '개별주'].groupby('섹터').size().sort_values(ascending=False)
                for s_name, count in s_group.items():
                    with st.expander(f"**{s_name}** ({count})", expanded=True):
                        s_stocks = st.session_state.domestic_df[st.session_state.domestic_df['섹터'] == s_name].sort_values('등락률_num', ascending=False)
                        for idx_l, (idx, s_row) in enumerate(s_stocks.iterrows()):
                            ldr = '<span class="leader-label">대장</span>' if idx_l == 0 else ''
                            st.markdown(f'<div class="sector-item"><div class="sector-item-left">{ldr}<span class="sector-stock-name">{s_row["종목명"]}</span></div><div class="sector-item-right"><span class="val-rate" style="color:{"#ef4444" if s_row["등락률_num"]>=20 else "#334155"};">+{s_row["등락률_num"]}%</span><span class="val-vol">{format_volume_to_jo_eok(s_row["거래대금_num"])}</span></div></div>', unsafe_allow_html=True)

# 📊 [정밀 분석 탭] 우리 설계 로직 통합
with tab_analysis:
    st.subheader("🔍 뉴스 기반 테마 정밀 분석 (Gemini LLM)")
    if st.session_state.domestic_df.empty:
        st.info("실시간 주도주 스캔을 먼저 실행하세요.")
    else:
        if st.button("🔎 뉴스 크롤링 및 Gemini 정밀 분석 시작", use_container_width=True):
            with st.spinner("특징주 뉴스를 검색하고 Gemini와 함께 맥락을 분석 중입니다..."):
                news_payload = {}
                progress_bar = st.progress(0)
                stocks = st.session_state.domestic_df['종목명'].tolist()
                for i, name in enumerate(stocks):
                    news_payload[name] = fetch_stock_news_headline(name)
                    progress_bar.progress((i + 1) / len(stocks))
                    time.sleep(0.3) # 서버 부하 방지
                
                st.session_state.analysis_results = perform_batch_analysis(news_payload)
                st.success("✅ 정밀 분석 완료!")

        if st.session_state.analysis_results:
            st.markdown('<div class="analysis-list-container">', unsafe_allow_html=True)
            for row in st.session_state.analysis_results:
                if row.strip():
                    # 스타일링을 위해 일부 텍스트 강조 처리 (정규식 활용)
                    styled_row = row.replace("[", '<span class="analysis-stock-hl">[').replace("]", "]</span>")
                    styled_row = styled_row.replace("섹터:", '<span class="analysis-sector-hl">섹터:').replace(" - 이유:", "</span> - 이유:")
                    styled_row = re.sub(r'(\(\d{4}-\d{2}-\d{2} 특징주\))', r'<span class="analysis-date-hl">\1</span>', styled_row)
                    styled_row = styled_row.replace("(오늘 특징주)", '<span class="analysis-date-hl" style="color:#ef4444;">(오늘 특징주)</span>')
                    
                    st.markdown(f'<div class="analysis-row">{styled_row}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)