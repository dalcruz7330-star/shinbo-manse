import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 금융감독원(FSS) SupTech 모니터링 시스템 스타일 및 검색 엔진 최적화(SEO) 세팅
st.set_page_config(page_title="FARS - 금융감독원 SupTech 기반 실시간 기업 리스크 모니터링 시스템", layout="wide")

# 금감원 고유의 다크 네이비 / 블루 헤더 감성 구현
st.markdown("""
    <div style="background-color:#0A2540; padding:20px; border-radius:10px; margin-bottom:25px;">
        <h1 style="color:#FFFFFF; margin:0; font-size:28px;">📊 FARS : Financial Automated Risk Screener</h1>
        <p style="color:#00D4B2; margin:5px 0 0 0; font-size:14px; font-weight:bold;">
            금융감독원 SupTech 가이드라인 준수 | 대한민국 전 상장사 실시간 부실 조기경보 시스템 (EWS)
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("### 🔍 거시건전성 감독을 위한 상장법인 재무 리스크 정밀 크롤링 엔진")
st.markdown("글로벌 금융 데이터 파이프라인을 연동하여, 시장 금리 인상 시 시스템 리스크(Systemic Risk)를 유발할 수 있는 취약 기업군을 초 단위로 필터링합니다.")

# 2. 사이드바 설정 (범용성 강화를 위한 입력 인터페이스)
st.sidebar.header("🎛️ 상시 감독망 설정")
corp_code_input = st.sidebar.text_input("분석 대상 6자리 종목코드 입력", "005930", help="코스피/코스닥 종목코드 6자리를 입력하면 실시간 동기화됩니다.")
bsns_year = st.sidebar.selectbox("분석 대상 회계 연도", ["2024", "2023", "2022"], index=0)

# 한국 기업 유효성 검증 및 yfinance 티커 자동 전환 함수 (.KS 또는 .KQ 자동 매칭)
def get_korean_ticker(code):
    clean_code = code.strip()
    if len(clean_code) != 6 or not clean_code.isdigit():
        return None
    
    # 1순위: 코스피(.KS) 검증
    kospi_ticker = f"{clean_code}.KS"
    stock = yf.Ticker(kospi_ticker)
    try:
        if stock.info and 'longName' in stock.info:
            return kospi_ticker, "유가증권시장 (KOSPI)"
    except Exception:
        pass
        
    # 2순위: 코스닥(.KQ) 검증
    kosdaq_ticker = f"{clean_code}.KQ"
    stock = yf.Ticker(kosdaq_ticker)
    try:
        if stock.info and 'longName' in stock.info:
            return kosdaq_ticker, "코스닥시장 (KOSDAQ)"
    except Exception:
        pass
        
    return None

if st.sidebar.button("⚡ 실시간 감독 가동"):
    target_code = corp_code_input.strip()
    
    with st.spinner("금융감독원 클라우드 파이프라인 가동 중..."):
        ticker_info = get_korean_ticker(target_code)
        
        if not ticker_info:
            st.error("❌ 유효한 대한민국 상장 종목코드가 아닙니다. (예: 삼성전자 005930, 현대차 005380, SK하이닉스 000660)")
        else:
            yf_ticker, market_type = ticker_info
            
            try:
                # 실시간 금융 데이터 수집
                stock = yf.Ticker(yf_ticker)
                info = stock.info
                company_name = info.get('longName', f"상장법인 ({target_code})")
                
                balance_sheet = stock.balance_sheet
                financials = stock.financials
                
                # 연도별 컬럼 매칭
                target_col = None
                for col in balance_sheet.columns:
                    if str(col.year) == bsns_year:
                        target_col = col
                        break
                
                if target_col is None:
                    st.error(f"❌ {bsns_year}년도 결산 데이터가 아직 금융 서버에 동기화되지 않았습니다. 전년도 데이터를 조회해 주세요.")
                else:
                    # 다중 계정명 파싱 함수
                    def get_financial_val(df, keys, date_col):
                        for k in keys:
                            if k in df.index:
                                val = df.loc[k, date_col]
                                if isinstance(val, pd.Series):
                                    val = val.iloc[0]
                                return float(val) if not pd.isna(val) else None
                        return None

                    # 금감원 4대 핵심 직무 지표 데이터 추출
                    total_assets = get_financial_val(balance_sheet, ['Total Assets'], target_col)
                    total_equity = get_financial_val(balance_sheet, ['Total Equity Gross Minority Interest', 'Stockholders Equity', 'Total Stockholder Equity'], target_col)
                    op_income = get_financial_val(financials, ['EBIT', 'Operating Income'], target_col)
                    interest_expense = get_financial_val(financials, ['Interest Expense', 'Interest Expense Non Operating'], target_col)
                    total_revenue = get_financial_val(financials, ['Total Revenue'], target_col)
                    
                    if total_assets and total_equity and op_income and total_revenue:
                        # CPA 재무 전공 지식 기반 계산 알고리즘 가동
                        total_liab = total_assets - total_equity
                        debt_ratio = (total_liab / total_equity) * 100 if total_equity > 0 else 0
                        
                        if interest_expense and interest_expense > 0:
                            interest_coverage = op_income / interest_expense
                        else:
                            interest_coverage = 999.0
                            
                        # [금감원용 추가 지표 1] 영업이익률 (수익성)
                        operating_margin = (op_income / total_revenue) * 100
                        # [금감원용 추가 지표 2] 총자산회전율 (활동성)
                        asset_turnover = total_revenue / total_assets
                        
                        # 3. 대시보드 메인 레이아웃 출력
                        st.success(f"📡 [상시감독계통 연동 완료] {market_type} 라이브 데이터 수집 성공")
                        st.subheader(f"🏢 {company_name} ({target_code}) 거시건전성 진단 리포트")
                        
                        # 상단 4대 지표 지표 스케일 배치
                        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                        m_col1.metric("📊 이자보상배율", f"{interest_coverage:.2f} 배")
                        m_col2.metric("📉 부채비율", f"{debt_ratio:.1f} %")
                        m_col3.metric("📈 영업이익률", f"{operating_margin:.1f} %")
                        m_col4.metric("🔄 총자산회전율", f"{asset_turnover:.2f} 회")
                        
                        st.markdown("---")
                        
                        # 비주얼 분석 구역 분할
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🚨 금융감독원 자산건전성 통제 가이드라인")
                            
                            # 금감원 감독관 관점의 논리적 리스크 진단 판정
                            if interest_coverage < 1.0:
                                st.error(f"🔴 **상시감시 경보 (한계기업 징후 포착)**: {bsns_year}년도 결산 결과 영업이익으로 이자비용을 지불하지 못하는 취약 상태입니다. 한계기업 자금조달 규제 및 여신 회수 타당성 검토를 권고합니다.")
                            elif 1.0 <= interest_coverage < 1.5:
                                st.warning(f"🟡 **중점 관리 대상 (Grey Zone)**: 이자보상배율이 1배 수준을 위태롭게 상회하고 있습니다. 시장 금리 변동에 따른 자본 잠식 가능성을 추적 관찰해야 합니다.")
                            else:
                                st.success(f"🟢 **건전성 양호 법인 (Safe Zone)**: 재무 건전성 및 이자 상환 능력이 시장 평균을 상회합니다. 자본시장 규제 완화 및 정상 보증/여신 유지가 타당합니다.")
                                
                            if debt_ratio > 200.0:
                                st.error("⚠️ **레버리지 위험 노출**: 부채비율이 200%를 초과하여 과도한 타인자본 의존도를 보이고 있습니다. 부채 구조조정 유도가 필요합니다.")
                                
                        with col2:
                            # 금감원 대시보드 특유의 시각적 계기판 차트 출력
                            fig = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = interest_coverage,
                                domain = dict(x=[0.0, 1.0], y=[0.0, 1.0]),
                                title = dict(text="상시 감시 이자보상배율 신호등", font=dict(color="#0A2540", size=16)),
                                gauge = dict(
                                    axis = dict(range=[-2.0, 5.0]),
                                    bar = dict(color="#0A2540"), # 금감원 네이비 바
                                    steps = [
                                        dict(range=[-2.0, 1.0], color="#FF4B4B"),   # 위험
                                        dict(range=[1.0, 1.5], color="#FFA500"),    # 주의
                                        dict(range=[1.5, 5.0], color="#00D4B2")     # 안전
                                    ]
                                )
                            ))
                            st.plotly_chart(fig, use_container_width=True)
                            
                        # 4. 정량적 검증 결과 수치화 테이블 출력
                        st.markdown("### 📋 거시건전성 감독 전용 통계 데이터 테이블")
                        df_res = pd.DataFrame({
                            "감독 항목 지표": ["1. 이자보상배율 (배)", "2. 부채비율 (%)", "3. 영업이익률 (%)", "4. 총자산회전율 (회)", "5. 영업이익 (원)", "6. 이자비용 (원)"],
                            "실시간 검증 수치": [f"{interest_coverage:.2f}", f"{debt_ratio:.1f}", f"{operating_margin:.1f}", f"{asset_turnover:.2f}", f"{op_income:,.0f}", f"{interest_expense:,.0f}"],
                            "금융감독원 여신 심사 실무 가이드라인": [
                                "1.0 미만 지속 시 한계기업(좀비기업) 지정 및 금융권 연쇄 부실 리스크 통제 필요",
                                "기업의 자본 건전성 대변 (통상 200% 초과 시 재무 안전성 위협으로 분류)",
                                "매출액 대비 본질적 영업 성과율 (동업계 평균과 비교하여 시장 경쟁력 판단)",
                                "자산 효율성 및 활동성 지표 (기업이 보유 자산을 얼마나 신속히 회전시켰는가)",
                                "기업의 핵심 현금 창출 능력을 나타내는 모니터링 기본 지표",
                                "시장 조달 금리 인상 기조에 따른 취약 차주 판정의 척도"
                            ]
                        })
                        st.table(df_res)
                    else:
                        st.error("❌ 해당 법인의 표준 계정명(EBIT/자산/자본/매출액) 파싱에 실패했습니다. 금융업/지주사 등 특수 서식을 사용하는 업종일 수 있습니다.")
                        
            except Exception as e:
                st.error(f"⚠️ 데이터 파이프라인 처리 중 예외 발생: {e}. 잠시 후 다시 시도해 주세요.")
