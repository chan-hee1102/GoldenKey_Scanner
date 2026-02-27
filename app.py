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
# 🎨 [UI/UX] 프리미엄 대시보드 커스텀 CSS
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

    /* 🌟 지수 폰트 크기 슬림화 및 한국식 등락 색상 강제 (상승: 빨강, 하락: 파랑) */
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #64748b !important;
        margin-bottom: -5px !important;
    }
    
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Up"] {
        color: #ef4444 !important;
        fill: #ef4444 !important;
    }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Up"]) > div {
        color: #ef4444 !important;
    }
    
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Down"] {
        color: #3b82f6 !important;
        fill: #3b82f6 !important;
    }
    [data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Down"]) > div {
        color: #3b82f6 !important;
    }

    /* 🌟 실시간 주도주 리스트 디자인 */
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

    /* 🌟 우측 섹터 리스트 칼정렬 */
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
if 'news_payload' not in st.session_state: st.session_state.news_payload = {} # 뉴스 데이터 보관용

# ==========================================
# 🌟 전역 설정 (섹터 색상 동기화)
# ==========================================
SECTOR_COLORS = {
    '반도체': '#dbeafe', '로봇/AI': '#ede9fe', '2차전지': '#d1fae5', 
    '전력/원전': '#fef3c7', '바이오': '#fee2e2', '방산/우주': '#f1f5f9', 
    '금융/지주': '#f3f4f6', '개별주': '#ffffff'
}

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
            themes.append({"name": name, "delta": r_etf, "color": SECTOR_COLORS.get(sector, "#ffffff")})
            time.sleep(0.2)
            
        st.session_state.global_indices = indices
        st.session_state.global_themes = themes
        st.session_state.global_briefing = f"최종 업데이트: {get_kst_time()}\n해외 지수 및 전력/원전 테마 복구가 완료되었습니다."
    except: st.session_state.global_briefing = "해외 서버 동기화 일시 지연 중"

# --- [3] 💡 종목 정밀 분석 엔진 (Gemini) ---

def fetch_stock_news_headlines(stock_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
        'Referer': "https://" + "finance.naver.com/"
    }
    titles = []
    try:
        encoded_kw = quote(f"특징주 {stock_name}", encoding='euc-kr')
        fin_url = "https://" + f"finance.naver.com/news/news_search.naver?q={encoded_kw}"
        res_fin = requests.get(fin_url, headers=headers, timeout=10)
        res_fin.encoding = 'euc-kr' 
        
        if res_fin.status_code == 200:
            soup_fin = BeautifulSoup(res_fin.text, 'html.parser')
            tags = soup_fin.select(".articleSubject a") or soup_fin.select(".tit") or soup_fin.select("dt a")
            for tag in tags[:10]:
                text = tag.text.strip()
                if text: titles.append(text)
    except: pass 

    if not titles:
        try:
            gen_url = "https://" + "search.naver.com/search.naver"
            params = {'where': 'news', 'query': f'특징주 {stock_name}', 'sort': '0'} 
            headers['Referer'] = "https://" + "search.naver.com/"
            
            res_gen = requests.get(gen_url, params=params, headers=headers, timeout=10)
            if res_gen.status_code == 200:
                soup_gen = BeautifulSoup(res_gen.text, 'html.parser')
                selectors = [".news_tit", ".title_link", "a.news_tit", ".dsc_txt_tit", ".api_txt_lines"]
                for sel in selectors:
                    tags = soup_gen.select(sel)
                    if tags: 
                        for tag in tags[:10]:
                            text = tag.text.strip()
                            if text: titles.append(text)
                        break 
        except: pass
            
    if not titles:
        return [f"[에러] 네이버 검색 전면 차단됨"]
        
    unique_titles = []
    for t in titles:
        if t not in unique_titles: unique_titles.append(t)
            
    return unique_titles[:10]

def perform_batch_analysis(news_map):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return [{"종목명": "오류", "섹터": ["시스템"], "이유": "API 키가 설정되지 않았습니다.", "기사날짜": "-"}]
    
    try:
        analysis_model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        당신은 한국 주식 퀀트 분석 전문가입니다. 
        아래 데이터는 실시간 주도주들에 대해 네이버 뉴스 제목을 종목당 최대 10개씩 크롤링한 결과입니다.
        
        [데이터]
        {json.dumps(news_map, ensure_ascii=False)}
        
        [출력 양식 및 분석 규칙]
        1. 각 종목당 제공된 여러 개의 뉴스 제목을 모두 읽고, 해당 종목이 상승한 '진짜 핵심 재료'를 파악하세요.
        2. 타 종목 기사는 무시하고, 데이터에 "[에러]" 라고 적혀있다면 이유를 "최근 뉴스 없음" 이라고 적어주세요.
        3. '섹터'는 해당 재료를 기반으로 판단하되, 꼭 1개가 아니어도 됩니다. (예: ["반도체", "로봇/AI"]). 뉴스가 없거나 파악이 불가능하면 ["개별주"] 로 분류하세요.
        4. 반드시 아래와 같은 순수 JSON 배열(Array) 형식으로만 응답하세요. 백틱(`)이나 부가 설명은 절대 넣지 마세요.
        
        [예시]
        [
          {{"종목명": "삼성전자", "섹터": ["반도체"], "이유": "엔비디아 HBM 퀄테스트 통과 기대감", "기사날짜": "최근 특징주"}},
          {{"종목명": "카카오", "섹터": ["개별주"], "이유": "최근 주요 재료 발견 안 됨", "기사날짜": "-"}}
        ]
        """
        response = analysis_model.generate_content(prompt)
        raw_text = response.text.strip()
        raw_text = re.sub(r"^```json\n?|^```\n?", "", raw_text) 
        raw_text = re.sub(r"\n?```$", "", raw_text)
        return json.loads(raw_text)
    except Exception as e:
        return [{"종목명": "분석 시스템 에러", "섹터": ["개별주"], "이유": f"Gemini 분석 오류", "기사날짜": "-"}]

# --- [4] 국내 데이터 크롤링 ---

def fetch_market_data(sosok, market_name):
    protocol = "https"
    host = "finance.naver.com"
    path = "sise/sise_quant.naver"
    
    url = f"{protocol}://{host}/{path}?sosok={sosok}"
    referer_url = f"{protocol}://{host}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
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
    st.title("🌐 글로벌 증시")
    if st.button("🚀 글로벌 실시간 스캔", use_container_width=True):
        get_global_market_status()
    if st.session_state.global_indices:
        for idx in st.session_state.global_indices:
            st.metric(label=idx['name'], value=idx['value'], delta=idx['delta'])
    st.markdown("---")
    st.subheader("🇺🇸 미국 테마(ETF) 흐름")
    if st.session_state.global_themes:
        for t in st.session_state.global_themes:
            v_c = "#ef4444" if '+' in str(t['delta']) else "#3b82f6"
            st.markdown(f'<div class="sidebar-theme-row" style="background-color: {t["color"]};"><span style="color: #1e293b;">{t["name"]}</span><span style="color: {v_c};">{t["delta"]}</span></div>', unsafe_allow_html=True)
    st.info(f"📍 **전문가 브리핑:**\n{st.session_state.global_briefing}")

col_title, col_btn = st.columns([8, 2])
with col_title: st.title("🔑 Golden Key Pro")

tab_scanner, tab_analysis = st.tabs(["🚀 실시간 주도주 스캐너", "📰 종목별 상세 뉴스"])

with tab_scanner:
    col_main, col_summary = st.columns([7, 3])
    with col_summary:
        st.subheader("🏆 주도 섹터")
        summary_placeholder = st.empty()
    with col_main:
        if st.button("🚀 국내 실시간 스캔 및 AI 분석 실행", use_container_width=True):
            # 1단계: 수급 데이터 크롤링
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
                    
            # 2단계: 종목별 뉴스 크롤링 및 Gemini 통합 분석
            if not df.empty:
                with st.spinner("2/2. 최신 뉴스 크롤링 및 Gemini 테마 정밀 분석 중... (약 1분 소요)"):
                    news_payload = {}
                    progress_bar = st.progress(0)
                    stocks = df['종목명'].tolist()
                    
                    for i, name in enumerate(stocks):
                        news_payload[name] = fetch_stock_news_headlines(name)
                        progress_bar.progress((i + 1) / len(stocks))
                        time.sleep(1.0) # 속도 개선을 위해 1초 대기로 변경
                    
                    # 탭 2를 위해 세션에 저장
                    st.session_state.news_payload = news_payload
                    
                    # Gemini 모델로 일괄 분석
                    ai_results = perform_batch_analysis(news_payload)
                    st.session_state.analysis_results = ai_results
                    
                    # AI가 판단한 섹터를 데이터프레임에 매핑
                    sector_dict = {}
                    for item in ai_results:
                        if isinstance(item, dict):
                            s_name = item.get("종목명", "")
                            sectors = item.get("섹터", ["개별주"])
                            # 여러 섹터가 오더라도 첫 번째 값을 대표 섹터로 지정
                            main_sec = sectors[0] if isinstance(sectors, list) and len(sectors) > 0 else "개별주"
                            sector_dict[s_name] = main_sec
                            
                    df['섹터'] = df['종목명'].map(sector_dict).fillna('개별주')
                    st.session_state.domestic_df = df
            else:
                st.info("ℹ️ 현재 조건에 맞는 주도주가 없습니다.")

        # 메인 화면 렌더링 (AI가 분류한 섹터 기반)
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

with tab_analysis:
    st.subheader("📰 AI 요약 및 종목별 특징주 리스트")
    if not st.session_state.news_payload:
        st.info("👈 [실시간 주도주 스캐너] 탭에서 스캔을 먼저 실행해 주세요.")
    else:
        st.markdown("<p style='color:#64748b; margin-bottom: 20px;'>스캔된 주도주들의 AI 상승 요약과 최근 기사 10개를 상세하게 확인합니다.</p>", unsafe_allow_html=True)
        
        for stock, headlines in st.session_state.news_payload.items():
            # AI 분석 결과에서 상승 이유 추출
            ai_reason = "최근 뚜렷한 재료 발견 안됨"
            for item in st.session_state.analysis_results:
                if isinstance(item, dict) and item.get("종목명") == stock:
                    ai_reason = item.get("이유", ai_reason)
                    break
            
            # 뉴스 리스트 HTML 조립
            news_li_html = ""
            if not headlines or headlines[0].startswith("[에러]"):
                news_li_html = "<li style='color: #94a3b8;'>수집된 관련 특징주 기사가 없습니다.</li>"
            else:
                news_li_html = "".join([f"<li style='margin-bottom: 8px; line-height: 1.4;'>{h}</li>" for h in headlines])
            
            # 카드 UI로 깔끔하게 렌더링
            card_html = f"""
            <div style="background: white; border-radius: 8px; padding: 18px; margin-bottom: 15px; border-left: 5px solid #3b82f6; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; align-items: baseline; justify-content: space-between;">
                    <h3 style="margin: 0; color: #0f172a; font-weight: 800;">{stock}</h3>
                </div>
                <div style="margin-top: 10px; padding: 10px 12px; background: #eff6ff; border-radius: 6px; color: #1e40af; font-size: 0.95rem; font-weight: 700;">
                    💡 AI 핵심 재료: {ai_reason}
                </div>
                <hr style="border: 0; height: 1px; background: #e2e8f0; margin: 15px 0;">
                <ul style="margin:0; padding-left: 20px; font-size: 0.9rem; color: #334155; font-weight: 600;">
                    {news_li_html}
                </ul>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)