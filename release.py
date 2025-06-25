from PyQt5.QtWidgets import QCheckBox   # 导入复选框控件
from PyQt5.QtWidgets import QLineEdit  # 导入单行输入框控件
import sys  # 导入系统模块
import json  # 导入JSON模块用于配置文件读写
import threading  # 导入线程模块
import time  # 导入时间模块
import ctypes  # 导入ctypes用于权限检查
import os  # 导入操作系统模块
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                            QPushButton, QLabel, QTextEdit)  # 导入PyQt5控件
from PyQt5.QtCore import Qt, pyqtSignal  # 导入Qt核心模块和信号
from pynput import keyboard, mouse  # 导入pynput用于键盘鼠标监听
from pynput.mouse import Button as MouseButton  # 导入鼠标按钮类型
from pynput.keyboard import HotKey, Key  # 导入热键和按键类型
import pyautogui  # 导入pyautogui用于自动化操作
import pydirectinput  # 导入pyautogui用于模拟按键
import random  # 导入随机模块

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()  # 检查是否为管理员权限
    except:
        return False  # 检查失败时返回False

STAR_LEVELS = ["一星", "二星", "三星", "四星", "五星", "六星"]  # 星级选项列表
ACTION_TYPES = ["第一张", "第二张", "第三张", "第四张", "第五张"]  # 动作类型选项列表
TRIGGER_OPTIONS = ["未配置", "鼠标侧键1", "鼠标侧键2"]  # 触发键选项列表
DPS_IMAGE = 'dps.png'  # DPS检测图片文件名
DPS_REGION = (613, 141, 63, 12)  # DPS检测区域坐标
configuration='configuration.png'  # 配置确认图片文件名
configuration_region=(850, 760, 200, 40)  # 配置确认区域坐标
BOSS='Boss.png'  # BOSS检测图片文件名
BOSS_region=(1240, 780,200, 40)  # BOSS检测区域坐标

def random_delay():
    time.sleep(0.1)  # 随机延迟0.1秒

class MacroApp(QWidget):
    log_signal = pyqtSignal(str)  # 定义日志信号

    def __init__(self):
        super().__init__()  # 初始化父类
        self.card_state = False  # 初始化卡状态
        self.Card_statistic = 0
        self.Card_statistic_ed = 0
        self.config_path = "config.json"  # 配置文件路径
        self.config = self.load_config()  # 加载配置文件
        self._exec_lock = threading.Lock()  # 初始化线程锁
        self.shoot_event = threading.Event()  # 初始化自动开枪事件
        self.run_event = threading.Event()  # 初始化自动循环事件
        self.loop_event = threading.Event()  # 初始化DPS检测事件
        self.mouse_down = threading.Event()  # 初始化鼠标按下事件
        self.hotkeys = {}  # 初始化热键状态字典
        self.init_ui()  # 初始化界面
        self.setup_signals()  # 初始化信号与监听器
        self.resize(600, 700)  # 设置窗口大小
        self.setWindowTitle("放卡挂机V1.3")  # 设置窗口标题

    def setup_listeners(self):
        if hasattr(self, 'key_listener'):
            self.key_listener.stop()  # 停止已有键盘监听器
        self.key_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )  # 创建新的键盘监听器
        self.key_listener.start()  # 启动键盘监听器
        self.mouse_listener = None  # 初始化鼠标监听器为None
        if self.config.get("trigger", "").startswith("鼠标"):
            self.start_mouse_listener()  # 根据配置启动鼠标监听器

    def init_ui(self):
        layout = QVBoxLayout()  # 创建垂直布局
        self.cmb_star = self.create_combobox("星级选择:", STAR_LEVELS, "star")  # 创建星级下拉框
        self.cmb_type = self.create_combobox("动作类型:", ACTION_TYPES, "action_type")  # 创建动作类型下拉框
        self.cmb_trigger = self.create_combobox("触发键:", TRIGGER_OPTIONS, "trigger")  # 创建触发键下拉框
        button_layout = QHBoxLayout()  # 创建水平布局
        btn_save = QPushButton("保存配置", self)  # 创建保存按钮
        btn_save.clicked.connect(self.save_config)  # 绑定保存配置方法
        btn_restart = QPushButton("重启脚本", self)  # 创建重启按钮
        btn_restart.clicked.connect(self.restart_program)  # 绑定重启方法
        btn_restart.setStyleSheet("background-color: #ffcc00;")  # 设置按钮颜色
        #button_layout.addWidget(btn_save)  # 添加保存按钮到布局
        button_layout.addWidget(btn_restart)  # 添加重启按钮到布局
        self.NotShoot = QCheckBox("F11只插卡不开枪", self)  # 创建保持开火复选框
        checkbox_layout = QHBoxLayout()  # 创建复选框水平布局
        checkbox_layout.addWidget(self.NotShoot)  # 添加保持不开火复选框
        layout.addLayout(checkbox_layout)  # 添加复选框布局到主布局
        lbl_tip = QLabel("触发按键: 触发一次自动放卡\n•F9: 自动开枪模式\n•F11: 自动放卡自动开枪\n•F12: 检测到BOSS出来自动开枪\n ")  # 创建提示标签
        lbl_tip.setStyleSheet("color: #666; font-style: italic; padding: 8px 0;")  # 设置标签样式
        self.log = QTextEdit()  # 创建日志文本框
        self.log.setReadOnly(True)  # 设置日志只读
        self.log.setMaximumHeight(200)  # 设置日志最大高度
        layout.addLayout(button_layout)  # 添加按钮布局到主布局
        layout.addWidget(self.cmb_star)  # 添加星级下拉框
        layout.addWidget(self.cmb_type)  # 添加动作类型下拉框
        layout.addWidget(self.cmb_trigger)  # 添加触发键下拉框
        stat_layout = QHBoxLayout()
        lbl_stat = QLabel("放卡数量：")
        self.Statistics = QLineEdit(self)
        self.Statistics.setPlaceholderText("请输入放卡数量")
        self.Statistics.setText("1000")  # 设置默认内容为1000
        stat_layout.addWidget(lbl_stat)
        stat_layout.addWidget(self.Statistics)
        layout.addLayout(stat_layout)
        layout.addWidget(btn_save)  # 添加保存按钮
        layout.addWidget(lbl_tip)  # 添加提示标签
        layout.addWidget(QLabel("操作日志:"))  # 添加日志标签
        layout.addWidget(self.log)  # 添加日志文本框
        self.setLayout(layout)  # 设置主布局

    def create_combobox(self, label, items, config_key):
        container = QWidget()  # 创建容器控件
        layout = QVBoxLayout(container)  # 创建垂直布局
        layout.setContentsMargins(0, 0, 0, 0)  # 设置边距
        lbl = QLabel(label)  # 创建标签
        lbl.setStyleSheet("font-weight: bold;")  # 设置标签加粗
        layout.addWidget(lbl)  # 添加标签到布局
        combo = QComboBox()  # 创建下拉框
        combo.addItems(items)  # 添加选项
        if self.config.get(config_key):
            combo.setCurrentText(self.config[config_key])  # 设置默认值
        combo.setStyleSheet("QComboBox { padding: 2px; }")  # 设置下拉框样式
        layout.addWidget(combo)  # 添加下拉框到布局
        return container  # 返回容器
    
    def Value_Get(self):
        value_str = self.Statistics.text()  # 获取文本框内容（字符串）
        try:
            value = int(value_str)  # 转换为整数
        except ValueError:
            value = 0  # 转换失败时设为0或其他默认值
        return value  # 返回整数值
    

    def restart_program(self):
        self.log_signal.emit("[系统] 正在重新获取键盘鼠标监听权限...")  # 输出日志
        if hasattr(self, 'key_listener') and self.key_listener is not None:
            self.key_listener.stop()  # 停止键盘监听器
        if hasattr(self, 'mouse_listener') and self.mouse_listener is not None:
            self.mouse_listener.stop()  # 停止鼠标监听器
        self.setup_listeners()  # 重新设置监听器
        self.update_hotkey_state()  # 更新热键状态
        self.log_signal.emit("[系统] 键盘鼠标监听权限已重新获取，重启完成")  # 输出日志

    def setup_signals(self):
        self.log_signal.connect(self.log.append)  # 连接日志信号到日志框
        self.key_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )  # 创建键盘监听器
        self.key_listener.start()  # 启动键盘监听器
        self.mouse_listener = None  # 初始化鼠标监听器
        if self.config.get("trigger", "").startswith("鼠标"):
            self.start_mouse_listener()  # 根据配置启动鼠标监听器
        self.update_hotkey_state()  # 初始化热键状态

    def update_hotkey_state(self):
        trigger = self.config.get("trigger", "F1")  # 获取触发键配置
        if trigger == "未配置":
            self.hotkeys = {}  # 清空热键状态
        elif not trigger.startswith("鼠标"):
            parsed = self.parse_hotkey(trigger)  # 解析热键
            self.hotkeys = {k: False for k in HotKey.parse(parsed)}  # 初始化热键状态字典

    def on_key_press(self, key):
        try:
            if key == Key.f11:
                self.handle_f11()  # 处理F11按下
            elif key == Key.f12:
                self.handle_f12()  # 处理F12按下
            elif key == Key.f9:
                self.handl_f9()  # 处理F9按下
        except Exception as e:
            self.log_signal.emit(f"[错误] 按键处理异常: {str(e)}")  # 输出异常日志

    def on_key_release(self, key):
        try:
            self.check_trigger_hotkey(key, pressed=False)  # 检查热键释放
        except:
            pass  # 忽略异常

    def check_trigger_hotkey(self, key, pressed):
        trigger = self.config.get("trigger", "F1")  # 获取触发键配置
        if trigger == "未配置":
            return False  # 未配置时不处理
        if trigger.startswith("鼠标"):
            return False  # 鼠标触发时不处理
        key_str = self.get_key_str(key)  # 获取按键字符串
        parsed = self.parse_hotkey(trigger)  # 解析热键
        expected_keys = HotKey.parse(parsed)  # 获取热键列表
        for k in expected_keys:
            if key_str == k:
                self.hotkeys[k] = pressed  # 更新热键状态
        return False  # 返回False

    def get_key_str(self, key):
        if hasattr(key, 'name'):
            return key.name.lower()  # 功能键转小写
        elif hasattr(key, 'char'):
            return key.char.lower()  # 字符键转小写
        return str(key).lower().strip("'")  # 其他情况转字符串

    def parse_hotkey(self, key_str):
        parts = []
        for part in key_str.replace('+', ' ').split():
            if part.upper().startswith('F') and part[1:].isdigit():
                parts.append(f'<{part.lower()}>')  # 功能键格式化
            else:
                part = part.lower()
                if part in ['ctrl', 'shift', 'alt']:
                    parts.append(f'<{part}>')  # 修饰键格式化
                else:
                    parts.append(part)  # 普通键
        return '+'.join(parts)  # 返回拼接后的热键字符串

    def start_mouse_listener(self):
        if self.mouse_listener is not None:
            self.mouse_listener.stop()  # 停止已有鼠标监听器
        button = self.parse_mouse_button(self.config.get("trigger"))  # 获取鼠标按钮类型
        def on_click(x, y, btn, pressed):
            if pressed and btn == button:
                if not self._exec_lock.locked():
                    self.log_signal.emit(f"[触发] 检测到鼠标侧键")  # 输出触发日志
                    self.card_state = False  # 重置卡状态
                    self.Card_statistic_ed = 0  # 重置已放卡数量
                    threading.Thread(target=self.execute_sequence, daemon=True).start()  # 启动操作线程
        self.mouse_listener = mouse.Listener(on_click=on_click)  # 创建鼠标监听器
        self.mouse_listener.start()  # 启动鼠标监听器

    def parse_mouse_button(self, button_str):
        return {
            "鼠标侧键1": MouseButton.x1,
            "鼠标侧键2": MouseButton.x2,
        }.get(button_str, MouseButton.x1)  # 返回鼠标按钮对象

    def handle_f11(self):
        self.card_state = False  # 重置卡状态
        self.Card_statistic= self.Value_Get()  # 获取放卡数量
        self.Card_statistic_ed = 0 # 设置已放卡数量
        if self.loop_event.is_set():
            self.loop_event.clear()  # 退出DPS检测模式
            self.log_signal.emit("[系统] 已退出DPS检测模式")
        if self.shoot_event.is_set():
            self.shoot_event.clear()  # 退出自动开枪模式
            self.log_signal.emit("[系统] 已退出自动开枪模式")
        time.sleep(0.1)  # 状态切换延迟
        if not self.run_event.is_set():
            self.start_auto_cycle()  # 启动自动循环
        else:
            self.stop_auto_cycle()  # 停止自动循环

    def handle_f12(self):
        self.Card_statistic = 0  # 卡数量
        if self.run_event.is_set():
            self.run_event.clear()  # 退出自动循环模式
            self.log_signal.emit("[系统] 已退出自动循环模式")
        if self.shoot_event.is_set():
            self.shoot_event.clear()  # 退出自动开枪模式
            self.log_signal.emit("[系统] 已退出自动开枪模式")
        time.sleep(0.1)  # 状态切换延迟
        if not self.loop_event.is_set():
            self.start_detection_loop()  # 启动DPS检测循环
        else:
            self.stop_detection_loop()  # 停止DPS检测循环

    def handl_f9(self):
        if self.loop_event.is_set():
            self.loop_event.clear()  # 退出DPS检测模式
            self.log_signal.emit("[系统] 已退出DPS检测模式")
        if self.run_event.is_set():
            self.run_event.clear()  # 退出自动循环模式
            self.log_signal.emit("[系统] 已退出自动循环模式")
        time.sleep(0.1)  # 状态切换延迟
        if not self.shoot_event.is_set():
            self.shoot_event.set()  # 启动自动开枪
            threading.Thread(target=self.Shoot_Mode, daemon=True).start()
        else:
            self.shoot_event.clear()  # 停止自动开枪
            self.log_signal.emit("[系统] 已退出自动开枪模式")
            self._mouse_left_up()  

    def start_auto_cycle(self):
        self.run_event.set()  # 设置自动循环事件
        self.log_signal.emit("[系统] 自动循环启动")
        threading.Thread(target=self.auto_cycle_worker, daemon=True).start()  # 启动自动循环线程

    def stop_auto_cycle(self):
        self.run_event.clear()  # 清除自动循环事件
        self.log_signal.emit("[系统] 自动循环停止")

    def start_detection_loop(self):
        self.loop_event.set()  # 设置DPS检测事件
        self.log_signal.emit("[系统] DPS检测循环启动")
        threading.Thread(target=self.detection_loop_worker, daemon=True).start()  # 启动DPS检测线程

    def stop_detection_loop(self):
        self.loop_event.clear()  # 清除DPS检测事件
        self._mouse_left_up(force=True)  # 强制释放鼠标
        self.log_signal.emit("[系统] DPS检测循环停止")

    def Shoot_Mode(self):
        first_state = True  # 标记首次启动
        while self.shoot_event.is_set():
            try:
                self._mouse_left_down() 
                pyautogui.press('f')  # 按下F键
                if first_state:
                    first_state = False
                    self.log_signal.emit("[系统] 自动开枪模式已启动")
            except Exception as e:
                self.log_signal.emit(f"[错误] 自动开枪异常: {str(e)}")
                self.shoot_event.clear()
                self._mouse_left_up()  
    

    def auto_cycle_worker(self):
        last_dps_state = False  # 记录上一次DPS状态
        while self.run_event.is_set():
            try:
                    has_dps = self.check_image(DPS_IMAGE, DPS_REGION, 0.6)  # 检测DPS图片
                    if last_dps_state != has_dps:
                        if has_dps is False:
                            self._mouse_left_up()   # 释放鼠标左键
                            #pyautogui.keyUp('p')    # 释放P键
                            #self.log_signal.emit("[检测] DPS不存在，弹起鼠标并且执行放卡")
                            #self.log_signal.emit("执行一次换弹")
                            pydirectinput.press('r')
                            random_delay()
                            pydirectinput.press('r')
                            random_delay()
                            pydirectinput.press('r')
                            self.card_state = False
                            last_dps_state = has_dps
                    if has_dps:
                        if self.NotShoot.isChecked() is False:
                            self.handle_dps_found()  # 处理DPS存在
                        last_dps_state = has_dps
                    else:
                        last_dps_state = has_dps
                        con_png = self.check_image(configuration, configuration_region, 0.6)
                        if con_png:
                            self.safe_click(960, 785, "确认")  # 点击确认
                        self.handle_no_dps()  # 处理DPS不存在
                        
                            
            except Exception as e:
                self.log_signal.emit(f"[错误] 循环异常: {str(e)}")
                self.stop_auto_cycle()

    def detection_loop_worker(self):
        last_has_dps = False  # 记录上一次DPS状态
        while self.loop_event.is_set():
            try:
                current_has_dps = self.check_image(DPS_IMAGE, DPS_REGION,0.6)  # 检测DPS图片
                if current_has_dps != last_has_dps:
                    if current_has_dps:
                        #self.log_signal.emit("DPS检测到，按下鼠标")
                        self._mouse_left_down() 
                    else:
                        self._mouse_left_up()  
                        #self.log_signal.emit("DPS未检测到，抬起鼠标")
                        #self.log_signal.emit("执行一次换弹")
                        pydirectinput.press('r')
                        random_delay()
                        pydirectinput.press('r')
                        random_delay()
                        pydirectinput.press('r')
                        self.Card_statistic +=1
                        self.log_signal.emit(f"吃到{self.Card_statistic}张卡")
                    last_has_dps = current_has_dps
                if not current_has_dps:
                    con_png = self.check_image(configuration, configuration_region,0.3)
                    if con_png:
                        self.safe_click(960, 785, "确认")
            except Exception as e:
                self.log_signal.emit(f"[错误] 检测循环异常: {str(e)}")
                self.stop_detection_loop()

    def handle_dps_found(self):
        self._mouse_left_down()  # 按下鼠标左键
        #pyautogui.keyDown('p')  
        #pyautogui.press('f')  # 按下F键

    def handle_no_dps(self):
        if self.mouse_down.is_set():
            self._mouse_left_up()  # 释放鼠标左键
        if self._exec_lock.acquire(blocking=False):
            try:
                self.execute_sequence()  # 执行操作序列
            finally:
                self._exec_lock.release()  # 释放锁

    def interruptible_sleep(self, duration):
        start = time.time()
        while time.time() - start < duration:
            if not self.run_event.is_set():
                return False  # 检查事件是否被清除
            random_delay()
        return True  # 完成等待

    def _mouse_left_down(self):
        if not self.mouse_down.is_set():
            try:
                #pyautogui.keyDown('p')  # 按下p键
                pyautogui.mouseDown(button='left')  # 按下鼠标左键
                self.mouse_down.set()  # 设置鼠标按下事件
                #self.log_signal.emit("[操作] 鼠标按下")
            except Exception as e:
                self.log_signal.emit(f"[错误] 按下失败: {str(e)}")

    def _mouse_left_up(self, force=False):
        if force or self.mouse_down.is_set():
            try:
                pyautogui.mouseUp(button='left')  # 释放鼠标左键
                #pyautogui.keyUp('p')  # 按下p键
                self.mouse_down.clear()  # 清除鼠标按下事件
                #self.log_signal.emit("[操作] 鼠标释放")
            except Exception as e:
                self.log_signal.emit(f"[错误] 释放失败: {str(e)}")

    def check_image(self,Image,Region,confid):
        try:
            return pyautogui.locateOnScreen(
                Image,
                region=Region,
                confidence=confid,
                grayscale=True
            ) is not None  # 检测屏幕指定区域图片
        except Exception as e:
            return False  # 检测异常返回False

    def execute_sequence(self):
        try:
            if self.card_state  is False:
                #self.log_signal.emit("[操作] 开始执行序列")
                has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)
                if has_dps:
                    return
                pyautogui.press('e')
                random_delay()
                BOSS_png = self.check_image(BOSS,BOSS_region,0.6)
                if BOSS_png:
                    #self.log_signal.emit("触发召唤面板")
                    has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)
                    if has_dps:
                        return
                    star_index = STAR_LEVELS.index(self.cmb_star.findChild(QComboBox).currentText())
                    self.safe_click(590 + star_index * 150, 367, "星级")
                    has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)
                    if has_dps:
                        return
                    type_index = ACTION_TYPES.index(self.cmb_type.findChild(QComboBox).currentText())
                    self.safe_click(630 + type_index * 200, 540, "类型")
                    has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)
                    if has_dps:
                        return
                    BOSS_png = self.check_image(BOSS,BOSS_region,0.6)
                    if BOSS_png:
                        time.sleep(0.1)  # 等待0.5秒
                        BOSS_png = self.check_image(BOSS,BOSS_region,0.6)
                        if BOSS_png:
                            if self.Card_statistic_ed < self.Card_statistic:
                                self.safe_click(1326, 804, "确认")
                                self.card_state  = True
                                self.Card_statistic_ed += 1  # 增加已放卡数量
                                self.log_signal.emit(f"[操作] 放卡完成，当前已放卡数量: {self.Card_statistic_ed}/{self.Card_statistic}")
                            else:
                                self.log_signal.emit("[操作] 已放卡数量达到目标，停止循环")
                                self.stop_auto_cycle()
                    has_dps = self.check_image(DPS_IMAGE,DPS_REGION,0.3)
                    if has_dps:
                        return
        except Exception as e:
            self.log_signal.emit(f"[错误] 执行失败: {str(e)}")
            self.run_event.clear()

    def safe_click(self, x, y, label):
        try:
            pyautogui.moveTo(x, y, duration=0.01)  # 移动鼠标到指定坐标
            pyautogui.click()  # 点击鼠标
            #self.log_signal.emit(f"[操作] 点击 {label}({x},{y})")
        except Exception as e:
            self.log_signal.emit(f"[错误] 点击失败: {str(e)}")
            raise

    def save_config(self):
        old_trigger = self.config.get("trigger", "")  # 获取旧触发键配置
        self.config = {
            "star": self.cmb_star.findChild(QComboBox).currentText(),
            "action_type": self.cmb_type.findChild(QComboBox).currentText(),
            "trigger": self.cmb_trigger.findChild(QComboBox).currentText()
        }  # 保存当前配置
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)  # 写入配置文件
            self.log_signal.emit("[系统] 配置已保存")
            if self.config["trigger"] != old_trigger:
                if self.config["trigger"] == "未配置":
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
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)  # 读取配置文件
        except:
            return {}  # 读取失败返回空字典

    def closeEvent(self, event):
        self.run_event.clear()  # 停止自动循环
        self.loop_event.clear()  # 停止DPS检测
        self._mouse_left_up(force=True)  # 强制释放鼠标
        if hasattr(self, 'key_listener') and self.key_listener is not None:
            self.key_listener.stop()  # 停止键盘监听器
        if hasattr(self, 'mouse_listener') and self.mouse_listener is not None:
            self.mouse_listener.stop()  # 停止鼠标监听器
        event.accept()  # 接受关闭事件

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()  # 检查并请求管理员权限
    app = QApplication(sys.argv)  # 创建应用实例
    window = MacroApp()  # 创建主窗口
    window.show()  # 显示窗口
    sys.exit(app.exec_())  # 运行应用主循环
