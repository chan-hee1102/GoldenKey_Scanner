import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os

# --- [1] 페이지 기본 설정 ---
st.set_page_config(layout="wide", page_title="Golden Key Pro | 퀀트 대시보드")

THEME_DB_FILE = "theme_db.csv"

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

    /* 🌟 실시간 주도주 리스트 간격 최적화 (모바일 한 줄 출력용) 🌟 */
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

    /* 구역별 비율 조정: 이름과 테마를 왼쪽으로 밀착 */
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

    /* 🌟 우측 섹터 리스트 칼정렬 (일직선 정렬) 🌟 */
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

    /* 왼쪽 종목명 영역 */
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

    /* 오른쪽 데이터 영역 (수직 일직선 정렬 핵심) */
    .sector-item-right {
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }
    .val-rate {
        width: 65px; /* 상승률 고정 너비로 삐뚤빼뚤 방지 */
        text-align: right;
        font-weight: 800;
        margin-right: 12px;
    }
    .val-vol {
        width: 75px; /* 거래대금 고정 너비 */
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

    /* 사이드바 테마 스타일 */
    .sidebar-theme-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        padding: 8px 10px;
        margin-bottom: 5px;
        border-radius: 6px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 🌟 전역 색상 설정 (글로벌-국내 동기화)
# ==========================================
SECTOR_COLORS = {
    '반도체': '#dbeafe', '로봇/AI': '#ede9fe', '2차전지': '#d1fae5', 
    '전력/원전': '#fef3c7', '바이오': '#fee2e2', '방산/우주': '#f1f5f9', 
    '금융/지주': '#f3f4f6', '개별주': '#ffffff'
}

CUSTOM_SECTOR_MAP = {"온코닉테라퓨틱스": "바이오", "현대ADM": "바이오"}

# --- [2] 미 증시 및 글로벌 테마 데이터 엔진 ---
def get_global_market_status():
    indices = [
        {"name": "나스닥 (기술주)", "value": "18,302", "delta": "+1.24%"},
        {"name": "S&P 500 (우량주)", "value": "5,137", "delta": "+0.85%"},
        {"name": "필라델피아 반도체", "value": "4,929", "delta": "+2.10%"}
    ]
    themes = [
        {"name": "반도체", "delta": "+3.5%", "color": SECTOR_COLORS['반도체']},
        {"name": "로봇/AI", "delta": "+2.8%", "color": SECTOR_COLORS['로봇/AI']},
        {"name": "2차전지", "delta": "-1.2%", "color": SECTOR_COLORS['2차전지']},
        {"name": "전력/원전", "delta": "+1.1%", "color": SECTOR_COLORS['전력/원전']}
    ]
    briefing = "미국 엔비디아(AI)발 훈풍이 지속되고 있습니다. 국내 반도체 소부장과 AI 관련주들의 강한 동조화가 예상됩니다."
    return indices, themes, briefing

# --- [3] 준비 엔진: 테마 DB 전체 크롤링 및 저장 ---
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
            time.sleep(0.05)
        pd.DataFrame(list(theme_dict.items()), columns=['종목명', '테마']).to_csv(THEME_DB_FILE, index=False, encoding='utf-8-sig')
        status_text.success("✅ 테마 DB 업데이트 완료!"); time.sleep(1); st.rerun()
    except Exception as e: status_text.error(f"오류: {e}")

# --- [4] 핵심 함수: 특정 시장 데이터 크롤링 ---
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

# --- [5] 메가 섹터 분류 및 데이터 포맷팅 ---
def apply_mega_sector(row):
    stock_name = row['종목명']; t = str(row['테마'])
    if stock_name in CUSTOM_SECTOR_MAP: return CUSTOM_SECTOR_MAP[stock_name]
    keywords = {
        '반도체': ['반도체', 'HBM', 'CXL', '온디바이스', '메모리', 'NPU', '유리기판'],
        '2차전지': ['2차전지', '리튬', '전고체', '배터리', '양극재'],
        '바이오': ['바이오', '제약', '신약', '임상', '비만'],
        '로봇/AI': ['로봇', 'AI', '인공지능', '챗봇'],
        '전력/원전': ['전력', '전선', '원자력', '변압기'],
        '방산/우주': ['방산', '우주', '항공', '조선'],
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

# --- [6] UI 레이아웃 구성 ---

# 1. 사이드바
with st.sidebar:
    st.title("🌐 글로벌 증시")
    indices, themes, briefing = get_global_market_status()
    for idx in indices: st.metric(label=idx['name'], value=idx['value'], delta=idx['delta'], delta_color="normal" if '+' in idx['delta'] else "inverse")
    st.markdown("---")
    st.subheader("🇺🇸 미국 테마 흐름")
    for t in themes:
        v_c = "#ef4444" if '+' in t['delta'] else "#2563eb"
        st.markdown(f'<div class="sidebar-theme-row" style="background-color: {t["color"]};"><span style="color: #1e293b;">{t["name"]}</span><span style="color: {v_c};">{t["delta"]}</span></div>', unsafe_allow_html=True)
    st.info(f"📍 **전문가 브리핑:**\n{briefing}")

# 2. 메인 화면 상단 타이틀 & 리프레시 버튼
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
        if st.button("🚀 실시간 스캔 실행", use_container_width=True):
            with st.spinner("시장 수급 분석 중..."):
                df_k = fetch_market_data(0, '코스피'); df_q = fetch_market_data(1, '코스닥')
                df = pd.concat([df_k, df_q], ignore_index=True)
                if not df.empty:
                    black_list = ['KODEX', 'TIGER', 'KBSTAR', 'ACE', 'SOL', '스팩', 'ETN']
                    df = df[~df['종목명'].str.contains('|'.join(black_list), na=False)]
                    df['등락률_num'] = pd.to_numeric(df['등락률'].str.replace('%|\+', '', regex=True), errors='coerce')
                    df['거래대금_num'] = pd.to_numeric(df['거래대금'].str.replace(',', ''), errors='coerce')
                    df = df.sort_values(by='거래대금_num', ascending=False).head(100)
                    df = df[df['등락률_num'] >= 4.0]
                    if os.path.exists(THEME_DB_FILE):
                        theme_df = pd.read_csv(THEME_DB_FILE)
                        df['테마'] = df['종목명'].map(dict(zip(theme_df['종목명'], theme_df['테마']))).fillna('-')
                    else: df['테마'] = '-'
                    df['섹터'] = df.apply(apply_mega_sector, axis=1)

                    st.subheader(f"🔥 실시간 주도주 ({len(df)}개)")
                    for _, row in df.iterrows():
                        bg = SECTOR_COLORS.get(row['섹터'], '#ffffff')
                        m_c = "market-kospi" if row['시장'] == '코스피' else "market-kosdaq"
                        rv = row['등락률_num']
                        rt_c = "#ef4444" if rv >= 20.0 else ("#22c55e" if rv >= 10.0 else "#1f2937")

                        st.markdown(f"""
                            <div class="stock-card">
                                <div class="left-zone">
                                    <span class="market-tag {m_c}">{row['시장']}</span>
                                    <span class="stock-name">{row['종목명']}</span>
                                </div>
                                <div class="center-zone">
                                    <span class="sector-badge" style="background: {bg}; color: #1e293b;">{row['섹터']}</span>
                                </div>
                                <div class="right-zone">
                                    <span style="color: {rt_c}; font-weight: 800; font-size: 1.1rem; min-width: 65px; text-align: right;">+{rv}%</span>
                                    <span class="stock-vol" style="font-size: 0.9rem; color: #64748b; font-weight: 500; min-width: 90px; text-align: right;">{format_volume_to_jo_eok(row['거래대금_num'])}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    # 우측 섹터 현황 업데이트 (정렬 보강)
                    with summary_placeholder.container():
                        sector_group = df[df['섹터'] != '개별주'].groupby('섹터').size().sort_values(ascending=False)
                        if not sector_group.empty:
                            for s_name, count in sector_group.items():
                                with st.expander(f"**{s_name}** ({count})", expanded=True):
                                    s_stocks = df[df['섹터'] == s_name].sort_values('등락률_num', ascending=False)
                                    for i, (idx, s_row) in enumerate(s_stocks.iterrows()):
                                        ldr = '<span class="leader-label">대장</span>' if i == 0 else ''
                                        s_rv = s_row['등락률_num']
                                        s_rt_c = "#ef4444" if s_rv >= 20.0 else ("#22c55e" if s_rv >= 10.0 else "#334155")
                                        
                                        st.markdown(f"""
                                        <div class="sector-item">
                                            <div class="sector-item-left">
                                                {ldr}<span class="sector-stock-name">{s_row['종목명']}</span>
                                            </div>
                                            <div class="sector-item-right">
                                                <span class="val-rate" style="color:{s_rt_c};">+{s_rv}%</span>
                                                <span class="val-vol">{format_volume_to_jo_eok(s_row['거래대금_num'])}</span>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else: st.info("주도 섹터 없음")
                else: st.info("데이터 없음")

with tab_analysis: st.info("📊 상세 분석 기능 준비 중")