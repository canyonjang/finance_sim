import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="재무 설계 스트레스 테스트", layout="wide")

# 2. 구글 시트 연결 초기화
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("구글 시트 연결 설정(Secrets)이 필요합니다.")

# 3. 상태 관리
if 'checked_scenarios' not in st.session_state:
    st.session_state.checked_scenarios = set()
if 'results_log' not in st.session_state:
    st.session_state.results_log = {}

st.title("🎯 목표 기반 저축 및 투자 시뮬레이션")
st.markdown("---")

# 4. 학생 정보 입력
col_info1, col_info2 = st.columns(2)
with col_info1:
    user_name = st.text_input("👤 이름", placeholder="이름을 입력하세요")
with col_info2:
    user_id = st.text_input("🆔 학번", placeholder="학번을 입력하세요")

# 5. 사이드바 설정
st.sidebar.header("📋 1. 재무 목표 및 조건 설정")
goal_text = st.sidebar.text_input("목적", "5년 뒤 대학원 학비 및 전세 보증금 마련")
target_amount = st.sidebar.number_input("목표 금액 (만원)", 1000, 100000, 10000, 500)
years = st.sidebar.slider("달성 기간 (년)", 1, 15, 5)
monthly_deposit = st.sidebar.number_input("필요 월 저축액 (만원)", 10, 1000, 100, 10)

st.sidebar.markdown("---")
st.sidebar.header("📈 2. 자산 배분 전략")
stock_ratio = st.sidebar.slider("주식 비중 (%)", 0, 100, 60)
bond_ratio = 100 - stock_ratio

st.sidebar.markdown("---")
st.sidebar.header("🚨 3. 시나리오 선택")
scenario_options = ["1. 정상 시장", "2. 위기(인플레)", "3. 위기(폭락)", "4. 복합 위기"]
scenario = st.sidebar.selectbox("현재 확인 중인 상황", scenario_options)

# 6. 시나리오별 로직
r_s, r_b = 0.10, 0.04
v_s, v_b = 0.18, 0.05
rho = -0.1

if "2. 위기(인플레)" in scenario:
    r_s -= 0.05; r_b -= 0.03
    rho = 0.3
elif "3. 위기(폭락)" in scenario:
    r_s -= 0.15; v_s *= 1.5
    rho = -0.5
elif "4. 복합 위기" in scenario:
    r_s -= 0.20; r_b -= 0.05
    v_s *= 1.8; v_b *= 1.2
    rho = 0.5

# 7. 포트폴리오 지표 계산
w_s, w_b = stock_ratio/100, bond_ratio/100
port_return = (w_s * r_s) + (w_b * r_b)
port_risk = np.sqrt((w_s*v_s)**2 + (w_b*v_b)**2 + (2*w_s*w_b*v_s*v_b*rho))

# 8. 시뮬레이션
n_sims, n_steps, dt = 1000, years * 12, 1/12
sim_results = np.zeros((n_steps, n_sims))
for i in range(n_sims):
    balance = 0
    for t in range(n_steps):
        shock = np.random.normal(port_return * dt, port_risk * np.sqrt(dt))
        balance = (balance + monthly_deposit) * (1 + shock)
        sim_results[t, i] = balance

success_rate = np.mean(sim_results[-1, :] >= target_amount) * 100
p10 = np.percentile(sim_results[-1, :], 10)
st.session_state.checked_scenarios.add(scenario)
st.session_state.results_log[scenario] = success_rate

# 9. 결과 출력
c1, c2 = st.columns(2)
with c1:
    st.subheader("1. 재무 목표 설정")
    st.write(f"**목적:** {goal_text}")
    st.write(f"**목표 금액:** {target_amount:,} 만원")
    st.write(f"**달성 기간:** {years} 년")
    st.write(f"**필요 월 저축액:** {monthly_deposit:,} 만원")
with c2:
    st.subheader("2. 자산 배분 전략")
    st.write(f"**주식 비중:** {stock_ratio}% / **채권 비중:** {bond_ratio}%")
    st.write(f"**기대 수익률:** {port_return*100:.2f}% / **위험:** {port_risk*100:.2f}%")

st.divider()
st.subheader(f"📊 {scenario} 결과")
st.write(f"**목표 달성 확률:** {success_rate:.1f}% / **하위 10% 최종 자산:** {int(p10):,} 만원")

fig = go.Figure()
t_axis = np.arange(1, n_steps + 1) / 12
fig.add_trace(go.Scatter(x=t_axis, y=np.percentile(sim_results, 50, axis=1), name="평균 경로"))
fig.add_trace(go.Scatter(x=t_axis, y=np.percentile(sim_results, 10, axis=1), name="하위 10%", line=dict(dash='dot')))
fig.add_hline(y=target_amount, line_dash="dash")
st.plotly_chart(fig, use_container_width=True)

# 10. 제어 영역 (에러 수정 포인트: color 옵션 제거)
st.divider()
if len(st.session_state.checked_scenarios) < 4:
    st.warning(f"💡 현재 {len(st.session_state.checked_scenarios)}/4 시나리오를 확인했습니다. 모두 확인해야 제출 가능합니다.")
else:
    st.success("✅ 모든 분석 완료!")
    bc1, bc2 = st.columns(2)
    
    if bc1.button("🔄 조건 다시 입력", use_container_width=True):
        st.session_state.checked_scenarios = set()
        st.rerun()

    # 버튼에서 color="primary" 인자를 삭제하여 호환성을 높였습니다.
    if bc2.button("📤 결과 제출하기", use_container_width=True):
        if not user_name or not user_id:
            st.error("이름과 학번을 입력해주세요.")
        else:
            try:
                submission = pd.DataFrame([{
                    "이름": user_name, "학번": user_id, "목적": goal_text,
                    "목표금액": target_amount, "기간": years, "월저축액": monthly_deposit,
                    "주식비중": stock_ratio, "채권비중": bond_ratio,
                    "정상_확률": st.session_state.results_log.get("1. 정상 시장"),
                    "인플레_확률": st.session_state.results_log.get("2. 위기(인플레)"),
                    "폭락_확률": st.session_state.results_log.get("3. 위기(폭락)"),
                    "복합_확률": st.session_state.results_log.get("4. 복합 위기")
                }])
                existing_df = conn.read(worksheet="Sheet1")
                updated_df = pd.concat([existing_df, submission], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.balloons()
                st.success("제출 완료!")
            except Exception as e:
                st.error(f"제출 오류: {e}")

    st.markdown("<p style='text-align: center; font-size: 0.8em;'>새로운 조건으로 시나리오를 충분히 테스트한 후 제출은 한 번만 하시기 바랍니다.</p>", unsafe_allow_html=True)
