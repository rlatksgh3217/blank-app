#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

#######################
# Page configuration
st.set_page_config(
    page_title="Titanic Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)
alt.themes.enable("default")

#######################
# CSS styling (투명배경 + 얇은 회색 경계선)
st.markdown("""
<style>
/* 레이아웃 여백 */
[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}
[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

/* Metric 카드: 투명 배경 + 얇은 회색 라인 */
[data-testid="stMetric"] {
    background-color: transparent !important;
    text-align: center;
    padding: 14px 0;
    border-radius: 10px;
    border: 1px solid rgba(0,0,0,0.12);   /* 얇은 회색 라인 */
    box-shadow: none !important;          /* 그림자 제거 */
}

/* Metric 라벨 중앙정렬 */
[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Metric 델타 아이콘 위치 미세 조정 */
[data-testid="stMetricDeltaIcon-Up"],
[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    transform: translateX(-50%);
}

/* 구분선 여백 보정 */
hr {
  margin: 0.8rem 0 1rem 0;
}

/* 데이터프레임 외곽선 라이트 그레이 */
div[data-testid="stDataFrame"] > div {
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 8px;
}

/* 사이드바 안 요소 간격 */
section[data-testid="stSidebar"] .block-container {
  padding-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv')  # 업로드한 분석 데이터

#######################
# Sidebar
with st.sidebar:
    st.title("🚢 Titanic Dashboard")
    st.caption("필터를 조정해 생존율과 분포 변화를 탐색하세요.")

    total_rows = len(df_reshaped)
    st.metric(label="총 승객 수", value=f"{total_rows:,}")

    st.divider()

    # 필터 위젯
    sex_options = sorted(df_reshaped["Sex"].dropna().unique().tolist())
    sel_sex = st.multiselect("성별 (Sex)", options=sex_options, default=sex_options)

    pclass_options = sorted(df_reshaped["Pclass"].dropna().unique().tolist())
    sel_pclass = st.multiselect("객실 등급 (Pclass)", options=pclass_options, default=pclass_options)

    embarked_options = [opt for opt in ["C", "Q", "S"] if opt in df_reshaped["Embarked"].dropna().unique()]
    sel_embarked = st.multiselect("승선 항구 (Embarked)", options=embarked_options, default=embarked_options)

    # 연령 / 요금 범위
    min_age = int(df_reshaped["Age"].min(skipna=True))
    max_age = int(df_reshaped["Age"].max(skipna=True))
    inc_na_age = st.checkbox("나이 결측치 포함", value=True)
    age_range = st.slider("연령 구간 (Age)", min_value=min_age, max_value=max_age, value=(min_age, max_age), step=1)

    min_fare = float(df_reshaped["Fare"].min(skipna=True))
    max_fare = float(df_reshaped["Fare"].max(skipna=True))
    fare_range = st.slider("요금 구간 (Fare)", min_value=float(min_fare), max_value=float(max_fare),
                           value=(float(min_fare), float(max_fare)))

    st.divider()

    # 필터 적용
    filtered = df_reshaped.copy()
    if sel_sex: filtered = filtered[filtered["Sex"].isin(sel_sex)]
    if sel_pclass: filtered = filtered[filtered["Pclass"].isin(sel_pclass)]
    if sel_embarked: filtered = filtered[filtered["Embarked"].isin(sel_embarked)]

    age_mask = filtered["Age"].between(age_range[0], age_range[1])
    if inc_na_age:
        age_mask = age_mask | filtered["Age"].isna()
    filtered = filtered[age_mask]

    filtered = filtered[filtered["Fare"].between(fare_range[0], fare_range[1])]

    st.metric(label="필터 적용 승객 수", value=f"{len(filtered):,}")
    st.session_state["filtered_df"] = filtered

#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

# -------------------------------
# col[0] 핵심 지표
with col[0]:
    st.subheader("🎯 핵심 지표")

    df = st.session_state["filtered_df"]

    total_passengers = len(df)
    survived = int(df["Survived"].sum())
    dead = total_passengers - survived
    survival_rate = (survived / total_passengers * 100) if total_passengers > 0 else 0

    st.metric("총 승객 수", f"{total_passengers:,}")
    st.metric("생존자 수", f"{survived:,}")
    st.metric("사망자 수", f"{dead:,}")

    st.divider()

    if total_passengers > 0:
        sex_survival = df.groupby("Sex")["Survived"].mean().mul(100).round(1).to_dict()
        for sex, rate in sex_survival.items():
            st.metric(f"{sex.capitalize()} 생존율", f"{rate}%")

    st.divider()

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=survival_rate,
        title={"text": "전체 생존율 (%)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "lightgreen"},
            "steps": [
                {"range": [0, 30], "color": "#ff4d4d"},
                {"range": [30, 60], "color": "#ffa64d"},
                {"range": [60, 100], "color": "#4dff88"},
            ],
        }
    ))
    gauge.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(gauge, use_container_width=True)

# -------------------------------
# col[1] 중앙 시각화
with col[1]:
    st.subheader("📊 인구/생존 시각화")
    df = st.session_state["filtered_df"]

    # 1) Embarked × Pclass 생존율 히트맵
    st.markdown("#### 🚢 승선 항구 × 객실 등급별 생존율")
    if len(df) > 0:
        pivot = df.pivot_table(values="Survived", index="Embarked", columns="Pclass", aggfunc="mean")
        pivot = (pivot * 100).round(1).reset_index().melt(id_vars="Embarked", var_name="Pclass", value_name="SurvivalRate")
        heatmap = alt.Chart(pivot).mark_rect().encode(
            x=alt.X("Pclass:O", title="객실 등급"),
            y=alt.Y("Embarked:O", title="승선 항구"),
            color=alt.Color("SurvivalRate:Q", scale=alt.Scale(scheme="blues"), title="생존율 %"),
            tooltip=["Embarked", "Pclass", "SurvivalRate"]
        ).properties(height=250)
        st.altair_chart(heatmap, use_container_width=True)
    else:
        st.info("데이터 없음 (필터 조건 확인)")

    st.divider()

    # 2) 연령 분포 (생존 여부별)
    st.markdown("#### 👶 연령 분포 (생존 여부별)")
    if len(df) > 0 and df["Age"].notna().sum() > 0:
        age_hist = px.histogram(
            df, x="Age", color="Survived",
            nbins=30, barmode="overlay",
            color_discrete_map={0: "red", 1: "green"},
            labels={"Survived": "생존 여부"}
        )
        age_hist.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(age_hist, use_container_width=True)
    else:
        st.info("연령 데이터가 부족합니다.")

    st.divider()

    # 3) 요금 vs 연령 산점도
    st.markdown("#### 💰 요금 vs 연령 산점도")
    if len(df) > 0 and df["Age"].notna().sum() > 0:
        scatter = px.scatter(
            df, x="Age", y="Fare", color="Survived",
            color_discrete_map={0: "red", 1: "green"},
            labels={"Survived": "생존 여부"},
            hover_data=["Pclass", "Sex", "Embarked"]
        )
        scatter.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(scatter, use_container_width=True)
    else:
        st.info("산점도를 그릴 수 있는 데이터가 부족합니다.")

# -------------------------------
# col[2] 요약 & 설명
with col[2]:
    st.subheader("📌 요약 & 설명")

    df = st.session_state["filtered_df"]

    st.markdown("#### 🏆 그룹별 생존율 TOP5")
    if len(df) > 0:
        group_cols = ["Sex", "Pclass", "Embarked"]
        grouped = (
            df.groupby(group_cols)["Survived"]
            .mean()
            .mul(100)
            .round(1)
            .reset_index()
            .rename(columns={"Survived": "SurvivalRate"})
        )

        top5 = grouped.sort_values("SurvivalRate", ascending=False).head(5)
        st.dataframe(top5, use_container_width=True)

        st.markdown("#### ⚠️ 그룹별 생존율 하위5")
        bottom5 = grouped.sort_values("SurvivalRate", ascending=True).head(5)
        st.dataframe(bottom5, use_container_width=True)
    else:
        st.info("데이터 없음 (필터 조건 확인)")

    st.divider()
    st.markdown("#### ℹ️ About")
    st.markdown("""
    - **데이터 출처**: [Kaggle Titanic Dataset](https://www.kaggle.com/c/titanic)  
    - **변수 설명**
        - `Survived`: 1 = 생존, 0 = 사망  
        - `Pclass`: 객실 등급  
        - `Sex`: 성별  
        - `Age`: 나이  
        - `Fare`: 운임 요금  
        - `Embarked`: 승선 항구 (C, Q, S)  
    """)
