import json
import random
import os
import math
import streamlit as st
import pandas as pd
import pydeck as pdk
from openai import OpenAI
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium  # pip install folium streamlit-folium

# 페이지 설정
st.set_page_config(
    page_title="고양경찰서 어플",
    page_icon="🚔",
    layout="centered"
)

# 사이드바: 메뉴 선택 및 데이터 표시
CCTV_CSV_PATH = "전처리_지오코딩.csv"
BELL_CSV_PATH = "비상벨_지오코딩.csv"
PATROL_CSV_PATH = "patrol_Geocoding.csv"  # 지오코딩된 X, Y 포함

# 데이터 로드
cctv_df = pd.read_csv(CCTV_CSV_PATH) if os.path.exists(CCTV_CSV_PATH) else None
bell_df = pd.read_csv(BELL_CSV_PATH) if os.path.exists(BELL_CSV_PATH) else None
patrol_df = pd.read_csv(PATROL_CSV_PATH) if os.path.exists(PATROL_CSV_PATH) else None

if cctv_df is None:
    st.sidebar.error(f"파일을 찾을 수 없습니다: {CCTV_CSV_PATH}")
if bell_df is None:
    st.sidebar.error(f"파일을 찾을 수 없습니다: {BELL_CSV_PATH}")
if patrol_df is None:
    st.sidebar.error(f"파일을 찾을 수 없습니다: {PATROL_CSV_PATH}")

# 사이드바 메뉴
st.sidebar.header("메뉴")
options = []
if cctv_df is not None:
    options.append("CCTV 지도")
if bell_df is not None:
    options.append("비상벨 지도")
if patrol_df is not None:
    options.append("순찰 추천")
mode = st.sidebar.radio("선택하세요", options)

# 사이드바 데이터 정보
if cctv_df is not None:
    st.sidebar.header("CCTV 데이터")
    st.sidebar.write(f"총 좌표 개수: {len(cctv_df)} 건")
if bell_df is not None:
    st.sidebar.header("비상벨 데이터")
    st.sidebar.write(f"총 좌표 개수: {len(bell_df)} 건")
if patrol_df is not None:
    st.sidebar.header("순찰 데이터")
    st.sidebar.write(f"총 순찰 지점: {len(patrol_df)} 건")

# 다크모드 토글
dark_mode = st.sidebar.checkbox("다크모드 전환", value=False)
text_color = "white" if dark_mode else "black"
bg_color = "#333333" if dark_mode else "white"

# CSS/JS 적용
st.markdown(f"""
    <style>
    body {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    .main .block-container {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    .element-container, .stFolio, .stBlock {{ margin-bottom: 0px !important; padding-bottom: 0px !important; }}
    iframe {{ display: block; margin: 0 auto !important; }}
    #map_container {{ margin: 0px !important; padding: 0px !important; }}
    [data-baseweb="select"] input {{ pointer-events: none !important; caret-color: transparent !important; }}
    </style>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        var inputs = document.querySelectorAll('[data-baseweb="select"] input');
        inputs.forEach(function(el) {{ el.setAttribute('readonly', true); el.setAttribute('onfocus', 'this.blur()'); el.addEventListener('touchstart', function(e) {{ e.preventDefault(); this.blur(); }}); }});
    }});
    </script>
""", unsafe_allow_html=True)

# 타이틀 및 설명
st.markdown(f"""
    <div style="text-align: center; font-size: 26px; color: {text_color}; margin-top: 20px;">
        <b>👮고양서 자율방범앱👮‍♂️</b>
    </div>
""", unsafe_allow_html=True)
st.markdown(f"""
    <div style="text-align: center; font-size: 17px; color: {text_color}; margin-top: 10px;">
        <b>우리 동네 순찰 필요 장소 안내</b><br>
        고양경찰서 방범대원 분들의 노고에 감사드립니다.
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# 모드별 화면 구성
if mode == "CCTV 지도":
    col_lower = [c.lower() for c in cctv_df.columns]
    lon_col = next((cctv_df.columns[i] for i,c in enumerate(col_lower) if c in ["x","lon","경도"]), None)
    lat_col = next((cctv_df.columns[i] for i,c in enumerate(col_lower) if c in ["y","lat","위도"]), None)
    if lon_col and lat_col:
        df_map = cctv_df.rename(columns={lon_col:"lon", lat_col:"lat"}).dropna(subset=["lat","lon"])
        df_map[["lat","lon"]] = df_map[["lat","lon"]].astype(float)
        avg_lat, avg_lon = df_map["lat"].mean(), df_map["lon"].mean()
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11, tiles="OpenStreetMap")
        for _, row in df_map.iterrows():
            folium.CircleMarker(location=[row["lat"], row["lon"]], radius=5, color='blue', fill=True, fill_opacity=0.6).add_to(m)
        st_folium(m, width=700, height=400)
    else:
        st.error("CCTV 데이터에 좌표 컬럼 없음")

elif mode == "비상벨 지도":
    col_lower = [c.lower() for c in bell_df.columns]
    lon_col = next((bell_df.columns[i] for i,c in enumerate(col_lower) if c in ["x","lon","경도"]), None)
    lat_col = next((bell_df.columns[i] for i,c in enumerate(col_lower) if c in ["y","lat","위도"]), None)
    if lon_col and lat_col:
        df_map = bell_df.rename(columns={lon_col:"lon", lat_col:"lat"}).dropna(subset=["lat","lon"])
        df_map[["lat","lon"]] = df_map[["lat","lon"]].astype(float)
        avg_lat, avg_lon = df_map["lat"].mean(), df_map["lon"].mean()
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles="OpenStreetMap")
        for _, row in df_map.iterrows():
            folium.Marker(location=[row["lat"], row["lon"]], icon=folium.Icon(color='red', icon='bell')).add_to(m)
        st_folium(m, width=700, height=400)

elif mode == "순찰 추천":
    st.markdown(f"""<div style="text-align:center; color:{text_color}; font-size:20px;"><b>✅ 소속 자율방범대를 선택하세요</b></div>""", unsafe_allow_html=True)
    teams = ["-선택-"] + sorted(patrol_df["_자율방범대"].unique().tolist())
    team = st.selectbox("", teams)
    if team != "-선택-":
        team_df = patrol_df[patrol_df["_자율방범대"] == team]
        locations = team_df["순찰장소"].tolist()
        selected = st.selectbox("순찰 노선 선택", locations)
        if selected:
            row = team_df[team_df["순찰장소"] == selected].iloc[0]
            lat, lon = float(row["Y"]), float(row["X"])
            m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")
            folium.Circle(location=[lat, lon], radius=300, color="red", fill=True, fill_opacity=0.2).add_to(m)
            folium.Marker([lat, lon], icon=folium.Icon(color="blue")).add_to(m)
            st_folium(m, width=700, height=400)

# 푸터
st.markdown(f"""<div style="text-align:center; color:{text_color}; font-size:14px; margin-top:10px;>
본 어플은 고양경찰서 범죄예방대응과 제작하였습니다.
</div>""", unsafe_allow_html=True)

st.markdown(
                f"""
                <div style="text-align: center; font-size: 16px; color: {text_color}; margin-top: 20px;">
                    <b>아래의 링크를 통해 경찰서 범죄예방진단팀에게<br>
                    취약지역을 통보해주세요.<br>
                    <a href="https://open.kakao.com/o/scgaTwdh" target="_blank" style="color: blue; font-weight: bold;">👉 고양경찰서 범죄예방진단팀</a><br>
                     <br>
                    대원분들의 소중한 의견을 통해 <br>
                    안전한 우리동네가 만들어집니다.</b>
                </div>
                """, unsafe_allow_html=True)