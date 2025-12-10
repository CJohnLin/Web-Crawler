import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 設定區塊 ---
DB_NAME = 'data.db'
TABLE_NAME = 'weather'

# --- 數據讀取函數 ---
@st.cache_data
def load_weather_data():
    """從 SQLite 讀取所有天氣資料並返回 Pandas DataFrame。"""
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(DB_NAME)
        # 讀取整個資料表，只選擇需要的欄位
        df = pd.read_sql_query(f"SELECT location, min_temp, max_temp, description FROM {TABLE_NAME}", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# --- Streamlit 介面設計 ---
st.set_page_config(layout="wide")
st.title("☀️ Part 1：CWA 區域天氣預報")
st.markdown("---")

df_weather = load_weather_data()

# 檢查資料庫狀態
if not os.path.exists(DB_NAME):
     st.error(f"❌ 錯誤：找不到資料庫檔案 '{DB_NAME}'。請先執行 cwa_crawler.py 來生成資料庫。")
elif df_weather.empty:
    st.warning(f"資料庫 `{DB_NAME}` 中沒有找到天氣資料，請確認 cwa_crawler.py 已成功執行並寫入資料。")
else:
    # --- 1. 側邊欄篩選器 (模仿範例風格) ---
    st.sidebar.header("🗺️ 區域篩選器")
    
    unique_locations = sorted(df_weather['location'].unique())
    selected_location = st.sidebar.selectbox("選擇查看的地區：", ["所有地區"] + unique_locations)
    
    st.sidebar.markdown("---")
    st.sidebar.info("數據爬取自 CWA F-A0010-001。")

    # 應用篩選
    if selected_location != "所有地區":
        df_filtered = df_weather[df_weather['location'] == selected_location]
    else:
        df_filtered = df_weather
    
    # --- 2. 主頁面：數據統計與表格 ---
    
    st.header("數據概覽與統計")
    
    # 使用 st.columns 實現多欄佈局 (模仿範例的並排統計)
    col1, col2, col3, col4 = st.columns(4)
    
    # 統計計算 (針對所有數據)
    max_temp_overall = df_weather['max_temp'].max()
    min_temp_overall = df_weather['min_temp'].min()
    avg_max_temp = df_weather['max_temp'].mean()
    
    with col1:
        st.metric(label="最高溫 (整體)", value=f"{max_temp_overall:.1f} °C")
    with col2:
        st.metric(label="最低溫 (整體)", value=f"{min_temp_overall:.1f} °C")
    with col3:
        st.metric(label="平均最高溫", value=f"{avg_max_temp:.1f} °C")
    with col4:
        st.metric(label="地區總數", value=len(df_weather))

    st.markdown("---")
    
    # --- 3. 顯示表格 ---
    st.subheader(f"📍 {selected_location} 預報資料表格 (共 {len(df_filtered)} 筆)")
    
    # 如果篩選了單一地區，只顯示一行
    if selected_location != "所有地區" and not df_filtered.empty:
        data_row = df_filtered.iloc[0]
        st.markdown(f"**天氣狀況：** {data_row['description']}")
        st.markdown(f"**溫度範圍：** {data_row['min_temp']:.1f}°C ~ {data_row['max_temp']:.1f}°C")
        
    # 顯示所有資料的表格
    st.dataframe(
        df_filtered, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "location": "地區 (Location)",
            "min_temp": st.column_config.NumberColumn("最低溫 (°C)", format="%.1f"),
            "max_temp": st.column_config.NumberColumn("最高溫 (°C)", format="%.1f"),
            "description": "天氣狀況 (Description)"
        }
    )

    st.caption("備註：本數據為 CWA F-A0010-001 提供的第一個預報時段資訊。")
