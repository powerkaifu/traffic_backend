# 安裝後端

## 建立 venv 虛擬環境

- 到官網下載 Python 3.12 版本

  - https://www.python.org/downloads/release/python-3120/
  - 安裝 3.12 版本時，請勾選「Add Python to PATH」

- 建立 python 3.12 虛擬環境

  ```
  py -3.12 -m venv traffic_env
  ```

## 啟動環境

- 到 traffic_env\Scripts 目錄下，執行 activate

  ```
  .\traffic_env\Scripts\activate
  ```

- 確定進入虛擬環境 (traffic_env)

  ```
  (traffic_env) D:\01.Project\traffic\traffic_project\backend\traffic_env\traffic>
  ```

- 升級 pip

  ```
  python -m pip install --upgrade pip
  ```

## 安裝套件(新環境)

- 回到 traffic_env\traffic\ 目錄底下
- 執行以下指令安裝套件

  ```
  pip install -r requirements.txt
  ```

## 備份套件清單(用於新環境安裝)

- 回到 traffic_env\traffic\ 目錄底下

  ```
  pip freeze > requirements.txt
  ```

- 產生 requirements.txt 套件清單，該檔案會與 manage.py 同目錄

## 離開虛擬環境

- 到 traffic_env\Scripts 目錄下，執行 deactivate

  ```
  .\traffic_env\Scripts\deactivate
  ```

---

# 專案設定

## 啟動伺服器

- 到 traffic 目錄底下，執行以下指令啟動後端服務

  ```
  py manage.py runserver
  ```

- 開啟後端服務才能進行前端串接

## 保留專案

- 保留 traffic 專案整個目錄即可

# API 測試

127.0.0.1:8000 為 Django 預設的開發伺服器網址

- 預測綠燈秒數

  POST http://127.0.0.1:8000/api/traffic/predict/

# 路口資料格式（餵模型）

資料順序如下，往東、往西、往南、往北。

| VD_ID   | 路段           | LinkID         | LaneNum |
| ------- | -------------- | -------------- | ------- |
| VLRJM20 | 南京東路(往東) | 6001190200010A | 5       |
| VLRJM60 | 南京東路(往西) | 6001190600010A | 3       |
| VLRJX00 | 松江路(往南)   | 6004930400060A | 4       |
|         | 松江路(往北)   | 6004930000080A | 4       |

```json
[
	{
		"VD_ID": "VLRJM20", // 路段 ID
		"DayOfWeek": 1, // 星期一
		"Hour": 23, // 小時
		"Minute": 45, // 分鐘
		"Second": 0, // 秒數
		"IsPeakHour": 0, // 是否為尖峰時段
		"LaneID": 2, // 車道 ID
		"LaneType": 1, // 車道類型
		"Speed": 62, // 車速
		"Occupancy": 7, // 車道佔用率
		"Volume_M": 4, // 機車數量
		"Speed_M": 58, // 機車平均車速
		"Volume_S": 7, // 小客車數量
		"Speed_S": 65, // 小客車平均車速
		"Volume_L": 1, // 大客車數量
		"Speed_L": 55, // 大客車平均車速
		"Volume_T": 0, // 聯結車數量
		"Speed_T": 0 // 聯結車平均車速
	},
	{
		"VD_ID": "VLRJM60",
		"DayOfWeek": 1,
		"Hour": 8,
		"Minute": 15,
		"Second": 0,
		"IsPeakHour": 1,
		"LaneID": 0,
		"LaneType": 1,
		"Speed": 14,
		"Occupancy": 92,
		"Volume_M": 32,
		"Speed_M": 11,
		"Volume_S": 45,
		"Speed_S": 15,
		"Volume_L": 9,
		"Speed_L": 9,
		"Volume_T": 0,
		"Speed_T": 0
	},
	{
		"VD_ID": "VLRJX00",
		"DayOfWeek": 1,
		"Hour": 13,
		"Minute": 30,
		"Second": 0,
		"IsPeakHour": 0,
		"LaneID": 1,
		"LaneType": 1,
		"Speed": 42,
		"Occupancy": 33,
		"Volume_M": 16,
		"Speed_M": 40,
		"Volume_S": 22,
		"Speed_S": 45,
		"Volume_L": 4,
		"Speed_L": 32,
		"Volume_T": 0,
		"Speed_T": 0
	},
	{
		"VD_ID": "VLRJX00",
		"DayOfWeek": 1,
		"Hour": 17,
		"Minute": 50,
		"Second": 0,
		"IsPeakHour": 1,
		"LaneID": 0,
		"LaneType": 1,
		"Speed": 11,
		"Occupancy": 96,
		"Volume_M": 38,
		"Speed_M": 9,
		"Volume_S": 50,
		"Speed_S": 13,
		"Volume_L": 11,
		"Speed_L": 7,
		"Volume_T": 0,
		"Speed_T": 0
	}
]
```

# 套件列表

- django
- djangorestframework
- django-cors-headers
- django-environ
- djangorestframework-simplejwt
- django-filter
- django-extensions
- django-debug-toolbar
- mysqlclient
- numpy
- pandas
- joblib
- stensorflow
- scikit-learn
