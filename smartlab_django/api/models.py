from django.db import models
from django.utils import timezone


class DataLog(models.Model):
    """
    设备状态日志
    """
    temperature = models.DecimalField(verbose_name="温度", max_digits=5, decimal_places=2)
    humidity = models.DecimalField(verbose_name="湿度", max_digits=5, decimal_places=2)
    led_1_status = models.BooleanField(verbose_name="LED_1", default=False)
    led_2_status = models.BooleanField(verbose_name="LED_2", default=False)
    led_3_status = models.BooleanField(verbose_name="LED_3", default=False)
    ac_status = models.BooleanField(verbose_name="AC", default=False)
    led_num = models.PositiveIntegerField(verbose_name="LED开启数量")
    create_time = models.DateTimeField(verbose_name="记录时间", default=timezone.now)
