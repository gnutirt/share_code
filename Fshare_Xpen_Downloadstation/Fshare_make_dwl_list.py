import xml.etree.ElementTree as ET
import csv

# Đọc file XML
file_name = "AB.xml"

try:
    # Phân tích nội dung file XML
    tree = ET.parse(file_name)
    root = tree.getroot()

    # Tạo danh sách lưu thông tin URL và progress
    fshare_data = []

    # Lọc ra các file có URL chứa "https://www.fshare.vn/file/"
    for file in root.findall('file'):
        url = file.get('url')
        progress = file.get('progress', '0')  # Nếu không có progress thì mặc định là 0
        if url and "https://www.fshare.vn/file/" in url:
            fshare_data.append([url, progress])

    # Xuất kết quả ra file CSV
    output_csv = "fshare_download_list.csv"
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Ghi tiêu đề
        csv_writer.writerow(["url", "progress"])
        # Ghi dữ liệu
        csv_writer.writerows(fshare_data)

    print(f"Dữ liệu đã được xuất ra file '{output_csv}' với {len(fshare_data)} dòng.")
except Exception as e:
    print(f"Lỗi khi xử lý file XML: {e}")
