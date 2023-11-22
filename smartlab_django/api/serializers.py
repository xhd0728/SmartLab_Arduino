from rest_framework import serializers
from .models import DataLog


class DataLogSerializer(serializers.ModelSerializer):
    """
    日志序列化器
    """
    lid = serializers.ReadOnlyField(source='id')
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = DataLog
        fields = (
            'lid',
            'temperature',
            'humidity',
            'led_1_status',
            'led_2_status',
            'led_3_status',
            'ac_status',
            'led_num',
            'air_conditioner_status',
            'create_time'
        )
