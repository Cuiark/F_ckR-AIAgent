#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QMetaType

from gui.screens.start_screen import StartScreen
from gui.screens.main_screen import MainScreen
import queue

# 全局变量，用于存储主窗口实例
_main_window = None

def get_main_window():
    """获取主窗口实例"""
    global _main_window
    return _main_window

# 全局决策队列
decision_queue = queue.Queue()

def get_decision_queue():
    """获取全局决策队列"""
    global decision_queue
    return decision_queue

# 检查app.py中的决策队列处理

def put_decision(decision):
    """将决策放入队列"""
    global decision_queue
    try:
        # 确保队列存在
        if decision_queue is None:
            from queue import Queue
            decision_queue = Queue()
        
        # 清空队列中的旧决策（如果有）
        while not decision_queue.empty():
            try:
                decision_queue.get_nowait()
            except:
                break
        
        # 放入新决策
        decision_queue.put(decision)
        print(f"DEBUG: 决策已放入队列: {decision}")
        
        # 处理事件，确保UI更新
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        return True
    except Exception as e:
        print(f"ERROR: 放入决策时出错: {str(e)}")
        return False

def get_decision(timeout=300):
    """从队列中获取决策，带超时"""
    global decision_queue
    try:
        # 确保队列存在
        if decision_queue is None:
            from queue import Queue
            decision_queue = Queue()
        
        # 等待决策，带超时
        import time
        start_time = time.time()
        
        while True:
            try:
                # 尝试获取决策，不阻塞
                decision = decision_queue.get_nowait()
                print(f"DEBUG: 获取到决策: {decision}")
                return decision
            except:
                # 检查是否超时
                if time.time() - start_time > timeout:
                    print(f"DEBUG: 获取决策超时({timeout}秒)")
                    return {"status": "timeout"}
                
                # 处理事件，确保UI响应
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)
    except Exception as e:
        print(f"ERROR: 获取决策时出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # 确保返回一个有效的决策对象，而不是None
        return {"status": "error", "message": str(e)}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置全局变量，确保get_main_window函数可以访问
        global _main_window
        _main_window = self
        
        self.setWindowTitle("AI-Agent 应急响应系统")
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(QIcon(QPixmap(1, 1)))
        central_widget = QStackedWidget()
        self.setCentralWidget(central_widget)
        self.start_screen = StartScreen(central_widget)
        self.main_screen = MainScreen(central_widget)
        central_widget.addWidget(self.start_screen)
        central_widget.addWidget(self.main_screen)
        central_widget.setCurrentWidget(self.start_screen)

    def show_main_screen(self):
        self.centralWidget().setCurrentWidget(self.main_screen)

def main():
    # 注册QTextCursor类型，解决警告 - 使用不同的方法
    try:
        # 尝试使用 PyQt5 5.12+ 的方法
        QMetaType.registerType("QTextCursor")
    except (AttributeError, TypeError):
        # 如果上面的方法失败，可能是较旧版本的 PyQt5
        # 在这种情况下，我们可以跳过注册，因为大多数情况下
        # PyQt5 会自动处理常见类型
        print("警告: 无法注册 QTextCursor 类型，可能会导致一些警告")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

