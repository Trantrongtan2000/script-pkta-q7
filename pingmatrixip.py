import requests
import json
import time

# --- CẤU HÌNH ---
# Danh sách các địa chỉ IP cần cào dữ liệu
IP_ADDRESSES = [
    "10.30.12.42",
    "10.30.12.41",
    "10.30.12.36",
    "10.30.12.37"
]

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

# --- LOGIC XỬ LÝ DỮ LIỆU ---

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
        # Chỉ in 'Không hiển thị' nếu nó không phải là Middle Tray bị bỏ qua
        if tray_name in ["Upper Tray", "Lower Tray"]:
             print(f"▶️ {tray_name}: Không hiển thị.")

def get_printer_status_for_ip(ip_address):
    """Thực hiện cào dữ liệu với logic tự động hóa phiên và thử lại cho một IP cụ thể."""
    URL_BASE = f"http://{ip_address}"
    print(f"\n========================================================")
    print(f"🚀 Đang xử lý Thiết bị tại IP: {ip_address}")
    print(f"========================================================")
    
    with requests.Session() as session:
        session.headers.update(headers)
        response_get = None
        
        # BƯỚC 1: GET trang chủ để tạo Session ID, thử lại nếu lỗi 500
        for attempt in range(MAX_RETRIES):
            # --- ĐÃ LOẠI BỎ IN SỐ LẦN THỬ ---
            try:
                response_get = session.get(URL_BASE + '/', timeout=10)
                
                if response_get.status_code == 200:
                    # print("✅ GET thành công. Cookie SessionID mới đã được tạo.")
                    break
                
                elif response_get.status_code == 500:
                    # Nếu lỗi 500, chờ và thử lại, không in số lần thử
                    time.sleep(RETRY_DELAY)
                
                else:
                    print(f"❌ GET LỖI: Mã trạng thái {response_get.status_code}. Dừng thử lại.")
                    return
            
            except requests.exceptions.RequestException as e:
                # Nếu lỗi kết nối, chờ và thử lại
                time.sleep(RETRY_DELAY)
        
        if not response_get or response_get.status_code != 200:
            print("❌ Thiết lập phiên thất bại. Không thể truy cập. Bỏ qua IP này.")
            return

        # BƯỚC 2: Gửi POST API để lấy Dữ liệu
        
        try:
            response_post = session.post(
                URL_BASE + API_ENDPOINT, 
                data='{}', 
                timeout=10
            )
            
            if response_post.status_code == 200:
                data = response_post.json()
                
                if data.get('Return_Successful'):
                    print("✅ Lấy dữ liệu thành công.")
                    print("\n--- KẾT QUẢ TRẠNG THÁI ---")
                    
                    print_tray_data(data, "Upper Tray", "UpperTray_")
                    # Không in Middle Tray
                    print_tray_data(data, "Lower Tray", "LowerTray_")
                    
                else:
                    print(f"❌ Lỗi ứng dụng (JSON): {data.get('Return_Error_Message', 'Lỗi không xác định')}")
            else:
                print(f"❌ POST LỖI: Mã trạng thái {response_post.status_code}. Dừng.")
                
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"❌ Lỗi trong bước POST: {e}")

# --- CHẠY CHƯƠNG TRÌNH CHÍNH ---
if __name__ == "__main__":
    for ip in IP_ADDRESSES:
        get_printer_status_for_ip(ip)