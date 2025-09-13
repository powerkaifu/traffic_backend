# 交通號誌視覺化 API 使用指南

## API 概述

本系統提供了兩個主要的視覺化 API 端點，專為前端 D3.js 圖表設計：

1. **TrafficAnalyticsView** (`/api/analytics/`) - 聚合分析資料
2. **TrafficTimeSeriesView** (`/api/timeseries/`) - 時間序列資料

## 1. 分析聚合 API (`/api/analytics/`)

### 使用方式

```
GET /api/analytics/?type={analysis_type}&days={days}&其他參數
```

### 分析類型 (type 參數)

#### 1.1 總覽摘要 (`type=summary`)

```
GET /api/analytics/?type=summary
```

**回傳資料結構：**

```json
{
	"total_groups": 150,
	"total_intersections": 450,
	"recent_groups_7days": 35,
	"prediction_stats": {
		"avg_east_west": 65.2,
		"avg_south_north": 58.7,
		"max_east_west": 120,
		"min_east_west": 40,
		"max_south_north": 110,
		"min_south_north": 35
	},
	"direction_stats": [
		{
			"direction": "東向",
			"vd_id": "VLRJX20",
			"count": 150,
			"avg_speed": 42.5,
			"avg_occupancy": 15.3
		}
	]
}
```

**適用圖表：** 儀表板卡片、圓餅圖、KPI 顯示

#### 1.2 時間趨勢分析 (`type=trend`)

```
GET /api/analytics/?type=trend&days=7&group_by=hour
```

**參數：**

- `days`: 分析天數 (預設: 7)
- `group_by`: 分組方式 (`hour`, `day`)

**回傳資料結構：**

```json
{
	"period": "7 days",
	"group_by": "hour",
	"trend_data": [
		{
			"time_label": "00:00",
			"hour": 0,
			"avg_east_west": 45.2,
			"avg_south_north": 42.1,
			"count": 5
		}
	]
}
```

**適用圖表：** 折線圖、面積圖、熱力圖

#### 1.3 交通流量分析 (`type=traffic_flow`)

```
GET /api/analytics/?type=traffic_flow&days=7&vd_id=VLRJX20
```

**參數：**

- `days`: 分析天數 (預設: 7)
- `vd_id`: 特定方向 ID (可選)

**回傳資料結構：**

```json
{
	"period": "7 days",
	"flow_analysis": [
		{
			"direction": "東向",
			"vd_id": "VLRJX20",
			"total_volume": 1250,
			"volume_breakdown": {
				"medium": 650,
				"small": 400,
				"large": 150,
				"special": 50
			},
			"avg_speeds": {
				"overall": 42.5,
				"medium": 45.2,
				"small": 48.1,
				"large": 35.8
			},
			"avg_occupancy": 15.3,
			"data_points": 168
		}
	]
}
```

**適用圖表：** 堆疊柱狀圖、甜甜圈圖、雷達圖

#### 1.4 尖峰時段分析 (`type=peak_analysis`)

```
GET /api/analytics/?type=peak_analysis&days=7
```

**回傳資料結構：**

```json
{
	"period": "7 days",
	"peak_comparison": [
		{
			"period_type": "尖峰時段",
			"is_peak": true,
			"avg_speed": 35.2,
			"avg_occupancy": 25.8,
			"total_volume": 850,
			"data_count": 120,
			"avg_predictions": {
				"east_west": 72.5,
				"south_north": 68.2
			}
		}
	],
	"hourly_peak_distribution": [
		{
			"hour": 8,
			"time_label": "08:00",
			"peak_count": 15,
			"total_count": 20,
			"peak_ratio": 75.0
		}
	]
}
```

**適用圖表：** 比較柱狀圖、熱力圖、極座標圖

#### 1.5 方向對比分析 (`type=direction_comparison`)

```
GET /api/analytics/?type=direction_comparison&days=7
```

**回傳資料結構：**

```json
{
	"period": "7 days",
	"direction_comparison": [
		{
			"direction": "東西向",
			"direction_code": "east_west",
			"avg_speed": 42.5,
			"avg_occupancy": 15.3,
			"total_volume": 1250,
			"avg_prediction_seconds": 65.2,
			"data_points": 168
		}
	],
	"prediction_samples": [
		{
			"east_west_seconds": 65,
			"south_north_seconds": 58
		}
	]
}
```

**適用圖表：** 雷達圖、平行座標圖、散佈圖

#### 1.6 預測效能分析 (`type=prediction_performance`)

```
GET /api/analytics/?type=prediction_performance&days=30
```

**回傳資料結構：**

```json
{
  "period": "30 days",
  "total_predictions": 450,
  "east_west_distribution": [
    {
      "range": "40-50秒",
      "min_seconds": 40,
      "max_seconds": 50,
      "count": 45
    }
  ],
  "south_north_distribution": [...],
  "performance_metrics": {
    "east_west": {
      "avg": 65.2,
      "max": 120,
      "min": 40,
      "range": 80
    }
  }
}
```

**適用圖表：** 直方圖、箱型圖、小提琴圖

## 2. 時間序列 API (`/api/timeseries/`)

### 使用方式

```
GET /api/timeseries/?days={days}&interval={interval}&metric={metric}
```

### 參數說明

- `days`: 天數範圍 (預設: 7)
- `interval`: 時間間隔 (`hour`, `day`)
- `metric`: 指標類型 (`predictions`, `traffic_volume`, `speed`)

### 範例請求

#### 2.1 預測秒數時間序列

```
GET /api/timeseries/?days=7&metric=predictions
```

**回傳資料：**

```json
{
	"metric": "predictions",
	"period": "7 days",
	"data_points": 168,
	"time_series": [
		{
			"timestamp": "2024-01-01T00:00:00Z",
			"group_id": "uuid-string",
			"east_west_seconds": 65,
			"south_north_seconds": 58
		}
	]
}
```

#### 2.2 交通流量時間序列

```
GET /api/timeseries/?days=7&metric=traffic_volume
```

**回傳資料：**

```json
{
	"metric": "traffic_volume",
	"period": "7 days",
	"data_points": 168,
	"time_series": [
		{
			"timestamp": "2024-01-01T00:00:00Z",
			"group_id": "uuid-string",
			"total_volume": 250,
			"avg_speed": 42.5,
			"avg_occupancy": 15.3
		}
	]
}
```

## 3. D3.js 視覺化建議

### 3.1 儀表板頁面

- **KPI 卡片**: 使用 `type=summary` 取得總覽數據
- **趨勢折線圖**: 使用 `type=trend&group_by=hour`
- **即時狀態**: 使用 `/api/timeseries/?days=1&metric=predictions`

### 3.2 流量分析頁面

- **方向比較雷達圖**: 使用 `type=direction_comparison`
- **車輛類型圓餅圖**: 使用 `type=traffic_flow`
- **流量熱力圖**: 使用 `type=trend&group_by=hour`

### 3.3 尖峰分析頁面

- **尖峰 vs 非尖峰比較**: 使用 `type=peak_analysis`
- **小時分布圖**: 從 `hourly_peak_distribution` 資料
- **預測效能分布**: 使用 `type=prediction_performance`

### 3.4 時間軸分析頁面

- **連續時間折線圖**: 使用 `/api/timeseries/?metric=predictions`
- **多指標時間圖**: 使用 `/api/timeseries/?metric=traffic_volume`

## 4. 錯誤處理

所有 API 都包含統一的錯誤處理：

```json
{
  "error": "錯誤描述信息",
  "available_types": ["summary", "trend", ...] // 僅在 analytics API
}
```

## 5. 使用範例 (JavaScript)

```javascript
// 取得儀表板摘要
async function getDashboardSummary() {
	const response = await fetch('/api/analytics/?type=summary')
	const data = await response.json()
	return data
}

// 取得趨勢資料
async function getTrendData(days = 7, groupBy = 'hour') {
	const response = await fetch(`/api/analytics/?type=trend&days=${days}&group_by=${groupBy}`)
	const data = await response.json()
	return data
}

// 取得時間序列資料
async function getTimeSeriesData(metric = 'predictions', days = 7) {
	const response = await fetch(`/api/timeseries/?metric=${metric}&days=${days}`)
	const data = await response.json()
	return data
}
```

此 API 設計讓前端可以靈活組合不同的視覺化需求，支援各種 D3.js 圖表類型和互動功能。
