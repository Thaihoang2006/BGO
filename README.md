# BGO – Board Games Online 🎲🌅

Nền tảng Board Game trực tuyến đa người chơi trên trình duyệt web, không cần cài đặt.

---

## 🎨 1. Bảng Màu Thiết Kế (Sunset Palette)
Dự án áp dụng bộ màu hoàng hôn ấm áp và phong cách Glassmorphism:
- **Cream:** `#FFE1BA`
- **Sunset Orange:** `#FF9966`
- **Dusty Rose:** `#BE807D`
- **Mauve:** `#795463`
- **Dark Plum:** `#251620`

---

## 🏗️ 2. Kiến Trúc Hệ Thống

### Frontend
- **Công nghệ:** HTML5, CSS3 hiện đại, ES6 JavaScript Modules (Vanilla SPA, không cần build step, tương thích mọi trình duyệt).
- **Giao diện:** Responsive hoàn chỉnh cho máy tính và điện thoại, hiệu ứng kính mờ (glassmorphism), chuyển cảnh mượt.
- **Đồng bộ thời gian thực:** WebSocket (Socket.IO client) kết hợp REST API fallback.
- **Quản lý phiên:** Tự động lưu `participant_token` trong `sessionStorage` để hỗ trợ Reconnect khi tải lại trang hoặc mất mạng tạm thời.

### Backend
- **Công nghệ:** Python Flask + Flask-SocketIO.
- **Kiến trúc:** **Server-Authoritative** (Backend xác thực 100% nước đi, lượt chơi, điều kiện thắng thua; không tin tưởng dữ liệu từ client).
- **Kiểm soát phiên bản:** Trạng thái bàn chơi có `state_version` và `sequence_number` chống xung đột thao tác đồng thời.
- **Mã phòng duy nhất:** Sinh mã 6 ký tự như `BGO742`, `BGO4NK`.
- **Game Engine độc lập:** Đặt trong thư mục `backend/games/` theo từng trò chơi riêng biệt, dùng chung cho cả Local và Online.

### Database
- **Mặc định phát triển cục bộ:** SQLite (`bgo_dev.db`) giúp chạy ngay lập tức mà không xung đột với bất kỳ database nào khác.
- **Cấu hình MySQL:** Hỗ trợ database riêng `bgo_db` (PyMySQL). Chỉ cần cập nhật chuỗi kết nối trong file `.env`:
  ```ini
  DATABASE_URL=mysql+pymysql://root:password@localhost:3306/bgo_db
  ```
- **Cam kết an toàn:** Tuyệt đối không can thiệp hay sửa đổi bất kỳ file hoặc database nào của MyGarage.

---

## 🚀 3. Hướng Dẫn Khởi Chạy

### Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

### Khởi chạy máy chủ:
```bash
python run.py
```
Máy chủ BGO sẽ hoạt động tại:
- **Local:** [http://localhost:5500](http://localhost:5500)
- **Mạng LAN:** `http://<IP_máy_của_bạn>:5500`

---

## 🧪 4. Chạy Kiểm Thử (Tests)

### Chạy Unit Test Game Engine & Room Service:
```bash
python -m pytest tests/
```

### Chạy Live Server Integration Test (Kiểm thử 2 người chơi độc lập):
```bash
python tests/test_live_server.py
```

---

## 📊 5. Danh Sách Trò Chơi Hoàn Thành

| Trò chơi | Loại | Local Hotseat | Online Multiplayer | Khán giả (Spectator) | Trạng thái |
|---|---|:---:|:---:|:---:|:---:|
| **Cờ Caro (Gomoku 15x15)** | Đấu trí 2 người | ✅ Hoạt động | ✅ Hoạt động | ✅ Hỗ trợ | **HOÀN THÀNH** |
| **Cờ Cá Ngựa (Ludo)** | Đua ngựa 2-4 người | ✅ Hoạt động | ✅ Hoạt động | ✅ Hỗ trợ | **HOÀN THÀNH** |
| **Gem Kingdom (Splendor)** | Thu thập đá quý 2-4 người | ✅ Hoạt động | ✅ Hoạt động | ✅ Hỗ trợ | **HOÀN THÀNH** |
| **Property Tycoon (Cờ Tỷ Phú)** | Bất động sản 2-4 người | ✅ Hoạt động | ✅ Hoạt động | ✅ Hỗ trợ | **HOÀN THÀNH** |
| **Undercover (Ai Là Gián Điệp?)** | Suy luận 3-20 người | ✅ Hoạt động | ✅ Hoạt động | ✅ Hỗ trợ | **HOÀN THÀNH** |

---

## 🚢 6. Triển Khai Docker & Kubernetes (CKA 2026)

### 1. Đóng gói Docker & Đẩy Image:
```bash
docker build -t nthoang06/bgo:v2 .
docker push nthoang06/bgo:v2
```

### 2. Triển khai lên Kubernetes Cluster (1 Control Plane + 2 Workers):
```bash
kubectl apply -f k8s/bgo-k8s.yaml
```

### 3. Kiểm tra trạng thái Cluster & Pods:
```bash
kubectl get nodes -o wide
kubectl get all -n bgo
kubectl get pods -n bgo -o wide
```

### 4. Vận hành Cluster (Scale, Update, Rollback):
```bash
# Scale lên 4 replicas
kubectl scale deployment/bgo-app --replicas=4 -n bgo

# Cập nhật image phiên bản mới
kubectl set image deployment/bgo-app bgo=nthoang06/bgo:v2 -n bgo
kubectl rollout status deployment/bgo-app -n bgo

# Rollback về phiên bản trước
kubectl rollout undo deployment/bgo-app -n bgo
```
