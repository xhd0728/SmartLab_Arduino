def gen_echarts_option(x_data, y_data):
    """
    echarts配置文件
    :param x_data: list
    :param y_data: list
    :return: dict
    """
    return {
        'grid': {
            'left': '1%',
            'right': '1%',
            'top': '5%',
            'bottom': '5%',
            'containLabel': 'true',
        },
        'xAxis': {
            'type': 'category',
            'data': x_data
        },
        'yAxis': {
            'type': 'value'
        },
        'series': [
            {

                'data': y_data,
                'type': 'line'
            }
        ]
    }
