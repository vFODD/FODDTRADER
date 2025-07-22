import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import threading
import datetime
import re
import os
import json
import decimal
import time
import asyncio
import sys
import ctypes
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
from binance.client import Client
from telethon import TelegramClient, events

channel_username = -1002871674544

class SignalBotApp:
    def handle_error(self, msg):
        self.is_running = False
        self._animation_active = False
        self.log(msg)
        self.update_status("hata")
        self.start_btn.config(state=tk.NORMAL, text="Başlat", font=("Segoe UI", 11, "bold"))
        self.stop_btn.config(state=tk.DISABLED)
        self.set_entries_state("normal")
        self.root.update()

    def set_entries_state(self, state):
        self.binance_key_entry.config(state=state)
        self.binance_secret_entry.config(state=state)
        self.tg_id_entry.config(state=state)
        self.tg_hash_entry.config(state=state)
        self.tg_phone_entry.config(state=state)

    def cleanup_orphan_orders(self):
        while True:
            try:
                open_orders = self.client.futures_get_open_orders()
                positions = self.client.futures_position_information()
                active_positions = {(p['symbol'], p['positionSide']): float(p['positionAmt']) for p in positions}
                for o in open_orders:
                    if o['type'] in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']:
                        key = (o['symbol'], o['positionSide'])
                        if active_positions.get(key, 0) == 0:
                            try:
                                self.client.futures_cancel_order(symbol=o['symbol'], orderId=o['orderId'])
                            except Exception as e:
                                pass
            except Exception as e:
                self.log(f"Otomatik emir kontrol hatası: {e}")
            time.sleep(3600)
    def start_btn_anim(self):
        if not self.is_running or not getattr(self, '_animation_active', False):
            self.start_btn.config(text="Başlat", font=("Segoe UI", 11, "bold"))
            return
        self._anim_counter = getattr(self, '_anim_counter', 0) + 1
        num = (self._anim_counter % 15) + 1
        text = '.' * num
        self.start_btn.config(text=text, font=("Segoe UI", 11, "bold"))
        self.root.after(2000, self.start_btn_anim)

    def __init__(self, root):
        self.root = root
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        session_file = os.path.join(self.base_dir, 'user.session')
        self.locked = os.path.exists(session_file)
        try:
            icon_path = resource_path("v2.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        self.root.title("FODDTRADER")
        self.root.configure(bg="#23272f")
        self.config_path = os.path.join(self.base_dir, "user.config")
        self.session_path = os.path.join(self.base_dir, "user.session")
        window_width = 700
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        self._cleanup_thread_started = False
        def on_closing():
            self.stop_bot()
            self.root.destroy()
        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        top_bar = tk.Frame(root, bg="#00b894", height=50)
        top_bar.pack(fill="x")
        logo = tk.Label(top_bar, text="⚡", font=("Segoe UI", 18), bg="#00b894", fg="white")
        logo.pack(side="left", padx=(15,5), pady=5)
        app_title = tk.Label(top_bar, text="FODDv2 (PRO)", font=("Segoe UI", 16, "bold"), bg="#00b894", fg="white")
        app_title.pack(side="left", padx=5, pady=5)

        risk_frame = tk.Frame(top_bar, bg="#00b894")
        risk_frame.pack(side="right", padx=15, pady=5)
        self.risk_level = tk.StringVar(value="medium")
        self.risk_info = {
            "low": ("🧱", "[0.1x - 1x] Dinamik Kaldıraç", "Her işlemde bakiyenizin %10'u ile işlem açılır."),
            "medium": ("⚖️", "[0.5x - 5x] Dinamik Kaldıraç", "Her işlemde bakiyenizin %50'si ile işlem açılır."),
            "high": ("🔥", "[1x - 10x] Dinamik Kaldıraç", "Her işlemde bakiyenizin %100'ü ile işlem açılır.")
        }
        def set_risk(level):
            if low_btn['state'] == tk.DISABLED:
                return
            self.risk_level.set(level)
            for btn, val in zip([low_btn, med_btn, high_btn], ["low", "medium", "high"]):
                if self.risk_level.get() == val:
                    btn.config(bg="#f4f8f7", fg="#00b894", highlightbackground="#b2dfd8", highlightcolor="#b2dfd8", bd=1, font=("Segoe UI", 10, "normal"))
                else:
                    btn.config(bg="#23272f", fg="#b2bec3", highlightbackground="#2d3436", highlightcolor="#2d3436", bd=0, font=("Segoe UI", 10, "normal"))
            emoji, bold_text, rest = self.risk_info[level]
            self.status_emoji_label.config(text=emoji)
            self.status_bold_label.config(text=bold_text)
            self.status_rest_label.config(text=": " + rest)

        def on_risk_enter(e):
            e.widget.config(bg="#3b3b3b")
        def on_risk_leave(e):
            level = None
            if e.widget == low_btn:
                level = "low"
            elif e.widget == med_btn:
                level = "medium"
            elif e.widget == high_btn:
                level = "high"
            if self.risk_level.get() == level:
                e.widget.config(bg="#f4f8f7")
            else:
                e.widget.config(bg="#23272f")

        style = {"font": ("Segoe UI", 10), "width": 16, "relief": "flat", "cursor": "hand2", "bd": 0, "highlightthickness": 1, "pady": 4, "padx": 3}
        low_btn = tk.Button(risk_frame, text="🧱 Low Risk", command=lambda: set_risk("low"), bg="#23272f", fg="#b2bec3", **style)
        med_btn = tk.Button(risk_frame, text="⚖️ Medium Risk", command=lambda: set_risk("medium"), bg="#f4f8f7", fg="#00b894", **style)
        high_btn = tk.Button(risk_frame, text="🔥 High Risk", command=lambda: set_risk("high"), bg="#23272f", fg="#b2bec3", **style)
        for btn in [low_btn, med_btn, high_btn]:
            btn.bind("<Enter>", on_risk_enter)
            btn.bind("<Leave>", on_risk_leave)
        def set_risk_buttons_state(state):
            low_btn.config(state=state)
            med_btn.config(state=state)
            high_btn.config(state=state)
        self.set_risk_buttons_state = set_risk_buttons_state
        low_btn.pack(side="left", padx=2)
        med_btn.pack(side="left", padx=2)
        high_btn.pack(side="left", padx=2)
        main_frame = tk.Frame(root, bg="#23272f")
        main_frame.pack(pady=(20,0), padx=20, fill="both", expand=True)

        self.status_bar_frame = tk.Frame(main_frame, bg="#23272f")
        self.status_bar_frame.pack(fill="x", pady=(0, 15))
        self.status_emoji_label = tk.Label(self.status_bar_frame, text=self.risk_info["medium"][0], font=("Segoe UI", 12), fg="#00b894", bg="#23272f", anchor="w")
        self.status_emoji_label.pack(side="left")
        self.status_bold_label = tk.Label(self.status_bar_frame, text=self.risk_info["medium"][1], font=("Segoe UI", 12, "bold"), fg="#00b894", bg="#23272f", anchor="w")
        self.status_bold_label.pack(side="left")
        self.status_rest_label = tk.Label(self.status_bar_frame, text=": " + self.risk_info["medium"][2], font=("Segoe UI", 12), fg="#00b894", bg="#23272f", anchor="w")
        self.status_rest_label.pack(side="left")

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(main_frame, textvariable=self.status_var, font=("Segoe UI", 11), fg="#00b894", bg="#23272f", anchor="w")
        self.status_label.pack(fill="x", pady=(0, 5))

        form_box = tk.Frame(main_frame, bg="#2d3436", bd=2, relief="groove")
        form_box.pack(pady=5, padx=10)

        def show_telegram_info():
            info = (
                "Telegram API ID ve API Hash Nasıl Alınır?\n\n"
                "1. https://my.telegram.org adresine gidin.\n"
                "2. Telegram hesabınızla giriş yapın (telefon numaranızı +90xxx şeklinde girin, Telegram’dan gelen kodu yazın).\n"
                "3. Giriş yaptıktan sonra 'API development tools' bölümüne tıklayın.\n"
                "4. 'Create new application' butonuna tıklayın.\n"
                "5. Uygulama adı ve kısa bir açıklama girin.\n"
                "6. 'Create application' butonuna basın.\n"
                "7. Açılan sayfada API ID ve API Hash bilgilerinizi göreceksiniz.\n"
                "8. Bu bilgileri kopyalayıp programa girin."
            )
            messagebox.showinfo("Telegram API Bilgisi", info)

        def add_entry(row, label, width, var, placeholder, icon=None, info_button=False):
            if icon:
                tk.Label(form_box, text=icon, font=("Segoe UI", 12), bg="#2d3436", fg="#00b894").grid(row=row, column=0, padx=(10,2), pady=7)
                col = 1
            else:
                col = 0
            label_widget = tk.Label(form_box, text=label, font=("Segoe UI", 10), fg="#dfe6e9", bg="#2d3436")
            label_widget.grid(row=row, column=col, sticky="w", padx=5, pady=7)
            if info_button:
                info_btn = tk.Button(form_box, text="API ID ve HASH ALMA", font=("Segoe UI", 8, "bold"), width=22, height=1, bg="#636e72", fg="white", relief="flat", cursor="hand2", command=show_telegram_info)
                info_btn.grid(row=row, column=col+1, padx=(112,10), pady=7, sticky="w")
            validate_cmd = None
            if label.startswith("Telegram Telefon"):
                def validate_phone(P):
                    return len(P) <= 10 and P.isdigit() or P == ""
                validate_cmd = form_box.register(validate_phone)
                entry = tk.Entry(form_box, width=width, font=("Segoe UI", 10), textvariable=var, relief="flat", bg="#23272f", fg="#dfe6e9", insertbackground="#dfe6e9", validate="key", validatecommand=(validate_cmd, '%P'))
            else:
                entry = tk.Entry(form_box, width=width, font=("Segoe UI", 10), textvariable=var, relief="flat", bg="#23272f", fg="#dfe6e9", insertbackground="#dfe6e9")
            entry.grid(row=row, column=col+1, padx=5, pady=7, sticky="w")
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda e: entry.delete(0, tk.END) if entry.get()==placeholder else None)
            entry.bind("<FocusOut>", lambda e: entry.insert(0, placeholder) if entry.get()=='' else None)
            return entry

        self.binance_key_var = tk.StringVar()
        self.binance_secret_var = tk.StringVar()
        self.tg_id_var = tk.StringVar()
        self.tg_hash_var = tk.StringVar()
        self.tg_phone_var = tk.StringVar()

        self.config_data = None
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.config_data = config
                self.tg_id_var.set(str(config.get("tg_id", "")))
                self.tg_hash_var.set(config.get("tg_hash", ""))
                self.tg_phone_var.set(config.get("tg_phone", ""))
            except Exception:
                self.config_data = None

        self.binance_key_entry = add_entry(0, "Binance API Key:", 40, self.binance_key_var, "API Key", "🔑")
        self.binance_secret_entry = add_entry(1, "Binance API Secret:", 40, self.binance_secret_var, "Secret Key", "🔒")
        self.tg_id_entry = add_entry(2, "Telegram API ID:", 10, self.tg_id_var, "API ID", "🆔", info_button=True)
        self.tg_hash_entry = add_entry(3, "Telegram API Hash:", 32, self.tg_hash_var, "API Hash", "#")
        self.tg_phone_entry = add_entry(4, "Telegram Telefon (535xxxxxxx):", 12, self.tg_phone_var, "535xxxxxxxx", "📱")

        if self.config_data:
            for i in [2, 3, 4]:
                for widget in form_box.grid_slaves(row=i):
                    widget.grid_remove()
            self.binance_key_entry.config(state="normal")
            self.binance_secret_entry.config(state="normal")

        btn_frame = tk.Frame(main_frame, bg="#23272f")
        btn_frame.pack(pady=15)
        self.start_btn = tk.Button(btn_frame, text="Başlat", command=self.start_bot, font=("Segoe UI", 11, "bold"), bg="#00b894", fg="white", activebackground="#00cec9", activeforeground="white", relief="flat", width=12, bd=0, cursor="hand2")
        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn = tk.Button(btn_frame, text="Durdur", command=self.stop_bot, state=tk.DISABLED, font=("Segoe UI", 11, "bold"), bg="#636e72", fg="white", activebackground="#b2bec3", activeforeground="white", relief="flat", width=12, bd=0, cursor="hand2")
        self.stop_btn.grid(row=0, column=1, padx=10)
        self.set_risk_buttons_state(tk.NORMAL)

        def on_enter(e): e.widget.config(bg="#00cec9")
        def on_leave(e): e.widget.config(bg="#00b894")
        self.start_btn.bind("<Enter>", on_enter)
        self.start_btn.bind("<Leave>", on_leave)

        def on_enter2(e): e.widget.config(bg="#b2bec3")
        def on_leave2(e): e.widget.config(bg="#636e72")
        self.stop_btn.bind("<Enter>", on_enter2)
        self.stop_btn.bind("<Leave>", on_leave2)

        log_frame = tk.LabelFrame(main_frame, text="Loglar", font=("Segoe UI", 10, "bold"), fg="#00b894", bg="#23272f", bd=2)
        log_frame.pack(padx=10, pady=(0, 15), fill="both", expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, width=80, height=14, state='disabled', font=("Consolas", 10), bg="#1e2127", fg="#dfe6e9", relief="flat", bd=2, highlightbackground="#00b894", highlightcolor="#00b894")
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.is_running = False
        self.tg_client = None
        self.client = None
    def save_config(self, tg_id, tg_hash, tg_phone):
        config = {
            "tg_id": tg_id,
            "tg_hash": tg_hash,
            "tg_phone": tg_phone
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def log(self, msg):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"{datetime.datetime.now().strftime('%H:%M:%S')} - {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
    def update_status(self, durum):
        if durum == "giris":
            self.status_var.set("✅ Giriş başarılı. Program başlatıldı.")
        elif durum == "sinyal":
            self._sinyal_anim_counter = 0
            self.sinyal_animasyon()
        elif durum == "durdur":
            self.status_var.set("⏹️ Durduruldu.")
        elif durum == "hata":
            self.status_var.set("Hata oluştu!")
        else:
            self.status_var.set(durum)

    def sinyal_animasyon(self):
        if not self.is_running:
            return
        emoji = "🔄"
        nokta_sayisi = (self._sinyal_anim_counter % 4) + 1
        self.status_var.set(f"{emoji} Sinyal bekleniyor{'.' * nokta_sayisi}")
        self._sinyal_anim_counter += 1
        self.root.after(2000, self.sinyal_animasyon)

    def start_bot(self):
        self._telegram_stop_event = threading.Event()
        binance_key = self.binance_key_var.get().strip()
        binance_secret = self.binance_secret_var.get().strip()
        self.is_running = False
        self._animation_active = False
        self.status_var.set("")
        self.update_status("Bağlantı başlatılıyor...")
        self.root.update()

        def validate_fields():
            tg_id = self.tg_id_var.get().strip() if hasattr(self, 'tg_id_var') else ""
            tg_hash = self.tg_hash_var.get().strip() if hasattr(self, 'tg_hash_var') else ""
            tg_phone = self.tg_phone_var.get().strip() if hasattr(self, 'tg_phone_var') else ""
            if (binance_key in ["", "API Key"] or
                binance_secret in ["", "Secret Key"] or
                tg_id in ["", "API ID"] or
                tg_hash in ["", "API Hash"] or
                tg_phone in ["", "5XXXXXXXXX"]):
                self.handle_error("Tüm alanları doldurunuz!")
                messagebox.showerror("Hata", "Tüm alanları doldurunuz!")
                return False, None, None, None
            try:
                tg_id_int = int(tg_id)
            except ValueError:
                self.handle_error("Telegram API ID alanı sayısal olmalıdır!")
                messagebox.showerror("Hata", "Telegram API ID alanı sayısal olmalıdır!")
                return False, None, None, None
            if tg_phone.startswith('0'):
                tg_phone = tg_phone[1:]
            if not tg_phone.startswith('+90'):
                tg_phone = '+90' + tg_phone
            return True, tg_id_int, tg_hash, tg_phone

        def after_telegram_success(new_session_flag, loop=None):
            async def save_session_if_authorized():
                try:
                    self.save_config(self.tg_id, self.tg_hash, self.tg_phone)
                    if hasattr(self, 'tg_client') and self.tg_client is not None:
                        is_auth = False
                        try:
                            is_auth = await self.tg_client.is_user_authorized()
                        except Exception as e:
                            self.log(f"Yetkilendirme kontrolü hatası: {e}")
                        if is_auth:
                            session_obj = getattr(self.tg_client, 'session', None)
                            if session_obj is not None:
                                try:
                                    session_obj.save()
                                except Exception as e:
                                    self.log(f"Session kaydedilemedi: {e}")
                            else:
                                self.log("Session nesnesi bulunamadı, kaydedilemedi.")
                        else:
                            self.log("Session kaydedilmedi: Telegram yetkilendirme başarısız.")
                    for i in [2, 3, 4]:
                        for widget in self.tg_id_entry.master.grid_slaves(row=i):
                            widget.grid_remove()
                    self.set_entries_state("normal")
                except Exception as e:
                    self.log(f"Config dosyası kaydedilemedi: {e}")

            if new_session_flag and loop is not None:
                try:
                    loop.run_until_complete(save_session_if_authorized())
                except Exception as e:
                    self.log(f"Session kaydetme coroutine hatası: {e}")
            if (new_session_flag or self.config_data) and self.client is not None:
                self.is_running = True
                self._animation_active = True
                self.set_risk_buttons_state(tk.DISABLED)
                self.start_btn_anim()
                self.update_status("giris")
                self.root.update()
                self.update_status("sinyal")
                self.root.update()
                self.binance_key_entry.config(state="disabled")
                self.binance_secret_entry.config(state="disabled")
                if not self._cleanup_thread_started:
                    threading.Thread(target=self.cleanup_orphan_orders, daemon=True).start()
                    self._cleanup_thread_started = True
            else:
                self.set_risk_buttons_state(tk.NORMAL)
                self.handle_error("Bağlantı başlatılamadı.")

        def binance_test():
            try:
                client = Client(self.binance_key, self.binance_secret)
                client.futures_account_balance()
                self.client = client
                self.run_bot(after_telegram_success)
            except Exception as e:
                self.root.after(0, lambda e=e: self.handle_error(f"Binance bağlantı hatası: {e}"))

        if self.config_data:
            self.binance_key = binance_key
            self.binance_secret = binance_secret
            self.tg_id = self.config_data.get("tg_id")
            self.tg_hash = self.config_data.get("tg_hash")
            self.tg_phone = self.config_data.get("tg_phone")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            if binance_key in ["", "API Key"] or binance_secret in ["", "Secret Key"]:
                self.handle_error("Binance API Key ve Secret alanlarını doldurunuz!")
                messagebox.showerror("Hata", "Binance API Key ve Secret alanlarını doldurunuz!")
                return
            threading.Thread(target=binance_test, daemon=True).start()
            return

        valid, tg_id_int, tg_hash, tg_phone = validate_fields()
        if not valid:
            return
        self.binance_key = binance_key
        self.binance_secret = binance_secret
        self.tg_id = tg_id_int
        self.tg_hash = tg_hash
        self.tg_phone = tg_phone
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=binance_test, daemon=True).start()

    def stop_bot(self):
        self.set_risk_buttons_state(tk.NORMAL)
        if not self.is_running:
            self.log("⛔ Bot zaten durdurulmuş.")
            return

        self.is_running = False
        self._animation_active = False
        self.start_btn.config(state=tk.NORMAL, text="Başlat", font=("Segoe UI", 11, "bold"))
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("durdur")
        self.log("⛔ Bot durduruldu.")
        self.set_entries_state("normal")

        if hasattr(self, '_telegram_stop_event'):
            self._telegram_stop_event.set()

        async def disconnect_and_save():
            if self.tg_client:
                if getattr(self.tg_client, '_state', None) and not self.tg_client._state.is_disconnected():
                    await self.tg_client.disconnect()
                if hasattr(self.tg_client, 'session') and self.tg_client.session:
                    try:
                        self.tg_client.session.save()
                        self.locked = True
                    except Exception:
                        pass
                self.tg_client = None

        def run_async_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(disconnect_and_save())
                loop.close()
            except Exception as e:
                self.log(f"Async stop hatası: {e}")

        threading.Thread(target=run_async_task, daemon=True).start()

    def run_bot(self, after_telegram_success, loop=None, stop_event=None):
        def telegram_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self.tg_client = TelegramClient(os.path.join(self.base_dir, 'user'), self.tg_id, self.tg_hash)

                @self.tg_client.on(events.NewMessage(chats=channel_username))
                async def handler(event):
                    signal = self.parse_signal(event.raw_text)
                    if signal:
                        self.open_position(signal)

                code_callback = None
                self._new_session_flag = False

                def ask_code():
                    self._new_session_flag = True
                    code_holder = {'code': None}
                    def get_code():
                        code_holder['code'] = simpledialog.askstring("Telegram Doğrulama", "Telegram'dan gelen kodu giriniz:")
                    self.root.after(0, get_code)
                    while code_holder['code'] is None:
                        self.root.update()
                    if code_holder['code'] is None or code_holder['code'].strip() == "":
                        self.handle_error("Telegram doğrulama kodu girilmedi, bağlantı iptal edildi.")
                        raise Exception("Telegram doğrulama kodu girilmedi.")
                    return code_holder['code']

                if not self.locked:
                    code_callback = ask_code
                    try:
                        self.tg_client.start(phone=self.tg_phone, code_callback=code_callback)
                    except Exception as e:
                        self.handle_error("Telegram doğrulama kodu girilmediği için bağlantı iptal edildi.")
                        return
                else:
                    self.tg_client.start(phone=self.tg_phone)

                is_authorized = loop.run_until_complete(self.tg_client.is_user_authorized())

                if (not self.locked and not self._new_session_flag) or not is_authorized:
                    self.handle_error("Telegram giriş hatası: Yetkilendirme başarısız.")
                    after_telegram_success(False, loop)
                    return

                self.log_area.config(state='normal')
                self.log_area.delete('1.0', tk.END)
                self.log_area.config(state='disabled')
                self.log("⚡ Program başlatıldı. Sinyal gelince işleme girecek..")
                after_telegram_success(self._new_session_flag if not self.locked else True, loop)

                try:
                    loop.run_until_complete(self.tg_client.run_until_disconnected())
                except Exception as e:
                    self.log(f"⚠️ Telegram bağlantısı sonlandırılırken hata oluştu: {e}")

            except Exception as e:
                error_str = str(e)
                if (
                    "Cannot find any entity corresponding to" in error_str or
                    "The user is not a participant" in error_str or
                    "not a participant" in error_str or
                    "CHANNEL_PRIVATE" in error_str or
                    "CHAT_WRITE_FORBIDDEN" in error_str
                ):
                    self.handle_error("Aboneliğiniz sona erdi. Lütfen aboneliğinizi yenileyin.")
                    messagebox.showerror("Abonelik Hatası", "Aboneliğiniz sona erdi. Lütfen aboneliğinizi yenileyin.")
                else:
                    self.handle_error("❌ Telegram hata")
                    self.log("Yeniden bağlanma denenecek...")
                    time.sleep(10)
            finally:
                try:
                    loop.close()
                except:
                    pass

        threading.Thread(target=telegram_thread, daemon=True).start()

    def parse_signal(self, text):
        try:
            first_line = text.split('\n')[0]
            symbol_match = re.search(r'([A-Z0-9]+USDT)', first_line)
            if not symbol_match:
                return None
            symbol = symbol_match.group(1)
            side = "LONG" if "LONG" in first_line else "SHORT" if "SHORT" in first_line else None
            if not side:
                return None
            entry_match = re.search(r'Entry:\s*([\d.]+)', text)
            sl_match = re.search(r'SL:\s*([\d.]+)', text)
            tp_match = re.search(r'TP:\s*([\d.]+)', text)
            entry = float(entry_match.group(1)) if entry_match else None
            sl = float(sl_match.group(1)) if sl_match else None
            tp = float(tp_match.group(1)) if tp_match else None
            def get_decimals(s):
                if s and '.' in s:
                    return len(s.split('.')[-1])
                return 0
            entry_dec = get_decimals(entry_match.group(1)) if entry_match else 0
            sl_dec = get_decimals(sl_match.group(1)) if sl_match else 0
            tp_dec = get_decimals(tp_match.group(1)) if tp_match else 0
            return {
                'symbol': symbol,
                'side': side,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'entry_dec': entry_dec,
                'sl_dec': sl_dec,
                'tp_dec': tp_dec
            }
        except:
            return None

    def open_position(self, signal):
        symbol = signal['symbol']
        side = signal['side']
        order_side = 'BUY' if side == 'LONG' else 'SELL'
        try:
            info = self.client.futures_exchange_info()
            symbol_info = next((s for s in info['symbols'] if s['symbol'] == symbol), None)
            if not symbol_info:
                self.log(f"Sembol bilgisi bulunamadı: {symbol}")
                return
            risk = getattr(self, 'risk_level', None)
            risk_val = risk.get() if risk else 'high'
            if risk_val == 'low':
                leverage = 1
                balance_factor = 0.10
            elif risk_val == 'medium':
                leverage = 5
                balance_factor = 0.5
            else:
                leverage = 10
                balance_factor = 1.0
            try:
                self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            except Exception as e:
                pass
            step_size = symbol_info['filters'][2]['stepSize']
            min_qty = float(symbol_info['filters'][2]['minQty'])

            balance_info = self.client.futures_account_balance()
            usdt_balance = next((float(b['balance']) for b in balance_info if b['asset'] == 'USDT'), 0)
            price_info = self.client.futures_symbol_ticker(symbol=symbol)
            last_price = float(price_info['price'])
            quantity = (usdt_balance * balance_factor * leverage) / last_price
            step_size_decimal = decimal.Decimal(step_size)
            quantity_decimal = decimal.Decimal(str(quantity)).quantize(step_size_decimal, rounding=decimal.ROUND_DOWN)
            quantity = max(float(quantity_decimal), min_qty)

            sl = signal.get('sl')
            tp = signal.get('tp')
            entry = signal.get('entry')
            emoji = '🟢' if side == 'LONG' else '🔴'
            entry_dec = signal.get('entry_dec', 2)
            sl_dec = signal.get('sl_dec', 2)
            tp_dec = signal.get('tp_dec', 2)
            log_line = f"{emoji} {symbol} {side} | Entry: {entry:.{entry_dec}f} | Risk: {risk_val.title()}"
            if sl is not None:
                log_line += f" | SL: {sl:.{sl_dec}f}"
            if tp is not None:
                log_line += f" | TP: {tp:.{tp_dec}f}"
            self.log(log_line)

            def create_exit_order(order_type, price, exit_side):
                try:
                    self.client.futures_create_order(
                        symbol=symbol,
                        side=exit_side,
                        type=order_type,
                        stopPrice=price,
                        quantity=quantity,
                        positionSide=side
                    )
                except Exception as e:
                    self.log(f"{order_type} emri hatası: {e}")

            try:
                self.client.futures_create_order(
                    symbol=symbol,
                    side=order_side,
                    type='MARKET',
                    quantity=quantity,
                    positionSide=side
                )
            except Exception as e:
                self.log(f"Pozisyon açma hatası: {e}")
            if sl:
                sl_side = 'SELL' if order_side == 'BUY' else 'BUY'
                create_exit_order('STOP_MARKET', sl, sl_side)
            if tp:
                tp_side = 'SELL' if order_side == 'BUY' else 'BUY'
                create_exit_order('TAKE_PROFIT_MARKET', tp, tp_side)
        except Exception as e:
            self.log(f"Hata oluştu: {e}")

def already_running():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, 1, "FODDTRADER_UNIQUE_MUTEX")
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:
        return True
    return False

if already_running():
    messagebox.showerror("Uygulama zaten açık", "FODDTRADER zaten çalışıyor!")
    sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = SignalBotApp(root)
    root.mainloop()