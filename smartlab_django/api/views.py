import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import serial
from config.serial_cfg import *
from pkg.data_process import led_num2light_intensity, ac_num2temperature
from .models import DataLog
from .serializers import DataLogSerializer


class DeviceInfoView(APIView):
    """
    获取设备状态
    """

    def get(self, request):
        """
        从COM2读取设备装填
        :param request: 请求体
        :return: Response
        """
        ser = serial.Serial(portx=PORTX, bps=BPS, timeout=TIMEX)
        opt_data = ser.read(ser.in_waiting).decode("utf-8")
        opt_ls = opt_data.split(",")
        tpl_ls = [
            'ac_status',
            'led_1_status',
            'led_2_status',
            'led_3_status',
            'temperature',
            'humidity'
        ]
        if len(opt_ls) != len(tpl_ls):
            return Response({"status": "error", "msg": "数据格式不匹配"}, status=status.HTTP_200_OK)

        opt_dict = zip(tpl_ls, opt_ls)

        try:
            DataLog.objects.create(
                temperature=opt_dict['temperature'],
                humidity=opt_dict['humidity'],
                led_1_status=opt_dict['led_1_status'],
                led_2_status=opt_dict['led_2_status'],
                led_3_status=opt_dict['led_3_status'],
                ac_status=opt_dict['ac_status'],
                led_num=int(opt_dict['led_1_status'] + opt_dict['led_2_status'] + opt_dict['led_3_status']),
            )
        except Exception as e:
            print(e)
            return Response({"status": "error", "msg": "数据库写入失败"}, status=status.HTTP_200_OK)
        return Response({"status": "ok", "data": opt_dict}, status=status.HTTP_200_OK)


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

        light_intensity = led_num2light_intensity(led1_status, led2_status, led3_status) + random.uniform(-0.5, 0.5)
        temperature = ac_num2temperature(ac_status) + random.uniform(-0.5, 0.5)

        ser = serial.Serial(PORTX, BPS, timeout=TIMEX)
        send_str = f"{ac_status},{led1_status},{led2_status},{led3_status},{light_intensity},{temperature}\r\n"
        # print(send_str.strip())
        try:
            ser.write(send_str.encode("utf-8"))
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
        temperature_option = {
            'xAxis': {
                'type': 'category',
                'data': id_list
            },
            'yAxis': {
                'type': 'value'
            },
            'series': [
                {

                    'data': temperature_list,
                    'type': 'line'
                }
            ]
        }
        humidity_option = {
            'xAxis': {
                'type': 'category',
                'data': id_list
            },
            'yAxis': {
                'type': 'value'
            },
            'series': [
                {

                    'data': humidity_list,
                    'type': 'line'
                }
            ]
        }
        return Response({
            "status": "ok",
            "temperature": temperature_option,
            "humidity": humidity_option,
            "temperature_now": temperature_list[0],
            "humidity_now": humidity_list[0]
        })
