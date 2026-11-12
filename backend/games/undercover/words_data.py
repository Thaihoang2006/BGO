"""Undercover Word Bank (Kho từ vựng tiếng Việt cho Undercover).
Contains 110+ carefully paired words across 7 categories.
Each pair shares common characteristics yet allows differentiation.
"""

import random
from typing import Dict, List, Optional, Tuple

WORD_PAIRS = [
    # 1. Đồ ăn & Thức uống (Food & Drinks) - 18 pairs
    {"id": 1, "category": "food", "word_civilian": "Cà phê", "word_undercover": "Trà"},
    {"id": 2, "category": "food", "word_civilian": "Bánh mì", "word_undercover": "Hamburger"},
    {"id": 3, "category": "food", "word_civilian": "Phở", "word_undercover": "Bún bò"},
    {"id": 4, "category": "food", "word_civilian": "Kem", "word_undercover": "Sữa chua"},
    {"id": 5, "category": "food", "word_civilian": "Nước cam", "word_undercover": "Nước chanh"},
    {"id": 6, "category": "food", "word_civilian": "Bánh quy", "word_undercover": "Bánh bông lan"},
    {"id": 7, "category": "food", "word_civilian": "Pizza", "word_undercover": "Bánh xèo"},
    {"id": 8, "category": "food", "word_civilian": "Bia", "word_undercover": "Rượu vang"},
    {"id": 9, "category": "food", "word_civilian": "Lẩu", "word_undercover": "Nướng"},
    {"id": 10, "category": "food", "word_civilian": "Socola", "word_undercover": "Kẹo ngọt"},
    {"id": 11, "category": "food", "word_civilian": "Táo", "word_undercover": "Lê"},
    {"id": 12, "category": "food", "word_civilian": "Xoài", "word_undercover": "Đu đủ"},
    {"id": 13, "category": "food", "word_civilian": "Dưa hấu", "word_undercover": "Dưa gang"},
    {"id": 14, "category": "food", "word_civilian": "Gà rán", "word_undercover": "Vịt quay"},
    {"id": 15, "category": "food", "word_civilian": "Chè", "word_undercover": "Trà sữa"},
    {"id": 16, "category": "food", "word_civilian": "Xôi xéo", "word_undercover": "Cơm tấm"},
    {"id": 17, "category": "food", "word_civilian": "Bánh bao", "word_undercover": "Há cảo"},
    {"id": 18, "category": "food", "word_civilian": "Mì tôm", "word_undercover": "Hủ tiếu"},

    # 2. Động vật (Animals) - 18 pairs
    {"id": 19, "category": "animals", "word_civilian": "Mèo", "word_undercover": "Chó"},
    {"id": 20, "category": "animals", "word_civilian": "Hổ", "word_undercover": "Sư tử"},
    {"id": 21, "category": "animals", "word_civilian": "Cá voi", "word_undercover": "Cá heo"},
    {"id": 22, "category": "animals", "word_civilian": "Đại bàng", "word_undercover": "Chim ưng"},
    {"id": 23, "category": "animals", "word_civilian": "Khỉ", "word_undercover": "Tinh tinh"},
    {"id": 24, "category": "animals", "word_civilian": "Ngựa", "word_undercover": "Lừa"},
    {"id": 25, "category": "animals", "word_civilian": "Bồ câu", "word_undercover": "Vẹt"},
    {"id": 26, "category": "animals", "word_civilian": "Rắn", "word_undercover": "Trăn"},
    {"id": 27, "category": "animals", "word_civilian": "Cá sấu", "word_undercover": "Thằn lằn"},
    {"id": 28, "category": "animals", "word_civilian": "Vịt", "word_undercover": "Thiên nga"},
    {"id": 29, "category": "animals", "word_civilian": "Chuột", "word_undercover": "Sóc"},
    {"id": 30, "category": "animals", "word_civilian": "Gấu trúc", "word_undercover": "Gấu bắc cực"},
    {"id": 31, "category": "animals", "word_civilian": "Sói", "word_undercover": "Cáo"},
    {"id": 32, "category": "animals", "word_civilian": "Ong", "word_undercover": "Bướm"},
    {"id": 33, "category": "animals", "word_civilian": "Rùa", "word_undercover": "Ba ba"},
    {"id": 34, "category": "animals", "word_civilian": "Cừu", "word_undercover": "Dê"},
    {"id": 35, "category": "animals", "word_civilian": "Lạc đà", "word_undercover": "Hươu cao cổ"},
    {"id": 36, "category": "animals", "word_civilian": "Ếch", "word_undercover": "Cóc"},

    # 3. Phương tiện giao thông (Vehicles) - 18 pairs
    {"id": 37, "category": "vehicles", "word_civilian": "Máy bay", "word_undercover": "Trực thăng"},
    {"id": 38, "category": "vehicles", "word_civilian": "Xe máy", "word_undercover": "Xe đạp"},
    {"id": 39, "category": "vehicles", "word_civilian": "Xe buýt", "word_undercover": "Tàu hỏa"},
    {"id": 40, "category": "vehicles", "word_civilian": "Tàu ngầm", "word_undercover": "Du thuyền"},
    {"id": 41, "category": "vehicles", "word_civilian": "Xe taxi", "word_undercover": "Xe ôm công nghệ"},
    {"id": 42, "category": "vehicles", "word_civilian": "Xe bán tải", "word_undercover": "Xe tải thùng"},
    {"id": 43, "category": "vehicles", "word_civilian": "Tàu thủy", "word_undercover": "Ca nô"},
    {"id": 44, "category": "vehicles", "word_civilian": "Xe lăn", "word_undercover": "Xe đẩy em bé"},
    {"id": 45, "category": "vehicles", "word_civilian": "Xe điện", "word_undercover": "Xe xăng"},
    {"id": 46, "category": "vehicles", "word_civilian": "Khinh khí cầu", "word_undercover": "Dù lượn"},
    {"id": 47, "category": "vehicles", "word_civilian": "Xe cứu thương", "word_undercover": "Xe cứu hỏa"},
    {"id": 48, "category": "vehicles", "word_civilian": "Thuyền buồm", "word_undercover": "Bè tre"},
    {"id": 49, "category": "vehicles", "word_civilian": "Tàu điện ngầm", "word_undercover": "Tàu trên cao"},
    {"id": 50, "category": "vehicles", "word_civilian": "Ván trượt", "word_undercover": "Patin"},
    {"id": 51, "category": "vehicles", "word_civilian": "Tên lửa", "word_undercover": "Vệ tinh nhân tạo"},
    {"id": 52, "category": "vehicles", "word_civilian": "Xe cẩu", "word_undercover": "Xe ủi"},
    {"id": 53, "category": "vehicles", "word_civilian": "Thuyền kayak", "word_undercover": "Thuyền rồng"},
    {"id": 54, "category": "vehicles", "word_civilian": "Cáp treo", "word_undercover": "Thang cuốn"},

    # 4. Công nghệ & Thiết bị (Technology) - 18 pairs
    {"id": 55, "category": "technology", "word_civilian": "Laptop", "word_undercover": "Máy tính bảng"},
    {"id": 56, "category": "technology", "word_civilian": "Bàn phím", "word_undercover": "Chuột máy tính"},
    {"id": 57, "category": "technology", "word_civilian": "Tai nghe có dây", "word_undercover": "Tai nghe bluetooth"},
    {"id": 58, "category": "technology", "word_civilian": "Tivi", "word_undercover": "Máy chiếu"},
    {"id": 59, "category": "technology", "word_civilian": "Loa bluetooth", "word_undercover": "Đài radio"},
    {"id": 60, "category": "technology", "word_civilian": "Điện thoại", "word_undercover": "Máy ảnh cơ"},
    {"id": 61, "category": "technology", "word_civilian": "Đồng hồ thông minh", "word_undercover": "Vòng tay sức khỏe"},
    {"id": 62, "category": "technology", "word_civilian": "USB", "word_undercover": "Ổ cứng di động"},
    {"id": 63, "category": "technology", "word_civilian": "Máy in", "word_undercover": "Máy photocopy"},
    {"id": 64, "category": "technology", "word_civilian": "Sạc dự phòng", "word_undercover": "Củ sạc tường"},
    {"id": 65, "category": "technology", "word_civilian": "Kính VR", "word_undercover": "Kính xem phim 3D"},
    {"id": 66, "category": "technology", "word_civilian": "Robot hút bụi", "word_undercover": "Máy hút bụi cầm tay"},
    {"id": 67, "category": "technology", "word_civilian": "Màn hình cong", "word_undercover": "Màn hình phẳng"},
    {"id": 68, "category": "technology", "word_civilian": "Cáp HDMI", "word_undercover": "Cáp Type-C"},
    {"id": 69, "category": "technology", "word_civilian": "Wifi", "word_undercover": "Mạng 4G"},
    {"id": 70, "category": "technology", "word_civilian": "Trí tuệ nhân tạo", "word_undercover": "Người máy"},
    {"id": 71, "category": "technology", "word_civilian": "Flycam", "word_undercover": "Máy bay mô hình"},
    {"id": 72, "category": "technology", "word_civilian": "Thẻ nhớ", "word_undercover": "Đĩa CD"},

    # 5. Địa điểm & Thiên nhiên (Places & Nature) - 18 pairs
    {"id": 73, "category": "places", "word_civilian": "Biển", "word_undercover": "Hồ nước"},
    {"id": 74, "category": "places", "word_civilian": "Rừng rậm", "word_undercover": "Công viên"},
    {"id": 75, "category": "places", "word_civilian": "Sa mạc", "word_undercover": "Đồi cát"},
    {"id": 76, "category": "places", "word_civilian": "Thác nước", "word_undercover": "Dòng suối"},
    {"id": 77, "category": "places", "word_civilian": "Đại học", "word_undercover": "Cao đẳng"},
    {"id": 78, "category": "places", "word_civilian": "Bệnh viện", "word_undercover": "Trạm y tế"},
    {"id": 79, "category": "places", "word_civilian": "Rạp chiếu phim", "word_undercover": "Nhà hát kịch"},
    {"id": 80, "category": "places", "word_civilian": "Siêu thị", "word_undercover": "Chợ truyền thống"},
    {"id": 81, "category": "places", "word_civilian": "Sân bay", "word_undercover": "Ga tàu hỏa"},
    {"id": 82, "category": "places", "word_civilian": "Khách sạn", "word_undercover": "Nhà nghỉ"},
    {"id": 83, "category": "places", "word_civilian": "Thư viện", "word_undercover": "Nhà sách"},
    {"id": 84, "category": "places", "word_civilian": "Sân vận động", "word_undercover": "Nhà thi đấu"},
    {"id": 85, "category": "places", "word_civilian": "Hòn đảo", "word_undercover": "Bán đảo"},
    {"id": 86, "category": "places", "word_civilian": "Ngọn núi", "word_undercover": "Ngọn đồi"},
    {"id": 87, "category": "places", "word_civilian": "Quán bar", "word_undercover": "Quán trà chanh"},
    {"id": 88, "category": "places", "word_civilian": "Bảo tàng", "word_undercover": "Phòng triển lãm tranh"},
    {"id": 89, "category": "places", "word_civilian": "Nhà tù", "word_undercover": "Trại cải tạo"},
    {"id": 90, "category": "places", "word_civilian": "Sở thú", "word_undercover": "Thủy cung"},

    # 6. Thể thao & Giải trí (Sports & Recreation) - 18 pairs
    {"id": 91, "category": "sports", "word_civilian": "Bóng đá", "word_undercover": "Bóng rổ"},
    {"id": 92, "category": "sports", "word_civilian": "Cầu lông", "word_undercover": "Quần vợt"},
    {"id": 93, "category": "sports", "word_civilian": "Bơi lội", "word_undercover": "Lặn biển"},
    {"id": 94, "category": "sports", "word_civilian": "Chạy bộ", "word_undercover": "Đi bộ nhanh"},
    {"id": 95, "category": "sports", "word_civilian": "Bóng chuyền", "word_undercover": "Bóng bầu dục"},
    {"id": 96, "category": "sports", "word_civilian": "Cờ vua", "word_undercover": "Cờ tướng"},
    {"id": 97, "category": "sports", "word_civilian": "Leo núi", "word_undercover": "Dã ngoại cắm trại"},
    {"id": 98, "category": "sports", "word_civilian": "Bida", "word_undercover": "Bowling"},
    {"id": 99, "category": "sports", "word_civilian": "Quyền anh", "word_undercover": "Võ cổ truyền"},
    {"id": 100, "category": "sports", "word_civilian": "Đua xe F1", "word_undercover": "Đua mô tô GP"},
    {"id": 101, "category": "sports", "word_civilian": "Trượt tuyết", "word_undercover": "Trượt băng nghệ thuật"},
    {"id": 102, "category": "sports", "word_civilian": "Bắn cung", "word_undercover": "Bắn súng trường"},
    {"id": 103, "category": "sports", "word_civilian": "Tập Gym", "word_undercover": "Yoga"},
    {"id": 104, "category": "sports", "word_civilian": "Bóng bàn", "word_undercover": "Cầu mây"},
    {"id": 105, "category": "sports", "word_civilian": "Nhảy dù", "word_undercover": "Bungee jumping"},
    {"id": 106, "category": "sports", "word_civilian": "Karate", "word_undercover": "Taekwondo"},
    {"id": 107, "category": "sports", "word_civilian": "Đấu kiếm", "word_undercover": "Kendo"},
    {"id": 108, "category": "sports", "word_civilian": "Chèo thuyền", "word_undercover": "Lướt ván"},

    # 7. Đời sống & Đồ gia dụng (Daily Life) - 18 pairs
    {"id": 109, "category": "daily_life", "word_civilian": "Bàn chải răng", "word_undercover": "Kem đánh răng"},
    {"id": 110, "category": "daily_life", "word_civilian": "Cái gương", "word_undercover": "Cái lược"},
    {"id": 111, "category": "daily_life", "word_civilian": "Áo mưa", "word_undercover": "Cây dù"},
    {"id": 112, "category": "daily_life", "word_civilian": "Giường ngủ", "word_undercover": "Ghế sofa"},
    {"id": 113, "category": "daily_life", "word_civilian": "Nồi cơm điện", "word_undercover": "Bếp từ"},
    {"id": 114, "category": "daily_life", "word_civilian": "Quạt máy", "word_undercover": "Máy điều hòa"},
    {"id": 115, "category": "daily_life", "word_civilian": "Đèn bàn", "word_undercover": "Đèn ngủ"},
    {"id": 116, "category": "daily_life", "word_civilian": "Kính cận", "word_undercover": "Kính râm"},
    {"id": 117, "category": "daily_life", "word_civilian": "Ví tiền", "word_undercover": "Balo"},
    {"id": 118, "category": "daily_life", "word_civilian": "Dầu gội", "word_undercover": "Sữa tắm"},
    {"id": 119, "category": "daily_life", "word_civilian": "Khăn tắm", "word_undercover": "Khăn mặt"},
    {"id": 120, "category": "daily_life", "word_civilian": "Bút bi", "word_undercover": "Bút chì"},
    {"id": 121, "category": "daily_life", "word_civilian": "Giày thể thao", "word_undercover": "Dép tổ ong"},
    {"id": 122, "category": "daily_life", "word_civilian": "Chảo rán", "word_undercover": "Nồi canh inox"},
    {"id": 123, "category": "daily_life", "word_civilian": "Cây chổi", "word_undercover": "Cây lau nhà"},
    {"id": 124, "category": "daily_life", "word_civilian": "Kéo cắt giấy", "word_undercover": "Dao rọc giấy"},
    {"id": 125, "category": "daily_life", "word_civilian": "Bình giữ nhiệt", "word_undercover": "Ấm siêu tốc"},
    {"id": 126, "category": "daily_life", "word_civilian": "Gối ôm", "word_undercover": "Chăn bông"},
]

CATEGORIES = {
    "all": "Tất cả chủ đề (Ngẫu nhiên)",
    "food": "Đồ ăn & Thức uống",
    "animals": "Động vật",
    "vehicles": "Phương tiện giao thông",
    "technology": "Công nghệ & Thiết bị",
    "places": "Địa điểm & Thiên nhiên",
    "sports": "Thể thao & Giải trí",
    "daily_life": "Đời sống & Vật dụng"
}

def get_word_pair(category: Optional[str] = None, exclude_ids: Optional[List[int]] = None) -> Tuple[str, str, Dict]:
    """Picks a random word pair matching category, avoiding recently used IDs."""
    candidates = WORD_PAIRS
    if category and category != "all" and category in CATEGORIES:
        candidates = [p for p in candidates if p["category"] == category]

    if exclude_ids:
        filtered = [p for p in candidates if p["id"] not in exclude_ids]
        if filtered:
            candidates = filtered

    selected = random.choice(candidates)

    # 50% chance to flip civilian and undercover word
    if random.random() < 0.5:
        return selected["word_civilian"], selected["word_undercover"], selected
    else:
        return selected["word_undercover"], selected["word_civilian"], selected
