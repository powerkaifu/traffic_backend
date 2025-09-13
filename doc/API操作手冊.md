# 交通號誌資料庫系統 API 操作手冊

## 📋 目錄

- [系統概述](#系統概述)
- [資料庫結構](#資料庫結構)
- [RESTful API 操作](#restful-api-操作)
- [Django Admin 管理](#django-admin-管理)
- [前端整合範例](#前端整合範例)
- [錯誤處理](#錯誤處理)

---

## 系統概述

本系統用於接收前端傳送的交通號誌資料，進行機器學習預測，並將結果儲存至 SQLite 資料庫。系統提供 RESTful API 供前端呼叫，並包含 Django Admin 後台管理功能。

### 主要功能

- 接收四個路口的交通特徵資料
- 使用 ML 模型預測東西向和南北向綠燈秒數
- 自動產生批次 UUID 進行資料分組
- 提供資料查詢和管理功能

---

## 資料庫結構

### Group 資料組主表

| 欄位名稱              | 資料型態      | 長度 | 允許空值 | 預設值       | 描述                                     |
| --------------------- | ------------- | ---- | -------- | ------------ | ---------------------------------------- |
| `id`                  | BigAutoField  | -    | No       | Auto         | 主鍵，自動生成的唯一識別碼               |
| `group_id`            | UUIDField     | 36   | No       | uuid.uuid4() | 批次唯一識別碼，一組四路口資料歸為同一批 |
| `timestamp`           | DateTimeField | -    | No       | timezone.now | 資料接收或預測時間                       |
| `east_west_seconds`   | IntegerField  | -    | Yes      | None         | 模型預測的東西向最大綠燈秒數 (40-120 秒) |
| `south_north_seconds` | IntegerField  | -    | Yes      | None         | 模型預測的南北向最大綠燈秒數 (40-120 秒) |

**索引：**

- 主鍵索引：`id`
- 唯一索引：`group_id`
- 排序索引：`timestamp` (DESC)

---

### Intersection 路口明細表

| 欄位名稱     | 資料型態      | 長度 | 允許空值 | 預設值 | 選擇限制 | 描述                       |
| ------------ | ------------- | ---- | -------- | ------ | -------- | -------------------------- |
| `id`         | BigAutoField  | -    | No       | Auto   | -        | 主鍵，自動生成             |
| `group_id`   | ForeignKey    | -    | No       | -      | -        | 關聯到 Group 表的外鍵      |
| `VD_ID`      | CharField     | 10   | No       | -      | 見下表   | 路口偵測器 ID              |
| `DayOfWeek`  | IntegerField  | -    | No       | -      | 1-7      | 星期 (1=星期一...7=星期日) |
| `Hour`       | IntegerField  | -    | No       | -      | 0-23     | 時                         |
| `Minute`     | IntegerField  | -    | No       | -      | 0-59     | 分                         |
| `Second`     | IntegerField  | -    | No       | -      | 0-59     | 秒                         |
| `IsPeakHour` | BooleanField  | -    | No       | -      | T/F      | 是否尖峰時段               |
| `LaneID`     | IntegerField  | -    | No       | -      | -        | 車道編號                   |
| `LaneType`   | IntegerField  | -    | No       | -      | -        | 車道類型                   |
| `Speed`      | FloatField    | -    | No       | -      | ≥0       | 平均速率 (km/h)            |
| `Occupancy`  | FloatField    | -    | No       | -      | 0-100    | 車道佔有率 (%)             |
| `Volume_M`   | IntegerField  | -    | No       | -      | ≥0       | 中型車流量                 |
| `Speed_M`    | FloatField    | -    | No       | -      | ≥0       | 中型車速率 (km/h)          |
| `Volume_S`   | IntegerField  | -    | No       | -      | ≥0       | 小型車流量                 |
| `Speed_S`    | FloatField    | -    | No       | -      | ≥0       | 小型車速率 (km/h)          |
| `Volume_L`   | IntegerField  | -    | No       | -      | ≥0       | 大型車流量                 |
| `Speed_L`    | FloatField    | -    | No       | -      | ≥0       | 大型車速率 (km/h)          |
| `Volume_T`   | IntegerField  | -    | No       | 0      | ≥0       | 特種車流量                 |
| `Speed_T`    | FloatField    | -    | No       | 0.0    | ≥0       | 特種車速率 (km/h)          |
| `created_at` | DateTimeField | -    | No       | Auto   | -        | 建立時間                   |

**VD_ID 選擇限制：**
| 值 | 顯示名稱 | 描述 |
| -------- | ----------------- | -------- |
| VLRJX20 | 往東 (VLRJX20) | 東向車道 |
| VLRJM60 | 往西 (VLRJM60) | 西向車道 |
| VLRJX00 | 往南/往北 (VLRJX00) | 南北向車道 |

**DayOfWeek 選擇限制：**
| 值 | 顯示名稱 |
| -- | ------- |
| 1 | 星期一 |
| 2 | 星期二 |
| 3 | 星期三 |
| 4 | 星期四 |
| 5 | 星期五 |
| 6 | 星期六 |
| 7 | 星期日 |

**索引：**

- 主鍵索引：`id`
- 外鍵索引：`group_id`
- 複合索引：`[group_id, VD_ID, LaneID]`
- 排序索引：`created_at` (DESC)

---

## RESTful API 操作

### API 基本資訊

**Base URL:** `http://localhost:8000/api/`

**Content-Type:** `application/json`

**支援的 HTTP 方法:** GET, POST

---

### 1. 交通預測 API

**端點:** `POST /api/predict/`

**功能:** 接收四個路口的交通資料，進行預測並儲存到資料庫

#### 請求格式

```http
POST /api/predict/
Content-Type: application/json

[
  {
    "VD_ID": "VLRJX20",
    "DayOfWeek": 6,
    "Hour": 19,
    "Minute": 41,
    "Second": 2,
    "IsPeakHour": 1,
    "LaneID": 0,
    "LaneType": 1,
    "Speed": 34.5,
    "Occupancy": 25.8,
    "Volume_M": 5,
    "Speed_M": 41.2,
    "Volume_S": 2,
    "Speed_S": 36.1,
    "Volume_L": 5,
    "Speed_L": 27.3,
    "Volume_T": 0,
    "Speed_T": 0.0
  },
  {
    "VD_ID": "VLRJM60",
    "DayOfWeek": 6,
    "Hour": 19,
    "Minute": 41,
    "Second": 2,
    "IsPeakHour": 1,
    "LaneID": 1,
    "LaneType": 1,
    "Speed": 38.2,
    "Occupancy": 20.5,
    "Volume_M": 5,
    "Speed_M": 41.0,
    "Volume_S": 2,
    "Speed_S": 36.0,
    "Volume_L": 1,
    "Speed_L": 27.0,
    "Volume_T": 0,
    "Speed_T": 0.0
  },
  {
    "VD_ID": "VLRJX00",
    "DayOfWeek": 6,
    "Hour": 19,
    "Minute": 41,
    "Second": 2,
    "IsPeakHour": 1,
    "LaneID": 2,
    "LaneType": 1,
    "Speed": 37.1,
    "Occupancy": 25.0,
    "Volume_M": 5,
    "Speed_M": 41.5,
    "Volume_S": 5,
    "Speed_S": 36.2,
    "Volume_L": 1,
    "Speed_L": 27.5,
    "Volume_T": 0,
    "Speed_T": 0.0
  },
  {
    "VD_ID": "VLRJX00",
    "DayOfWeek": 6,
    "Hour": 19,
    "Minute": 41,
    "Second": 2,
    "IsPeakHour": 1,
    "LaneID": 3,
    "LaneType": 1,
    "Speed": 33.8,
    "Occupancy": 20.2,
    "Volume_M": 3,
    "Speed_M": 41.1,
    "Volume_S": 2,
    "Speed_S": 36.3,
    "Volume_L": 5,
    "Speed_L": 27.2,
    "Volume_T": 0,
    "Speed_T": 0.0
  }
]
```

#### 成功回應 (200)

```json
{
	"group_id": "550e8400-e29b-41d4-a716-446655440000",
	"east_west_seconds": 75,
	"south_north_seconds": 65,
	"timestamp": "2025-09-13T12:30:45.123456Z",
	"message": "資料已成功儲存並完成預測"
}
```

#### 錯誤回應

**400 Bad Request - 資料格式錯誤**

```json
{
	"error": "請傳入四筆路口特徵資料的清單"
}
```

**500 Internal Server Error - 預測失敗**

```json
{
	"error": "預測處理失敗: [詳細錯誤訊息]"
}
```

---

### 2. 資料查詢 API

**端點:** `GET /api/data/`

**功能:** 查詢已儲存的交通資料

#### 查詢所有批次資料

```http
GET /api/data/
GET /api/data/?limit=10
```

**參數:**

- `limit` (可選): 限制回傳的批次數量，預設為 10

**回應:**

```json
{
	"groups": [
		{
			"group_id": "550e8400-e29b-41d4-a716-446655440000",
			"timestamp": "2025-09-13T12:30:45.123456Z",
			"east_west_seconds": 75,
			"south_north_seconds": 65,
			"intersection_count": 4
		},
		{
			"group_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
			"timestamp": "2025-09-13T11:15:30.987654Z",
			"east_west_seconds": 80,
			"south_north_seconds": 60,
			"intersection_count": 4
		}
	]
}
```

#### 查詢特定批次資料

```http
GET /api/data/?group_id=550e8400-e29b-41d4-a716-446655440000
```

**參數:**

- `group_id` (必須): 要查詢的批次 UUID

**回應:**

```json
{
	"group": {
		"group_id": "550e8400-e29b-41d4-a716-446655440000",
		"timestamp": "2025-09-13T12:30:45.123456Z",
		"east_west_seconds": 75,
		"south_north_seconds": 65
	},
	"intersections": [
		{
			"id": 1,
			"VD_ID": "VLRJX20",
			"direction": "往東",
			"DayOfWeek": 6,
			"Hour": 19,
			"Minute": 41,
			"Second": 2,
			"IsPeakHour": true,
			"LaneID": 0,
			"LaneType": 1,
			"Speed": 34.5,
			"Occupancy": 25.8,
			"Volume_M": 5,
			"Speed_M": 41.2,
			"Volume_S": 2,
			"Speed_S": 36.1,
			"Volume_L": 5,
			"Speed_L": 27.3,
			"Volume_T": 0,
			"Speed_T": 0.0,
			"total_volume": 12
		}
		// ... 其他三個路口資料
	]
}
```

**錯誤回應:**

**404 Not Found - 找不到批次**

```json
{
	"error": "找不到指定的批次資料"
}
```

**500 Internal Server Error - 查詢失敗**

```json
{
	"error": "查詢失敗: [詳細錯誤訊息]"
}
```

---

## Django Admin 管理

### 存取管理介面

**URL:** `http://localhost:8000/admin/`

### 建立超級使用者

```bash
cd "d:\01.Project\traffic\traffic_project\backend\traffic_env\traffic"
D:/01.Project/traffic/traffic_project/backend/traffic_env/Scripts/python.exe manage.py createsuperuser
```

### 管理功能

1. **Group 管理**

   - 瀏覽所有批次資料
   - 搜尋特定 group_id
   - 依時間篩選
   - 查看預測結果
   - 統計路口資料數量

2. **Intersection 管理**

   - 瀏覽所有路口資料
   - 依 VD_ID、星期、尖峰時段篩選
   - 搜尋特定批次
   - 內嵌編輯功能
   - 欄位分組顯示

3. **資料導出**
   - 支援 CSV, JSON 格式導出
   - 可選擇特定欄位
   - 批次操作功能

---

## 前端整合範例

### JavaScript/Fetch API

```javascript
// 傳送交通資料進行預測
async function submitTrafficData(trafficData) {
	try {
		const response = await fetch('http://localhost:8000/api/predict/', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(trafficData),
		})

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`)
		}

		const result = await response.json()
		console.log('預測成功:', result)
		return result
	} catch (error) {
		console.error('預測失敗:', error)
		throw error
	}
}

// 查詢資料
async function getTrafficData(groupId = null, limit = 10) {
	try {
		let url = 'http://localhost:8000/api/data/'
		const params = new URLSearchParams()

		if (groupId) {
			params.append('group_id', groupId)
		} else {
			params.append('limit', limit)
		}

		if (params.toString()) {
			url += '?' + params.toString()
		}

		const response = await fetch(url)

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`)
		}

		const data = await response.json()
		console.log('查詢成功:', data)
		return data
	} catch (error) {
		console.error('查詢失敗:', error)
		throw error
	}
}

// 使用範例
const trafficData = [
	{
		VD_ID: 'VLRJX20',
		DayOfWeek: 6,
		Hour: 19,
		Minute: 41,
		Second: 2,
		IsPeakHour: 1,
		LaneID: 0,
		LaneType: 1,
		Speed: 34.5,
		Occupancy: 25.8,
		Volume_M: 5,
		Speed_M: 41.2,
		Volume_S: 2,
		Speed_S: 36.1,
		Volume_L: 5,
		Speed_L: 27.3,
		Volume_T: 0,
		Speed_T: 0.0,
	},
	// ... 其他三個路口資料
]

// 執行預測
submitTrafficData(trafficData)
	.then((result) => {
		console.log('Group ID:', result.group_id)
		console.log('東西向綠燈秒數:', result.east_west_seconds)
		console.log('南北向綠燈秒數:', result.south_north_seconds)
	})
	.catch((error) => {
		console.error('預測錯誤:', error)
	})
```

### Python/Requests

```python
import requests
import json

# API 基本設定
BASE_URL = "http://localhost:8000/api"
HEADERS = {"Content-Type": "application/json"}

def submit_traffic_data(traffic_data):
    """傳送交通資料進行預測"""
    url = f"{BASE_URL}/predict/"

    try:
        response = requests.post(url, json=traffic_data, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"預測失敗: {e}")
        return None

def get_traffic_data(group_id=None, limit=10):
    """查詢交通資料"""
    url = f"{BASE_URL}/data/"
    params = {}

    if group_id:
        params['group_id'] = group_id
    else:
        params['limit'] = limit

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"查詢失敗: {e}")
        return None

# 使用範例
traffic_data = [
    {
        "VD_ID": "VLRJX20",
        "DayOfWeek": 6,
        "Hour": 19,
        "Minute": 41,
        "Second": 2,
        "IsPeakHour": 1,
        "LaneID": 0,
        "LaneType": 1,
        "Speed": 34.5,
        "Occupancy": 25.8,
        "Volume_M": 5,
        "Speed_M": 41.2,
        "Volume_S": 2,
        "Speed_S": 36.1,
        "Volume_L": 5,
        "Speed_L": 27.3,
        "Volume_T": 0,
        "Speed_T": 0.0
    }
    # ... 其他三個路口資料
]

# 執行預測
result = submit_traffic_data(traffic_data)
if result:
    print(f"Group ID: {result['group_id']}")
    print(f"東西向綠燈秒數: {result['east_west_seconds']}")
    print(f"南北向綠燈秒數: {result['south_north_seconds']}")

    # 查詢剛才建立的資料
    data = get_traffic_data(group_id=result['group_id'])
    if data:
        print(f"找到 {len(data['intersections'])} 筆路口資料")
```

---

## 錯誤處理

### 常見錯誤碼

| HTTP 狀態碼 | 錯誤類型              | 可能原因       | 解決方法                 |
| ----------- | --------------------- | -------------- | ------------------------ |
| 400         | Bad Request           | 資料格式不正確 | 檢查 JSON 格式和必要欄位 |
| 404         | Not Found             | 找不到指定資料 | 確認 group_id 是否正確   |
| 500         | Internal Server Error | 伺服器內部錯誤 | 檢查伺服器日誌和模型狀態 |

### 資料驗證規則

1. **必須包含四筆路口資料**
2. **VD_ID 必須是有效值** (VLRJX20, VLRJM60, VLRJX00)
3. **時間值必須在有效範圍內**
   - DayOfWeek: 1-7
   - Hour: 0-23
   - Minute: 0-59
   - Second: 0-59
4. **數值必須為非負數**
   - Speed ≥ 0
   - Occupancy: 0-100
   - 所有 Volume 和 Speed 欄位 ≥ 0

### 除錯建議

1. **使用瀏覽器開發者工具** 檢查網路請求
2. **檢查 Django 伺服器日誌** 查看詳細錯誤訊息
3. **確認資料格式** 使用 JSON 驗證工具
4. **測試 API 端點** 使用 Postman 或 curl 進行測試

---

## 資料庫檔案位置

**SQLite 檔案:** `d:\01.Project\traffic\traffic_project\backend\traffic_env\traffic\db.sqlite3`

**工具建議:**

- DB Browser for SQLite
- SQLite Expert
- DBeaver

---

## 啟動系統

```bash
# 進入專案目錄
cd "d:\01.Project\traffic\traffic_project\backend\traffic_env\traffic"

# 啟動 Django 開發伺服器
D:/01.Project/traffic/traffic_project/backend/traffic_env/Scripts/python.exe manage.py runserver

# 伺服器將在 http://localhost:8000 啟動
```

---

**📝 最後更新:** 2025-09-13
**🔧 系統版本:** Django 5.2.3
**💾 資料庫:** SQLite 3
