from datetime import datetime

def convert_timestamp_to_datetime(timestamp):
    """
    Chuyển timestamp Unix sang dạng thời gian chuẩn
    """
    return datetime.utcfromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")

def format_currency(value, decimals=2):
    """
    Định dạng giá trị tiền tệ
    """
    return f"{value:.{decimals}f}"

def is_valid_number(value):
    """
    Kiểm tra nếu một giá trị là số hợp lệ
    """
    return isinstance(value, (int, float)) and not (value is None or value != value)  # value != value để check NaN
