# Hướng dẫn

## 1-Tải toàn bộ file trên trong 1 thư mục 

## 2-Vào Download Station DSM

Add File Host vào và kích hoạt

![Add File Host vào ](https://github.com/gnutirt/share_code/blob/main/Fshare_Xpen_Downloadstation/Screenshot%202024-11-28%20202832.png?raw=true)

![và kích hoạt](https://github.com/gnutirt/share_code/blob/main/Fshare_Xpen_Downloadstation/Screenshot%202024-11-28%20203030.png?raw=true)
## 3-Mở fsharetool lên - dán link folder vào, sau khi dán xong sẽ hiện ra danh sách đường link fshare


## 4-Truy cập vào `C:\Users\<tên user>\AppData\Local\Fshare` và lấy file xml có thê history.dl.xxxxx (lưu ý có 1 file nữa tên history.ul.xxxx, không lấy về)

## 5- Copy file đó vào thư mục đã download, đổi tên file đó thành AB
## 6- Tiến hành chạy file python Fshare_make_dwl_list.py sẽ tạo ra 1 file csv với tên là fshare_download_list.csv
## 7- Tiến hành chạy file Syn_Download_Fshare_1.1.py để tiến hành gửi lệnh lên DSM thực hiện download và kiểm tra quá trình
# Lưu ý 
 [x] Cài các dependencies cần thiết ở python gồm:
 
 1. `pip3 install synology-api`

