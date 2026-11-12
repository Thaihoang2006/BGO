# Definition of 90 Development Cards and 10 Noble Tiles for Gem Kingdom (Splendor mechanics)

GEMS = ["emerald", "diamond", "sapphire", "onyx", "ruby"]

NOBLES = [
    {"id": "n1", "name": "Bá Tước Sứ Giả", "points": 3, "requires": {"diamond": 3, "sapphire": 3, "emerald": 3}},
    {"id": "n2", "name": "Nữ Hoàng Tuyết", "points": 3, "requires": {"diamond": 4, "sapphire": 4}},
    {"id": "n3", "name": "Đại Hiệp Sĩ Rồng", "points": 3, "requires": {"ruby": 4, "onyx": 4}},
    {"id": "n4", "name": "Đại Pháp Sư Rừng", "points": 3, "requires": {"emerald": 4, "ruby": 4}},
    {"id": "n5", "name": "Chúa Tể Hắc Ám", "points": 3, "requires": {"onyx": 3, "ruby": 3, "diamond": 3}},
    {"id": "n6", "name": "Đô Đốc Biển Đông", "points": 3, "requires": {"sapphire": 4, "onyx": 4}},
    {"id": "n7", "name": "Thống Đốc Sa Mạc", "points": 3, "requires": {"emerald": 4, "diamond": 4}},
    {"id": "n8", "name": "Công Tước Kim Quang", "points": 3, "requires": {"diamond": 3, "sapphire": 3, "ruby": 3}},
    {"id": "n9", "name": "Hiền Triết Thung Lũng", "points": 3, "requires": {"sapphire": 3, "emerald": 3, "onyx": 3}},
    {"id": "n10", "name": "Nữ Bá Tước Hỏa Diệm", "points": 3, "requires": {"ruby": 3, "emerald": 3, "onyx": 3}}
]

# 40 Level 1 Development Cards
LEVEL_1_CARDS = [
    # Diamond bonus
    {"id": "c1_01", "level": 1, "gem": "diamond", "points": 0, "cost": {"sapphire": 1, "emerald": 1, "ruby": 1, "onyx": 1}},
    {"id": "c1_02", "level": 1, "gem": "diamond", "points": 0, "cost": {"sapphire": 1, "emerald": 2, "ruby": 1, "onyx": 1}},
    {"id": "c1_03", "level": 1, "gem": "diamond", "points": 0, "cost": {"sapphire": 2, "ruby": 2, "onyx": 1}},
    {"id": "c1_04", "level": 1, "gem": "diamond", "points": 0, "cost": {"diamond": 0, "sapphire": 3, "emerald": 0, "ruby": 0, "onyx": 0}},
    {"id": "c1_05", "level": 1, "gem": "diamond", "points": 0, "cost": {"diamond": 0, "sapphire": 0, "emerald": 2, "ruby": 2, "onyx": 0}},
    {"id": "c1_06", "level": 1, "gem": "diamond", "points": 0, "cost": {"diamond": 0, "sapphire": 0, "emerald": 1, "ruby": 3, "onyx": 1}},
    {"id": "c1_07", "level": 1, "gem": "diamond", "points": 0, "cost": {"diamond": 0, "sapphire": 2, "emerald": 0, "ruby": 2, "onyx": 1}},
    {"id": "c1_08", "level": 1, "gem": "diamond", "points": 1, "cost": {"sapphire": 0, "emerald": 0, "ruby": 0, "onyx": 4}},

    # Sapphire bonus
    {"id": "c1_09", "level": 1, "gem": "sapphire", "points": 0, "cost": {"diamond": 1, "emerald": 1, "ruby": 1, "onyx": 1}},
    {"id": "c1_10", "level": 1, "gem": "sapphire", "points": 0, "cost": {"diamond": 1, "emerald": 1, "ruby": 2, "onyx": 1}},
    {"id": "c1_11", "level": 1, "gem": "sapphire", "points": 0, "cost": {"diamond": 1, "emerald": 0, "ruby": 2, "onyx": 2}},
    {"id": "c1_12", "level": 1, "gem": "sapphire", "points": 0, "cost": {"diamond": 0, "emerald": 0, "ruby": 0, "onyx": 3}},
    {"id": "c1_13", "level": 1, "gem": "sapphire", "points": 0, "cost": {"diamond": 0, "emerald": 2, "ruby": 0, "onyx": 2}},
    {"id": "c1_14", "level": 1, "gem": "sapphire", "points": 0, "cost": {"diamond": 2, "emerald": 1, "ruby": 0, "onyx": 1}},
    {"id": "c1_15", "level": 1, "gem": "sapphire", "points": 0, "cost": {"diamond": 1, "emerald": 3, "ruby": 1, "onyx": 0}},
    {"id": "c1_16", "level": 1, "gem": "sapphire", "points": 1, "cost": {"ruby": 4}},

    # Emerald bonus
    {"id": "c1_17", "level": 1, "gem": "emerald", "points": 0, "cost": {"diamond": 1, "sapphire": 1, "ruby": 1, "onyx": 1}},
    {"id": "c1_18", "level": 1, "gem": "emerald", "points": 0, "cost": {"diamond": 1, "sapphire": 1, "ruby": 1, "onyx": 2}},
    {"id": "c1_19", "level": 1, "gem": "emerald", "points": 0, "cost": {"diamond": 0, "sapphire": 1, "ruby": 3, "onyx": 1}},
    {"id": "c1_20", "level": 1, "gem": "emerald", "points": 0, "cost": {"ruby": 3}},
    {"id": "c1_21", "level": 1, "gem": "emerald", "points": 0, "cost": {"diamond": 2, "sapphire": 0, "ruby": 2, "onyx": 0}},
    {"id": "c1_22", "level": 1, "gem": "emerald", "points": 0, "cost": {"diamond": 2, "sapphire": 2, "ruby": 0, "onyx": 1}},
    {"id": "c1_23", "level": 1, "gem": "emerald", "points": 0, "cost": {"diamond": 1, "sapphire": 2, "ruby": 1, "onyx": 1}},
    {"id": "c1_24", "level": 1, "gem": "emerald", "points": 1, "cost": {"onyx": 4}},

    # Ruby bonus
    {"id": "c1_25", "level": 1, "gem": "ruby", "points": 0, "cost": {"diamond": 1, "sapphire": 1, "emerald": 1, "onyx": 1}},
    {"id": "c1_26", "level": 1, "gem": "ruby", "points": 0, "cost": {"diamond": 2, "sapphire": 1, "emerald": 1, "onyx": 1}},
    {"id": "c1_27", "level": 1, "gem": "ruby", "points": 0, "cost": {"diamond": 2, "sapphire": 0, "emerald": 1, "onyx": 2}},
    {"id": "c1_28", "level": 1, "gem": "ruby", "points": 0, "cost": {"diamond": 3}},
    {"id": "c1_29", "level": 1, "gem": "ruby", "points": 0, "cost": {"sapphire": 2, "emerald": 2}},
    {"id": "c1_30", "level": 1, "gem": "ruby", "points": 0, "cost": {"diamond": 1, "sapphire": 1, "emerald": 0, "onyx": 3}},
    {"id": "c1_31", "level": 1, "gem": "ruby", "points": 0, "cost": {"diamond": 1, "sapphire": 2, "emerald": 2, "onyx": 0}},
    {"id": "c1_32", "level": 1, "gem": "ruby", "points": 1, "cost": {"diamond": 4}},

    # Onyx bonus
    {"id": "c1_33", "level": 1, "gem": "onyx", "points": 0, "cost": {"diamond": 1, "sapphire": 1, "emerald": 1, "ruby": 1}},
    {"id": "c1_34", "level": 1, "gem": "onyx", "points": 0, "cost": {"diamond": 1, "sapphire": 2, "emerald": 1, "ruby": 1}},
    {"id": "c1_35", "level": 1, "gem": "onyx", "points": 0, "cost": {"diamond": 2, "sapphire": 2, "emerald": 0, "ruby": 1}},
    {"id": "c1_36", "level": 1, "gem": "onyx", "points": 0, "cost": {"emerald": 3}},
    {"id": "c1_37", "level": 1, "gem": "onyx", "points": 0, "cost": {"diamond": 0, "sapphire": 2, "emerald": 0, "ruby": 2}},
    {"id": "c1_38", "level": 1, "gem": "onyx", "points": 0, "cost": {"diamond": 3, "sapphire": 1, "emerald": 1, "ruby": 0}},
    {"id": "c1_39", "level": 1, "gem": "onyx", "points": 0, "cost": {"diamond": 2, "sapphire": 0, "emerald": 2, "ruby": 1}},
    {"id": "c1_40", "level": 1, "gem": "onyx", "points": 1, "cost": {"emerald": 4}}
]

# 30 Level 2 Development Cards
LEVEL_2_CARDS = [
    # Diamond
    {"id": "c2_01", "level": 2, "gem": "diamond", "points": 1, "cost": {"emerald": 3, "ruby": 2, "onyx": 2}},
    {"id": "c2_02", "level": 2, "gem": "diamond", "points": 1, "cost": {"diamond": 2, "sapphire": 3, "onyx": 3}},
    {"id": "c2_03", "level": 2, "gem": "diamond", "points": 2, "cost": {"ruby": 4, "onyx": 2, "diamond": 1}},
    {"id": "c2_04", "level": 2, "gem": "diamond", "points": 2, "cost": {"ruby": 5}},
    {"id": "c2_05", "level": 2, "gem": "diamond", "points": 2, "cost": {"sapphire": 4, "emerald": 2, "ruby": 1}},
    {"id": "c2_06", "level": 2, "gem": "diamond", "points": 3, "cost": {"diamond": 6}},

    # Sapphire
    {"id": "c2_07", "level": 2, "gem": "sapphire", "points": 1, "cost": {"sapphire": 2, "emerald": 2, "ruby": 3}},
    {"id": "c2_08", "level": 2, "gem": "sapphire", "points": 1, "cost": {"diamond": 2, "sapphire": 2, "onyx": 3}},
    {"id": "c2_09", "level": 2, "gem": "sapphire", "points": 2, "cost": {"diamond": 5, "sapphire": 3}},
    {"id": "c2_10", "level": 2, "gem": "sapphire", "points": 2, "cost": {"sapphire": 5}},
    {"id": "c2_11", "level": 2, "gem": "sapphire", "points": 2, "cost": {"emerald": 4, "ruby": 2, "onyx": 1}},
    {"id": "c2_12", "level": 2, "gem": "sapphire", "points": 3, "cost": {"sapphire": 6}},

    # Emerald
    {"id": "c2_13", "level": 2, "gem": "emerald", "points": 1, "cost": {"diamond": 3, "sapphire": 2, "ruby": 2}},
    {"id": "c2_14", "level": 2, "gem": "emerald", "points": 1, "cost": {"diamond": 2, "emerald": 3, "onyx": 2}},
    {"id": "c2_15", "level": 2, "gem": "emerald", "points": 2, "cost": {"diamond": 4, "sapphire": 2, "onyx": 1}},
    {"id": "c2_16", "level": 2, "gem": "emerald", "points": 2, "cost": {"emerald": 5}},
    {"id": "c2_17", "level": 2, "gem": "emerald", "points": 2, "cost": {"sapphire": 5, "emerald": 3}},
    {"id": "c2_18", "level": 2, "gem": "emerald", "points": 3, "cost": {"emerald": 6}},

    # Ruby
    {"id": "c2_19", "level": 2, "gem": "ruby", "points": 1, "cost": {"diamond": 2, "emerald": 2, "onyx": 3}},
    {"id": "c2_20", "level": 2, "gem": "ruby", "points": 1, "cost": {"diamond": 3, "sapphire": 3, "ruby": 2}},
    {"id": "c2_21", "level": 2, "gem": "ruby", "points": 2, "cost": {"diamond": 1, "emerald": 4, "onyx": 2}},
    {"id": "c2_22", "level": 2, "gem": "ruby", "points": 2, "cost": {"onyx": 5}},
    {"id": "c2_23", "level": 2, "gem": "ruby", "points": 2, "cost": {"ruby": 5, "onyx": 3}},
    {"id": "c2_24", "level": 2, "gem": "ruby", "points": 3, "cost": {"ruby": 6}},

    # Onyx
    {"id": "c2_25", "level": 2, "gem": "onyx", "points": 1, "cost": {"diamond": 3, "sapphire": 2, "emerald": 2}},
    {"id": "c2_26", "level": 2, "gem": "onyx", "points": 1, "cost": {"sapphire": 3, "emerald": 3, "onyx": 2}},
    {"id": "c2_27", "level": 2, "gem": "onyx", "points": 2, "cost": {"diamond": 2, "ruby": 4, "sapphire": 1}},
    {"id": "c2_28", "level": 2, "gem": "onyx", "points": 2, "cost": {"diamond": 5}},
    {"id": "c2_29", "level": 2, "gem": "onyx", "points": 2, "cost": {"emerald": 5, "ruby": 3}},
    {"id": "c2_30", "level": 2, "gem": "onyx", "points": 3, "cost": {"onyx": 6}}
]

# 20 Level 3 Development Cards
LEVEL_3_CARDS = [
    # Diamond
    {"id": "c3_01", "level": 3, "gem": "diamond", "points": 3, "cost": {"sapphire": 3, "emerald": 3, "ruby": 5, "onyx": 3}},
    {"id": "c3_02", "level": 3, "gem": "diamond", "points": 4, "cost": {"ruby": 7}},
    {"id": "c3_03", "level": 3, "gem": "diamond", "points": 4, "cost": {"onyx": 7}},
    {"id": "c3_04", "level": 3, "gem": "diamond", "points": 5, "cost": {"diamond": 3, "ruby": 7}},

    # Sapphire
    {"id": "c3_05", "level": 3, "gem": "sapphire", "points": 3, "cost": {"diamond": 3, "emerald": 3, "ruby": 3, "onyx": 5}},
    {"id": "c3_06", "level": 3, "gem": "sapphire", "points": 4, "cost": {"diamond": 7}},
    {"id": "c3_07", "level": 3, "gem": "sapphire", "points": 4, "cost": {"emerald": 7}},
    {"id": "c3_08", "level": 3, "gem": "sapphire", "points": 5, "cost": {"sapphire": 3, "diamond": 7}},

    # Emerald
    {"id": "c3_09", "level": 3, "gem": "emerald", "points": 3, "cost": {"diamond": 5, "sapphire": 3, "ruby": 3, "onyx": 3}},
    {"id": "c3_10", "level": 3, "gem": "emerald", "points": 4, "cost": {"sapphire": 7}},
    {"id": "c3_11", "level": 3, "gem": "emerald", "points": 4, "cost": {"ruby": 7}},
    {"id": "c3_12", "level": 3, "gem": "emerald", "points": 5, "cost": {"emerald": 3, "sapphire": 7}},

    # Ruby
    {"id": "c3_13", "level": 3, "gem": "ruby", "points": 3, "cost": {"diamond": 3, "sapphire": 5, "emerald": 3, "onyx": 3}},
    {"id": "c3_14", "level": 3, "gem": "ruby", "points": 4, "cost": {"diamond": 7}},
    {"id": "c3_15", "level": 3, "gem": "ruby", "points": 4, "cost": {"onyx": 7}},
    {"id": "c3_16", "level": 3, "gem": "ruby", "points": 5, "cost": {"ruby": 3, "onyx": 7}},

    # Onyx
    {"id": "c3_17", "level": 3, "gem": "onyx", "points": 3, "cost": {"diamond": 3, "sapphire": 3, "emerald": 5, "ruby": 3}},
    {"id": "c3_18", "level": 3, "gem": "onyx", "points": 4, "cost": {"emerald": 7}},
    {"id": "c3_19", "level": 3, "gem": "onyx", "points": 4, "cost": {"sapphire": 7}},
    {"id": "c3_20", "level": 3, "gem": "onyx", "points": 5, "cost": {"onyx": 3, "emerald": 7}}
]
