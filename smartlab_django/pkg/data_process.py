def led_num2light_intensity(*args):
    """
    计算光照强度
    :param args: int
    :return: float
    """
    led_num = sum(args)
    return led_num * 50 + 100


def ac_num2temperature(*args):
    """
    计算温度
    :param args: int
    :return: float
    """
    ac_num = sum(args)
    return max(25 - ac_num * 3, 16)
