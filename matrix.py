import requests
import json
import time
import os
import platform

# --- CẤU HÌNH ---
# Danh sách các địa chỉ IP và tên mô tả
IP_ADDRESSES = {
    "10.30.12.42": "(Gần VB30)",
    "10.30.12.41": "(Giữa 2 phòng MRI)",
    "10.30.12.36": "(Tầng 1)",
    "10.30.12.37": "(Tầng 2)"
}
API_ENDPOINT = "/Home/GetPrinterStatus"
MAX_RETRIES = 5  
RETRY_DELAY = 3  

# Headers đầy đủ để mô phỏng trình duyệt và yêu cầu AJAX
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Content-Type': 'application/json; charset=utf-8',
    'X-Requested-With': 'XMLHttpRequest',
}

# --- CHỨC NĂNG PING ---

def check_ping(ip_address):
    """
    Kiểm tra trạng thái ping của một địa chỉ IP.
    Trả về True nếu ping thành công, False nếu thất bại.
    """
    # -n 1 là cho Windows (chỉ gửi 1 gói tin)
    # -c 1 là cho Linux/macOS
    param = '-n 1' if platform.system().lower() == 'windows' else '-c 1'
    # Gửi lệnh và chuyển hướng đầu ra để giữ console sạch hơn
    command = f"ping {param} {ip_address} > nul 2>&1"
    
    # os.system trả về 0 nếu lệnh thành công
    return os.system(command) == 0

# --- LOGIC CÀO DỮ LIỆU ---

def print_tray_data(data, tray_name, data_prefix):
    """Hàm in dữ liệu khay (loại bỏ Middle Tray)."""
    if tray_name == "Middle Tray":
        return

    if data.get(f'{data_prefix}Visible_Value'):
        print(f"▶️ {tray_name}:")
        print(f"  Loại Phim: {data.get(f'{data_prefix}FilmType_Value', 'N/A').strip()}")
        print(f"  Số Lượng: {data.get(f'{data_prefix}FilmCount_Value', 'N/A').strip()}")
        print(f"  Trạng Thái: {data.get(f'{data_prefix}FilmStatus_Value', 'N/A').strip()}")
    else:
        if tray_name in ["Upper Tray", "Lower Tray"]:
             print(f"▶️ {tray_name}: Không hiển thị.")

def get_printer_status_for_ip(ip_address):
    """Thực hiện cào dữ liệu với logic tự động hóa phiên và thử lại."""
    URL_BASE = f"http://{ip_address}"
    print(f"\n--- Bắt đầu cào dữ liệu ---")
    
    with requests.Session() as session:
        session.headers.update(headers)
        response_get = None
        
        # BƯỚC 1: GET trang chủ để tạo Session ID, thử lại nếu lỗi 500
        for attempt in range(MAX_RETRIES):
            try:
                response_get = session.get(URL_BASE + '/', timeout=10)
                if response_get.status_code == 200:
                    break
                elif response_get.status_code == 500:
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"❌ GET LỖI: Mã trạng thái {response_get.status_code}. Bỏ qua IP này.")
                    return
            except requests.exceptions.RequestException:
                time.sleep(RETRY_DELAY)
        
        if not response_get or response_get.status_code != 200:
            print("❌ Thiết lập phiên thất bại. Không thể truy cập API.")
            return

        # BƯỚC 2: Gửi POST API để lấy Dữ liệu
        try:
            response_post = session.post(URL_BASE + API_ENDPOINT, data='{}', timeout=10)
            
            if response_post.status_code == 200:
                data = response_post.json()
                if data.get('Return_Successful'):
                    print("\n--- KẾT QUẢ TRẠNG THÁI ---")
                    print_tray_data(data, "Upper Tray", "UpperTray_")
                    print_tray_data(data, "Lower Tray", "LowerTray_")
                else:
                    print(f"❌ Lỗi ứng dụng (JSON): {data.get('Return_Error_Message', 'Lỗi không xác định')}")
            else:
                print(f"❌ POST LỖI: Mã trạng thái {response_post.status_code}. Dừng.")
                
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"❌ Lỗi trong bước POST: {e}")

# --- CHƯƠNG TRÌNH CHÍNH VỚI MENU ---

def main_menu():
    """Hiển thị menu và xử lý lựa chọn của người dùng."""
    ip_list = list(IP_ADDRESSES.keys()) # Lấy danh sách IP theo thứ tự

    while True:
        print("\n========================================================")
        print("          MENU KIỂM TRA TRẠNG THÁI MÁY IN")
        print("========================================================")
        
        # In danh sách IP kèm tên mô tả
        for i, ip in enumerate(ip_list):
            description = IP_ADDRESSES[ip]
            print(f"[{i + 1}] {ip} {description}")
            
        print("[P] Kiểm tra PING tất cả")
        print("[A] Cào DỮ LIỆU tất cả")
        print("[Q] Thoát")
        print("--------------------------------------------------------")
        
        choice = input("Vui lòng chọn IP (số) hoặc chức năng (P/A/Q): ").upper().strip()

        if choice == 'Q':
            print("Đã thoát chương trình.")
            break
        
        elif choice == 'P':
            print("\n--- KẾT QUẢ PING TẤT CẢ ---")
            for ip in ip_list:
                description = IP_ADDRESSES[ip]
                status = "✅ ONLINE" if check_ping(ip) else "❌ OFFLINE"
                print(f"{ip} {description}: {status}")

        elif choice == 'A':
            print("\n--- BẮT ĐẦU CÀO DỮ LIỆU TẤT CẢ ---")
            for ip in ip_list:
                description = IP_ADDRESSES[ip]
                print(f"\n🚀 XỬ LÝ IP: {ip} {description}")
                get_printer_status_for_ip(ip)

        elif choice.isdigit() and 1 <= int(choice) <= len(ip_list):
            selected_ip = ip_list[int(choice) - 1]
            description = IP_ADDRESSES[selected_ip]
            print(f"\n--- XỬ LÝ IP ĐÃ CHỌN: {selected_ip} {description} ---")
            
            # Hỏi người dùng muốn làm gì với IP đã chọn
            action = input("Chọn hành động: [P]ing / [C]ào Dữ liệu: ").upper().strip()
            
            if action == 'P':
                status = "✅ ONLINE" if check_ping(selected_ip) else "❌ OFFLINE"
                print(f"{selected_ip} {description}: {status}")
            elif action == 'C':
                get_printer_status_for_ip(selected_ip)
            else:
                print("Lựa chọn hành động không hợp lệ.")

        else:
            print("Lựa chọn không hợp lệ. Vui lòng thử lại.")

if __name__ == "__main__":
    main_menu()