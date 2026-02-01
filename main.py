from logging import root
from PIL import Image, ImageTk
import customtkinter as ctk
import cv2
import mediapipe as mp
import pygame
import time, threading
from datetime import datetime, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from collections import defaultdict
import sys, os
import tkinter as tk
from tkinter import ttk
import math

class AntiTriggerFingersApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        
        # --- Screen & Scaling Setup ---
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        # Base resolution for calculation (Original design)
        base_w = 1920
        base_h = 1080

        # Calculate scale factors
        self.scale_w = self.screen_width / base_w
        self.scale_h = self.screen_height / base_h
        # Use the smaller scale for things that must maintain aspect ratio (fonts, circles, images)
        self.u_scale = min(self.scale_w, self.scale_h)

        self.title("AI-Powered Anti-trigger Fingers")
        self.attributes("-fullscreen", True)
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.overrideredirect(True)       
        self.bind("<Escape>", lambda e: self.on_close())
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")

        # --- Variables ---
        self.key_held = False
        self.time_max = 5
        self.time_current = self.time_max
        self.hand_posit = 0
        self.still_hold = False
        self.current_pose = 1
        self.key = ""
        self.is_pass = False
        self.round = 0
        self.set = 0
        self.pose_name = [
            "placeholder",
            "เหยียดมือตรง",
            "ทำมือคล้ายตะขอ",
            "กำมือ",
            "กำมือแบบเหยียดปลายนิ้ว",
            "งอโค้นนิ้วแต่เหยียดปลายนิ้วมือ"
        ]
        self.extent = 0
        self.progress = 0

        # --- Camera Setup ---
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Cannot open webcam")
        else:
            # Try to set camera to a decent resolution, will be resized later
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # --- UI Colors ---
        self.purple_bg = "#6a0dad"
        self.light_gray_bg = "#d9d9d9"
        self.light_gray_bg_program = "white"
        self.red_btn = "#ff5656"
        self.hover_red_bt = "#cc4444"
        self.yellow_btn = "#fbbc05"
        self.hover_yellow_bt = "#e0a800"
        self.green_btn = "#34a853"
        self.hover_green_bt = "#247539"
        self.white_fg = "#ffffff"
        self.black_fg = "black"

        # --- Scaled Fonts ---
        self.font_large_title = ("Sarabun", int(60 * self.u_scale), "bold")
        self.font_medium_text = ("Sarabun", int(50 * self.u_scale), "bold")
        self.font_timer = ("Sarabun", int(60 * self.u_scale), "bold")
        self.font_pose_text = ("Sarabun", int(40 * self.u_scale), "bold") # Reduced slightly for better fit
        self.font_btn_text = ("Sarabun", int(50 * self.u_scale), "bold")
        self.font_small = ("Sarabun", int(25 * self.u_scale))

        # --- Scaled Dimensions ---
        top_bar_h = int(150 * self.scale_h)
        logo_size = int(140 * self.u_scale)
        self.camera_width = int(400 * self.scale_w)
        self.camera_height = int(570 * self.scale_h)
        btn_h = int(80 * self.scale_h)
        btn_w = int(260 * self.scale_w)
        
        # Timer canvas scaling
        self.timer_canvas_size = int(260 * self.u_scale)
        self.timer_pad = 10

        # --- UI Layout ---
        self.top_bar_frame = ctk.CTkFrame(self, fg_color=self.purple_bg, height=top_bar_h)
        self.top_bar_frame.pack(side="top", fill="x")
        self.top_bar_frame.pack_propagate(False)

        try:
            logo_image_pil = Image.open("pictures/logo.png")
            logo_image_pil = logo_image_pil.resize((logo_size, logo_size), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image_pil)
            self.logo_label = ctk.CTkLabel(
                self.top_bar_frame, image=self.logo_photo, fg_color=self.purple_bg, text=""
            )
            self.logo_label.pack(side="left", padx=int(20 * self.scale_w), pady=int(10 * self.scale_h))
        except FileNotFoundError:
            self.logo_label = ctk.CTkLabel(
                self.top_bar_frame, text="LOGO", font=("Sarabun", 20), text_color=self.white_fg, fg_color=self.purple_bg
            )
            self.logo_label.pack(side="left", padx=20, pady=10)

        self.app_title_label = ctk.CTkLabel(
            self.top_bar_frame,
            text="AI-Powered Anti-trigger Fingers",
            font=self.font_large_title,
            text_color=self.white_fg,
            fg_color=self.purple_bg,
        )
        self.app_title_label.pack(side="left", padx=20, pady=10)

        # Main Content Grid
        self.main_content_frame = ctk.CTkFrame(self, fg_color=self.light_gray_bg_program)
        self.main_content_frame.pack(side="top", fill="both", expand=True, pady=int(20 * self.scale_h))
        
        # Calculate column weights and minsize dynamically
        col_min = int(self.screen_width / 3)
        self.main_content_frame.grid_columnconfigure(0, weight=1, minsize=col_min)
        self.main_content_frame.grid_columnconfigure(1, weight=1, minsize=col_min)
        self.main_content_frame.grid_columnconfigure(2, weight=1, minsize=col_min)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(1, weight=1)
        self.main_content_frame.grid_rowconfigure(2, weight=1)

        # Left Column: Camera
        placeholder = Image.new("RGB", (self.camera_width, self.camera_height), (200, 200, 200))
        self.camera_photo = ImageTk.PhotoImage(placeholder)
        self.camera_label = ctk.CTkLabel(self.main_content_frame, image=self.camera_photo, text="")
        self.camera_label.grid(row=0, column=0, rowspan=3, padx=int(40 * self.scale_w), pady=20, sticky="nsew")

        # --- Center Column: Info (จัดกึ่งกลางจอสมบูรณ์) ---
        # 1. สร้างพื้นที่หลักสำหรับคอลัมน์กลาง (ครอบคลุม Row 0 และ 1 เพื่อให้มีพื้นที่เต็มความสูง)
        self.center_info_container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.center_info_container.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=20, pady=10)

        # 2. สร้าง Wrapper (กรอบลอย) เพื่อจัดเนื้อหาให้อยู่กึ่งกลาง
        # การใช้ pack(expand=True) จะทำให้กรอบนี้ลอยอยู่กลางพื้นที่ว่างโดยอัตโนมัติ
        self.center_wrapper = ctk.CTkFrame(self.center_info_container, fg_color="transparent")
        self.center_wrapper.pack(expand=True, fill="x")

        # --- ส่วนประกอบที่ 1: กล่องสีเทาบน (Set Info) ---
        self.set_times_frame = ctk.CTkFrame(self.center_wrapper, fg_color=self.light_gray_bg, border_width=1)
        self.set_times_frame.pack(side="top", fill="x", pady=(0, 15)) # เว้นระยะล่าง 15

        # เนื้อหาข้างในกล่องบน (เหมือนเดิม)
        self.times_line_frame = ctk.CTkFrame(self.set_times_frame, fg_color=self.light_gray_bg)
        self.times_line_frame.pack(side="top", pady=(10, 0))
        
        self.Label_times_text = ctk.CTkLabel(
            self.times_line_frame,
            text="ครั้งที่ : ",
            font=self.font_medium_text,
            text_color=self.black_fg,
            fg_color=self.light_gray_bg,
        )
        self.Label_times_text.pack(side="left", padx=(10, 0))
        self.Label_set_times_number = ctk.CTkLabel(
            self.times_line_frame, text=f"{self.round}", font=self.font_medium_text, text_color=self.black_fg, fg_color=self.light_gray_bg
        )
        self.Label_set_times_number.pack(side="left", padx=(0, 10))

        self.sets_line_frame = ctk.CTkFrame(self.set_times_frame, fg_color=self.light_gray_bg)
        self.sets_line_frame.pack(side="top", pady=(0, 10))
        
        self.Label_set_text = ctk.CTkLabel(
            self.sets_line_frame, text="เซ็ตที่ : ", font=self.font_medium_text, text_color=self.black_fg, fg_color=self.light_gray_bg
        )
        self.Label_set_text.pack(side="left", padx=(10, 0))
        self.Label_set_number = ctk.CTkLabel(
            self.sets_line_frame, text=f"{self.set}", font=self.font_medium_text, text_color=self.black_fg, fg_color=self.light_gray_bg
        )
        self.Label_set_number.pack(side="left", padx=(0, 10))

        # --- ส่วนประกอบที่ 2: ข้อความคั่นกลาง ---
        self.guideline_label = ctk.CTkLabel(
            self.center_wrapper,
            text="ควรทำอย่างน้อย 2-3 เซ็ตต่อวัน",
            font=self.font_small, 
            text_color=self.black_fg,
            fg_color="transparent"
        )
        self.guideline_label.pack(side="top", pady=15) # เว้นระยะ บน-ล่าง

        # --- ส่วนประกอบที่ 3: กล่องสีเทาล่าง (Pose Info) ---
        self.pose_text_frame = ctk.CTkFrame(self.center_wrapper, fg_color=self.light_gray_bg, border_width=1)
        self.pose_text_frame.pack(side="top", fill="x", pady=(15, 0)) # เว้นระยะบน 15

        # เนื้อหาข้างในกล่องล่าง (เหมือนเดิม)
        self.Label_pose_thai_text = ctk.CTkLabel(
            self.pose_text_frame, text=f"ท่าที่ {self.current_pose}", font=self.font_pose_text, text_color=self.black_fg, fg_color=self.light_gray_bg
        )
        self.Label_pose_thai_text.pack(side="top", pady=(10, 0))
        self.Label_pose_action_text = ctk.CTkLabel(
            self.pose_text_frame, text=f"{self.pose_name[self.current_pose]}", font=self.font_pose_text, text_color=self.black_fg, fg_color=self.light_gray_bg
        )
        self.Label_pose_action_text.pack(side="top", pady=(0, 10))

        # Buttons
        self.controls_center_frame = ctk.CTkFrame(self.main_content_frame, fg_color=self.light_gray_bg_program)
        self.controls_center_frame.grid(row=2, column=0, columnspan=3, pady=(10, 20), sticky="ew")
        self.buttons_inner = ctk.CTkFrame(self.controls_center_frame, fg_color=self.light_gray_bg_program)
        self.buttons_inner.pack(expand=True)
        
        self.start_stop_button = ctk.CTkButton(
            self.buttons_inner,
            text="เริ่มต้น",
            font=self.font_btn_text,
            fg_color=self.green_btn,
            text_color=self.white_fg,
            command=lambda: self.toggle_start_pause(),
            height=btn_h,
            width=btn_w,
            hover_color=self.hover_green_bt,
        )
        self.start_stop_button.grid(row=0, column=0, padx=int(50 * self.scale_w), pady=5)
        
        self.reset_button = ctk.CTkButton(
            self.buttons_inner,
            text="รีเซ็ต",
            font=self.font_btn_text,
            fg_color=self.red_btn,
            text_color=self.white_fg,
            command=lambda: self.reset_action(),
            height=btn_h,
            width=btn_w,
            hover_color=self.hover_red_bt,
        )
        self.reset_button.grid(row=0, column=1, padx=int(30 * self.scale_w), pady=5)

        # Right Column: Timer & Example
        self.timer_frame = ctk.CTkFrame(self.main_content_frame, fg_color=self.white_fg)
        self.timer_frame.grid(row=0, column=2, padx=20, pady=20, sticky="n")
        
        self.timer_canvas = ctk.CTkCanvas(
            self.timer_frame, width=self.timer_canvas_size, height=self.timer_canvas_size, bg=self.white_fg, highlightthickness=0
        )
        self.timer_canvas.pack()
        
        left = self.timer_pad
        top = self.timer_pad
        right = self.timer_canvas_size - self.timer_pad
        bottom = self.timer_canvas_size - self.timer_pad
        self.timer_canvas.create_oval(left, top, right, bottom, outline="#3CB371", width=10, tags="progress")
        center = self.timer_canvas_size // 2
        self.timer_text = self.timer_canvas.create_text(center, center, text=f"{self.time_current}", font=self.font_timer, fill=self.black_fg)

        self.timer_anim_job = None
        self._timer_anim_from = 0.0
        self._timer_anim_to = 0.0
        self._timer_anim_start = 0.0
        self._timer_anim_duration = 0.0

        # Example Pose Image
        img_size = int(300 * self.u_scale)
        try:
            small_hand_image_pil = Image.open("pictures/EX_POSE/pose1.png")
            small_hand_image_pil = small_hand_image_pil.resize((img_size, img_size), Image.LANCZOS)
            self.small_hand_photo = ImageTk.PhotoImage(small_hand_image_pil)
            self.small_hand_label = ctk.CTkLabel(self.main_content_frame, image=self.small_hand_photo, text="")
            self.small_hand_label.grid(row=1, column=2, padx=20, pady=(0, 20), sticky="n")
        except FileNotFoundError:
            self.small_hand_label = ctk.CTkLabel(
                self.main_content_frame, text="Example Pose", font=("Sarabun", 16), bg="lightgray", width=15, height=10
            )
            self.small_hand_label.grid(row=1, column=2, padx=20, pady=(0, 20), sticky="n")

        self.small_hand_bottom_frame = ctk.CTkFrame(self.main_content_frame, fg_color=self.light_gray_bg_program)
        self.small_hand_bottom_frame.grid(row=2, column=2, pady=(0, 20))
        
        self.log_button = ctk.CTkButton(
            self.small_hand_bottom_frame,
            text="รายงาน",
            font=self.font_btn_text,
            fg_color="#4285F4",
            text_color=self.white_fg,
            command=lambda: self.show_history_page(),
            height=btn_h,
            width=int(240 * self.scale_w),
            hover_color="#3367D6",
        )
        self.log_button.pack(side="right", padx=int(140 * self.scale_w))

        # --- History Page ---
        self.history_page = ctk.CTkFrame(self, fg_color=self.light_gray_bg_program)
        self.history_title = ctk.CTkLabel(self.history_page, text="รายงานย้อนหลัง", font=("Sarabun", int(55 * self.u_scale), "bold"), text_color=self.black_fg)
        self.history_title.pack(pady=5)
        
        self.chart_container = tk.Frame(self.history_page, bg="white")
        self.chart_container.pack(fill="both", expand=True, padx=40, pady=(10, 5))
        self.history_content_frame = ctk.CTkFrame(self.history_page, fg_color=self.light_gray_bg_program)
        self.history_content_frame.pack(fill="x", padx=40, pady=(0, 0))

        self.history_textbox = ctk.CTkTextbox(
            self.history_content_frame,
            width=int(1000 * self.scale_w),
            height=int(250 * self.scale_h),
            font=("Sarabun", int(20 * self.u_scale)),
            text_color=self.black_fg,
            fg_color="#CCC9C9",
        )
        self.history_textbox.pack(side="left", padx=int(100 * self.scale_w), pady=0)

        self.back_button = ctk.CTkButton(
            self.history_content_frame,
            text="กลับ",
            font=("Sarabun", int(40 * self.u_scale), "bold"),
            fg_color="#FF9800",
            text_color="white",
            hover_color="#E68900",
            command=self.show_main_page,
            height=btn_h,
            width=btn_w
        )
        self.back_button.pack(side="right", padx=(int(70 * self.scale_w), int(100 * self.scale_w)), pady=(int(100 * self.scale_h), 0))

        self.pose_sounds = {1: ["001.mp3"], 2: ["002.mp3"], 3: ["003.mp3"], 4: ["004.mp3"], 5: ["005.mp3"]}
        self.current_chart = None

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"[Sound] Pygame mixer init error: {e}")

        self.running = False
        self.countdown_active = False
        self.countdown_job = None
        self.countdown_total = 0
        self.countdown_end_time = 0

        self.mp_running = True
        self.mp_thread = threading.Thread(target=self._mediapipe_loop, daemon=True)
        self.mp_thread.start()

        self.check_sensor_loop()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_history_from_file(self):
        FILE_PATH = "Anti-Finger.txt"
        DAILY_TARGET_REPS = 30
        poses_per_rep = 5
        reps_per_set = 10
        daily_poses = defaultdict(int)

        if not os.path.exists(FILE_PATH):
            return []

        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or not line.startswith("["):
                        continue
                    try:
                        date_str = line.split("]")[0][1:]
                        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        daily_poses[date.date()] += 1
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

        if not daily_poses:
            return []

        history = []
        first_day = min(daily_poses.keys())
        last_day = max(daily_poses.keys())
        day = first_day

        while day <= last_day:
            poses = daily_poses.get(day, 0)
            reps = poses // poses_per_rep
            sets_done = reps // reps_per_set
            if DAILY_TARGET_REPS > 0:
                progress = min((reps / float(DAILY_TARGET_REPS)) * 100.0, 100.0)
            else:
                progress = 0.0

            history.append({
                'date': datetime.combine(day, datetime.min.time()),
                'poses': poses,
                'reps': reps,
                'sets_done': sets_done,
                'progress': progress,
            })
            day += timedelta(days=1)

        history.sort(key=lambda x: x['date'])
        return history

    def draw_progress_chart(self):
        """Draw the progress chart in history page"""
        history = self.get_history_from_file()
        
        # Clear previous chart
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        if not history:
            label = tk.Label(self.chart_container, text="No data available", bg="white", font=("Sarabun", 14))
            label.pack(fill="both", expand=True)
            return

        try:
            font_path = "Sarabun.ttf" 
            
            # ตรวจสอบว่าเจอไฟล์ไหม ถ้าไม่เจอให้ใช้ Tahoma แทน (กัน error)
            if os.path.exists(font_path):
                thai_font_prop = fm.FontProperties(fname=font_path, size=14)
                title_font_prop = fm.FontProperties(fname=font_path, size=16, weight='bold')
            else:
                # Fallback กรณีหาไฟล์ไม่เจอ ให้ลองเรียกชื่อฟอนต์มาตรฐานใน Windows
                print(f"Warning: Font file {font_path} not found. Using Tahoma.")
                thai_font_prop = fm.FontProperties(family='Tahoma', size=14)
                title_font_prop = fm.FontProperties(family='Tahoma', size=16, weight='bold')
            # -------------------------------

            # Main frame สำหรับ chart + control
            main_frame = tk.Frame(self.chart_container, bg="white")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Chart frame (ซ้าย)
            chart_frame = tk.Frame(main_frame, bg="white")
            chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Control frame (ขวา)
            control_frame = tk.Frame(main_frame, bg="white", width=int(200 * self.scale_w))
            control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

            # ... (ส่วน Dropdown และ Legend เหมือนเดิม) ...
            tk.Label(control_frame, text="Select Date:", bg="white", font=("Sarabun", 14)).pack(anchor='w', pady=5)
            date_var = tk.StringVar()
            date_combo = ttk.Combobox(control_frame, textvariable=date_var, width=15, state='readonly')
            date_combo.pack(anchor='w', padx=5)

            tk.Label(control_frame, text="\nLegend", bg="white", font=("Sarabun", 12, "bold")).pack(anchor='w', pady=(10, 5))
            tk.Label(control_frame, text="🔴 Red: <50%", bg="white", fg="red", font=("Sarabun", 12)).pack(anchor='w')
            tk.Label(control_frame, text="🟢 Green: ≥50%", bg="white", fg="green", font=("Sarabun", 12)).pack(anchor='w')
            tk.Label(control_frame, text="↑ ดีขึ้น", bg="white", fg="green", font=("Sarabun", 12)).pack(anchor='w')
            tk.Label(control_frame, text="↓ แย่ลง", bg="white", fg="orange", font=("Sarabun", 12)).pack(anchor='w')

            feedback_label = tk.Label(control_frame, text="", bg="lightyellow", justify='left', wraplength=int(400 * self.scale_w), 
                                     font=("Sarabun", 12), relief=tk.SUNKEN, padx=5, pady=5)
            feedback_label.pack(fill='x', pady=10, padx=5)

            # Create chart
            fig, ax = plt.subplots(figsize=(10, 4), dpi=80) 
            fig.patch.set_facecolor('white')

            dates = [h['date'] for h in history]
            progresses = [h['progress'] for h in history]

            # Prepare OHLC data (เหมือนเดิม)
            o, h_, l, c = [], [], [], []
            prev = progresses[0] if progresses else 0
            for p in progresses:
                o.append(prev)
                c.append(p)
                high = max(prev, p)
                low = min(prev, p)
                h_.append(high)
                l.append(low)
                prev = p

            # Draw bars (เหมือนเดิม)
            points = []
            for i, p in enumerate(progresses):
                prev_prog = progresses[i-1] if i > 0 else None
                if prev_prog is None:
                    color = (1, 0, 0) if p < 50 else (0, 1, 0)
                elif p > prev_prog:
                    color = (0, 1, 0)
                elif p < prev_prog:
                    color = (1, 0.65, 0)
                else:
                    color = (1, 0, 0) if p < 50 else (0, 1, 0)

                ax.vlines(dates[i], l[i], h_[i], color=color, linewidth=2)
                ax.vlines(dates[i], o[i], c[i], color=color, linewidth=8)
                
                if prev_prog is not None:
                    if p > prev_prog:
                        # ใช้ fontproperties แทน font
                        ax.annotate('↑', xy=(dates[i], c[i]+3), ha='center', color='green', fontproperties=thai_font_prop)
                    elif p < prev_prog:
                        ax.annotate('↓', xy=(dates[i], c[i]+3), ha='center', color='black', fontproperties=thai_font_prop)
                
                point, = ax.plot(dates[i], c[i], 'o', color='black', markersize=8)
                points.append((point, dates[i], p, history[i]['sets_done'], i))

            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
            
            # --- จุดสำคัญที่แก้: ใช้ fontproperties ---
            ax.set_ylabel("ความสำเร็จ (%)", fontproperties=thai_font_prop)
            ax.set_title("สถิติของคุณ", fontproperties=title_font_prop)
            # ------------------------------------

            ax.set_ylim(0, 110)
            ax.grid(True, linestyle='--', alpha=0.5)
            fig.autofmt_xdate()
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            # ... (ส่วนที่เหลือเหมือนเดิม) ...
            date_list = [h['date'].strftime('%d-%b-%Y') for h in history]
            date_combo['values'] = date_list
            if date_list:
                date_combo.set(date_list[-1])

            def feedback_text(prog, prev_prog):
                # ... (Logic เหมือนเดิม) ...
                if prog == 0: return "วันนี้คุณยังไม่ได้ทำ 🔴"
                elif prev_prog is not None and prog < prev_prog: return "วันนี้คุณทำได้น้อยลง ↓"
                elif prev_prog is not None and prog > prev_prog: return "วันนี้คุณทำได้ดีขึ้น ↑"
                elif prog < 50: return "วันนี้คุณทำได้น้อยลง ↓"
                else: return "วันนี้คุณทำได้ตามปกติ ✓"

            def update_feedback(event=None):
                # ... (Logic เหมือนเดิม) ...
                selected_date_str = date_var.get()
                if not selected_date_str: return
                try:
                    selected_date = datetime.strptime(selected_date_str, '%d-%b-%Y').date()
                    idx = next((i for i, h in enumerate(history) if h['date'].date() == selected_date), None)
                    if idx is not None:
                        prog = history[idx]['progress']
                        sets = history[idx]['sets_done']
                        prev_prog = history[idx-1]['progress'] if idx > 0 else None
                        fb = feedback_text(prog, prev_prog)
                        feedback_label.config(text=f"{selected_date_str}\nProgress: {prog:.0f}%\nSets: {sets}\n{fb}")
                except Exception as e: print(f"Error: {e}")

            def on_click(event):
                # ... (Logic เหมือนเดิม) ...
                if event.inaxes != ax: return
                for point, date, prog, sets, idx in points:
                    xdata = mdates.date2num(date)
                    ydata = prog
                    if abs(event.xdata - xdata) < 0.3 and abs(event.ydata - ydata) < 5:
                        prev_prog = progresses[idx-1] if idx > 0 else None
                        fb = feedback_text(prog, prev_prog)
                        feedback_label.config(text=f"{date.strftime('%d-%b-%Y')}\nProgress: {prog:.0f}%\nSets: {sets}\n{fb}")
                        date_var.set(date.strftime('%d-%b-%Y'))
                        return

            date_combo.bind("<<ComboboxSelected>>", update_feedback)
            canvas.mpl_connect("button_press_event", on_click)
            update_feedback()
            self.current_chart = (fig, canvas)

        except Exception as e:
            print(f"Error drawing chart: {e}")
            label = tk.Label(self.chart_container, text=f"Error: {e}", bg="white", font=("Sarabun", 12), fg="red")
            label.pack(fill="both", expand=True)

    def play_sounds_sequential(self, filename):
        def _play(f=filename):
            try:
                if not f.endswith(".mp3"):
                    f += ".mp3"
                sound_path = f"Voices/{f}"
                if os.path.exists(sound_path):
                    sound = pygame.mixer.Sound(sound_path)
                    sound.play()
            except Exception as e:
                print(f"Sound error: {e}")
        threading.Thread(target=_play, daemon=True).start()

    def load_history(self):
        try:
            with open("Anti-Finger.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = ["No history found.\n"]
        
        # Limit lines to prevent lag
        max_lines = 5000 
        if len(lines) > max_lines:
            lines = lines[-max_lines:]

        self.history_textbox.configure(state="normal")
        self.history_textbox.delete("1.0", "end")
        self.history_textbox.insert("end", "".join(lines))
        self.history_textbox.see("end")
        self.history_textbox.configure(state="disabled")

    def show_main_page(self):
        self.history_page.pack_forget()
        self.main_content_frame.pack(side="top", fill="both", expand=True, pady=int(20 * self.scale_h))
        self.play_sounds_sequential("010.mp3")

    def show_history_page(self):
        self.main_content_frame.pack_forget()
        self.play_sounds_sequential("009.mp3")
        self.history_page.pack(side="top", fill="both", expand=True, pady=int(20 * self.scale_h))
        self.draw_progress_chart()
        self.load_history()

    def write_log(self, message):
        now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log_message = f"{now} เซ็ตที่ {self.set} ครั้งที่ {self.round} : {message}"
        try:
            with open("Anti-Finger.txt", "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
            print(log_message)
        except Exception as e:
            print(f"Error writing log: {e}")

    def check_fingers(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                return
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]
            white_pixels = cv2.countNonZero(thresh)
            if white_pixels > 50000:
                if self.hand_posit < 5:
                    self.hand_posit += 1
        except Exception as e:
            print(f"[check_fingers] Error: {e}")

    def _mediapipe_loop(self):
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        drawing_spec_landmark = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4)
        drawing_spec_connection = mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)

        hands = mp_hands.Hands(
            static_image_mode=False, max_num_hands=1,
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )

        pose_ranges = {
            1: [(0, 200), (150, 185), (150, 185), (150, 185), (150, 185)],
            2: [(0, 200), (40, 170), (40, 170), (40, 170), (40, 170)],
            3: [(0, 200), (0, 60), (0, 60), (0, 60), (0, 60)],
            4: [(0, 200), (0, 50), (0, 50), (0, 50), (0, 50)],
            5: [(0, 200), (50, 185), (50, 185), (50, 160), (50, 160)],
        }

        def _angle_between(a, b):
            ax, ay = a
            bx, by = b
            dot = ax * bx + ay * by
            na = (ax * ax + ay * ay) ** 0.5
            nb = (bx * bx + by * by) ** 0.5
            if na == 0 or nb == 0:
                return 0.0
            cosv = max(-1.0, min(1.0, dot / (na * nb)))
            return math.degrees(math.acos(cosv))

        try:
            while self.mp_running:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                h, w = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                thumb_a = index_a = middle_a = ring_a = pinky_a = 0
                pose_match = False

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(
                            frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                            drawing_spec_landmark, drawing_spec_connection
                        )

                        lm = hand_landmarks.landmark

                        def to_pt(idx):
                            return (lm[idx].x * w, lm[idx].y * h)

                        wrist = to_pt(0)
                        
                        # Calculate angles
                        v1 = (to_pt(4)[0] - to_pt(2)[0], to_pt(4)[1] - to_pt(2)[1])
                        v2 = (wrist[0] - to_pt(2)[0], wrist[1] - to_pt(2)[1])
                        thumb_a = _angle_between(v1, v2)

                        v1 = (to_pt(8)[0] - to_pt(5)[0], to_pt(8)[1] - to_pt(5)[1])
                        v2 = (wrist[0] - to_pt(5)[0], wrist[1] - to_pt(5)[1])
                        index_a = _angle_between(v1, v2)

                        v1 = (to_pt(12)[0] - to_pt(9)[0], to_pt(12)[1] - to_pt(9)[1])
                        v2 = (wrist[0] - to_pt(9)[0], wrist[1] - to_pt(9)[1])
                        middle_a = _angle_between(v1, v2)

                        v1 = (to_pt(16)[0] - to_pt(13)[0], to_pt(16)[1] - to_pt(13)[1])
                        v2 = (wrist[0] - to_pt(13)[0], wrist[1] - to_pt(13)[1])
                        ring_a = _angle_between(v1, v2)

                        v1 = (to_pt(20)[0] - to_pt(17)[0], to_pt(20)[1] - to_pt(17)[1])
                        v2 = (wrist[0] - to_pt(17)[0], wrist[1] - to_pt(17)[1])
                        pinky_a = _angle_between(v1, v2)

                        reqs = pose_ranges.get(self.current_pose, pose_ranges[1])
                        angles = [thumb_a, index_a, middle_a, ring_a, pinky_a]
                        
                        ok = True
                        for ang, (mn, mx) in zip(angles, reqs):
                            if ang is None or not (mn <= ang <= mx):
                                ok = False
                                break
                        pose_match = ok

                        try:
                            cv2.putText(frame, f"Match:{'YES' if pose_match else 'NO'}", (10, 180),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0) if pose_match else (0, 0, 200), 2)
                        except Exception:
                            pass

                display_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(display_rgb)

                def _crop_and_resize(img, target_w, target_h):
                    src_w, src_h = img.size
                    target_ratio = target_w / target_h
                    src_ratio = src_w / src_h
                    if src_ratio > target_ratio:
                        new_w = int(src_h * target_ratio)
                        left = (src_w - new_w) // 2
                        img = img.crop((left, 0, left + new_w, src_h))
                    else:
                        new_h = int(src_w / target_ratio)
                        top = (src_h - new_h) // 2
                        img = img.crop((0, top, src_w, top + new_h))
                    return img.resize((target_w, target_h), Image.LANCZOS)

                # Use dynamic dimensions
                pil_img = _crop_and_resize(pil_img, self.camera_width, self.camera_height)

                try:
                    self.after(0, lambda im=pil_img, a=(thumb_a, index_a, middle_a, ring_a, pinky_a), m=pose_match: (
                        self._update_camera_label(im),
                        self._apply_pose_detection(a, m)
                    ))
                except RuntimeError:
                    break
                time.sleep(0.02)
        finally:
            hands.close()

    def _apply_pose_detection(self, angles, match):
        try:
            if match:
                if self.hand_posit < 5:
                    self.hand_posit += 1
            else:
                self.hand_posit = 0
        except Exception as e:
            print(f"[Pose Apply] {e}")

    def _update_camera_label(self, pil_image):
        try:
            self.camera_photo = ImageTk.PhotoImage(pil_image)
            self.camera_label.configure(image=self.camera_photo)
        except Exception as e:
            pass

    def timer_reset(self):
        self.time_current = self.time_max
        self.hand_posit = 0
        self.update_timer()
        self.reset_pic()
        try:
            self.update_EX_pose()
        except Exception:
            pass

    def update_pic(self):
        return

    def reset_pic(self):
        self.timer_canvas.delete("progress")
        l = self.timer_pad
        r = self.timer_canvas_size - self.timer_pad
        self.timer_canvas.create_oval(l, l, r, r, outline="#3CB371", width=10, tags="progress")

    def update_timer(self):
        try:
            prev_time = self.time_current + 1
            from_prog = max(0.0, min(1.0, (self.time_max - prev_time) / float(self.time_max)))
            to_prog = max(0.0, min(1.0, (self.time_max - self.time_current) / float(self.time_max)))

            self._stop_timer_animation()

            self._timer_prev_sec = prev_time
            self._timer_anim_from = from_prog
            self._timer_anim_to = to_prog
            self._timer_anim_start = time.time()
            self._timer_anim_duration = 1.0
            self.timer_anim_job = self.after(0, self._animate_timer)
        except Exception as e:
            print(f"[update_timer] {e}")

    def _animate_timer(self):
        try:
            now = time.time()
            elapsed = now - self._timer_anim_start
            t = min(1.0, max(0.0, elapsed / float(self._timer_anim_duration)))
            progress = self._timer_anim_from + (self._timer_anim_to - self._timer_anim_from) * t
            extent = 360 * progress

            self.timer_canvas.delete("progress")
            l = self.timer_pad
            r = self.timer_canvas_size - self.timer_pad
            self.timer_canvas.create_arc(l, l, r, r, start=-90, extent=-extent, style="arc", width=10, outline="#3CB371", tags="progress")

            try:
                prev = getattr(self, "_timer_prev_sec", self.time_current + 1)
                interp = prev + (self.time_current - prev) * t
                interp = max(float(self.time_current), min(float(prev), interp))
                secs = int(math.ceil(interp))
            except Exception:
                secs = int(max(0, self.time_current))
            self.timer_canvas.itemconfig(self.timer_text, text=str(secs))

            if t < 1.0:
                self.timer_anim_job = self.after(50, self._animate_timer)
            else:
                self.timer_anim_job = None
                self.timer_canvas.delete("progress")
                l = self.timer_pad
                r = self.timer_canvas_size - self.timer_pad
                self.timer_canvas.create_arc(l, l, r, r, start=-90, extent=-360 * self._timer_anim_to, style="arc", width=10, outline="#3CB371", tags="progress")
                self.timer_canvas.itemconfig(self.timer_text, text=str(self.time_current))
        except Exception as e:
            self.timer_anim_job = None

    def _stop_timer_animation(self):
        try:
            if self.timer_anim_job:
                try:
                    self.after_cancel(self.timer_anim_job)
                except Exception:
                    pass
                self.timer_anim_job = None
            progress = (self.time_max - self.time_current) / float(self.time_max) if self.time_max else 0.0
            extent = 360 * progress
            self.timer_canvas.delete("progress")
            l = self.timer_pad
            r = self.timer_canvas_size - self.timer_pad
            self.timer_canvas.create_arc(l, l, r, r, start=-90, extent=-extent, style="arc", width=10, outline="#3CB371", tags="progress")
            self.timer_canvas.itemconfig(self.timer_text, text=str(self.time_current))
        except Exception as e:
            pass

    def update_text(self):
        self.Label_pose_action_text.configure(text=f"{self.pose_name[self.current_pose]}")
        self.Label_pose_thai_text.configure(text=f"ท่าที่ {self.current_pose}")

    def update_round(self):
        self.Label_set_times_number.configure(text=f"{self.round}")
        self.Label_set_number.configure(text=f"{self.set}")

    def update_EX_pose(self):
        try:
            img_size = int(300 * self.u_scale)
            small_hand_image_pil = Image.open(f"pictures/EX_POSE/pose{self.current_pose}.png")
            small_hand_image_pil = small_hand_image_pil.resize((img_size, img_size))
            self.small_hand_photo = ImageTk.PhotoImage(small_hand_image_pil)
            self.small_hand_label.configure(image=self.small_hand_photo)
        except:
            pass

    def toggle_start_pause(self):
        if self.start_stop_button.cget("text") == "เริ่มต้น":
            self.start_stop_button.configure(text="หยุด", fg_color=self.yellow_btn, hover_color=self.hover_yellow_bt)
            self.start_pose_countdown(2)
            self.play_sounds_sequential("006.mp3")
            if self.current_pose == 1:
                try:
                    self.after(1500, lambda: self.play_sounds_sequential(self.pose_sounds[self.current_pose][0]))
                except Exception:
                    pass
        else:
            self.start_stop_button.configure(text="เริ่มต้น", fg_color=self.green_btn, hover_color=self.hover_green_bt)
            self.running = False
            self._cancel_countdown()
            self.play_sounds_sequential("007.mp3")

    def start_pose_countdown(self, seconds: int):
        self._cancel_countdown()
        self.countdown_active = True
        self.countdown_total = max(1, seconds)
        self.countdown_end_time = time.time() + self.countdown_total
        self.countdown_job = self.after(0, self._animate_countdown)

    def _animate_countdown(self):
        if not self.countdown_active:
            return
        now = time.time()
        remaining = self.countdown_end_time - now
        if remaining <= 0:
            self.countdown_active = False
            self.countdown_job = None
            self.running = True
            try:
                self.timer_canvas.itemconfig(self.timer_text, text=str(self.time_current))
                self.timer_canvas.delete("progress")
                l = self.timer_pad
                r = self.timer_canvas_size - self.timer_pad
                self.timer_canvas.create_oval(l, l, r, r, outline="#3CB371", width=10, tags="progress")
            except Exception:
                pass

        frac = max(0.0, min(1.0, remaining / float(self.countdown_total)))
        extent = 360 * frac

        try:
            self.timer_canvas.delete("progress")
            l = self.timer_pad
            r = self.timer_canvas_size - self.timer_pad
            self.timer_canvas.create_arc(l, l, r, r, start=-90, extent=-extent, style="arc", width=10, outline="#FFA500", tags="progress")
            secs = int(math.ceil(remaining))
            self.timer_canvas.itemconfig(self.timer_text, text=str(secs))
        except Exception:
            pass

        try:
            self.countdown_job = self.after(50, self._animate_countdown)
        except Exception:
            self.countdown_active = False
            self.countdown_job = None

    def _cancel_countdown(self):
        if self.countdown_active:
            self.countdown_active = False
            if self.countdown_job:
                try:
                    self.after_cancel(self.countdown_job)
                except Exception:
                    pass
                self.countdown_job = None
            try:
                self.timer_canvas.itemconfig(self.timer_text, text=str(self.time_current))
                self.timer_canvas.delete("progress")
                l = self.timer_pad
                r = self.timer_canvas_size - self.timer_pad
                self.timer_canvas.create_oval(l, l, r, r, outline="#3CB371", width=10, tags="progress")
            except Exception:
                pass

    def reset_action(self):
        self.running = False
        try:
            self._cancel_countdown()
        except Exception:
            pass

        self.start_stop_button.configure(text="เริ่มต้น", fg_color=self.green_btn, hover_color=self.hover_green_bt)
        self.round = 0
        self.set = 0
        self.current_pose = 1
        self.timer_reset()
        self.update_text()
        self.update_round()

        try:
            self.play_sounds_sequential("008.mp3")
        except Exception as e:
            print(f"[reset_action] play sound error: {e}")

    def on_close(self):
        self.mp_running = False
        self.running = False
        try:
            if hasattr(self, "mp_thread") and self.mp_thread.is_alive():
                self.mp_thread.join(timeout=1.0)
        except Exception:
            pass
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        self.destroy()
        os._exit(0)
        
    def check_sensor_loop(self):
        if self.running:
            try:
                self.check_fingers()
            except Exception as e:
                pass

            if self.hand_posit == 5 and self.time_current > 0 and not self.still_hold:
                try:
                    self.time_current -= 1
                    self.update_timer()
                except Exception as e:
                    pass

                if self.time_current <= 0:
                    try:
                        delay_ms = int(getattr(self, "_timer_anim_duration", 1.0) * 1000) + 50
                        self.after(delay_ms, self._on_pose_success)
                    except Exception as e:
                        pass

        try:
            self.after(1000, self.check_sensor_loop)
        except Exception as e:
            pass

    def _on_pose_success(self):
        try:
            if self.time_current > 0:
                return
            self.write_log(f"ท่า{self.pose_name[self.current_pose]}สำเร็จ!")
        except Exception as e:
            print(f"[_on_pose_success] write_log error: {e}")

        self.current_pose += 1
        if self.current_pose > 5:
            self.current_pose = 1
            self.round += 1
            if self.round >= 10:
                self.round = 0
                self.set += 1

        try:
            self.update_round()
            self.timer_reset()
            self.update_EX_pose()
            self.update_text()
            sound_file = self.pose_sounds.get(self.current_pose, [None])[0]
            if sound_file:
                try:
                    self.play_sounds_sequential(sound_file)
                except Exception as e:
                    pass
        except Exception as e:
            pass

if __name__ == "__main__":
    app = AntiTriggerFingersApp()
    app.mainloop()