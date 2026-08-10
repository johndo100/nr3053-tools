# unlock-nr3053

Công cụ host-side để mở quyền SSH/Telnet trên router **Viettel SDMC NR3053** bằng cách xử lý bản sao lưu cấu hình. Chỉ dùng với thiết bị bạn sở hữu hoặc được ủy quyền quản trị.

## Yêu cầu

- Python 3
- Router NR3053 ở mạng LAN mặc định

## Cách dùng

```bash
git clone https://github.com/quytttb/unlock-nr3053.git
cd unlock-nr3053
python3 -m pip install -r requirements.txt
python3 unlock_nr3053.py --password SERIAL_NUMBER
```

Nếu router không trả được backup qua API, tải `config.bin` từ giao diện web rồi chỉ rõ đường dẫn:

```bash
python3 unlock_nr3053.py --password SERIAL_NUMBER --config-input /path/to/config.bin
```

Không commit file backup cấu hình hoặc thông tin định danh router vào repository. Đọc output của công cụ và sao lưu cấu hình trước khi chạy.
