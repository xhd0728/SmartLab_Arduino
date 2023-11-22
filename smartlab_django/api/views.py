from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import serial
from config.serial_cfg import *
from pkg.data_process import led_num2light_intensity, ac_num2temperature
from .models import DataLog
from .serializers import DataLogSerializer


class DeviceInfoView(APIView):
    def get(self, request):
        ser = serial.Serial(portx=PORTX, bps=BPS, timeout=TIMEX)
        opt_data = ser.read(ser.in_waiting).decode("utf-8")
        opt_ls = opt_data.split(",")
        tpl_ls = [
            'air_conditioner_status',
            'led_num',
            'light_intensity',
            'temperature',
            'humidity'
        ]
        if len(opt_ls) != len(tpl_ls):
            return Response({"status": "error", "msg": "通讯失败"}, status=status.HTTP_200_OK)

        opt_dict = zip(tpl_ls, opt_ls)

        try:
            DataLog.objects.create(
                temperature=opt_dict.get('temperature'),
                humidity=opt_dict.get('humidity'),
                led_num=opt_dict.get('led_num'),
                air_conditioner_status=opt_dict.get('air_conditioner_status')
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

        light_intensity = led_num2light_intensity(led1_status, led2_status, led3_status)
        temperature = ac_num2temperature(ac_status)

        ser = serial.Serial(PORTX, BPS, timeout=TIMEX)
        send_str = f"{ac_status},{led1_status},{led2_status},{led3_status},{light_intensity},{temperature}\r\n"
        try:
            ser.write(send_str.encode("utf-8"))
        except Exception as e:
            print(e)
            return Response({"status": "error", "msg": "与Arduino通信失败"})
        return Response({"status": "ok"})
