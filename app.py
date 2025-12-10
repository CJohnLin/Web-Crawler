import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 設定區塊 ---
DB_NAME = 'data.db'
TABLE_NAME = 'weather'

# --- 函數定義 ---
@st.cache_data
def load_weather_data():
    """從 SQLite 讀取所有天氣資料並返回 Pandas DataFrame。"""
    
    # 檢查資料庫檔案是否存在
    if not os.path.exists(DB_NAME):
        st.error(f"❌ 錯誤：找不到資料庫檔案 '{DB_NAME}'。請先執行 cwa_crawler.py 來生成資料庫。")
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(DB_NAME)
        # 讀取整個資料表
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        st.error(f"❌ 無法載入資料庫 '{DB_NAME}' 的資料: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"發生未知錯誤: {e}")
        return pd.DataFrame()

# --- Streamlit 介面設計 ---
st.set_page_config(layout="wide")
st.title("☀️ Part 1：CWA 天氣預報資料顯示 App")
st.markdown("---")

df_weather = load_weather_data()

if not df_weather.empty:
    st.header(f"🏛️ SQLite 資料表 `{TABLE_NAME}` 資料 ({len(df_weather)} 筆記錄)")
    
    # 根據作業要求，顯示資料表格
    st.dataframe(
        df_weather, 
        use_container_width=True, 
        hide_index=True,
        # 設置欄位顯示名稱和格式，提高可讀性
        column_config={
            "id": "ID",
            "location": "地區 (Location)",
            "min_temp": st.column_config.NumberColumn("最低溫 (°C)", format="%.1f"),
            "max_temp": st.column_config.NumberColumn("最高溫 (°C)", format="%.1f"),
            "description": "天氣狀況 (Description)"
        }
    )

    st.markdown("---")
    st.info(f"資料來源：本地 SQLite 資料庫 `{DB_NAME}`。")

else:
    st.warning(f"資料庫 `{DB_NAME}` 中沒有找到天氣資料，請確認 cwa_crawler.py 已成功執行。")