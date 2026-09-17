import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 검색 엔진 최적화(SEO) 및 제목 설정 (구글 노출용 '신보만세' 키워드 탑재)
st.set_page_config(page_title="신보만세 - 신용보증기금 맞춤형 실시간 한국 기업 리스크 스크리너", layout="wide")
st.title("🏢 신보만세 (SHINBO-MANSE) : Live Corporate Risk Screen")
st.markdown("### 📊 신용보증기금 심사역을 위한 대한민국 전 상장사 부실 징후 실시간 모니터링 대시보드")
st.markdown("글로벌 금융 파이프라인(yfinance)을 활용하여 인증키 없이 한국 기업의 이자보상배율·부채비율을 실시간 검증합니다.")

# 2. 사이드바 설정 (인증키 칸 완전 제거 ➡️ 편의성 극대화)
st.sidebar.header("🔍 분석 대상 설정")
corp_code_input = st.sidebar.text_input("분석할 한국 상장사 6자리 종목코드 입력 (예: 005930, 000660, 005380)", "005930")
bsns_year = st.sidebar.selectbox("분석 회계 연도 선택", ["2024", "2023", "2022"], index=0)

# 한국 기업 유효성 검증 및 yfinance 티커 자동 전환 함수 (.KS 또는 .KQ 자동 매칭)
def get_korean_ticker(code):
    clean_code = code.strip()
    if len(clean_code) != 6 or not clean_code.isdigit():
        return None
    
    # 1순위: 코스피(.KS)로 먼저 테스트 시도
    kospi_ticker = f"{clean_code}.KS"
    stock = yf.Ticker(kospi_ticker)
    try:
        # 실제 데이터가 존재하는지 가볍게 확인
        if stock.info and 'longName' in stock.info:
            return kospi_ticker, "KOSPI"
    except Exception:
        pass
        
    # 2순위: 실패 시 코스닥(.KQ)으로 테스트 시도
    kosdaq_ticker = f"{clean_code}.KQ"
    stock = yf.Ticker(kosdaq_ticker)
    try:
        if stock.info and 'longName' in stock.info:
            return kosdaq_ticker, "KOSDAQ"
    except Exception:
        pass
        
    return None

if st.sidebar.button("📊 실시간 리스크 스크리닝 시작"):
    target_code = corp_code_input.strip()
    
    with st.spinner("글로벌 금융 서버 통신 및 실시간 한국 기업 데이터 분석 중..."):
        # 코스피/코스닥 자동 매칭 파이프라인 가동
        ticker_info = get_korean_ticker(target_code)
        
        if not ticker_info:
            st.error("❌ 유효한 대한민국 상장 종목코드가 아니거나 데이터를 가져올 수 없습니다. 다시 확인해 주세요. (예: 삼성전자 005930, 현대차 005380)")
        else:
            yf_ticker, market_type = ticker_info
            
            try:
                # yfinance 데이터 실시간 로드
                stock = yf.Ticker(yf_ticker)
                info = stock.info
                company_name = info.get('longName', f"한국 상장기업 ({target_code})")
                
                # 재무제표 데이터 추출
                balance_sheet = stock.balance_sheet
                financials = stock.financials
                
                # 연도 매칭 우회 선택 엔진 구현 (yfinance 인덱스는 datetime 형태임)
                target_col = None
                for col in balance_sheet.columns:
                    if str(col.year) == bsns_year:
                        target_col = col
                        break
                
                if target_col is None:
                    st.error(f"❌ 선택하신 {bsns_year}년도 공시 데이터가 아직 야후 금융 서버에 동기화되지 않았습니다. 다른 연도를 선택해 주세요.")
                else:
                    # 회계 계정 다중 매칭 필터 시스템 (한국 기업 고유 계정명 대응)
                    def get_financial_val(df, keys, date_col):
                        for k in keys:
                            if k in df.index:
                                val = df.loc[k, date_col]
                                # 시리즈 형태로 반환될 경우 첫 값 추출
                                if isinstance(val, pd.Series):
                                    val = val.iloc[0]
                                return float(val) if not pd.isna(val) else None
                        return None

                    # 핵심 4대 재무 정보 실시간 추출
                    total_assets = get_financial_val(balance_sheet, ['Total Assets'], target_col)
                    total_equity = get_financial_val(balance_sheet, ['Total Equity Gross Minority Interest', 'Stockholders Equity', 'Total Stockholder Equity'], target_col)
                    op_income = get_financial_val(financials, ['EBIT', 'Operating Income'], target_col)
                    interest_expense = get_financial_val(financials, ['Interest Expense', 'Interest Expense Non Operating'], target_col)
                    
                    if total_assets and total_equity and op_income:
                        # CPA 회계 항등식 및 논리 연산 가동
                        total_liab = total_assets - total_equity
                        debt_ratio = (total_liab / total_equity) * 100 if total_equity > 0 else 0
                        
                        if interest_expense and interest_expense > 0:
                            interest_coverage = op_income / interest_expense
                        else:
                            interest_coverage = 999.0 # 무차입 경영 우량기업 예외 방어
                        
                        # 3. 대시보드 화면 출력 (100% 라이브 데이터)
                        st.success(f"🟢 [라이브 데이터 연동] 글로벌 금융 엔진을 통해 {market_type} 시장 실시간 데이터 수신 완료")
                        st.subheader(f"🏢 {company_name} ({target_code}) - {bsns_year}년도 신용 분석 결과")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric(label="📊 이자보상배율 (Interest Coverage Ratio)", value=f"{interest_coverage:.2f} 배")
                            st.metric(label="📉 부채비율 (Debt-to-Equity Ratio)", value=f"{debt_ratio:.1f} %")
                            
                            if interest_coverage < 1.0:
                                st.error("🔴 **한계기업 위협 (Distress)**: 영업이익으로 이자비용조차 감당하지 못하는 잠재적 부실 한계기업입니다. 신보 보증 심사 시 고위험군 관리가 필요합니다.")
                            elif 1.0 <= interest_coverage < 1.5:
                                st.warning("🟡 **관찰 대상 기업 (Grey Zone)**: 이자 지급 능력의 완급 조절이 필요하며 부채비율 모니터링 강화를 권고합니다.")
                            else:
                                st.success("🟢 **우량 보증 대상 (Safe)**: 이자 상환 능력이 매우 충분하며 재무 안정성이 뛰어난 신보 적극 지원 대상 기업군입니다.")
                                
                        with col2:
                            # 리스크 계기판 시각화
                            fig = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = interest_coverage,
                                domain = dict(x=tuple([0.0, 1.0]), y=tuple([0.0, 1.0])),
                                title = dict(text="신보 이자보상배율 건전성 계기판"),
                                gauge = dict(
                                    axis = dict(range=tuple([-2.0, 5.0])),
                                    bar = dict(color="black"),
                                    steps = [
                                        dict(range=tuple([-2.0, 1.0]), color="red"),
                                        dict(range=tuple([1.0, 1.5]), color="orange"),
                                        dict(range=tuple([1.5, 5.0]), color="green")
                                    ]
                                )
                            ))
                            st.plotly_chart(fig, use_container_width=True)
                            
                        # 요약 데이터 테이블 출력
                        st.markdown("### 📋 신보 전용 리스크 스크리닝 요약표")
                        df_res = pd.DataFrame({
                            "핵심 리스크 지표": ["이자보상배율 (배)", "부채비율 (%)", "영업이익 (원)", "이자비용 (원)"],
                            "검증 결과": [f"{interest_coverage:.2f}", f"{debt_ratio:.1f}", f"{op_income:,.0f}", f"{interest_expense:,.0f}"],
                            "신보 심사역 가이드라인": [
                                "1.0 미만 시 보증 제한 한계기업 의심 (3년 연속 지속 여부 확인 요망)",
                                "통상 200% 이하 안정권, 초과 시 레버리지 위험 관리 필요",
                                "기업의 본질적인 현금 창출력 및 수익성 대변",
                                "금융 비용 부담도로서 시장 금리 인상 시 취약성 판단 기준"
                            ]
                        })
                        st.table(df_res)
                    else:
                        st.error("❌ 해당 기업의 핵심 회계 항목(자산/자본/영업이익) 중 일부가 누락되어 분석할 수 없습니다. 금융/지주사 등 표준 양식과 다른 업종일 수 있습니다.")
                        
            except Exception as e:
                st.error(f"⚠️ 실시간 데이터 처리 중 오류 발생: {e}. 잠시 후 다시 시도해 주세요.")
