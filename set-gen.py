from datetime import datetime, timedelta
import random

FILE_PATH = "Anti-Finger.txt"

# จำนวนวัน
num_days = 30

# วันเริ่มต้น
start_date = datetime(2026, 1, 1, 8, 30, 0)

# รายการท่าฝึก (5 ท่า)
exercises = [
    "ท่าเหยียดมือตรงสําเร็จ!",
    "ท่าทำมือคล้ายตะขอสําเร็จ!",
    "ท่ากำมือสําเร็จ!",
    "ท่ากำมือแบบเหยียดปลายนิ้วสําเร็จ!",
    "ท่างอโคนนิ้วแต่เหยียดปลายนิ้วมือสําเร็จ!"
]

with open(FILE_PATH, "w", encoding="utf-8") as f:
    for day_offset in range(num_days):
        day = start_date + timedelta(days=day_offset)
        
        # สุ่มจำนวนเซ็ตต่อวัน (1–3 เซ็ต)
        sets_today = random.choice([1, 2, 3])
        
        for set_index in range(1, sets_today + 1):
            # 1 เซ็ต = 10 ครั้ง, 1 ครั้ง = ทำครบ 5 ท่า
            for rep_index in range(1, 11):  # 10 ครั้งต่อเซ็ต
                for pose_index, exercise in enumerate(exercises, start=1):
                    # เพิ่มเวลาต่อเนื่อง (แต่ละท่าห่างกัน 7 วินาที)
                    seconds_passed = ((rep_index - 1) * len(exercises) + pose_index) * 7
                    timestamp = day + timedelta(seconds=seconds_passed)
                    
                    line = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] เซ็ตที่ {set_index} ครั้งที่ {rep_index} : {exercise}\n"
                    f.write(line)


print(f"สร้างไฟล์ {FILE_PATH} เสร็จเรียบร้อย!")
