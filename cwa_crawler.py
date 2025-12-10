import requests
import json
import sqlite3
from pprint import pprint

# --- 1. 設定區塊 ---
# ⚠️ 請將此處的 CWA-API-KEY 替換為您自己註冊 CWA 帳號後取得的「有效」金鑰。
CWA_API_KEY = "CWA-779A7F6C-B1CC-4763-8762-A2D43A4F2671" 

# 資料庫與資料表名稱
DB_NAME = 'data.db'
TABLE_NAME = 'weather'

# API 資訊
API_URL = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001"
params = {
    "Authorization": CWA_API_KEY,
    "downloadType": "WEB", 
    "format": "JSON"
}
# --- 函數定義 ---

def download_cwa_data():
    """下載中央氣象局 JSON 資料，返回 Python 字典。"""
    print("📥 正在下載 CWA 預報 JSON 資料...")
    
    if CWA_API_KEY == "請在此處貼上您的個人有效 API 金鑰":
        print("❌ 錯誤：請先將 CWA_API_KEY 替換為您的有效金鑰！")
        return None

    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status() 
        weather_data = response.json()
        print("✅ 資料下載成功！")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下載資料時發生錯誤: {e}")
        print("💡 提示：若錯誤為 500 Server Error，請檢查您的 API 金鑰是否有效且正確。")
        return None

def parse_weather_data(weather_data):
    """解析 JSON 資料，取出各地區的第一個預報時段的溫度與描述。"""
    parsed_weather_data = []

    # 1. 根據提供的 JSON 結構，精準定位到 'location' 列表
    try:
        locations = weather_data['cwaopendata']['resources']['resource']['data']['agrWeatherForecasts']['weatherForecasts']['location']
    except KeyError as e:
        print(f"❌ 解析錯誤：JSON 結構不符，找不到鍵 {e}。")
        return []

    if not locations:
        print("⚠️ 警告：'location' 列表是空的，沒有地區資料。")
        return []

    # 2. 遍歷每個地區，提取所需的氣象元素
    for loc in locations:
        location_name = loc.get('locationName', 'N/A')
        min_temp, max_temp, description = None, None, None

        # 氣象元素在 'weatherElements' 下
        weather_elements = loc.get('weatherElements', {})
        
        # Wx (天氣描述)
        # 由於這是週間預報，我們取第一個 'daily' 預報 (即明天的預報)
        wx_daily = weather_elements.get('Wx', {}).get('daily', [{}])[0]
        description = wx_daily.get('weather')
        
        # MinT (最低溫)
        minT_daily = weather_elements.get('MinT', {}).get('daily', [{}])[0]
        min_temp_str = minT_daily.get('temperature')
        
        # MaxT (最高溫)
        maxT_daily = weather_elements.get('MaxT', {}).get('daily', [{}])[0]
        max_temp_str = maxT_daily.get('temperature')

        # 3. 轉換資料類型並檢查
        try:
            min_temp = float(min_temp_str) if min_temp_str else None
            max_temp = float(max_temp_str) if max_temp_str else None
        except ValueError:
            # 如果溫度不是數字，則跳過此地區
            continue 
        
        # 4. 儲存結果 (只儲存資料完整的)
        if all([min_temp is not None, max_temp is not None, description is not None]):
             parsed_weather_data.append({
                "location": location_name,
                "min_temp": min_temp,
                "max_temp": max_temp,
                "description": description
            })
            
    print(f"✅ 資料解析完成，共解析出 {len(parsed_weather_data)} 個地區的第一個預報時段資料。")
    return parsed_weather_data

def save_to_sqlite(data_list):
    """將解析後的資料存入 SQLite 資料庫。"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 建立資料表 (如果不存在)
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            min_temp REAL,
            max_temp REAL,
            description TEXT
        );
        """
        cursor.execute(create_table_sql)

        # 清空舊資料
        cursor.execute(f"DELETE FROM {TABLE_NAME}")
        
        # 準備待寫入的資料
        data_to_insert = [
            (item['location'], item['min_temp'], item['max_temp'], item['description'])
            for item in data_list
        ]

        # 批量寫入資料
        insert_sql = f"""
        INSERT INTO {TABLE_NAME} (location, min_temp, max_temp, description)
        VALUES (?, ?, ?, ?);
        """
        cursor.executemany(insert_sql, data_to_insert)
        
        conn.commit()
        print(f"✅ 成功將 {len(data_to_insert)} 筆資料存入 SQLite3 資料庫 '{DB_NAME}'。")

    except sqlite3.Error as e:
        print(f"❌ SQLite 操作時發生錯誤: {e}")
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()

# --- 主程式執行區塊 ---
if __name__ == '__main__':
    # 步驟 1: 下載資料
    raw_data = download_cwa_data()
    
    if raw_data:
        # 步驟 2: 解析資料
        parsed_data = parse_weather_data(raw_data)
        
        if parsed_data:
            # 步驟 3 & 4: 存入 SQLite
            save_to_sqlite(parsed_data)
            
            print("\n🎉 Part 1 的下載、解析與資料庫寫入已完成！")
            print("請記得執行 Streamlit App (app.py) 來顯示結果。")