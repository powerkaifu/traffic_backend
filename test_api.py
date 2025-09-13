"""
簡單的 API 測試腳本
用於測試交通資料 API 的功能
"""
import requests
import json
from datetime import datetime

# API 基本 URL（根據您的設定調整）
BASE_URL = "http://localhost:8000/api"

# 測試資料
TEST_DATA = [
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


def test_prediction_api():
    """測試預測 API"""
    print("=== 測試預測 API ===")

    url = f"{BASE_URL}/predict/"
    headers = {
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(url,
                               data=json.dumps(TEST_DATA),
                               headers=headers)

        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 預測成功！")
            print(f"   批次 ID: {result.get('group_id')}")
            print(f"   東西向綠燈秒數: {result.get('east_west_seconds')}")
            print(f"   南北向綠燈秒數: {result.get('south_north_seconds')}")
            return result.get('group_id')
        else:
            print(f"❌ 預測失敗: {response.text}")
            return None

    except Exception as e:
        print(f"❌ API 請求錯誤: {str(e)}")
        return None


def test_data_query_api(group_id=None):
    """測試資料查詢 API"""
    print("\\n=== 測試資料查詢 API ===")

    if group_id:
        url = f"{BASE_URL}/data/?group_id={group_id}"
        print(f"查詢特定批次: {group_id}")
    else:
        url = f"{BASE_URL}/data/?limit=3"
        print("查詢最近 3 筆資料")

    try:
        response = requests.get(url)

        print(f"狀態碼: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 查詢成功！")

            if group_id:
                # 特定批次查詢
                group_info = result.get('group', {})
                intersections = result.get('intersections', [])

                print(f"   批次資訊:")
                print(f"     ID: {group_info.get('group_id')}")
                print(f"     時間: {group_info.get('timestamp')}")
                print(f"     東西向: {group_info.get('east_west_seconds')}秒")
                print(f"     南北向: {group_info.get('south_north_seconds')}秒")
                print(f"   路口資料數量: {len(intersections)}")

                for i, intersection in enumerate(intersections, 1):
                    print(f"     路口 {i}: {intersection.get('VD_ID')} "
                          f"({intersection.get('direction')}) "
                          f"車道 {intersection.get('LaneID')}")
            else:
                # 列表查詢
                groups = result.get('groups', [])
                print(f"   找到 {len(groups)} 筆批次資料:")

                for group in groups:
                    print(f"     {group.get('group_id')[:8]}... "
                          f"東西向: {group.get('east_west_seconds')}秒 "
                          f"南北向: {group.get('south_north_seconds')}秒 "
                          f"路口數: {group.get('intersection_count')}")
        else:
            print(f"❌ 查詢失敗: {response.text}")

    except Exception as e:
        print(f"❌ API 請求錯誤: {str(e)}")


def main():
    """主要測試函數"""
    print(f"開始測試交通資料 API")
    print(f"基本 URL: {BASE_URL}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    # 測試預測 API
    group_id = test_prediction_api()

    # 測試一般查詢 API
    test_data_query_api()

    # 如果預測成功，測試特定批次查詢
    if group_id:
        test_data_query_api(group_id)

    print("\\n" + "=" * 50)
    print("測試完成！")


if __name__ == "__main__":
    main()
