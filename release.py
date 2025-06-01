"""
穿越火线试炼岛）
更新说明：
1. F12改为控制循环检测模式（检测到DPS自动按住鼠标）
2. 移除原有鼠标保持模式
3. 新增循环检测线程
4. 优化模式互斥逻辑
"""
from PyQt5.QtWidgets import QCheckBox
import sys
import json
import threading
import time
import ctypes
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                            QPushButton, QLabel, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from pynput import keyboard, mouse
from pynput.mouse import Button as MouseButton
from pynput.keyboard import HotKey, Key
import pyautogui
import pydirectinput

# 管理员权限检查函数
def is_admin():
    """检查程序是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 常量定义
STAR_LEVELS = ["一星", "二星", "三星", "四星", "五星", "六星"]  # 星级选项
ACTION_TYPES = ["第一张", "第二张", "第三张", "第四张", "第五张"]  # 动作类型选项
TRIGGER_OPTIONS = ["未配置", "鼠标侧键1", "鼠标侧键2"]  # 触发键选项
DPS_IMAGE = 'dps.png'  # DPS检测用图片文件名
DPS_REGION = (613, 141, 63, 12)  # DPS检测区域(x, y, width, height)
configuration='configuration.png'
configuration_region=(850, 760, 200, 40) #区域
R5='5.png'
R5_region=(944, 432, 21, 6) #区域

# 主应用类
class MacroApp(QWidget):
    log_signal = pyqtSignal(str)  # 日志信号
    
    def __init__(self):
        """类初始化构造函数"""
        super().__init__()
        
        # 配置文件路径
        self.config_path = "config.json"
        
        # 加载配置
        self.config = self.load_config()
        
        # 线程锁（保证操作序列的原子性）
        self._exec_lock = threading.Lock()
        
        # 状态控制事件
        self.shoot_event = threading.Event() 
        self.run_event = threading.Event()         # 自动循环运行标志
        self.loop_event = threading.Event()       # DPS检测循环标志（新增）
        self.mouse_down = threading.Event()        # 鼠标左键按下状态
        
        # 热键状态跟踪字典
        self.hotkeys = {}

        # 初始化UI
        self.init_ui()
        
        # 设置信号与监听器
        self.setup_signals()
        
        # 窗口设置
        self.resize(600, 700)
        self.setWindowTitle("放卡挂机V1.3")

    # ------------------------- UI初始化部分 -------------------------
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()

        # 创建下拉选择框
        self.cmb_star = self.create_combobox("星级选择:", STAR_LEVELS, "star")
        self.cmb_type = self.create_combobox("动作类型:", ACTION_TYPES, "action_type")
        self.cmb_trigger = self.create_combobox("触发键:", TRIGGER_OPTIONS, "trigger")
        
        # 保存按钮
        btn_save = QPushButton("保存配置", self)
        btn_save.clicked.connect(self.save_config)
        self.hold_left_btn_check = QCheckBox("放一次卡之后保持开火", self)
        self.F11_only_release = QCheckBox("F11纯放卡", self)
        #self.R5 = QCheckBox("检测5换弹", self)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.hold_left_btn_check)
        checkbox_layout.addWidget(self.F11_only_release)
        #checkbox_layout.addWidget(self.R5)
        layout.addLayout(checkbox_layout)
        # 操作提示标签
        lbl_tip = QLabel("触发按键: 触发一次自动放卡\n•F9: 自动开枪模式\n•F11: 自动放卡自动开枪\n•F12: 检测到BOSS出来自动开枪\n ")
        lbl_tip.setStyleSheet("color: #666; font-style: italic; padding: 8px 0;")

        # 日志显示框
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(200)

        # 布局管理
        layout.addWidget(self.cmb_star)
        layout.addWidget(self.cmb_type)
        layout.addWidget(self.cmb_trigger)
        layout.addWidget(btn_save)
        layout.addWidget(lbl_tip)
        layout.addWidget(QLabel("操作日志:"))
        layout.addWidget(self.log)
        self.setLayout(layout)

    def create_combobox(self, label, items, config_key):
        """创建统一风格的下拉选择框"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)
        
        # 下拉框
        combo = QComboBox()
        combo.addItems(items)
        if self.config.get(config_key):
            combo.setCurrentText(self.config[config_key])
        combo.setStyleSheet("QComboBox { padding: 2px; }")
        layout.addWidget(combo)
        
        return container

    # ------------------------- 信号与监听部分 -------------------------
    def setup_signals(self):
        """初始化信号连接和输入监听器"""
        # 连接日志信号
        self.log_signal.connect(self.log.append)
        
        # 初始化键盘监听器
        self.key_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.key_listener.start()
        
        # 按需初始化鼠标监听器
        self.mouse_listener = None
        if self.config.get("trigger", "").startswith("鼠标"):
            self.start_mouse_listener()
        
        # 初始化热键状态跟踪
        self.update_hotkey_state()

    def update_hotkey_state(self):
        """初始化热键状态跟踪字典"""
        trigger = self.config.get("trigger", "F1")
        if not trigger.startswith("鼠标"):
            parsed = self.parse_hotkey(trigger)
            self.hotkeys = {k: False for k in HotKey.parse(parsed)}

    # ------------------------- 输入处理部分 -------------------------
    def on_key_press(self, key):
        """键盘按下事件处理"""
        try:
            # 处理全局功能键
            if key == Key.f11:
                self.handle_f11()
            elif key == Key.f12:
                self.handle_f12()
            elif key == Key.f9:
                self.handl_f9()
            
            # 处理用户配置的触发键
            self.check_trigger_hotkey(key, pressed=True)
            
        except Exception as e:
            self.log_signal.emit(f"[错误] 按键处理异常: {str(e)}")

    def on_key_release(self, key):
        """键盘释放事件处理"""
        try:
            self.check_trigger_hotkey(key, pressed=False)
        except:
            pass

    def check_trigger_hotkey(self, key, pressed):
        """
        检查并更新触发键状态
        :param key: 按键对象
        :param pressed: 按下/释放状态
        :return: 是否触发操作
        """
        trigger = self.config.get("trigger", "F1")
        
        # 新增未配置判断
        if trigger == "未配置":
            return False  # 未配置时直接返回不处理
        
        if trigger.startswith("鼠标"):
            return False

        key_str = self.get_key_str(key)
        parsed = self.parse_hotkey(trigger)
        expected_keys = HotKey.parse(parsed)

        # 更新按键状态字典
        for k in expected_keys:
            if key_str == k:
                self.hotkeys[k] = pressed

        # 检查所有需要按键是否都处于按下状态
        if all(self.hotkeys.get(k, False) for k in expected_keys):
            if pressed and not self._exec_lock.locked():
                self.log_signal.emit(f"[触发] 检测到热键 {trigger}")
                threading.Thread(target=self.execute_sequence, daemon=True).start()
            return True
        return False

    # 修改update_hotkey_state方法（在信号与监听部分）
    def update_hotkey_state(self):
        """初始化热键状态跟踪字典"""
        trigger = self.config.get("trigger", "F1")
        if trigger == "未配置":
            self.hotkeys = {}  # 清空热键状态
        elif not trigger.startswith("鼠标"):
            parsed = self.parse_hotkey(trigger)
            self.hotkeys = {k: False for k in HotKey.parse(parsed)}

    def get_key_str(self, key):
        """将按键转换为标准化字符串"""
        if hasattr(key, 'name'):    # 处理功能键（如F1、Ctrl等）
            return key.name.lower()
        elif hasattr(key, 'char'):  # 处理普通字符键
            return key.char.lower()
        return str(key).lower().strip("'")

    def parse_hotkey(self, key_str):
        """解析热键字符串为pynput可识别格式"""
        parts = []
        for part in key_str.replace('+', ' ').split():
            # 处理功能键（F1-F12）
            if part.upper().startswith('F') and part[1:].isdigit():
                parts.append(f'<{part.lower()}>')
            # 处理修饰键
            else:
                part = part.lower()
                if part in ['ctrl', 'shift', 'alt']:
                    parts.append(f'<{part}>')
                else:
                    parts.append(part)
        return '+'.join(parts)

    # ------------------------- 鼠标监听部分 -------------------------
    def start_mouse_listener(self):
        """启动鼠标侧键监听器"""
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        button = self.parse_mouse_button(self.config.get("trigger"))
        
        def on_click(x, y, btn, pressed):
            """鼠标点击事件回调"""
            if pressed and btn == button:
                if not self._exec_lock.locked():
                    self.log_signal.emit(f"[触发] 检测到鼠标侧键")
                    threading.Thread(target=self.execute_sequence, daemon=True).start()
        
        # 创建并启动监听器
        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.mouse_listener.start()

    def parse_mouse_button(self, button_str):
        """将配置字符串转换为鼠标按钮对象"""
        return {
            "鼠标侧键1": MouseButton.x1,
            "鼠标侧键2": MouseButton.x2,
        }.get(button_str, MouseButton.x1)

    # ------------------------- 功能模式控制 -------------------------
    def handle_f11(self):
        """F11键处理：切换自动循环模式"""
        # 停止冲突模式
        if self.loop_event.is_set():
            self.loop_event.clear()
            self.log_signal.emit("[系统] 已退出DPS检测模式")

        if self.shoot_event.is_set():
            self.shoot_event.clear()
            self.log_signal.emit("[系统] 已退出自动开枪模式")
        time.sleep(0.1)  # 确保状态切换稳定
        
        # 切换自动循环状态
        if not self.run_event.is_set():
            self.start_auto_cycle()
        else:
            self.stop_auto_cycle()

    def handle_f12(self):
        """F12键处理：切换DPS检测循环模式"""
        # 停止冲突模式
        if self.run_event.is_set():
            self.run_event.clear()
            self.log_signal.emit("[系统] 已退出自动循环模式")
        if self.shoot_event.is_set():
            self.shoot_event.clear()
            self.log_signal.emit("[系统] 已退出自动开枪模式")
        time.sleep(0.1)  # 确保状态切换稳定
        # 切换检测循环状态
        if not self.loop_event.is_set():
            self.start_detection_loop()
        else:
            self.stop_detection_loop()

    def handl_f9(self):
        """F9键处理：切换自动开枪状态"""
        if self.loop_event.is_set():
            self.loop_event.clear()
            self.log_signal.emit("[系统] 已退出DPS检测模式")
        if self.run_event.is_set():
            self.run_event.clear()
            self.log_signal.emit("[系统] 已退出自动循环模式")
        time.sleep(0.1)  # 确保状态切换稳定
        if not self.shoot_event.is_set():
            self.shoot_event.set()
            self.log_signal.emit("[系统] 自动开枪模式启动")
            threading.Thread(target=self.Shoot_Mode, daemon=True).start()
        else:
            self.shoot_event.clear()
            pyautogui.mouseUp(button='left')

    def start_auto_cycle(self):
        """启动自动循环模式"""
        self.run_event.set()
        self.log_signal.emit("[系统] 自动循环启动")
        threading.Thread(target=self.auto_cycle_worker, daemon=True).start()

    def stop_auto_cycle(self):
        """停止自动循环模式"""
        self.run_event.clear()
        self.log_signal.emit("[系统] 自动循环停止")

    def start_detection_loop(self):
        """启动DPS检测循环"""
        self.loop_event.set()
        self.log_signal.emit("[系统] DPS检测循环启动")
        threading.Thread(target=self.detection_loop_worker, daemon=True).start()

    def stop_detection_loop(self):
        """停止DPS检测循环"""
        self.loop_event.clear()
        self._mouse_left_up(force=True)  # 确保释放鼠标
        self.log_signal.emit("[系统] DPS检测循环停止")

    def Shoot_Mode(self):
        """自动开枪模式工作线程"""
        while self.shoot_event.is_set():
            first_state = True  
            try:
                pyautogui.mouseDown(button='left')
                pydirectinput.press('f')
                if first_state:
                    first_state = False
                    self.log_signal.emit("[系统] 自动开枪模式已启动")
            except Exception as e:
                self.log_signal.emit(f"[错误] 自动开枪异常: {str(e)}")
                self.shoot_event.clear()
                pyautogui.mouseUp(button='left')

            #time.sleep(0.1)  # 控制开枪频率
               
    # ------------------------- 自动循环逻辑 -------------------------
    def auto_cycle_worker(self):
        """自动循环工作线程"""
        last_dps_state = None  # 记录上一次的DPS状态
        
        while self.run_event.is_set():
            try:
                if self.F11_only_release.isChecked():
                    self.log_signal.emit("[操作] 纯放卡开始")
                    # 如果F11纯放卡选项被选中，直接释放鼠标
                    pyautogui.press('e')
                    time.sleep(0.1)
                    # 步骤3：选择星级
                    star_index = STAR_LEVELS.index(self.cmb_star.findChild(QComboBox).currentText())
                    self.safe_click(590 + star_index * 150, 367, "星级")
                    # 步骤4：选择动作类型
                    type_index = ACTION_TYPES.index(self.cmb_type.findChild(QComboBox).currentText())
                    self.safe_click(630 + type_index * 200, 540, "类型")
                    # 步骤5：确认操作
                    self.safe_click(1326, 804, "确认")
                    self.log_signal.emit("[操作] 纯放卡执行完成")
                
                else:
                    # DPS检测
                    has_dps = self.check_image(DPS_IMAGE, DPS_REGION, 0.6)
                    
                    # 只在DPS状态变化时打印日志
                    if last_dps_state is None:
                        # 首次检测
                        if has_dps:
                            self.log_signal.emit("[检测] DPS已存在，按下鼠标")
                        else:
                            self.log_signal.emit("[检测] DPS不存在，弹起鼠标并且执行放卡")
                        last_dps_state = has_dps
                    elif last_dps_state != has_dps:
                        # 状态发生变化
                        if has_dps:
                            self.log_signal.emit("[检测] DPS已存在，按下鼠标")
                        else:
                            pyautogui.mouseUp(button='left')
                            self.log_signal.emit("[检测] DPS不存在，弹起鼠标并且执行放卡")
                            self.log_signal.emit("执行一次换弹")
                            pydirectinput.press('r')
                            time.sleep(0.1)  # 确保鼠标释放稳定
                            pydirectinput.press('r')
                            time.sleep(0.1)  # 确保换弹稳定
                            pydirectinput.press('r')
                        last_dps_state = has_dps
                    
                    # 根据检测结果处理
                    if has_dps:
                        self.handle_dps_found()
                    else:
                        # if self.R5.isChecked():
                        #     # 检测5换弹
                        #     has_r5 = self.check_image(R5, R5_region, 0.3)
                        #     if has_r5:
                        #         self.log_signal.emit("[检测] 执行换弹")
                        #         pydirectinput.press('r')
                        #     con_png = self.check_image(configuration, configuration_region, 0.3)
                        #     if con_png:
                        #         self.safe_click(960, 785, "确认")
                        # else:
                        con_png = self.check_image(configuration, configuration_region, 0.3)
                        if con_png:
                            self.safe_click(960, 785, "确认")
                        #pydirectinput.press('r')
                        self.handle_no_dps()
                
                # 可中断的等待
                # self.interruptible_sleep(0.01)
                
            except Exception as e:
                self.log_signal.emit(f"[错误] 循环异常: {str(e)}")
                self.stop_auto_cycle()

    def detection_loop_worker(self):
        """DPS检测循环工作线程"""
        last_has_dps = None  # 用于记录上一次的DPS状态
        while self.loop_event.is_set():
            try:
                current_has_dps = self.check_image(DPS_IMAGE, DPS_REGION,0.6)
            
                # 仅在状态变化时操作并打印log
                if current_has_dps != last_has_dps:
                    if current_has_dps:
                        self.log_signal.emit("DPS检测到，按下鼠标")
                        pyautogui.mouseDown(button='left')
                    else:
                        pyautogui.mouseUp(button='left')
                        self.log_signal.emit("DPS未检测到，抬起鼠标")
                        self.log_signal.emit("执行一次换弹")
                        pydirectinput.press('r')
                        time.sleep(0.1)  # 确保鼠标释放稳定
                        pydirectinput.press('r') 
                        time.sleep(0.1)  # 确保换弹稳定
                        pydirectinput.press('r')
                    last_has_dps = current_has_dps  # 更新状态记录
                
                # 检测确认按钮图片
                if not current_has_dps:
                        con_png = self.check_image(configuration, configuration_region,0.3)
                        if con_png:
                            self.safe_click(960, 785, "确认")
                            #pydirectinput.press('r')

            except Exception as e:
                    self.log_signal.emit(f"[错误] 检测循环异常: {str(e)}")
                    self.stop_detection_loop()

    def handle_dps_found(self):
        """发现DPS时的处理逻辑"""
        self._mouse_left_down()
        pydirectinput.press('f')

    def handle_no_dps(self):
        """未发现DPS时的处理逻辑"""
        #self.log_signal.emit("[检测] DPS不存在")
        if self.mouse_down.is_set():
            self._mouse_left_up()
        
        # 执行操作序列
        if self._exec_lock.acquire(blocking=False):
            try:
                self.execute_sequence()
            finally:
                self._exec_lock.release()

    def interruptible_sleep(self, duration):
        """
        可中断的延时函数
        :param duration: 目标等待时间（秒）
        :return: 是否完成完整等待
        """
        start = time.time()
        while time.time() - start < duration:
            if not self.run_event.is_set():
                return False
            time.sleep(0.05)
        return True

    # ------------------------- 鼠标控制 -------------------------
    def _mouse_left_down(self):
        """模拟鼠标左键按下"""
        if not self.mouse_down.is_set():
            try:
                pyautogui.mouseDown(button='left')
                self.mouse_down.set()
                self.log_signal.emit("[操作] 鼠标按下")
            except Exception as e:
                self.log_signal.emit(f"[错误] 按下失败: {str(e)}")

    def _mouse_left_up(self, force=False):
        """模拟鼠标左键释放"""
        if force or self.mouse_down.is_set():
            try:
                pyautogui.mouseUp(button='left')
                self.mouse_down.clear()
                self.log_signal.emit("[操作] 鼠标释放")
            except Exception as e:
                self.log_signal.emit(f"[错误] 释放失败: {str(e)}")

    # ------------------------- 图像检测 -------------------------
    def check_image(self,Image,Region,confid):
        """使用pyautogui进行屏幕截图检测"""
        try:
            return pyautogui.locateOnScreen(
                Image,
                region=Region,
                confidence=confid,    # 匹配置信度阈值
                grayscale=True     # 灰度匹配提升性能
            ) is not None
        except Exception as e:
            #self.log_signal.emit(f"[警告] 检测异常: {str(e)}")
            
            return False

    # ------------------------- 操作序列执行 -------------------------
    def execute_sequence(self):
        """执行预定义的操作序列"""
        try:
            self.log_signal.emit("[操作] 开始执行序列")
            has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)   
            if has_dps:
                return
            # 步骤2：发送E键
            pyautogui.press('e')
            time.sleep(0.1)
            has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)   
            if has_dps:
                return
            # 步骤3：选择星级
            star_index = STAR_LEVELS.index(self.cmb_star.findChild(QComboBox).currentText())
            self.safe_click(590 + star_index * 150, 367, "星级")
            has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)   
            if has_dps:
                return
            # 步骤4：选择动作类型
            type_index = ACTION_TYPES.index(self.cmb_type.findChild(QComboBox).currentText())
            self.safe_click(630 + type_index * 200, 540, "类型")
            has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)   
            if has_dps:
                return
            # 步骤5：确认操作
            self.safe_click(1326, 804, "确认")
            has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)   
            if has_dps:
                return
            self.log_signal.emit("[操作] 序列执行完成")
            if self.hold_left_btn_check.isChecked():
                self.log_signal.emit("[操作] 检测到保持左键选项，触发按下")
                pyautogui.mouseDown(button='left')
            
        except Exception as e:
            self.log_signal.emit(f"[错误] 执行失败: {str(e)}")
            self.run_event.clear()

    def safe_click(self, x, y, label):
        """
        安全的鼠标点击操作
        :param x: 目标X坐标
        :param y: 目标Y坐标
        :param label: 操作标识（用于日志）
        """
        try:
            #original_pos = pyautogui.position()  # 保存原始位置
            pyautogui.moveTo(x, y, duration=0.1) # 缓慢移动防止检测
            pyautogui.click()
            #pyautogui.moveTo(original_pos, duration=0.1)  # 返回原位
            self.log_signal.emit(f"[操作] 点击 {label}({x},{y})")
        except Exception as e:
            self.log_signal.emit(f"[错误] 点击失败: {str(e)}")
            raise

    # ------------------------- 配置管理 -------------------------
    def save_config(self):
        """保存当前配置到文件"""
        old_trigger = self.config.get("trigger", "")
        self.config = {
            "star": self.cmb_star.findChild(QComboBox).currentText(),
            "action_type": self.cmb_type.findChild(QComboBox).currentText(),
            "trigger": self.cmb_trigger.findChild(QComboBox).currentText()
        }
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.log_signal.emit("[系统] 配置已保存")
            
            # 监听器更新逻辑
            if self.config["trigger"] != old_trigger:
                if self.config["trigger"] == "未配置":
                    # 停止所有监听器
                    if self.mouse_listener:
                        self.mouse_listener.stop()
                    self.key_listener.stop()
                elif self.config["trigger"].startswith("鼠标"):
                    self.start_mouse_listener()
                    self.key_listener.stop()
                else:
                    if self.mouse_listener:
                        self.mouse_listener.stop()
                    self.key_listener = keyboard.Listener(
                        on_press=self.on_key_press,
                        on_release=self.on_key_release
                    )
                    self.key_listener.start()
                self.update_hotkey_state()
                
        except Exception as e:
            self.log_signal.emit(f"[错误] 保存失败: {str(e)}")

    def load_config(self):
        """从文件加载配置"""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except:
            return {}

    # ------------------------- 窗口事件 -------------------------
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 停止所有运行状态
        self.run_event.clear()
        self.loop_event.clear()
        self._mouse_left_up(force=True)
        
        # 停止监听器
        if self.key_listener:
            self.key_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        event.accept()

# ------------------------- 主程序入口 -------------------------
if __name__ == "__main__":
    # 检查管理员权限
    if not is_admin():
        # 请求管理员权限
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    
    # 创建应用实例
    app = QApplication(sys.argv)
    window = MacroApp()
    window.show()
    sys.exit(app.exec_())