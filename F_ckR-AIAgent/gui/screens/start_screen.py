from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient
from PyQt5.QtCore import Qt, QTimer
import random
import math

# 流动多边形类
class FlowingPolygon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.points = []
        self.lines = []
        self.dots = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)  # 50ms更新一次
        self.init_polygon()
        
    def init_polygon(self):
        # 创建多边形的顶点
        center_x, center_y = self.width() // 2, self.height() // 2
        radius = min(self.width(), self.height()) // 3
        num_points = 8  # 八边形
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.points.append({'x': x, 'y': y, 'dx': random.uniform(-1, 1), 'dy': random.uniform(-1, 1)})
        
        # 创建内部连线
        for i in range(num_points):
            for j in range(i+2, num_points):
                if j != (i+1) % num_points:  # 避免相邻点连线
                    self.lines.append((i, j))
        
        # 创建动态点
        for _ in range(15):  # 15个动态点
            x = random.uniform(center_x - radius, center_x + radius)
            y = random.uniform(center_y - radius, center_y + radius)
            self.dots.append({'x': x, 'y': y, 'dx': random.uniform(-2, 2), 'dy': random.uniform(-2, 2)})
    
    def update_animation(self):
        # 更新顶点位置
        for point in self.points:
            point['x'] += point['dx']
            point['y'] += point['dy']
            
            # 边界检查和反弹
            if point['x'] < 0 or point['x'] > self.width():
                point['dx'] *= -1
            if point['y'] < 0 or point['y'] > self.height():
                point['dy'] *= -1
        
        # 更新动态点位置
        for dot in self.dots:
            dot['x'] += dot['dx']
            dot['y'] += dot['dy']
            
            # 边界检查和反弹
            if dot['x'] < 0 or dot['x'] > self.width():
                dot['dx'] *= -1
            if dot['y'] < 0 or dot['y'] > self.height():
                dot['dy'] *= -1
        
        self.update()  # 触发重绘
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制连线
        pen = QPen(QColor(255, 255, 255, 100))
        pen.setWidth(1)
        painter.setPen(pen)
        
        for line in self.lines:
            i, j = line
            painter.drawLine(
                int(self.points[i]['x']), int(self.points[i]['y']),
                int(self.points[j]['x']), int(self.points[j]['y'])
            )
        
        # 绘制顶点
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        
        for point in self.points:
            painter.drawEllipse(int(point['x']) - 3, int(point['y']) - 3, 6, 6)
        
        # 绘制动态点
        painter.setBrush(QBrush(QColor(255, 255, 255, 150)))
        
        for dot in self.dots:
            painter.drawEllipse(int(dot['x']) - 2, int(dot['y']) - 2, 4, 4)

# 开始界面
class StartScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建一个空白区域，使多边形居中
        spacer_top = QWidget()
        spacer_top.setMinimumHeight(50)
        layout.addWidget(spacer_top)
        
        # 创建中心容器，用于放置流动多边形
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setAlignment(Qt.AlignCenter)
        
        # 创建流动多边形并放置在中心
        self.polygon = FlowingPolygon(self)
        center_layout.addWidget(self.polygon)
        layout.addWidget(center_container, 1)  # 1表示拉伸因子
        
        # 添加提示文本
        hint_label = QLabel("点击任意处开始", self)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(hint_label)
        layout.addSpacing(30)  # 在底部添加一些空间
        
        # 设置背景渐变色
        self.setAutoFillBackground(True)
        p = self.palette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(41, 128, 185))  # 浅蓝色
        gradient.setColorAt(1.0, QColor(44, 62, 80))    # 深蓝色
        p.setBrush(self.backgroundRole(), QBrush(gradient))
        self.setPalette(p)
    
    def mousePressEvent(self, event):
        # 点击任意处触发切换到主界面
        # 查找MainWindow父窗口
        main_window = self.window()
        if hasattr(main_window, 'show_main_screen'):
            main_window.show_main_screen()
        else:
            print("无法找到show_main_screen方法")