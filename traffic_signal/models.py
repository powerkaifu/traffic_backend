from django.db import models
import uuid
from django.utils import timezone

class Group(models.Model):
    """
    資料組主表 - 存放每次前端送來的四路口資料的整體批次資訊以及預測的東西、南北最大綠燈秒數
    """
    id = models.BigAutoField(primary_key=True, verbose_name='主鍵ID')
    group_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name='批次唯一識別碼',
        help_text='一組四路口資料歸為同一批'
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name='資料接收或預測時間'
    )
    east_west_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='東西向最大綠燈秒數',
        help_text='模型預測的東西向最大綠燈秒數'
    )
    south_north_seconds = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='南北向最大綠燈秒數',
        help_text='模型預測的南北向最大綠燈秒數'
    )

    class Meta:
        verbose_name = '資料組主表'
        verbose_name_plural = '資料組主表'
        ordering = ['-timestamp']  # 依時間倒序排列

    def __str__(self):
        return f"Group {self.group_id} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class Intersection(models.Model):
    """
    路口明細表 - 存放每次傳送過來四個路口的詳細交通特徵資料
    """
    VD_ID_CHOICES = [
        ('VLRJX20', '往東 (VLRJX20)'),
        ('VLRJM60', '往西 (VLRJM60)'),
        ('VLRJX00', '往南/往北 (VLRJX00)'),
    ]

    WEEKDAY_CHOICES = [
        (1, '星期一'),
        (2, '星期二'),
        (3, '星期三'),
        (4, '星期四'),
        (5, '星期五'),
        (6, '星期六'),
        (7, '星期日'),
    ]

    id = models.BigAutoField(primary_key=True, verbose_name='主鍵ID')
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='intersections',
        verbose_name='關聯到資料組主表'
    )

    # 基本資訊
    VD_ID = models.CharField(
        max_length=10,
        choices=VD_ID_CHOICES,
        verbose_name='路口偵測器ID'
    )
    DayOfWeek = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        verbose_name='星期'
    )
    Hour = models.IntegerField(
        verbose_name='時',
        help_text='0-23'
    )
    Minute = models.IntegerField(
        verbose_name='分',
        help_text='0-59'
    )
    Second = models.IntegerField(
        verbose_name='秒',
        help_text='0-59'
    )
    IsPeakHour = models.BooleanField(
        verbose_name='是否尖峰時段',
        help_text='True=尖峰時段, False=非尖峰時段'
    )

    # 車道資訊
    LaneID = models.IntegerField(verbose_name='車道編號')
    LaneType = models.IntegerField(verbose_name='車道類型')

    # 基本交通數據
    Speed = models.FloatField(verbose_name='平均速率')
    Occupancy = models.FloatField(verbose_name='車道佔有率')

    # 中型車數據
    Volume_M = models.IntegerField(verbose_name='中型車流量')
    Speed_M = models.FloatField(verbose_name='中型車速率')

    # 小型車數據
    Volume_S = models.IntegerField(verbose_name='小型車流量')
    Speed_S = models.FloatField(verbose_name='小型車速率')

    # 大型車數據
    Volume_L = models.IntegerField(verbose_name='大型車流量')
    Speed_L = models.FloatField(verbose_name='大型車速率')

    # 特種車數據（可選）
    Volume_T = models.IntegerField(
        default=0,
        verbose_name='特種車流量',
        help_text='特種車流量，預設為0'
    )
    Speed_T = models.FloatField(
        default=0.0,
        verbose_name='特種車速率',
        help_text='特種車速率，預設為0.0'
    )

    # 建立時間
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='建立時間'
    )

    class Meta:
        verbose_name = '路口明細表'
        verbose_name_plural = '路口明細表'
        ordering = ['group', 'VD_ID', 'LaneID']

    def __str__(self):
        return f"{self.VD_ID} - Lane {self.LaneID} (Group: {self.group.group_id})"

    @property
    def get_direction_display(self):
        """取得方向的中文顯示"""
        direction_map = {
            'VLRJX20': '往東',
            'VLRJM60': '往西',
            'VLRJX00': '往南/往北'
        }
        return direction_map.get(self.VD_ID, self.VD_ID)

    @property
    def total_volume(self):
        """計算總車流量"""
        return self.Volume_M + self.Volume_S + self.Volume_L + self.Volume_T
