"""
測試交通資料的 Django management command
使用方式: python manage.py test_traffic_data
"""
from django.core.management.base import BaseCommand
from ...data_utils import TrafficDataManager, TrafficDataValidator
from ...models import Group, Intersection
import json


class Command(BaseCommand):
    help = '測試交通資料的建立、查詢和驗證功能'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='建立範例資料',
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='顯示資料庫統計',
        )
        parser.add_argument(
            '--list-recent',
            type=int,
            default=5,
            help='列出最近的 N 筆資料 (預設: 5)',
        )

    def handle(self, *args, **options):
        if options['create_sample']:
            self.create_sample_data()

        if options['show_stats']:
            self.show_statistics()

        if options['list_recent']:
            self.list_recent_data(options['list_recent'])

    def create_sample_data(self):
        """建立範例交通資料"""
        self.stdout.write("正在建立範例交通資料...")

        # 使用文件中提供的範例資料
        sample_data = [
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

        try:
            # 驗證資料
            errors = TrafficDataValidator.validate_batch_data(sample_data)
            if errors:
                self.stdout.write(
                    self.style.ERROR(f"資料驗證失敗:")
                )
                for error in errors:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
                return

            # 建立資料
            group = TrafficDataManager.create_traffic_batch(
                sample_data,
                east_west_seconds=75,
                south_north_seconds=65
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"成功建立範例資料! Group ID: {group.group_id}"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"建立範例資料失敗: {str(e)}")
            )

    def show_statistics(self):
        """顯示資料庫統計資訊"""
        self.stdout.write("=== 資料庫統計資訊 ===")

        try:
            stats = TrafficDataManager.get_statistics()

            self.stdout.write(f"總批次數: {stats['total_batches']}")
            self.stdout.write(f"總路口資料數: {stats['total_intersections']}")
            self.stdout.write(f"最新資料時間: {stats['latest_timestamp']}")

            self.stdout.write("\\n各方向資料統計:")
            for direction, count in stats['direction_statistics'].items():
                self.stdout.write(f"  {direction}: {count} 筆")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"取得統計資訊失敗: {str(e)}")
            )

    def list_recent_data(self, limit):
        """列出最近的資料"""
        self.stdout.write(f"=== 最近 {limit} 筆資料 ===")

        try:
            recent_batches = TrafficDataManager.get_recent_batches(limit)

            if not recent_batches:
                self.stdout.write("目前沒有資料")
                return

            for batch in recent_batches:
                self.stdout.write(
                    f"批次 ID: {batch['group_id'][:8]}... "
                    f"時間: {batch['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} "
                    f"東西向: {batch['east_west_seconds']}秒 "
                    f"南北向: {batch['south_north_seconds']}秒 "
                    f"路口數: {batch['intersection_count']}"
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"列出資料失敗: {str(e)}")
            )
