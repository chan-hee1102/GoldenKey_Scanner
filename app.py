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
    .center-zone { display: flex; align-items: center; gap: 4px; flex: 0 1 auto; margin-left: 10px; flex-wrap: wrap; }
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
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
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
    
    /* 🌟 시장 브리핑 박스 스타일 */
    .briefing-box {
        background: #eff6ff;
        border-left: 5px solid #3b82f6;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        color: #1e3a8a;
        line-height: 1.5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .briefing-title {
        font-weight: 800;
        font-size: 1.1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
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
if 'market_briefing' not in st.session_state: st.session_state.market_briefing = "" 
if 'news_payload' not in st.session_state: st.session_state.news_payload = {} 

# ==========================================
# 🌟 전역 설정 (섹터 색상 동기화 및 헬퍼 함수)
# ==========================================
SECTOR_COLORS = {
    '반도체': '#dbeafe', '로봇/AI': '#ede9fe', '2차전지': '#d1fae5', 
    '전력/원전': '#fef3c7', '전력/신재생에너지': '#fef3c7', '바이오': '#fee2e2', 
    '방산/우주': '#f1f5f9', '우주항공': '#f1f5f9', '스페이스X/우주항공': '#e2e8f0',
    '금융/지주': '#f3f4f6', '자동차': '#e0f2fe', '현대차그룹': '#cffafe', '철강': '#f1f5f9',
    '비만치료제': '#fce7f3', '가상화폐/블록체인': '#fef9c3', '조선': '#e0e7ff'
}

def get_sector_color(sector_name):
    for key in SECTOR_COLORS:
        if key in sector_name:
            return SECTOR_COLORS[key]
    return '#f8fafc'

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
            themes.append({"name": name, "delta": r_etf, "color": SECTOR_COLORS.get(sector, "#ffffff")})
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
    
    # 1. 메인 타겟: 네이버 금융 뉴스 (본문 요약 Snippet 추가)
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
                        summary = re.sub(r'\|.*?$', '', summary).strip() # 언론사, 날짜 정보 클리닝
                        if summary:
                            news_str = f"제목: {title} (내용: {summary})"
                        else:
                            news_str = f"제목: {title}"
                        if news_str not in titles:
                            titles.append(news_str)
            else:
                # 블록 구조가 안 보이면 제목만 가져오는 폴백
                tags = soup_fin.select(".articleSubject a, .tit, dt a")
                for tag in tags:
                    text = tag.text.strip()
                    if text:
                        news_str = f"제목: {text}"
                        if news_str not in titles: titles.append(news_str)
    except: pass 

    # 2. 보조 타겟: 다음(Daum) 뉴스 우회 (본문 요약 Snippet 추가)
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
                    # 폴백
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
        
        # 💡 [핵심 혁신] CoT(사고의 사슬) 프롬프트 및 본문 내용 종합 분석 추가
        prompt = f"""
        당신은 여의도 최고 수준의 프랍 트레이더이자 시장 트렌드 분석의 권위자입니다.
        아래 데이터는 오늘 시장에서 강한 수급(거래대금 상위 & 급등)이 들어온 주도주들의 뉴스 '제목'과 '본문 요약(내용)' 모음입니다.
        
        [데이터]
        {json.dumps(news_map, ensure_ascii=False)}
        
        [분석 지시사항 - 반드시 지킬 것]
        1. 전체 시장 조감(Macro): 제공된 모든 종목과 뉴스를 종합적으로 읽고, 오늘 시장의 핵심 자금이 어디로 쏠리고 있는지(2~3개의 주도 테마) 파악하세요.
        2. 시장 브리핑 작성: 파악된 주도 테마를 바탕으로 "오늘 시장은 OO 테마와 XX 관련주가 강하게 시장을 이끌고 있습니다." 형태의 트레이더 브리핑을 2~3줄로 작성하세요.
        3. 사고의 사슬 (Chain of Thought) 적용: 종목별 테마를 결정하기 전, 반드시 '분석과정' 필드에 뉴스의 본문 내용을 바탕으로 핵심 키워드와 맥락을 1~2줄로 먼저 요약하고 논리적으로 검증하세요. (예: "본업은 시멘트지만 내용의 대부분이 성수동 부지 개발 호재이므로 부동산/개발 테마가 적합함")
        4. 종목별 테마 할당(Micro):
           - 단순한 회사 본업(예: 벤처캐피탈, 시멘트)이나 비테마성 호재(예: 실적개선, 흑자전환, 신규상장, 액면분할, 투자유치)는 '섹터'로 지정 절대 금지.
           - 시장 주도 테마에 속하는 종목들은 확실하게 그 주도 테마명(예: "스페이스X/우주항공")으로 묶으세요.
           - 단일 종목 호재로 여러 테마를 쪼개지 마세요. (예: 한미반도체 하나를 '반도체', 'HBM' 두 개로 분리 금지. -> "반도체/HBM" 1개로 통일)
           - 동반 상승하는 종목이 없는 '나홀로 호재' 종목은 억지로 주도 테마를 만들지 말고, "개별주(업종명)" 형태로 묶어주세요. (예: "개별주(제약)", "개별주(건자재)")
        5. 출력 형식: 반드시 아래와 같은 구조의 순수 JSON 포맷으로만 응답하세요. (마크다운 백틱 억제)
        
        [예시 포맷]
        {{
          "시장브리핑": "오늘 시장은 현대차그룹의 대규모 투자에 따른 로봇/AI 섹터와, 스페이스X 수혜를 입은 우주항공 테마에 강한 매수세가 집중되고 있습니다. 그 외 개별 호재를 동반한 종목들이 각개전투 중입니다.",
          "종목분석": [
            {{
              "종목명": "현대차", 
              "분석과정": "뉴스의 핵심은 새만금 9조 통큰 투자와 AI·로봇 거점 추진임. 자동차 본업보다 그룹 차원의 로봇/AI 모멘텀이 주가를 견인 중이므로 해당 테마로 분류함.",
              "섹터": ["현대차그룹/로봇"], 
              "이유": "새만금 투자 및 로봇 거점 추진 기대감"
            }},
            {{
              "종목명": "아주IB투자", 
              "분석과정": "벤처투자사이지만, 뉴스 내용을 보면 스페이스X 지분 가치 상승에 집중되어 있음. 실전 트레이딩 관점에서 우주항공 관련주로 묶는 것이 타당함.",
              "섹터": ["스페이스X/우주항공"], 
              "이유": "스페이스X 지분 가치 상승 부각"
            }},
            {{
              "종목명": "한미반도체", 
              "분석과정": "본문 내용에서 엔비디아 호실적 및 해외 고객사 장비 공급 이슈가 확인됨. 전형적인 반도체 주도주 흐름임.",
              "섹터": ["반도체/HBM"], 
              "이유": "해외 고객사 장비 공급 및 호실적"
            }},
            {{
              "종목명": "삼표시멘트", 
              "분석과정": "본업 호재보다는 성수동 부지 개발 기대감 관련 뉴스가 주를 이룸. 현재 시장을 이끄는 메가 테마라기보다는 개별 호재임.",
              "섹터": ["개별주(건자재)"], 
              "이유": "성수동 부지 개발 기대감"
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
                    
            # 2단계: 종목별 뉴스 크롤링 및 Gemini 통합 분석 (시장 브리핑 포함)
            if not df.empty:
                with st.spinner("2/2. 탑티어 AI 트레이더의 주도장세 및 테마 정밀 분석 중... (약 1분 소요)"):
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
                    bg = get_sector_color(sec)
                    badges_html += f'<span class="sector-badge" style="background: {bg}; color: #1e293b;">{sec}</span>'
                
                rv = row['등락률_num']; rt_c = "#ef4444" if rv >= 20.0 else ("#22c55e" if rv >= 10.0 else "#1f2937")
                
                st.markdown(f'''
                <div class="stock-card">
                    <div class="left-zone">
                        <span class="market-tag {"market-kospi" if row["시장"]=="코스피" else "market-kosdaq"}">{row["시장"]}</span>
                        <span class="stock-name">{row["종목명"]}</span>
                    </div>
                    <div class="center-zone">{badges_html}</div>
                    <div class="right-zone">
                        <span style="color: {rt_c}; font-weight: 800; font-size: 1.1rem; min-width: 65px; text-align: right;">+{rv}%</span>
                        <span class="stock-vol">{format_volume_to_jo_eok(row["거래대금_num"])}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with summary_placeholder.container():
                theme_counts = {}
                for idx, row in st.session_state.domestic_df.iterrows():
                    safe_sectors = force_list(row['섹터'])
                    for sec in safe_sectors:
                        if sec == '개별주' and len(safe_sectors) > 1: continue 
                        if sec not in theme_counts: theme_counts[sec] = []
                        theme_counts[sec].append(row)
                
                sorted_themes = sorted(theme_counts.items(), key=lambda x: (len(x[1]), sum(r['거래대금_num'] for r in x[1])), reverse=True)
                
                for s_name, stocks_list in sorted_themes:
                    stocks_df = pd.DataFrame(stocks_list).sort_values('등락률_num', ascending=False)
                    
                    with st.expander(f"**{s_name}** ({len(stocks_df)})", expanded=True):
                        for idx_l, (_, s_row) in enumerate(stocks_df.iterrows()):
                            ldr = '<span class="leader-label">대장</span>' if idx_l == 0 else ''
                            rv = s_row["등락률_num"]
                            
                            rate_color = "#ef4444" if rv >= 20.0 else ("#22c55e" if rv >= 10.0 else "#334155")
                            
                            st.markdown(f'''
                            <div class="sector-item">
                                <div class="sector-item-left">{ldr}<span class="sector-stock-name">{s_row["종목명"]}</span></div>
                                <div class="sector-item-right">
                                    <span class="val-rate" style="color:{rate_color};">+{rv}%</span>
                                    <span class="val-vol">{format_volume_to_jo_eok(s_row["거래대금_num"])}</span>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)

with tab_analysis:
    st.subheader("📰 AI 요약 및 종목별 특징주 리스트")
    if not st.session_state.news_payload:
        st.info("👈 [실시간 주도주 스캐너] 탭에서 스캔을 먼저 실행해 주세요.")
    else:
        st.markdown("<p style='color:#64748b; margin-bottom: 20px;'>스캔된 주도주들의 AI 상승 요약, <b>논리적 추론 과정</b>, 그리고 최근 기사(본문 포함)를 상세하게 확인합니다.</p>", unsafe_allow_html=True)
        
        for stock, headlines in st.session_state.news_payload.items():
            ai_reason = "최근 뚜렷한 재료 발견 안됨"
            ai_cot = "추론 과정 없음"
            for item in st.session_state.analysis_results:
                if isinstance(item, dict) and item.get("종목명") == stock:
                    ai_reason = item.get("이유", ai_reason)
                    # 💡 JSON에서 모델이 스스로 생각한 분석과정(CoT)을 가져옵니다.
                    ai_cot = item.get("분석과정", "추론 데이터가 없습니다.")
                    break
            
            news_li_html = ""
            if not headlines or headlines[0].startswith("[에러]"):
                news_li_html = "<li style='color: #94a3b8;'>수집된 관련 특징주 기사가 없습니다.</li>"
            else:
                news_li_html = "".join([f"<li style='margin-bottom: 8px; line-height: 1.4;'>{h}</li>" for h in headlines])
            
            # 💡 두 번째 탭에 뇌 구조(추론 과정)를 보여주는 UI 블록 추가
            card_html = f"""
            <div style="background: white; border-radius: 8px; padding: 18px; margin-bottom: 15px; border-left: 5px solid #3b82f6; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; align-items: baseline; justify-content: space-between;">
                    <h3 style="margin: 0; color: #0f172a; font-weight: 800;">{stock}</h3>
                </div>
                <div style="margin-top: 10px; padding: 10px 12px; background: #eff6ff; border-radius: 6px; color: #1e40af; font-size: 0.95rem; font-weight: 700;">
                    💡 AI 핵심 재료: {ai_reason}
                </div>
                <div style="margin-top: 6px; padding: 8px 12px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; color: #475569; font-size: 0.85rem;">
                    🧠 <b>AI 분석 추론:</b> {ai_cot}
                </div>
                <hr style="border: 0; height: 1px; background: #e2e8f0; margin: 15px 0;">
                <ul style="margin:0; padding-left: 20px; font-size: 0.9rem; color: #334155; font-weight: 600;">
                    {news_li_html}
                </ul>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)