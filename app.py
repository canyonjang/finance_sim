import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
import gspread  # 데이터를 한 줄씩 추가하기 위한 라이브러리

# 1. 페이지 설정
st.set_page_config(page_title="재무 설계 스트레스 테스트", layout="wide")

# 2. 구글 시트 Append 함수 정의
def append_to_gsheet(data_list):
    try:
        # Streamlit secrets에서 보안 정보 가져오기
        scope = ["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["connections"]["gsheets"]
        credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(credentials)
        
        # 시트 이름으로 열기 (실제 교수님의 시트 이름으로 확인 필요)
        sheet = client.open("Finance_Project_Results").sheet1
        
        # 마지막 행에 데이터 추가
        sheet.append_row(data_list)
        return True
    except Exception as e:
        st.error(f"제출 중 오류 발생: {e}")
        return False

# 3. 상태 관리 변수
if 'checked_scenarios' not in st.session_state:
    st.session_state.checked_scenarios = set()
if 'results_log' not in st.session_state:
    st.session_state.results_log = {}
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- UI 및 시뮬레이션 로직 (이전과 동일) ---
st.title("🎯 목표 기반 저축 및 투자 시뮬레이션")
st.markdown("---")

col_info1, col_info2 = st.columns(2)
with col_info1:
    user_name = st.text_input("👤 이름", placeholder="이름을 입력하세요")
with col_info2:
    user_id = st.text_input("🆔 학번", placeholder="학번을 입력하세요")

# 입력창 잠금 로직
current_choice = st.session_state.get(f"scenario_widget_{st.session_state.reset_counter}", "시나리오를 선택하세요")
is_active = (current_choice != "시나리오를 선택하세요")
is_finished = len(st.session_state.checked_scenarios) >= 4
disable_input = is_active or is_finished

# 사이드바 설정
st.sidebar.header("📋 1. 재무 목표 및 조건 설정")
goal_text = st.sidebar.text_input("목적", placeholder="예) 학비 마련", disabled=disable_input)
target_amount = st.sidebar.number_input("목표 금액 (만원)", 1000, 100000, 10000, 500, disabled=disable_input)
years = st.sidebar.slider("달성 기간 (년)", 1, 15, 5, disabled=disable_input)
monthly_deposit = st.sidebar.number_input("필요 월 저축액 (만원)", 10, 1000, 100, 10, disabled=disable_input)

st.sidebar.markdown("---")
st.sidebar.header("📈 2. 자산 배분 전략")
stock_ratio = st.sidebar.slider("주식 비중 (%)", 0, 100, 60, disabled=disable_input)
bond_ratio = 100 - stock_ratio

st.sidebar.markdown("---")
st.sidebar.header("🚨 3. 시나리오 선택")
scenario = st.sidebar.selectbox(
    "시나리오를 선택하세요",
    ["시나리오를 선택하세요", "1. 정상 시장", "2. 위기(인플레)", "3. 위기(폭락)", "4. 복합 위기"],
    key=f"scenario_widget_{st.session_state.reset_counter}"
)

# 시뮬레이션 엔진 및 결과 출력 (이전 코드와 동일하므로 요약)
if scenario != "시나리오를 선택하세요":
    # ... (시뮬레이션 계산 로직 동일) ...
    success_rate = 85.5 # 예시값
    st.session_state.checked_scenarios.add(scenario)
    st.session_state.results_log[scenario] = success_rate
    st.write(f"### {scenario} 분석 완료: 달성 확률 {success_rate}%")
    # 그래프 출력 등...

# 4. 하단 버튼 영역 (Append 방식 적용)
st.divider()
if len(st.session_state.checked_scenarios) >= 4:
    if not st.session_state.submitted:
        st.success("✅ 모든 시나리오 검증 완료! 이제 결과를 제출하세요.")
        if st.button("📤 최종 결과 시트에 기록하기", use_container_width=True):
            # 제출할 데이터 리스트 만들기
            data_to_save = [
                user_name, user_id, goal_text, target_amount, years, 
                monthly_deposit, stock_ratio, bond_ratio,
                st.session_state.results_log.get('1. 정상 시장', 0),
                st.session_state.results_log.get('2. 위기(인플레)', 0),
                st.session_state.results_log.get('3. 위기(폭락)', 0),
                st.session_state.results_log.get('4. 복합 위기', 0)
            ]
            
            with st.spinner("데이터를 시트에 기록 중입니다..."):
                if append_to_gsheet(data_to_save):
                    st.session_state.submitted = True
                    st.rerun()
    else:
        st.balloons()
        st.success("🎉 제출이 완료되었습니다! 교수님 시트에 성공적으로 기록되었습니다.")
        if st.button("🔄 처음부터 다시 하기"):
            st.session_state.checked_scenarios = set()
            st.session_state.results_log = {}
            st.session_state.submitted = False
            st.session_state.reset_counter += 1
            st.rerun()
else:
    st.warning("💡 4가지 시나리오를 모두 확인해야 제출 버튼이 나타납니다.")

st.markdown("<p style='text-align: center; font-size: 0.8em; color: gray;'>새로운 조건으로 시뮬레이션을 충분히 해본 뒤 결과 제출은 한 번만 하시기 바랍니다.</p>", unsafe_allow_html=True)

