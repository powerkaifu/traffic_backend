# 交通號誌資料庫系統

## 概述

這個系統設計用於儲存和管理交通號誌預測所需的資料。系統包含兩個主要資料表：

1. **Group（資料組主表）**: 儲存每批次的交通資料和預測結果
2. **Intersection（路口明細表）**: 儲存詳細的路口交通數據

## 資料庫結構

### Group 表

- `id`: 主鍵，自動生成
- `group_id`: UUID，批次唯一識別碼
- `timestamp`: 資料接收或預測時間
- `east_west_seconds`: 東西向最大綠燈秒數
- `south_north_seconds`: 南北向最大綠燈秒數

### Intersection 表

- `id`: 主鍵，自動生成
- `group`: 外鍵，關聯到 Group 表
- `VD_ID`: 路口偵測器 ID (VLRJX20/VLRJM60/VLRJX00)
- `DayOfWeek`: 星期 (1-7)
- `Hour`, `Minute`, `Second`: 時間
- `IsPeakHour`: 是否尖峰時段
- `LaneID`, `LaneType`: 車道資訊
- `Speed`, `Occupancy`: 基本交通數據
- `Volume_M`, `Speed_M`: 中型車數據
- `Volume_S`, `Speed_S`: 小型車數據
- `Volume_L`, `Speed_L`: 大型車數據
- `Volume_T`, `Speed_T`: 特種車數據
- `created_at`: 建立時間

## API 端點

### 1. 預測 API

```
POST /api/predict/
```

接收四筆路口資料，進行預測並儲存到資料庫。

**請求格式**:

```json
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
		"Speed": 34,
		"Occupancy": 25,
		"Volume_M": 5,
		"Speed_M": 41,
		"Volume_S": 2,
		"Speed_S": 36,
		"Volume_L": 5,
		"Speed_L": 27,
		"Volume_T": 0,
		"Speed_T": 0
	}
	// ... 其他三筆資料
]
```

**回應格式**:

```json
{
	"group_id": "uuid-string",
	"east_west_seconds": 75,
	"south_north_seconds": 65,
	"timestamp": "2025-01-13T19:41:02.123456+08:00",
	"message": "資料已成功儲存並完成預測"
}
```

### 2. 資料查詢 API

```
GET /api/data/
```

查詢交通資料。

**查詢參數**:

- `group_id`: 特定批次的 UUID
- `limit`: 限制返回數量（預設: 10）

**範例**:

```
GET /api/data/?group_id=xxxx-xxxx-xxxx-xxxx
GET /api/data/?limit=5
```

## 使用方式

### 1. 資料庫遷移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. 創建管理員帳號

```bash
python manage.py createsuperuser
```

### 3. 測試資料功能

```bash
# 建立範例資料
python manage.py test_traffic_data --create-sample

# 顯示統計資訊
python manage.py test_traffic_data --show-stats

# 列出最近 5 筆資料
python manage.py test_traffic_data --list-recent 5
```

### 4. 啟動開發伺服器

```bash
python manage.py runserver
```

### 5. 訪問管理介面

開啟瀏覽器，前往 `http://localhost:8000/admin` 查看和管理資料。

## 程式化操作

### 使用 TrafficDataManager

```python
from traffic_signal.data_utils import TrafficDataManager, TrafficDataValidator

# 建立一批交通資料
traffic_data = [...]  # 四筆路口資料
group = TrafficDataManager.create_traffic_batch(
    traffic_data,
    east_west_seconds=75,
    south_north_seconds=65
)

# 查詢特定批次
batch_data = TrafficDataManager.get_traffic_batch(str(group.group_id))

# 取得最近的批次
recent_batches = TrafficDataManager.get_recent_batches(limit=10)

# 取得統計資訊
stats = TrafficDataManager.get_statistics()
```

### 資料驗證

```python
# 驗證單筆路口資料
errors = TrafficDataValidator.validate_intersection_data(intersection_data)

# 驗證整批資料
errors = TrafficDataValidator.validate_batch_data(traffic_data)
```

## 路口偵測器說明

系統支援三種路口偵測器：

- **VLRJX20**: 往東方向
- **VLRJM60**: 往西方向
- **VLRJX00**: 往南/往北方向

每次傳送必須包含四筆資料：

1. VLRJX20 (往東)
2. VLRJM60 (往西)
3. VLRJX00 (往南, LaneID=2)
4. VLRJX00 (往北, LaneID=3)

## 資料驗證規則

- VD_ID 必須為有效值
- DayOfWeek 範圍：1-7
- Hour 範圍：0-23
- Minute, Second 範圍：0-59
- Speed, Occupancy 必須為非負數
- Occupancy 範圍：0-100
- 所有流量數據必須為非負整數

## 注意事項

1. 每次 API 呼叫會自動產生唯一的 `group_id`
2. 資料會自動記錄建立時間
3. 使用事務確保資料一致性
4. 支援 Django Admin 介面進行資料管理
5. 所有時間使用台北時區 (Asia/Taipei)

## 疑難排解

### 常見錯誤

1. **"請傳入四筆路口特徵資料的清單"**

   - 確認傳送的是包含四個物件的陣列

2. **"缺少必要欄位"**

   - 檢查每筆資料是否包含所有必要欄位

3. **"無效的 VD_ID"**

   - 確認 VD_ID 為 VLRJX20、VLRJM60 或 VLRJX00

4. **"預測處理失敗"**
   - 檢查機器學習模型是否正常運作
   - 查看伺服器日誌獲取詳細錯誤資訊

### 資料庫管理

- SQLite 檔案位置：`db.sqlite3`
- 可使用 DB Browser for SQLite 等工具直接查看
- 定期備份資料庫檔案
