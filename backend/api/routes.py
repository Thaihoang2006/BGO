from flask import Blueprint, request, jsonify
from backend.config import Config
from backend.services.room_service import RoomService
from backend.extensions import socketio

api_bp = Blueprint("api", __name__, url_prefix="/api")

RULES_DATA = {
    "caro": {
        "title": "Luật Chơi Cờ Caro (Gomoku Freestyle)",
        "objective": "Là người chơi đầu tiên xếp được đúng hoặc hơn 5 quân cờ liên tiếp theo hàng ngang, hàng dọc hoặc đường chéo trên bàn cờ 15x15.",
        "players": "2 người chơi (Quân X và Quân O).",
        "setup": [
            "Bàn cờ có kích thước chuẩn 15x15 ô vuông.",
            "Người chơi 1 cầm quân X (Sunset Orange) và đi trước.",
            "Người chơi 2 cầm quân O (Cream) và đi sau."
        ],
        "gameplay": [
            "Hai người chơi lần lượt đặt 1 quân cờ vào một giao điểm/ô trống trên bàn cờ.",
            "Mỗi ô chỉ được đặt một lần, sau khi đặt quân sẽ không được di chuyển hoặc gỡ bỏ.",
            "Người chơi không được bỏ lượt trừ khi không còn ô trống hợp lệ."
        ],
        "win_conditions": [
            "Chiến thắng: Người chơi đầu tiên tạo thành một hàng liên tục gồm ít nhất 5 quân cờ cùng màu theo một trong 4 hướng (ngang, dọc, chéo chính \\, chéo phụ /).",
            "Hòa cờ: Khi toàn bộ 225 ô trên bàn cờ đã được lấp đầy mà không có người chơi nào tạo được chuỗi 5 quân liên tiếp.",
            "Luật áp dụng: Gomoku Freestyle tiêu chuẩn (không giới hạn nước chặn 2 đầu, không cấm nước đi)."
        ],
        "tips": [
            "Hãy chủ động tạo thế cờ đôi (tấn công 2 hướng cùng lúc như chữ V hoặc chữ L) để đối thủ không thể chặn cả hai.",
            "Luôn để ý nước cờ của đối thủ khi họ có chuỗi 3 hoặc 4 quân liên tiếp."
        ]
    },
    "ludo": {
        "title": "Luật Chơi Cờ Cá Ngựa (Ludo)",
        "objective": "Đưa toàn bộ 4 quân ngựa của mình đi hết 1 vòng bàn cờ và về đích an toàn đầu tiên.",
        "players": "2 đến 4 người chơi (tương ứng 4 màu sắc).",
        "setup": [
            "Mỗi người chơi có 4 quân ngựa xuất phát trong chuồng màu tương ứng.",
            "Một xúc xắc 6 mặt (1-6)."
        ],
        "gameplay": [
            "Người chơi lần lượt tung xúc xắc theo chiều kim đồng hồ.",
            "Để xuất quân khỏi chuồng ra ô xuất phát, người chơi cần tung được nút 6.",
            "Sau khi đã có quân trên đường đua, di chuyển quân theo số nút tung được.",
            "Tung được 6 sẽ được quyền tung tiếp một lượt bổ sung.",
            "Nếu quân đi tới ô đang có quân đối phương (không phải ô an toàn), quân đối phương bị đá về chuồng."
        ],
        "win_conditions": [
            "Người chơi đầu tiên đưa đủ 4 quân về các ô đích (chuồng đích) theo đúng thứ tự 1-2-3-4 sẽ giành chiến thắng tuyệt đối."
        ],
        "tips": [
            "Tận dụng lượt tung 6 để vừa xuất quân mới vừa tạo lợi thế ép sân.",
            "Tránh dừng quân ở các ô nguy hiểm nằm ngay trong tầm ngắm xúc xắc của đối thủ."
        ]
    },
    "gem_kingdom": {
        "title": "Luật Chơi Gem Kingdom (Splendor Board Game Chuẩn)",
        "objective": "Trở thành thương gia đá quý danh giá nhất với việc tích lũy tối thiểu 15 điểm uy tín (Prestige Points) để kích hoạt vòng chung kết và giành chiến thắng chung cuộc.",
        "players": "2 đến 4 người chơi.",
        "setup": [
            "35 Token đá quý chia làm 5 loại màu cơ bản (mỗi loại 7 viên cho 4 người, 5 viên cho 3 người, 4 viên cho 2 người): Ngọc lục bảo (Emerald - Xanh lá), Kim cương (Diamond - Trắng), Sapphire (Xanh dương), Mã não (Onyx - Đen), Ruby (Đỏ).",
            "5 Token Vàng (Gold / Wild) dùng để thay thế cho bất kỳ loại đá quý nào khi mua thẻ.",
            "90 Thẻ tinh luyện (Development Cards) chia làm 3 cấp độ: Cấp 1 (40 thẻ), Cấp 2 (30 thẻ), Cấp 3 (20 thẻ). Mỗi cấp độ được lật ngửa 4 thẻ trên bàn chơi (tổng cộng 12 thẻ mở).",
            "10 Thẻ Quý tộc (Nobles), xáo trộn và lật mở số lượng bằng Số người chơi + 1 (2 người lật 3 thẻ; 3 người lật 4 thẻ; 4 người lật 5 thẻ). Mỗi quý tộc mặc định thưởng 3 điểm uy tín."
        ],
        "gameplay": [
            "Người chơi lần lượt hành động theo chiều kim đồng hồ. Mỗi lượt chơi, bạn CHỈ ĐƯỢC CHỌN ĐÚNG 1 TRONG 4 HÀNH ĐỘNG:",
            "1. Lấy 3 token đá quý KHÁC màu nhau từ kho chung (không lấy token Vàng).",
            "2. Lấy 2 token đá quý CÙNG màu nhau (Chỉ được phép khi kho chung còn ít nhất 4 viên màu đó trước khi lấy).",
            "3. Dự trữ (Reserve) 1 lá bài tinh luyện và nhận 1 token Vàng (Gold): Có thể dự trữ thẻ đang mở trên bàn hoặc rút thẻ bí mật từ đỉnh chồng bài. Tối đa chỉ được cầm 3 thẻ dự trữ trên tay.",
            "4. Mua 1 lá bài tinh luyện: Có thể mua thẻ trên bàn hoặc thẻ đang dự trữ trên tay. Chi phí thực tế = (Chi phí trên thẻ) - (Số đá quý vĩnh viễn/bonus từ các thẻ đã mua trước đó). Thiếu màu nào có thể bù bằng token Vàng!",
            "Quy tắc Token (Tối đa 10 viên): Cuối lượt, người chơi không được giữ quá 10 token. Nếu vượt quá, phải chọn trả bớt token dư về kho chung."
        ],
        "win_conditions": [
            "Quý tộc viếng thăm: Cuối lượt, nếu người chơi tích lũy đủ số thẻ tinh luyện (bonus) mà quý tộc yêu cầu, quý tộc sẽ tự động ghé thăm và cộng ngay 3 điểm uy tín.",
            "Kích hoạt vòng cuối: Khi có người đạt từ 15 điểm uy tín trở lên, vòng chơi hiện tại sẽ tiếp tục cho đến người chơi cuối cùng (để đảm bảo số lượt đi hoàn toàn công bằng).",
            "Phân định thắng cuộc: Người có tổng điểm uy tín cao nhất sẽ chiến thắng.",
            "Quy tắc hòa (Tie-breaker): Nếu bằng điểm, người chơi nào MUA ÍT THẺ TINH LUYỆN HƠN sẽ giành chiến thắng tuyệt đối!"
        ],
        "tips": [
            "Tập trung mua các thẻ Cấp 1 giá rẻ ở đầu trận để tích lũy giảm giá (bonus), từ đó mua các thẻ Cấp 2 và Cấp 3 hoàn toàn miễn phí mà không cần tiêu tốn token.",
            "Quan sát yêu cầu của các Quý tộc đang mở để định hướng gom màu thẻ phù hợp và ẵm trọn 3 điểm thưởng quý giá.",
            "Dự trữ thẻ khôn ngoan vừa giúp bạn nhận token Vàng linh hoạt, vừa chặn đường đối thủ khi họ đang chuẩn bị gom đủ tài nguyên mua lá bài đó."
        ]
    },
    "property_tycoon": {
        "title": "Luật Chơi Property Tycoon (Cờ Tỷ Phú)",
        "objective": "Đầu tư kinh doanh, mua bán bất động sản khôn ngoan và làm phá sản các đối thủ trên bàn cờ.",
        "players": "2 đến 4 người chơi.",
        "setup": [
            "Bàn cờ vuông gồm 40 ô: các khu đất phố, bến xe, nhà máy, ô cơ hội/khí vận, ô thuế, nhà tù và ô Bắt đầu (START).",
            "Mỗi người chơi nhận một số vốn khởi điểm như nhau (ví dụ: $1,500)."
        ],
        "gameplay": [
            "Người chơi lần lượt tung 2 xúc xắc và di chuyển theo tổng số nút.",
            "Đi qua hoặc dừng ở ô START được nhận thưởng lương vòng đua ($200).",
            "Đến ô đất chưa có chủ: Có quyền mua theo giá niêm yết, hoặc đem ra đấu giá nếu từ chối mua.",
            "Đến ô đất của đối thủ: Phải trả phí thuê đất tương ứng cấp độ công trình trên đó.",
            "Sở hữu trọn bộ màu phố: Cho phép xây nhà và khách sạn để tăng vọt phí thu tiền thuê.",
            "Rơi vào ô Nhà tù: Phải nộp phạt, tung xúc xắc đôi hoặc dùng thẻ ra tù để thoát."
        ],
        "win_conditions": [
            "Người chơi cuối cùng còn trụ lại và không bị phá sản sẽ chiến thắng.",
            "Ở chế độ giới hạn thời gian/lượt: Người chơi có tổng giá trị tài sản ròng (tiền mặt + giá trị nhà đất) lớn nhất sẽ thắng."
        ],
        "tips": [
            "Nhanh chóng thâu tóm trọn bộ một cụm màu đất để xây nhà sớm, chặn đứng dòng tiền của người khác."
        ]
    }
}

@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "app": "BGO - Board Games Online", "version": "1.0.0"})

RULES_DATA["monopoly"] = RULES_DATA["property_tycoon"]
RULES_DATA["undercover"] = {
    "title": "Luật Chơi Undercover (Ai Là Gián Điệp?)",
    "objective": "Dân thường suy luận để loại bỏ toàn bộ Gián điệp; Mũ Đen hòa nhập để sống sót áp đảo; Mũ Trắng suy đoán từ khóa Dân thường để lật ngược tình thế.",
    "players": "3 đến 20 người chơi chính thức (Hỗ trợ khán giả theo dõi).",
    "setup": [
        "3 vai trò bí mật: Dân thường (nhận từ khóa A), Mũ Đen (nhận từ khóa B có ý nghĩa tương đồng), Mũ Trắng (không nhận từ khóa).",
        "Chủ phòng có thể tùy chỉnh: số lượng Mũ Đen, Mũ Trắng, thời gian mô tả & bỏ phiếu, và chủ đề từ vựng."
    ],
    "gameplay": [
        "Giai đoạn 1 - Xem bí mật: Mỗi người chơi xem từ khóa bí mật của riêng mình và xác nhận.",
        "Giai đoạn 2 - Mô tả: Hệ thống sắp xếp thứ tự ngẫu nhiên. Từng người chơi lần lượt nhập 1 câu mô tả về từ khóa của mình (không được nhắc trực tiếp từ khóa).",
        "Giai đoạn 3 - Thảo luận: Toàn bộ mô tả trong vòng được công khai để mọi người thảo luận, suy đoán ai có biểu hiện bất thường.",
        "Giai đoạn 4 - Bỏ phiếu: Mỗi người còn sống bỏ phiếu bí mật chọn 1 người đáng nghi. Người nhận nhiều phiếu nhất sẽ bị loại. Nếu hòa phiếu, sẽ tổ chức bỏ phiếu lại giữa những người hòa.",
        "Giai đoạn 5 - Mũ Trắng đoán từ: Nếu Mũ Trắng bị loại, họ có DUY NHẤT 1 cơ hội đoán từ khóa của Dân thường. Nếu đoán đúng, Mũ Trắng THẮNG NGAY LẬP TỨC!"
    ],
    "win_conditions": [
        "Dân thường thắng: Khi tất cả Mũ Đen và Mũ Trắng đều bị loại và không có Mũ Trắng nào đoán đúng từ khóa.",
        "Phe Gián điệp thắng: Khi số Dân thường còn sống không nhiều hơn tổng số Mũ Đen và Mũ Trắng còn sống.",
        "Mũ Trắng thắng riêng: Khi Mũ Trắng đoán chính xác từ khóa Dân thường lúc bị bỏ phiếu loại."
    ],
    "tips": [
        "Dân thường nên mô tả khéo léo để đồng đội nhận ra nhưng tránh quá cụ thể kẻo Mũ Trắng đoán được từ.",
        "Mũ Đen cần chú ý sự khác biệt nhỏ trong câu mô tả của người khác để nhận ra mình là Mũ Đen.",
        "Mũ Trắng cần lắng nghe kỹ các mô tả đi trước để hòa nhập và tìm cơ hội đoán đúng từ khóa."
    ]
}

@api_bp.route("/games", methods=["GET"])
def list_games():
    return jsonify({"games": list(Config.GAMES.values())})

@api_bp.route("/games/<game_type>/rules", methods=["GET"])
def get_rules(game_type):
    rules = RULES_DATA.get(game_type)
    if not rules:
        return jsonify({"error": f"Không tìm thấy luật cho game '{game_type}'"}), 404
    return jsonify({"game_type": game_type, "rules": rules})

@api_bp.route("/rooms", methods=["POST"])
def create_room():
    data = request.get_json() or {}
    game_type = data.get("game_type", "caro")
    player_name = data.get("player_name", "Player 1")
    is_local = bool(data.get("is_local", False))
    local_players = data.get("local_players")
    settings = data.get("settings")
    custom_max_players = data.get("max_players")

    try:
        room, player, token = RoomService.create_room(
            game_type=game_type,
            host_name=player_name,
            is_local=is_local,
            local_players=local_players,
            settings=settings,
            custom_max_players=custom_max_players
        )
        return jsonify({
            "success": True,
            "room_code": room.code,
            "participant_token": token,
            "player_index": player.player_index,
            "room": room.to_dict(viewer_token=token)
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@api_bp.route("/rooms/<room_code>/join", methods=["POST"])
def join_room(room_code):
    data = request.get_json() or {}
    player_name = data.get("player_name", "Player")
    role = data.get("role", "player")

    try:
        room, player, token = RoomService.join_room(room_code, player_name, role=role)
        # Notify room via socketio
        socketio.emit("room_sync", room.to_dict(), to=room.code)
        return jsonify({
            "success": True,
            "room_code": room.code,
            "participant_token": token,
            "player_index": player.player_index,
            "is_spectator": getattr(player, "is_spectator", False),
            "room": room.to_dict(viewer_token=token)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@api_bp.route("/rooms/<room_code>/action", methods=["POST"])
def post_game_action(room_code):
    data = request.get_json() or {}
    token = request.headers.get("X-Participant-Token") or data.get("participant_token")
    action = data.get("action", {})
    client_version = data.get("client_version")
    if not token:
        return jsonify({"success": False, "error": "Thiếu participant_token"}), 401
    try:
        room, event_data = RoomService.process_action(room_code, token, action, client_version)
        socketio.emit("game_update", {
            "room_code": room.code,
            "state_version": room.state_version,
            "game_state": room.game_state,
            "event": event_data,
            "status": room.status,
            "winner": room.winner,
            "session_scores": room.session_scores,
            "room": room.to_dict()
        }, to=room.code)
        return jsonify({
            "success": True,
            "room": room.to_dict(viewer_token=token),
            "state_version": room.state_version,
            "event": event_data
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@api_bp.route("/rooms/<room_code>/restart", methods=["POST"])
def restart_game_api(room_code):
    data = request.get_json() or {}
    token = request.headers.get("X-Participant-Token") or data.get("participant_token")
    if not token:
        return jsonify({"success": False, "error": "Thiếu participant_token"}), 401
    try:
        room = RoomService.restart_game(room_code, token)
        socketio.emit("game_restarted", {
            "room_code": room.code,
            "state_version": room.state_version,
            "game_state": room.game_state,
            "status": room.status,
            "session_scores": room.session_scores,
            "room": room.to_dict()
        }, to=room.code)
        return jsonify({
            "success": True,
            "room": room.to_dict(viewer_token=token),
            "state_version": room.state_version,
            "session_scores": room.session_scores
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@api_bp.route("/rooms/<room_code>/settings", methods=["POST"])
def update_room_settings_api(room_code):
    data = request.get_json() or {}
    token = request.headers.get("X-Participant-Token") or data.get("participant_token")
    settings = data.get("settings", {})
    if not token:
        return jsonify({"success": False, "error": "Thiếu participant_token"}), 401
    try:
        room = RoomService.update_room_settings(room_code, token, settings)
        socketio.emit("room_sync", room.to_dict(), to=room.code)
        return jsonify({"success": True, "room": room.to_dict(viewer_token=token)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@api_bp.route("/words/categories", methods=["GET"])
def get_word_categories():
    from backend.games.undercover.words_data import CATEGORIES
    return jsonify({"categories": CATEGORIES})

@api_bp.route("/rooms/<room_code>", methods=["GET"])
def get_room(room_code):
    token = request.headers.get("X-Participant-Token") or request.args.get("token")
    room = RoomService.get_room_by_code(room_code)
    if not room:
        return jsonify({"error": "Không tìm thấy phòng"}), 404
    return jsonify({"room": room.to_dict(viewer_token=token)})

@api_bp.route("/rooms/<room_code>/ready", methods=["POST"])
def set_ready_api(room_code):
    data = request.get_json() or {}
    token = request.headers.get("X-Participant-Token") or data.get("participant_token")
    is_ready = bool(data.get("is_ready", True))
    if not token:
        return jsonify({"error": "Thiếu participant_token"}), 401
    try:
        player = RoomService.set_player_ready(room_code, token, is_ready)
        room = RoomService.get_room_by_code(room_code)
        socketio.emit("player_ready_changed", {
            "player_index": player.player_index,
            "is_ready": player.is_ready,
            "room": room.to_dict()
        }, to=room.code)
        return jsonify({"success": True, "room": room.to_dict(viewer_token=token)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@api_bp.route("/rooms/<room_code>/chat", methods=["GET"])
def get_room_chat_api(room_code):
    try:
        messages = RoomService.get_chat_messages(room_code)
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@api_bp.route("/rooms/<room_code>/chat", methods=["POST"])
def send_room_chat_api(room_code):
    data = request.get_json() or {}
    token = request.headers.get("X-Participant-Token") or data.get("participant_token")
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"success": False, "error": "Thiếu nội dung tin nhắn"}), 400

    try:
        msg_obj = RoomService.add_chat_message(room_code, token, message, msg_type="user")
        socketio.emit("new_chat_message", msg_obj, to=room_code.upper())
        return jsonify({"success": True, "message": msg_obj})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
