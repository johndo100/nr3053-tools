# nr3053-tools

Công cụ chạy trên máy host cho router **Viettel SDMC NR3053**. Chỉ dùng với thiết bị bạn sở hữu hoặc được ủy quyền quản trị.

## Công cụ

| Công cụ | Mục đích |
| --- | --- |
| `unlock_nr3053.py` | Mở SSH/Telnet bằng cách xử lý bản sao lưu cấu hình rồi upload lại. |
| `factory/patch_factory_throughwall.py` | Patch một bản dump Factory 2 MiB với giá trị through-wall đã xác minh. Không kết nối hoặc ghi trực tiếp vào router. |

## Cài đặt

```bash
git clone https://github.com/quytttb/nr3053-tools.git
cd nr3053-tools
python3 -m pip install -r requirements.txt
```

## Unlock SSH/Telnet

```bash
python3 unlock_nr3053.py --password SERIAL_NUMBER
```

Nếu router không trả được backup qua API, tải `config.bin` từ giao diện web rồi chỉ rõ đường dẫn:

```bash
python3 unlock_nr3053.py --password SERIAL_NUMBER --config-input /path/to/config.bin
```

## Patch Factory through-wall

Input phải là bản dump `Factory` của **NR3053**, đúng 2 MiB. Giữ nguyên file gốc và checksum để có đường phục hồi. Script tạo file mới, chỉ thay đổi vùng calibration through-wall, in SHA-256 trước/sau và không cho ghi đè output nếu không có `--force`.

```bash
python3 factory/patch_factory_throughwall.py factory-original.bin
python3 factory/patch_factory_throughwall.py --check \
  factory-original.throughwall_mtd_Factory_0x0-0x200000.bin
```

Tên output mặc định có hậu tố `_mtd_Factory_0x0-0x200000.bin`, để Keenetic U-Boot Flash Editor nhận dạng chính xác toàn bộ `mtd:Factory`. Nếu dùng `--output`, tên cũng phải có hậu tố này. Việc ghi lại Factory qua U-Boot là thao tác riêng, có rủi ro brick: chỉ thực hiện sau khi đã có backup và phương án recovery UART.

## Dự án liên quan

- [U-Boot DHCPD cho NR3053 và 32X6](https://github.com/quytttb/bl-mt798x-dhcpd): build bootloader và Failsafe Web UI.
- ImmortalWrt/Keenetic là các firmware/port độc lập; repository này không đóng gói hay tự động flash chúng.

Không commit file backup cấu hình, Factory dump, MAC/serial, mật khẩu hoặc bất kỳ dữ liệu riêng tư nào của router.
