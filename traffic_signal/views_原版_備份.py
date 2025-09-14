from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q, Avg, Count, Max, Min, Sum
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta
from .models import Group, Intersection
from .ml.predictor import Predictor

predictor = Predictor()  # 初始化一次


class TrafficPrediction(APIView):
    """
    交通號誌預測 API
    接收四個路口的交通資料，進行預測並儲存結果
    """

    def post(self, request):
        """
        範例：交通號誌預測 API
        POST /api/traffic/predict/
        Content-Type: application/json

        Body (JSON):
        [
          {
            "VD_ID": "VLRJX20",
            "DayOfWeek": 1,
            "Hour": 8,
            "Minute": 30,
            "Second": 0,
            "IsPeakHour": 1,
            "LaneID": 1,
            "LaneType": "直行",
            "Speed": 42.5,
            "Occupancy": 15.3,
            "Volume_M": 100,
            "Speed_M": 45.2,
            "Volume_S": 80,
            "Speed_S": 48.1,
            "Volume_L": 20,
            "Speed_L": 35.8,
            "Volume_T": 5,
            "Speed_T": 30.0
          },
          ...共4筆路口資料...
        ]

        回傳範例：
        {
          "group_id": "123e4567-e89b-12d3-a456-426614174000",
          "east_west_seconds": 65,
          "south_north_seconds": 58,
          "timestamp": "2024-01-01T08:30:00Z",
          "message": "資料已成功儲存並完成預測"
        }

        錯誤回傳：
        {
          "error": "請傳入四筆路口特徵資料的清單"
        }
        """
        input_data = request.data
        print(f"收到的輸入資料: {input_data}")

        # 確認輸入是 list 且有四筆資料
        if not isinstance(input_data, list) or len(input_data) != 4:
            return Response({
                "error": "請傳入四筆路口特徵資料的清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 使用預測器取得秒數
            preds = predictor.predict_batch(input_data)

            # 驗證預測結果
            if len(preds) != 4:
                return Response({
                    "error": "預測結果格式錯誤"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 東西向是第 0 與 1 筆，南北向是第 2 與 3 筆
            east_west_max = max(preds[0], preds[1])
            south_north_max = max(preds[2], preds[3])

            # 設定最小和最大秒數限制
            MIN_SECONDS = 40  # 最少40秒
            MAX_SECONDS = 120  # 最多120秒

            east_west_seconds = max(MIN_SECONDS, min(int(east_west_max), MAX_SECONDS))
            south_north_seconds = max(MIN_SECONDS, min(int(south_north_max), MAX_SECONDS))

            print(f"預測結果 - 東西向: {east_west_seconds} 秒, 南北向: {south_north_seconds} 秒")

            # 使用事務來確保資料一致性
            with transaction.atomic():
                # 1. 創建 Group 記錄
                group = Group.objects.create(
                    east_west_seconds=east_west_seconds,
                    south_north_seconds=south_north_seconds
                )

                # 2. 創建 Intersection 記錄
                for intersection_data in input_data:
                    Intersection.objects.create(
                        group=group,
                        VD_ID=intersection_data.get('VD_ID'),
                        DayOfWeek=intersection_data.get('DayOfWeek'),
                        Hour=intersection_data.get('Hour'),
                        Minute=intersection_data.get('Minute'),
                        Second=intersection_data.get('Second'),
                        IsPeakHour=bool(intersection_data.get('IsPeakHour', 0)),
                        LaneID=intersection_data.get('LaneID'),
                        LaneType=intersection_data.get('LaneType'),
                        Speed=intersection_data.get('Speed'),
                        Occupancy=intersection_data.get('Occupancy'),
                        Volume_M=intersection_data.get('Volume_M'),
                        Speed_M=intersection_data.get('Speed_M'),
                        Volume_S=intersection_data.get('Volume_S'),
                        Speed_S=intersection_data.get('Speed_S'),
                        Volume_L=intersection_data.get('Volume_L'),
                        Speed_L=intersection_data.get('Speed_L'),
                        Volume_T=intersection_data.get('Volume_T', 0),
                        Speed_T=intersection_data.get('Speed_T', 0.0),
                    )

            return Response({
                "group_id": str(group.group_id),
                "east_west_seconds": east_west_seconds,
                "south_north_seconds": south_north_seconds,
                "timestamp": group.timestamp.isoformat(),
                "message": "資料已成功儲存並完成預測"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"預測處理失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrafficDataView(APIView):
    """用於查詢交通資料的 API"""

    def get(self, request):
        """
        範例：查詢交通資料 API

        1. 查詢最近10筆批次：
           GET /api/traffic/data/?format=json

        2. 查詢指定批次詳細資料：
           GET /api/traffic/data/?group_id=123e4567-e89b-12d3-a456-426614174000&format=json

        3. 查詢多筆批次（限制數量）：
           GET /api/traffic/data/?limit=20&format=json

        回傳範例1（批次列表）：
        {
          "groups": [
            {
              "group_id": "123e4567-e89b-12d3-a456-426614174000",
              "timestamp": "2024-01-01T08:30:00Z",
              "east_west_seconds": 65,
              "south_north_seconds": 58,
              "intersection_count": 4
            }
          ]
        }

        回傳範例2（特定批次詳細資料）：
        {
          "group": {
            "group_id": "123e4567-e89b-12d3-a456-426614174000",
            "timestamp": "2024-01-01T08:30:00Z",
            "east_west_seconds": 65,
            "south_north_seconds": 58
          },
          "intersections": [
            {
              "id": 1,
              "VD_ID": "VLRJX20",
              "direction": "東向",
              "DayOfWeek": 1,
              "Hour": 8,
              "IsPeakHour": true,
              "Speed": 42.5,
              "Occupancy": 15.3,
              "total_volume": 205
            }
          ]
        }

        """
        try:
            # 取得查詢參數
            group_id = request.query_params.get('group_id')
            limit = request.query_params.get('limit', 10)

            if group_id:
                # 查詢特定批次
                try:
                    group = Group.objects.get(group_id=group_id)
                    intersections = group.intersections.all()

                    return Response({
                        "group": {
                            "group_id": str(group.group_id),
                            "timestamp": group.timestamp.isoformat(),
                            "east_west_seconds": group.east_west_seconds,
                            "south_north_seconds": group.south_north_seconds,
                        },
                        "intersections": [{
                            "id": intersection.id,
                            "VD_ID": intersection.VD_ID,
                            "direction": intersection.get_direction_display,
                            "DayOfWeek": intersection.DayOfWeek,
                            "Hour": intersection.Hour,
                            "Minute": intersection.Minute,
                            "Second": intersection.Second,
                            "IsPeakHour": intersection.IsPeakHour,
                            "LaneID": intersection.LaneID,
                            "LaneType": intersection.LaneType,
                            "Speed": intersection.Speed,
                            "Occupancy": intersection.Occupancy,
                            "Volume_M": intersection.Volume_M,
                            "Speed_M": intersection.Speed_M,
                            "Volume_S": intersection.Volume_S,
                            "Speed_S": intersection.Speed_S,
                            "Volume_L": intersection.Volume_L,
                            "Speed_L": intersection.Speed_L,
                            "Volume_T": intersection.Volume_T,
                            "Speed_T": intersection.Speed_T,
                            "total_volume": intersection.total_volume,
                        } for intersection in intersections]
                    }, status=status.HTTP_200_OK)

                except Group.DoesNotExist:
                    return Response({
                        "error": "找不到指定的批次資料"
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # 查詢最近的資料
                groups = Group.objects.all()[:int(limit)]

                return Response({
                    "groups": [{
                        "group_id": str(group.group_id),
                        "timestamp": group.timestamp.isoformat(),
                        "east_west_seconds": group.east_west_seconds,
                        "south_north_seconds": group.south_north_seconds,
                        "intersection_count": group.intersections.count(),
                    } for group in groups]
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"查詢失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrafficAnalyticsView(APIView):
    """交通資料分析 API - 提供各種視覺化需要的資料聚合"""

    def get(self, request):
        """
        範例：交通資料分析 API

        1. 總覽摘要（儀表板 KPI）：
           GET /api/traffic/analytics/?type=summary&format=json

        2. 時間趨勢分析（折線圖、熱力圖）：
           GET /api/traffic/analytics/?type=trend&days=7&group_by=hour&format=json

        3. 交通流量分析（柱狀圖、圓餅圖）：
           GET /api/traffic/analytics/?type=traffic_flow&days=7&format=json

        4. 尖峰時段分析（比較圖、熱力圖）：
           GET /api/traffic/analytics/?type=peak_analysis&days=7&format=json

        5. 方向對比分析（雷達圖、散佈圖）：
           GET /api/traffic/analytics/?type=direction_comparison&days=7&format=json

        6. 預測效能分析（直方圖、箱型圖）：
           GET /api/traffic/analytics/?type=prediction_performance&days=30&format=json

        回傳：依據 type 參數不同，詳細格式請參考 visualization_api_guide.md
        """
        analysis_type = request.query_params.get('type', 'summary')

        if analysis_type == 'summary':
            return self._get_summary_data(request)
        elif analysis_type == 'trend':
            return self._get_trend_data(request)
        elif analysis_type == 'traffic_flow':
            return self._get_traffic_flow_data(request)
        elif analysis_type == 'peak_analysis':
            return self._get_peak_analysis_data(request)
        elif analysis_type == 'direction_comparison':
            return self._get_direction_comparison_data(request)
        elif analysis_type == 'prediction_performance':
            return self._get_prediction_performance_data(request)
        else:
            return Response({
                "error": "無效的分析類型",
                "available_types": ["summary", "trend", "traffic_flow", "peak_analysis", "direction_comparison", "prediction_performance"]
            }, status=status.HTTP_400_BAD_REQUEST)

    def _get_summary_data(self, request):
        """總覽儀表板資料"""
        try:
            # 基本統計
            total_groups = Group.objects.count()
            total_intersections = Intersection.objects.count()

            # 最近7天的資料
            week_ago = datetime.now() - timedelta(days=7)
            recent_groups = Group.objects.filter(timestamp__gte=week_ago).count()

            # 平均預測秒數
            avg_predictions = Group.objects.aggregate(
                avg_east_west=Avg('east_west_seconds'),
                avg_south_north=Avg('south_north_seconds'),
                max_east_west=Max('east_west_seconds'),
                min_east_west=Min('east_west_seconds'),
                max_south_north=Max('south_north_seconds'),
                min_south_north=Min('south_north_seconds')
            )

            # 各方向資料統計
            direction_stats = []
            for vd_id, direction_name in Intersection.VD_ID_CHOICES:
                count = Intersection.objects.filter(VD_ID=vd_id).count()
                avg_speed = Intersection.objects.filter(VD_ID=vd_id).aggregate(Avg('Speed'))['Speed__avg']
                avg_occupancy = Intersection.objects.filter(VD_ID=vd_id).aggregate(Avg('Occupancy'))['Occupancy__avg']

                direction_stats.append({
                    'direction': direction_name,
                    'vd_id': vd_id,
                    'count': count,
                    'avg_speed': round(avg_speed or 0, 2),
                    'avg_occupancy': round(avg_occupancy or 0, 2)
                })

            return Response({
                "total_groups": total_groups,
                "total_intersections": total_intersections,
                "recent_groups_7days": recent_groups,
                "prediction_stats": {
                    "avg_east_west": round(avg_predictions['avg_east_west'] or 0, 1),
                    "avg_south_north": round(avg_predictions['avg_south_north'] or 0, 1),
                    "max_east_west": avg_predictions['max_east_west'] or 0,
                    "min_east_west": avg_predictions['min_east_west'] or 0,
                    "max_south_north": avg_predictions['max_south_north'] or 0,
                    "min_south_north": avg_predictions['min_south_north'] or 0
                },
                "direction_stats": direction_stats
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_trend_data(self, request):
        """時間趨勢分析資料"""
        try:
            # 參數處理
            days = int(request.query_params.get('days', 7))
            group_by = request.query_params.get('group_by', 'hour')  # hour, day, week

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            groups = Group.objects.filter(timestamp__gte=start_date, timestamp__lte=end_date)

            if group_by == 'hour':
                # 按小時分組
                trend_data = []
                for hour in range(24):
                    hour_groups = groups.filter(timestamp__hour=hour)
                    if hour_groups.exists():
                        avg_east_west = hour_groups.aggregate(Avg('east_west_seconds'))['east_west_seconds__avg']
                        avg_south_north = hour_groups.aggregate(Avg('south_north_seconds'))['south_north_seconds__avg']
                        count = hour_groups.count()

                        trend_data.append({
                            'time_label': f"{hour:02d}:00",
                            'hour': hour,
                            'avg_east_west': round(avg_east_west or 0, 1),
                            'avg_south_north': round(avg_south_north or 0, 1),
                            'count': count
                        })

            elif group_by == 'day':
                # 按日期分組
                trend_data = []
                current_date = start_date.date()
                while current_date <= end_date.date():
                    day_groups = groups.filter(timestamp__date=current_date)
                    if day_groups.exists():
                        avg_east_west = day_groups.aggregate(Avg('east_west_seconds'))['east_west_seconds__avg']
                        avg_south_north = day_groups.aggregate(Avg('south_north_seconds'))['south_north_seconds__avg']
                        count = day_groups.count()

                        trend_data.append({
                            'time_label': current_date.strftime('%Y-%m-%d'),
                            'date': current_date.isoformat(),
                            'avg_east_west': round(avg_east_west or 0, 1),
                            'avg_south_north': round(avg_south_north or 0, 1),
                            'count': count
                        })
                    current_date += timedelta(days=1)

            return Response({
                "period": f"{days} days",
                "group_by": group_by,
                "trend_data": trend_data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_traffic_flow_data(self, request):
        """交通流量分析資料"""
        try:
            # 參數處理
            vd_id = request.query_params.get('vd_id')  # 可選擇特定方向
            days = int(request.query_params.get('days', 7))

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 基本查詢條件
            intersections = Intersection.objects.filter(
                group__timestamp__gte=start_date,
                group__timestamp__lte=end_date
            )

            if vd_id:
                intersections = intersections.filter(VD_ID=vd_id)

            # 流量分析
            flow_data = []
            for vd_id, direction_name in Intersection.VD_ID_CHOICES:
                direction_data = intersections.filter(VD_ID=vd_id)

                if direction_data.exists():
                    # 各類型車輛流量統計
                    vehicle_stats = direction_data.aggregate(
                        total_volume_m=Sum('Volume_M'),
                        total_volume_s=Sum('Volume_S'),
                        total_volume_l=Sum('Volume_L'),
                        total_volume_t=Sum('Volume_T'),
                        avg_speed_m=Avg('Speed_M'),
                        avg_speed_s=Avg('Speed_S'),
                        avg_speed_l=Avg('Speed_L'),
                        avg_speed=Avg('Speed'),
                        avg_occupancy=Avg('Occupancy')
                    )

                    total_volume = (vehicle_stats['total_volume_m'] or 0) + \
                                 (vehicle_stats['total_volume_s'] or 0) + \
                                 (vehicle_stats['total_volume_l'] or 0) + \
                                 (vehicle_stats['total_volume_t'] or 0)

                    flow_data.append({
                        'direction': direction_name,
                        'vd_id': vd_id,
                        'total_volume': total_volume,
                        'volume_breakdown': {
                            'medium': vehicle_stats['total_volume_m'] or 0,
                            'small': vehicle_stats['total_volume_s'] or 0,
                            'large': vehicle_stats['total_volume_l'] or 0,
                            'special': vehicle_stats['total_volume_t'] or 0
                        },
                        'avg_speeds': {
                            'overall': round(vehicle_stats['avg_speed'] or 0, 2),
                            'medium': round(vehicle_stats['avg_speed_m'] or 0, 2),
                            'small': round(vehicle_stats['avg_speed_s'] or 0, 2),
                            'large': round(vehicle_stats['avg_speed_l'] or 0, 2)
                        },
                        'avg_occupancy': round(vehicle_stats['avg_occupancy'] or 0, 2),
                        'data_points': direction_data.count()
                    })

            return Response({
                "period": f"{days} days",
                "flow_analysis": flow_data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_peak_analysis_data(self, request):
        """尖峰時段分析資料"""
        try:
            days = int(request.query_params.get('days', 7))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            intersections = Intersection.objects.filter(
                group__timestamp__gte=start_date,
                group__timestamp__lte=end_date
            )

            # 尖峰 vs 非尖峰比較
            peak_comparison = []
            for is_peak in [True, False]:
                peak_data = intersections.filter(IsPeakHour=is_peak)

                if peak_data.exists():
                    stats = peak_data.aggregate(
                        avg_speed=Avg('Speed'),
                        avg_occupancy=Avg('Occupancy'),
                        total_volume=Sum('Volume_M') + Sum('Volume_S') + Sum('Volume_L') + Sum('Volume_T'),
                        count=Count('id')
                    )

                    # 預測秒數統計
                    prediction_stats = Group.objects.filter(
                        id__in=peak_data.values_list('group_id', flat=True)
                    ).aggregate(
                        avg_east_west=Avg('east_west_seconds'),
                        avg_south_north=Avg('south_north_seconds')
                    )

                    peak_comparison.append({
                        'period_type': '尖峰時段' if is_peak else '非尖峰時段',
                        'is_peak': is_peak,
                        'avg_speed': round(stats['avg_speed'] or 0, 2),
                        'avg_occupancy': round(stats['avg_occupancy'] or 0, 2),
                        'total_volume': stats['total_volume'] or 0,
                        'data_count': stats['count'],
                        'avg_predictions': {
                            'east_west': round(prediction_stats['avg_east_west'] or 0, 1),
                            'south_north': round(prediction_stats['avg_south_north'] or 0, 1)
                        }
                    })

            # 每小時尖峰分布
            hourly_peak_distribution = []
            for hour in range(24):
                hour_data = intersections.filter(Hour=hour)
                peak_count = hour_data.filter(IsPeakHour=True).count()
                total_count = hour_data.count()
                peak_ratio = (peak_count / total_count * 100) if total_count > 0 else 0

                hourly_peak_distribution.append({
                    'hour': hour,
                    'time_label': f"{hour:02d}:00",
                    'peak_count': peak_count,
                    'total_count': total_count,
                    'peak_ratio': round(peak_ratio, 1)
                })

            return Response({
                "period": f"{days} days",
                "peak_comparison": peak_comparison,
                "hourly_peak_distribution": hourly_peak_distribution
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_direction_comparison_data(self, request):
        """方向對比分析資料"""
        try:
            days = int(request.query_params.get('days', 7))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 取得相關的群組和路口資料
            groups = Group.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )

            # 東西向 vs 南北向預測比較
            direction_predictions = []

            # 東西向資料 (VLRJX20 + VLRJM60)
            east_west_intersections = Intersection.objects.filter(
                group__in=groups,
                VD_ID__in=['VLRJX20', 'VLRJM60']
            )

            if east_west_intersections.exists():
                ew_stats = east_west_intersections.aggregate(
                    avg_speed=Avg('Speed'),
                    avg_occupancy=Avg('Occupancy'),
                    total_volume=Sum('Volume_M') + Sum('Volume_S') + Sum('Volume_L') + Sum('Volume_T')
                )

                ew_prediction_avg = groups.aggregate(Avg('east_west_seconds'))['east_west_seconds__avg']

                direction_predictions.append({
                    'direction': '東西向',
                    'direction_code': 'east_west',
                    'avg_speed': round(ew_stats['avg_speed'] or 0, 2),
                    'avg_occupancy': round(ew_stats['avg_occupancy'] or 0, 2),
                    'total_volume': ew_stats['total_volume'] or 0,
                    'avg_prediction_seconds': round(ew_prediction_avg or 0, 1),
                    'data_points': east_west_intersections.count()
                })

            # 南北向資料 (VLRJX00)
            south_north_intersections = Intersection.objects.filter(
                group__in=groups,
                VD_ID='VLRJX00'
            )

            if south_north_intersections.exists():
                sn_stats = south_north_intersections.aggregate(
                    avg_speed=Avg('Speed'),
                    avg_occupancy=Avg('Occupancy'),
                    total_volume=Sum('Volume_M') + Sum('Volume_S') + Sum('Volume_L') + Sum('Volume_T')
                )

                sn_prediction_avg = groups.aggregate(Avg('south_north_seconds'))['south_north_seconds__avg']

                direction_predictions.append({
                    'direction': '南北向',
                    'direction_code': 'south_north',
                    'avg_speed': round(sn_stats['avg_speed'] or 0, 2),
                    'avg_occupancy': round(sn_stats['avg_occupancy'] or 0, 2),
                    'total_volume': sn_stats['total_volume'] or 0,
                    'avg_prediction_seconds': round(sn_prediction_avg or 0, 1),
                    'data_points': south_north_intersections.count()
                })

            # 預測秒數分布
            prediction_distribution = groups.values('east_west_seconds', 'south_north_seconds')

            return Response({
                "period": f"{days} days",
                "direction_comparison": direction_predictions,
                "prediction_samples": list(prediction_distribution[:50])  # 最近50筆樣本
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_prediction_performance_data(self, request):
        """預測效能分析資料"""
        try:
            days = int(request.query_params.get('days', 30))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            groups = Group.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )

            # 預測秒數分布統計
            prediction_ranges = [
                (40, 50, '40-50秒'),
                (51, 60, '51-60秒'),
                (61, 70, '61-70秒'),
                (71, 80, '71-80秒'),
                (81, 90, '81-90秒'),
                (91, 100, '91-100秒'),
                (101, 120, '101-120秒')
            ]

            east_west_distribution = []
            south_north_distribution = []

            for min_val, max_val, label in prediction_ranges:
                ew_count = groups.filter(
                    east_west_seconds__gte=min_val,
                    east_west_seconds__lte=max_val
                ).count()

                sn_count = groups.filter(
                    south_north_seconds__gte=min_val,
                    south_north_seconds__lte=max_val
                ).count()

                east_west_distribution.append({
                    'range': label,
                    'min_seconds': min_val,
                    'max_seconds': max_val,
                    'count': ew_count
                })

                south_north_distribution.append({
                    'range': label,
                    'min_seconds': min_val,
                    'max_seconds': max_val,
                    'count': sn_count
                })

            # 預測準確性指標
            performance_metrics = groups.aggregate(
                avg_east_west=Avg('east_west_seconds'),
                avg_south_north=Avg('south_north_seconds'),
                std_east_west=Avg('east_west_seconds'),  # 簡化版標準差
                std_south_north=Avg('south_north_seconds'),
                max_east_west=Max('east_west_seconds'),
                min_east_west=Min('east_west_seconds'),
                max_south_north=Max('south_north_seconds'),
                min_south_north=Min('south_north_seconds')
            )

            return Response({
                "period": f"{days} days",
                "total_predictions": groups.count(),
                "east_west_distribution": east_west_distribution,
                "south_north_distribution": south_north_distribution,
                "performance_metrics": {
                    "east_west": {
                        "avg": round(performance_metrics['avg_east_west'] or 0, 1),
                        "max": performance_metrics['max_east_west'] or 0,
                        "min": performance_metrics['min_east_west'] or 0,
                        "range": (performance_metrics['max_east_west'] or 0) - (performance_metrics['min_east_west'] or 0)
                    },
                    "south_north": {
                        "avg": round(performance_metrics['avg_south_north'] or 0, 1),
                        "max": performance_metrics['max_south_north'] or 0,
                        "min": performance_metrics['min_south_north'] or 0,
                        "range": (performance_metrics['max_south_north'] or 0) - (performance_metrics['min_south_north'] or 0)
                    }
                }
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrafficTimeSeriesView(APIView):
    """時間序列資料 API - 專門用於時間軸圖表"""

    def get(self, request):
        """
        範例：時間序列資料 API

        1. 預測秒數時間序列（折線圖）：
           GET /api/traffic/timeseries/?days=7&metric=predictions&format=json

        2. 交通流量時間序列（面積圖）：
           GET /api/traffic/timeseries/?days=7&metric=traffic_volume&format=json

        3. 長期趨勢分析：
           GET /api/traffic/timeseries/?days=30&metric=predictions&format=json

        4. 指定日期範圍查詢（優先於 days 參數）：
           GET /api/traffic/timeseries/?start_date=2024-01-01&end_date=2024-01-31&metric=predictions&format=json

        5. 單一日期查詢：
           GET /api/traffic/timeseries/?start_date=2024-01-15&end_date=2024-01-15&metric=traffic_volume&format=json

        回傳範例1（預測序列）：
        {
          "metric": "predictions",
          "period": "2024-01-01 ~ 2024-01-31",
          "data_points": 168,
          "time_series": [
            {
              "timestamp": "2024-01-01T00:00:00Z",
              "group_id": "123e4567-e89b-12d3-a456-426614174000",
              "east_west_seconds": 65,
              "south_north_seconds": 58
            }
          ]
        }

        回傳範例2（流量序列）：
        {
          "metric": "traffic_volume",
          "period": "7 days",
          "data_points": 168,
          "time_series": [
            {
              "timestamp": "2024-01-01T00:00:00Z",
              "group_id": "123e4567-e89b-12d3-a456-426614174000",
              "total_volume": 820,
              "avg_speed": 42.5,
              "avg_occupancy": 15.3
            }
          ]
        }

        錯誤回傳：
        {
          "error": "查詢失敗: ..."
        }
        """
        try:
            # 參數處理
            import re
            days = int(request.query_params.get('days', 7))
            interval = request.query_params.get('interval', 'hour')  # hour, day
            metric = request.query_params.get('metric', 'predictions')  # predictions, traffic_volume, speed
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')

            # 日期格式驗證 YYYY-MM-DD
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            now = datetime.now()

            # 優先使用日期範圍參數，否則使用 days 參數
            if start_date_str and re.match(date_pattern, start_date_str):
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            else:
                start_date = now - timedelta(days=days)

            if end_date_str and re.match(date_pattern, end_date_str):
                # end_date 設定為當天的 23:59:59
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
            else:
                end_date = now

            groups = Group.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')

            # 期間顯示字串
            if start_date_str and end_date_str:
                period_str = f"{start_date_str} ~ {end_date_str}"
            else:
                period_str = f"{days} days"

            if metric == 'predictions':
                # 預測秒數時間序列
                time_series = []
                for group in groups:
                    time_series.append({
                        'timestamp': group.timestamp.isoformat(),
                        'group_id': str(group.group_id),
                        'east_west_seconds': group.east_west_seconds,
                        'south_north_seconds': group.south_north_seconds
                    })

                return Response({
                    "metric": "predictions",
                    "period": period_str,
                    "data_points": len(time_series),
                    "time_series": time_series
                })

            elif metric == 'traffic_volume':
                # 交通流量時間序列
                time_series = []
                for group in groups:
                    intersections = group.intersections.all()
                    total_volume = sum(
                        intersection.total_volume for intersection in intersections
                    )
                    avg_speed = intersections.aggregate(Avg('Speed'))['Speed__avg'] or 0
                    avg_occupancy = intersections.aggregate(Avg('Occupancy'))['Occupancy__avg'] or 0

                    time_series.append({
                        'timestamp': group.timestamp.isoformat(),
                        'group_id': str(group.group_id),
                        'total_volume': total_volume,
                        'avg_speed': round(avg_speed, 2),
                        'avg_occupancy': round(avg_occupancy, 2)
                    })

                return Response({
                    "metric": "traffic_volume",
                    "period": period_str,
                    "data_points": len(time_series),
                    "time_series": time_series
                })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
