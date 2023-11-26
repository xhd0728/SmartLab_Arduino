import random
import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import serial
from config.serial_cfg import *
from config.echarts import gen_echarts_option
from pkg.data_process import led_num2light_intensity, ac_num2temperature
from .models import DataLog
from .serializers import DataLogSerializer

ser = serial.Serial(PORTX, BPS, timeout=TIMEX)


class DeviceHistoryView(APIView):
    """
    获取操作日志
    """

    def get(self, request):
        """
        请求设备操作日志
        :param request: 请求体
        :return: Response
        """
        query_set = DataLog.objects.all().order_by("-create_time")[:20]
        return Response(DataLogSerializer(query_set, many=True).data, status=status.HTTP_200_OK)


class OptionSetView(APIView):
    """
    设置设备状态
    """

    def post(self, request):
        """
        向COM1传递控制字
        :param request: 请求体
        :return: Response
        """
        ac_status = int(request.data.get('ac_status')) or 0
        led1_status = int(request.data.get('led1_status')) or 0
        led2_status = int(request.data.get('led2_status')) or 0
        led3_status = int(request.data.get('led3_status')) or 0
        # is_update = int(request.data.get('is_update')) or 0

        light_intensity = led_num2light_intensity(led1_status, led2_status, led3_status) + random.uniform(-0.5, 0.5)
        # temperature = ac_num2temperature(ac_status) + random.uniform(-0.5, 0.5)
        # ser = serial.Serial(PORTX, BPS, timeout=TIMEX)

        temperature = 7
        # light_intensity = 8
        get_temperature = False
        get_light_intensity = False
        while not get_temperature and not get_light_intensity:
            opt_data = ser.read_until().decode('utf-8')
            if opt_data:
                print(opt_data)
                tmp_str = opt_data.strip().split(",")
                if tmp_str[0] == '2' and not get_temperature:
                    temperature = int(tmp_str[1])
                    get_temperature = True

        if True:
            try:
                ser.write(f"3,0,{led1_status}".encode("utf-8"))
                time.sleep(0.4)
                ser.write(f"3,1,{led2_status}".encode("utf-8"))
                time.sleep(0.4)
                ser.write(f"3,2,{led3_status}".encode("utf-8"))
                time.sleep(0.4)
                ser.write(f"3,3,{ac_status}".encode("utf-8"))
            except Exception as e:
                print(e)
                return Response({"status": "error", "msg": "与Arduino通信失败"})

        try:
            DataLog.objects.create(
                temperature=temperature,
                humidity=light_intensity,
                led_1_status=led1_status,
                led_2_status=led2_status,
                led_3_status=led3_status,
                ac_status=ac_status,
                led_num=led1_status + led2_status + led3_status
            )
        except Exception as e:
            print(e)
            return Response({"status": "error", "msg": "MySQL写日志失败"})
        try:
            latest_ids_to_keep = DataLog.objects.order_by("-create_time").values_list('id', flat=True)[:30]
            DataLog.objects.exclude(id__in=latest_ids_to_keep).delete()
        except Exception as e:
            print(e)
            return Response({"status": "error", "msg": "MySQL清除冗余日志失败"})
        return Response({"status": "ok"})


class EChartsView(APIView):
    """
    图表数据处理
    """

    def get(self, request):
        """
        获取图表
        :param request: 请求体
        :return: Response
        """
        query_set = DataLog.objects.all().order_by("-create_time")[:20]
        id_list = query_set.values_list('id', flat=True)
        temperature_list = query_set.values_list('temperature', flat=True)
        humidity_list = query_set.values_list('humidity', flat=True)
        temperature_option = gen_echarts_option(id_list, temperature_list)
        humidity_option = gen_echarts_option(id_list, humidity_list)
        return Response({
            "status": "ok",
            "temperature": temperature_option,
            "humidity": humidity_option,
            "temperature_now": temperature_list[0],
            "humidity_now": humidity_list[0]
        })
