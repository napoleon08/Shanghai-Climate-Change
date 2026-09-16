import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="상하이 기후 데이터 그래프",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# 흰색 배경 + 검은색 글씨
# ------------------------------------------------------------
st.markdown("""
<style>
.stApp { background: #FFFFFF !important; color: #111111 !important; }
.block-container { max-width: 1500px; padding-top: 1.5rem; }
p, span, label, h1, h2, h3, h4, li { color: #111111 !important; }
section[data-testid="stSidebar"] { background: #F5F5F5 !important; }
section[data-testid="stSidebar"] * { color: #111111 !important; }
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #D9D9D9;
    border-radius: 16px;
    padding: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,.05);
}
div[data-testid="stMetric"] * { color: #111111 !important; }
.hero {
    background: #FFFFFF;
    border: 1px solid #D9D9D9;
    border-radius: 20px;
    padding: 28px 32px;
    box-shadow: 0 4px 18px rgba(0,0,0,.06);
    margin-bottom: 22px;
}
.hero-title { color: #111111 !important; font-size: 2.5rem; font-weight: 800; }
.hero-subtitle { color: #333333 !important; font-size: 1.05rem; margin-top: 8px; }
.section-title { color: #111111 !important; font-size: 1.45rem; font-weight: 800; margin-top: 28px; }
.source-box {
    background: #FFFFFF; color: #111111 !important;
    border: 1px solid #D9D9D9; border-left: 5px solid #4C78A8;
    padding: 18px; border-radius: 12px;
}
.source-box * { color: #111111 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-title">🌏 상하이 기후 데이터 그래프</div>
  <div class="hero-subtitle">
    2000년부터 2025년까지 상하이의 기온과 강수량 변화를 분석합니다.
  </div>
</div>
""", unsafe_allow_html=True)

DATA_URL = "https://data.meteostat.net/monthly/58362.csv.gz"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    required = ["year", "month", "temp", "tmin", "tmax", "prcp"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("필요한 열을 찾을 수 없습니다: " + ", ".join(missing))

    for c in required:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df[(df["year"] >= 2000) & (df["year"] <= 2025)].copy()
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1),
        errors="coerce"
    )
    return df.sort_values("date")

try:
    df = load_data()
except Exception as e:
    st.error("기후 데이터를 불러오지 못했습니다.")
    st.write("데이터 주소 또는 인터넷 연결을 확인하세요.")
    st.code(str(e))
    st.stop()

if df.empty:
    st.error("2000년부터 2025년까지의 데이터를 찾을 수 없습니다.")
    st.stop()

st.sidebar.title("⚙️ 분석 설정")
year_range = st.sidebar.slider(
    "분석 기간", 2000, 2025, (2000, 2025)
)
show_monthly = st.sidebar.checkbox("월별 기후 분석 보기", True)
show_map = st.sidebar.checkbox("상하이 주변 지도 보기", True)

selected = df[
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1])
].copy()

annual = selected.groupby("year").agg(
    평균기온=("temp", "mean"),
    평균최저기온=("tmin", "mean"),
    평균최고기온=("tmax", "mean"),
    연강수량=("prcp", "sum")
).reset_index()

annual["기온차"] = annual["평균최고기온"] - annual["평균최저기온"]

latest = annual.iloc[-1]
warming_change = annual.iloc[-1]["평균기온"] - annual.iloc[0]["평균기온"]
trend_per_decade = None

if len(annual) >= 2:
    trend_per_decade = np.polyfit(
        annual["year"].to_numpy(),
        annual["평균기온"].to_numpy(),
        1
    )[0] * 10

st.markdown('<div class="section-title">📊 기후 대시보드</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("평균 기온", f"{latest['평균기온']:.1f} °C")
with c2:
    st.metric("연간 강수량", f"{latest['연강수량']:,.0f} mm")
with c3:
    st.metric(
        "10년당 기온 변화 추세",
        f"{trend_per_decade:+.2f} °C" if trend_per_decade is not None else "계산 불가"
    )
with c4:
    st.metric("평균 기온 범위", f"{latest['기온차']:.1f} °C")

# 그래프 1
st.markdown('<div class="section-title">🌡️ 그래프 1. 연도별 평균 기온 변화</div>', unsafe_allow_html=True)
fig1 = px.line(
    annual, x="year", y="평균기온", markers=True,
    labels={"year": "연도", "평균기온": "평균 기온 (°C)"},
    title="2000–2025 상하이 평균 기온 변화"
)
fig1.update_traces(
    mode="lines+markers",
    hovertemplate="연도: %{x}<br>평균 기온: %{y:.2f} °C<extra></extra>"
)
fig1.update_layout(
    height=520, hovermode="x unified",
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(color="#111111")
)
st.plotly_chart(fig1, use_container_width=True)
st.info("이 그래프에서는 상하이의 장기적인 평균 기온 변화와 기온 추세를 확인할 수 있습니다.")

# 그래프 2
st.markdown('<div class="section-title">📈 그래프 2. 최저·평균·최고 기온 비교</div>', unsafe_allow_html=True)
temp_long = annual.melt(
    id_vars="year",
    value_vars=["평균최저기온", "평균기온", "평균최고기온"],
    var_name="구분", value_name="기온"
)
fig2 = px.line(
    temp_long, x="year", y="기온", color="구분", markers=True,
    labels={"year": "연도", "기온": "기온 (°C)", "구분": "기온 종류"},
    title="연도별 기온 범위 변화"
)
fig2.update_layout(
    height=540, hovermode="x unified",
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(color="#111111")
)
st.plotly_chart(fig2, use_container_width=True)

# 그래프 3
st.markdown('<div class="section-title">🌧️ 그래프 3. 연도별 강수량 변화</div>', unsafe_allow_html=True)
fig3 = px.bar(
    annual, x="year", y="연강수량",
    labels={"year": "연도", "연강수량": "연간 강수량 (mm)"},
    title="연도별 상하이 강수량"
)
fig3.update_layout(
    height=520, paper_bgcolor="white", plot_bgcolor="white",
    font=dict(color="#111111")
)
st.plotly_chart(fig3, use_container_width=True)

# 월별 분석
if show_monthly:
    st.markdown('<div class="section-title">🗓️ 그래프 4. 월별 기후 특징</div>', unsafe_allow_html=True)

    monthly = selected.groupby("month").agg(
        평균기온=("temp", "mean"),
        평균최저기온=("tmin", "mean"),
        평균최고기온=("tmax", "mean"),
        평균강수량=("prcp", "mean")
    ).reset_index()

    month_names = {
        1:"1월",2:"2월",3:"3월",4:"4월",5:"5월",6:"6월",
        7:"7월",8:"8월",9:"9월",10:"10월",11:"11월",12:"12월"
    }
    monthly["월"] = monthly["month"].map(month_names)

    tab1, tab2 = st.tabs(["🌡️ 월별 기온", "🌧️ 월별 강수량"])

    with tab1:
        mlong = monthly.melt(
            id_vars=["month", "월"],
            value_vars=["평균최저기온", "평균기온", "평균최고기온"],
            var_name="구분", value_name="기온"
        )
        fig4 = px.line(
            mlong, x="월", y="기온", color="구분", markers=True,
            category_orders={"월": list(month_names.values())},
            labels={"월":"월", "기온":"기온 (°C)", "구분":"기온 종류"},
            title="월별 평균 기온 변화"
        )
        fig4.update_layout(
            height=480, paper_bgcolor="white", plot_bgcolor="white",
            font=dict(color="#111111")
        )
        st.plotly_chart(fig4, use_container_width=True)

    with tab2:
        fig5 = px.bar(
            monthly, x="월", y="평균강수량",
            category_orders={"월": list(month_names.values())},
            labels={"월":"월", "평균강수량":"평균 강수량 (mm)"},
            title="월별 평균 강수량"
        )
        fig5.update_layout(
            height=480, paper_bgcolor="white", plot_bgcolor="white",
            font=dict(color="#111111")
        )
        st.plotly_chart(fig5, use_container_width=True)

# 통계
st.markdown('<div class="section-title">🔎 기후 통계 분석</div>', unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)

warmest = annual.loc[annual["평균기온"].idxmax()]
wettest = annual.loc[annual["연강수량"].idxmax()]
coolest = annual.loc[annual["평균기온"].idxmin()]

with s1:
    st.metric("가장 더운 해", f"{int(warmest['year'])}년", f"{warmest['평균기온']:.2f} °C")
with s2:
    st.metric("강수량이 가장 많은 해", f"{int(wettest['year'])}년", f"{wettest['연강수량']:.0f} mm")
with s3:
    st.metric("가장 서늘한 해", f"{int(coolest['year'])}년", f"{coolest['평균기온']:.2f} °C")

# 지도
if show_map:
    st.markdown('<div class="section-title">🗺️ 상하이와 주변 지역</div>', unsafe_allow_html=True)
    st.write("상하이와 양쯔강 삼각주 주변 주요 도시의 위치를 인터랙티브 지도로 확인할 수 있습니다.")

    cities = pd.DataFrame({
        "도시":["Shanghai","Suzhou","Wuxi","Nantong","Jiaxing","Hangzhou","Ningbo"],
        "위도":[31.2304,31.2989,31.4912,31.9807,30.7461,30.2741,29.8683],
        "경도":[121.4737,120.5853,120.3119,120.8943,120.7555,120.1551,121.5440]
    })

    fig_map = px.scatter_map(
        cities, lat="위도", lon="경도", hover_name="도시",
        zoom=5.6, center={"lat":31.0,"lon":120.9},
        height=620, map_style="open-street-map",
        title="상하이와 양쯔강 삼각주 주변 지역"
    )
    fig_map.update_traces(marker=dict(size=14))
    fig_map.update_layout(margin=dict(l=0,r=0,t=55,b=0))
    st.plotly_chart(fig_map, use_container_width=True)

# 자동 분석
st.markdown('<div class="section-title">🧠 데이터로 확인할 수 있는 변화</div>', unsafe_allow_html=True)
direction = "상승했습니다" if warming_change > 0 else "하락했습니다"
st.write(
    f"선택한 기간의 첫해와 마지막 해를 비교하면 평균 기온은 "
    f"약 **{abs(warming_change):.2f} °C {direction}**."
)
if trend_per_decade is not None:
    st.write(
        f"선형 추세 계산 결과 평균 기온은 10년당 약 "
        f"**{trend_per_decade:+.2f} °C**의 변화를 보입니다."
    )
st.caption("※ 선형 추세는 과거 데이터의 통계적 변화 경향이며 미래를 확정적으로 예측하는 값은 아닙니다.")

# 데이터 표
st.markdown('<div class="section-title">📋 데이터 표</div>', unsafe_allow_html=True)
with st.expander("연도별 분석 데이터 보기"):
    st.dataframe(annual, use_container_width=True, hide_index=True)
with st.expander("월별 원본 데이터 보기"):
    st.dataframe(selected, use_container_width=True, hide_index=True)

# 출처
st.markdown("""
<div class="source-box">
<b>데이터 출처:</b> Meteostat 월별 기후 데이터<br>
<b>관측 지점:</b> Shanghai / 58362<br>
<b>분석 기간:</b> 2000년–2025년<br>
<b>분석 항목:</b> 평균 기온, 최저 기온, 최고 기온, 강수량
</div>
""", unsafe_allow_html=True)
