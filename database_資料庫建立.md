以下需求設計的 SQLite 資料庫結構，
目的將前端送來的交通資料存入資料庫，
請分析前端送來的資料結構，設計適合的資料表與欄位（以下為參考欄位），
前端會傳來一組四個路口的交通資料，會經由模型來預測出東西向與南北向的最大綠燈秒數，
需要有一個批次的唯一識別碼 (group_id) 來區分每次送來的資料。

我分成兩張表來設計：

1. 資料組主表 (Group)：存放每次前端送來的四路口資料的整體批次資訊以及預測的東西、南北最大綠燈秒數。
2. 路口明細表 (Intersection)：存放每次傳送過來四個路口的詳細交通特徵資料。

---

# 前端傳送的四個路口資料格式

VD_ID: 路口偵測器 ID，只有三支

- VLRJX20 為往東
- VLRJM60 為往西
- VLRJX00 為往南、往北

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
		"Speed": 38,
		"Occupancy": 20,
		"Volume_M": 5,
		"Speed_M": 41,
		"Volume_S": 2,
		"Speed_S": 36,
		"Volume_L": 1,
		"Speed_L": 27,
		"Volume_T": 0,
		"Speed_T": 0
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
		"Speed": 37,
		"Occupancy": 25,
		"Volume_M": 5,
		"Speed_M": 41,
		"Volume_S": 5,
		"Speed_S": 36,
		"Volume_L": 1,
		"Speed_L": 27,
		"Volume_T": 0,
		"Speed_T": 0
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
		"Speed": 33,
		"Occupancy": 20,
		"Volume_M": 3,
		"Speed_M": 41,
		"Volume_S": 2,
		"Speed_S": 36,
		"Volume_L": 5,
		"Speed_L": 27,
		"Volume_T": 0,
		"Speed_T": 0
	}
]
```

---

# SQLite 資料庫設計文件（Django 適用）

## 1. 資料組主表（Group）

| 欄位名稱            | 資料型態       | 描述                                     |
| ------------------- | -------------- | ---------------------------------------- |
| id                  | 整數，自動主鍵 | 主鍵，自動生成的唯一識別碼               |
| group_id            | UUID 字串      | 批次唯一識別碼，一組四路口資料歸為同一批 |
| timestamp           | DateTime       | 資料接收或預測時間                       |
| east_west_seconds   | 整數           | 模型預測的東西向最大綠燈秒數             |
| south_north_seconds | 整數           | 模型預測的南北向最大綠燈秒數             |

- 此表用以儲存一次前端批次送來的四路口資料的「整體批次」資訊。
- group_id 為每批資料的唯一識別，方便前端視覺化及後續資料查詢。

---

## 2. 路口明細表（Intersection）

| 欄位名稱   | 資料型態       | 描述                         |
| ---------- | -------------- | ---------------------------- |
| id         | 整數，自動主鍵 | 主鍵，自動生成               |
| group      | ForeignKey     | 關聯到 Group 表的 group_id   |
| VD_ID      | 字串           | 路口偵測器 ID                |
| DayOfWeek  | 整數           | 星期 (1=星期一 ... 7=星期日) |
| Hour       | 整數           | 時                           |
| Minute     | 整數           | 分                           |
| Second     | 整數           | 秒                           |
| IsPeakHour | 布林           | 是否尖峰時段                 |
| LaneID     | 整數           | 車道編號                     |
| LaneType   | 整數           | 車道類型                     |
| Speed      | 浮點數         | 平均速率                     |
| Occupancy  | 浮點數         | 車道佔有率                   |
| Volume_M   | 整數           | 中型車流量                   |
| Speed_M    | 浮點數         | 中型車速率                   |
| Volume_S   | 整數           | 小型車流量                   |
| Speed_S    | 浮點數         | 小型車速率                   |
| Volume_L   | 整數           | 大型車流量                   |
| Speed_L    | 浮點數         | 大型車速率                   |
| Volume_T   | 整數           | 特種車流量（可選）           |
| Speed_T    | 浮點數         | 特種車速率（可選）           |

---

在 Django 中，存入的資料庫資料可透過以下方式查詢與管理：

## 1. Django Admin 管理介面

- 啟用 Django 內建的 Admin 功能，對應的 Model 會自動有資料管理頁面。
- 透過瀏覽器訪問 `/admin`（如 http://localhost:8000/admin）登入後，即可瀏覽、搜尋、編輯、刪除資料。
- 需先於 `admin.py` 註冊你的 Model，例如：

  ```python
  from django.contrib import admin
  from .models import Group, Intersection

  admin.site.register(Group)
  admin.site.register(Intersection)
  ```

## 2. Django shell (互動命令列)

- 可以透過命令 `python manage.py shell` 進入互動模式查詢。
- 例如查詢所有 Group：
  ```python
  from yourapp.models import Group
  groups = Group.objects.all()
  print(groups)
  ```
- 查詢特定 group 相關的路口明細：
  ```python
  group = Group.objects.first()
  intersections = group.intersections.all()
  print(intersections)
  ```

## 3. 在 Django 視圖中操作

- 使用 Django ORM 在 view、API 或命令中查詢，如：

  ```python
  from yourapp.models import Group

  def view_function(request):
      data = Group.objects.filter(id=1)
      # 傳給模板或回傳 json
  ```

## 資料庫實際檔案位置（SQLite）

- SQLite 的資料庫檔案預設為 `db.sqlite3`，位於 Django 專案根目錄中（與 manage.py 同級）
- 可用任何 SQLite 工具（如 DB Browser for SQLite）打開此檔案查看與編輯資料。

---

總結：

- 在瀏覽器用 Django Admin 介面最直覺。
- 開發者可用 Django shell 或 ORM 自訂查詢。
- SQLite 檔案位於專案目錄下的 `db.sqlite3`，可用通用工具管理。
