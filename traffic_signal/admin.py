from django.contrib import admin
from .models import Group, Intersection

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """資料組主表的管理介面"""
    list_display = [
        'id',
        'group_id',
        'timestamp',
        'east_west_seconds',
        'south_north_seconds',
        'get_intersection_count'
    ]
    list_filter = ['timestamp']
    search_fields = ['group_id']
    readonly_fields = ['group_id', 'timestamp']
    ordering = ['-timestamp']

    def get_intersection_count(self, obj):
        """顯示該批次包含的路口資料數量"""
        return obj.intersections.count()
    get_intersection_count.short_description = '路口資料數量'


class IntersectionInline(admin.TabularInline):
    """路口明細的內嵌編輯"""
    model = Intersection
    extra = 0
    readonly_fields = ['created_at']
    fields = [
        'VD_ID', 'LaneID', 'DayOfWeek', 'Hour', 'Minute', 'Second',
        'IsPeakHour', 'Speed', 'Occupancy',
        'Volume_M', 'Speed_M', 'Volume_S', 'Speed_S',
        'Volume_L', 'Speed_L', 'Volume_T', 'Speed_T'
    ]


@admin.register(Intersection)
class IntersectionAdmin(admin.ModelAdmin):
    """路口明細表的管理介面"""
    list_display = [
        'id',
        'group',
        'VD_ID',
        'get_direction_display',
        'LaneID',
        'DayOfWeek',
        'Hour',
        'Minute',
        'IsPeakHour',
        'Speed',
        'Occupancy',
        'total_volume',
        'created_at'
    ]
    list_filter = [
        'VD_ID',
        'DayOfWeek',
        'IsPeakHour',
        'LaneType',
        'created_at'
    ]
    search_fields = ['group__group_id', 'VD_ID']
    ordering = ['-created_at', 'group', 'VD_ID', 'LaneID']

    fieldsets = (
        ('基本資訊', {
            'fields': ('group', 'VD_ID', 'LaneID', 'LaneType')
        }),
        ('時間資訊', {
            'fields': ('DayOfWeek', 'Hour', 'Minute', 'Second', 'IsPeakHour')
        }),
        ('交通數據', {
            'fields': ('Speed', 'Occupancy')
        }),
        ('中型車數據', {
            'fields': ('Volume_M', 'Speed_M'),
            'classes': ('collapse',)
        }),
        ('小型車數據', {
            'fields': ('Volume_S', 'Speed_S'),
            'classes': ('collapse',)
        }),
        ('大型車數據', {
            'fields': ('Volume_L', 'Speed_L'),
            'classes': ('collapse',)
        }),
        ('特種車數據', {
            'fields': ('Volume_T', 'Speed_T'),
            'classes': ('collapse',)
        }),
        ('系統資訊', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']

    def get_direction_display(self, obj):
        """顯示方向的中文說明"""
        return obj.get_direction_display
    get_direction_display.short_description = '方向'


# 將 Intersection 作為 Group 的內嵌編輯
GroupAdmin.inlines = [IntersectionInline]
