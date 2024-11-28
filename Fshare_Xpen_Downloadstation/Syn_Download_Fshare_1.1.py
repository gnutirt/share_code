import time
from synology_api import downloadstation
import csv

# Thông tin kết nối của bạn
DSM_IP = ""
DSM_PORT = "5001"
USERNAME = ""
PASSWORD = ""
filename = 'fshare_download_list.csv'
delta_t = 60  # Khoảng thời gian giữa các lần kiểm tra trạng thái (giây)
num_download = 10  # Số lượng tối đa tác vụ tải xuống đang chạy đồng thời

# Khởi tạo đối tượng DownloadStation
ds = downloadstation.DownloadStation(DSM_IP, DSM_PORT, USERNAME, PASSWORD, secure=True, cert_verify=False, dsm_version=7, debug=True)

# Hàm đọc CSV và lấy URL và tiến trình
def read_csv(filename):
    url_progress = {}
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                url = row['url'].split('?')[0]  # Xử lý URL nếu có query string
                url_progress[url] = float(row['progress']) if row['progress'] != 'broken' else 'broken'
    except FileNotFoundError:
        print(f"File {filename} không tìm thấy.")
    return url_progress

# Hàm ghi tiến trình cập nhật vào CSV
def write_csv(filename, url_progress):
    try:
        # Đọc file CSV cũ và thay thế tiến trình cho từng URL
        rows = []
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                url = row['url'].split('?')[0]
                if url in url_progress:
                    row['progress'] = url_progress[url]  # Cập nhật tiến trình
                rows.append(row)
        
        # Ghi lại dữ liệu vào CSV
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ['url', 'progress']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    except Exception as e:
        print(f"Lỗi khi ghi file CSV: {e}")

# Hàm kiểm tra trạng thái tải xuống và cập nhật tiến trình
def check_download_status_and_update_progress(ds, filename):
    num_ongoing_dl = 0
    num_error_dl = 0
    downloading_list = []
    url_progress = read_csv(filename)

    try:
        tasks = ds.tasks_list()
        if not isinstance(tasks, dict):
            print(f"Phản hồi không hợp lệ: {tasks}")
            return num_ongoing_dl, num_error_dl, downloading_list, url_progress

        task_list = tasks.get('data', {}).get('tasks', [])
        total_tasks = len(task_list)

        if not task_list:
            print("Không có tác vụ tải xuống nào đang chạy.")
            return num_ongoing_dl, num_error_dl, downloading_list, url_progress
        print("--------------------------------------------------")
        print("--------------------------------------------------")
        print(f"Tổng tải: {total_tasks}, Đang tải: {num_ongoing_dl}, Lỗi: {num_error_dl}")

        for task in task_list:
            uri = task.get("additional", {}).get("detail", {}).get("uri", "")
            uri_clean = uri.split('?')[0]  # Loại bỏ phần ?token= nếu có

            size_downloaded = task.get("additional", {}).get("transfer", {}).get("size_downloaded", 0)
            size_total = task.get("size", 0)
            progress = (size_downloaded / size_total * 100) if size_total > 0 else 0
            status = task.get("status", "")

            # In thông tin chi tiết về trạng thái và tiến trình
            # print("--------------------------------------------------")
            print(f"URL: {uri_clean}, Status: {status}, Size downloaded: {size_downloaded}, Size total: {size_total}, Progress: {progress:.2f}%")

            # Nếu trạng thái là "error", đánh dấu progress là "broken" và không tính vào num_ongoing_dl
            if status == "error":
                url_progress[uri_clean] = "broken"  # Đánh dấu là broken
                num_error_dl += 1
                print(f"URL {uri_clean} bị lỗi, progress được cập nhật thành broken.")
                continue  # Bỏ qua tác vụ lỗi và không tính vào số lượng tác vụ đang tải

            downloading_list.append(uri_clean)
            num_ongoing_dl += 1

            # In ra để debug trước khi ghi vào CSV
            # print("--------------------------------------------------")
            # print(f"Cập nhật progress cho URL: {uri_clean} - Progress: {progress:.2f}%")
            url_progress[uri_clean] = progress  # Cập nhật tiến trình vào url_progress
            # print("--------------------------------------------------")

        # Cập nhật file CSV sau khi thay đổi tiến trình
        print(f"Cập nhật tiến trình vào file CSV với {len(url_progress)} URL.")
        write_csv(filename, url_progress)

        # Hiển thị thông tin tổng quát về các tác vụ tải xuống
        print(f"Tổng tải: {total_tasks}, Đang tải: {num_ongoing_dl}, Lỗi: {num_error_dl}")

        return num_ongoing_dl, num_error_dl, downloading_list, url_progress

    except Exception as e:
        print(f"Lỗi khi lấy trạng thái các tác vụ: {e}")
        return num_ongoing_dl, num_error_dl, downloading_list, url_progress


# Hàm thêm tác vụ tải xuống vào DownloadStation
def add_download_task(url):
    try:
        task = ds.create_task(url)
        print(f"Tác vụ tải xuống đã được tạo: {task}")
    except Exception as e:
        print(f"Lỗi khi tạo tác vụ tải xuống từ URL {url}: {e}")

# Hàm chính để thực hiện quy trình
def main():
    while True:
        # Kiểm tra trạng thái và cập nhật tiến trình
        num_ongoing_dl, num_error_dl, downloading_list, url_progress = check_download_status_and_update_progress(ds, filename)

        # Nếu số lượng tác vụ tải xuống hiện tại ít hơn num_download, quét file CSV và thêm tác vụ
        if num_ongoing_dl < num_download:
            # Tính số lượng tác vụ cần thêm vào
            num_tasks_to_add = num_download - num_ongoing_dl
            tasks_added = 0

            for url, progress in url_progress.items():
                # Kiểm tra điều kiện: URL chưa có trong danh sách đang tải và progress = 0
                if url not in downloading_list and progress == 0 and tasks_added < num_tasks_to_add:
                    add_download_task(url)
                    tasks_added += 1  # Đếm số tác vụ đã thêm vào

                    # Nếu đã thêm đủ số tác vụ, dừng vòng lặp
                    if tasks_added >= num_tasks_to_add:
                        break
                    time.sleep(5)

        # Đợi một khoảng thời gian delta_t trước khi thực hiện lại
        print(f"Đang đợi {delta_t} giây trước khi kiểm tra lại...")
        time.sleep(delta_t)

# Bắt đầu quy trình chính
main()
