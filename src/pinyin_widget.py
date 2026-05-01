from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QApplication, QPushButton, QSizeGrip, QSizePolicy
)

from PyQt5.QtCore import Qt, QPoint, QTimer, QSize
from PyQt5.QtGui import QPainter, QBrush, QColor, QIcon
from pypinyin import pinyin, Style
import sys
import requests

DEEPL_API_KEY = '9e3bdca8-87b4-4288-852b-54f35829b72b:fx'  # 替换成你的真实 DeepL API 密钥


class PinyinWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_always_on_top = True
        self.is_maximized = False
        self.is_translate_on = False 
        self.is_pin_on = False
        self.old_pos = self.pos()
        self.current_font_size = 28
        self.translate_mode = 0  # 0: 不翻译，1: 英语 + 法语
        self.use_heteronym = False  # 多音字默认不启用
        self.translate_timer = QTimer()
        self.translate_timer.setInterval(3000)  # 3 秒
        self.translate_timer.setSingleShot(True)
        self.translate_timer.timeout.connect(self.handle_delayed_translation)
        self.initUI()

    def initUI(self):

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 240)

        # 顶部按钮
        self.btn_pin = QPushButton()
        self.btn_pin.setIcon(QIcon("icons/pin-off.png"))
        self.btn_pin.clicked.connect(self.toggle_pin)

        self.btn_translate = QPushButton()
        self.btn_translate.setIcon(QIcon("icons/translate-off.png"))
        self.btn_translate.clicked.connect(self.toggle_translate)

        btn_font = QPushButton()
        btn_font.setIcon(QIcon("icons/font-size.png"))

        btn_heteronym = QPushButton('多')

        btn_minimize = QPushButton()
        btn_minimize.setIcon(QIcon("icons/minimize.png"))
      

        btn_maximize = QPushButton()
        btn_maximize.setIcon(QIcon("icons/maximize.png"))
      

        btn_close = QPushButton()
        btn_close.setIcon(QIcon("icons/close.png"))
        
        

        for btn in [self.btn_pin, btn_font, self.btn_translate, btn_heteronym, btn_minimize, btn_maximize, btn_close]:
            btn.setFixedSize(32, 32)
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: #e3e3e3;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #cccccc;
                }
            """)

        btn_minimize.clicked.connect(self.showMinimized)
        btn_maximize.clicked.connect(self.toggle_maximize)
        btn_font.clicked.connect(self.toggle_font_size)
        btn_heteronym.clicked.connect(self.toggle_heteronym)
        btn_close.clicked.connect(self.close)

        # 顶部栏

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        for btn in [self.btn_pin, btn_font, self.btn_translate, btn_heteronym, btn_minimize, btn_maximize, btn_close]:
            top_bar.addWidget(btn)
        top_bar.setSpacing(6)
        top_bar.setContentsMargins(10, 0, 10, 0)

        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("background-color: #e3e3e3; border-top-left-radius: 15px; border-top-right-radius: 15px;")
        self.title_bar.setContentsMargins(0, 0, 0, 0)
        self.title_bar_layout = QVBoxLayout(self.title_bar)
        self.title_bar_layout.addLayout(top_bar)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.title_bar_layout.setSpacing(0)

        # 输入输出区域
        self.input = QTextEdit()
        self.input.setPlaceholderText("请输入中文…")
        self.input.setFixedHeight(80)  
        self.input.setLineWrapMode(QTextEdit.WidgetWidth)  # 自动换行
        self.input.textChanged.connect(self.convert_to_pinyin)

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.translation_output = QTextEdit()
        self.translation_output.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.title_bar)
        layout.addWidget(self.input)
        layout.addWidget(self.output)
        layout.addWidget(self.translation_output)
        layout.addWidget(QSizeGrip(self), alignment=Qt.AlignBottom | Qt.AlignRight)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self.apply_font_size()

    def convert_to_pinyin(self):
        text = self.input.toPlainText()

        result = pinyin(text, style=Style.TONE, heteronym=self.use_heteronym)
        output_text = ' '.join('/'.join(p_list) for p_list in result)
        self.output.setText(output_text)
        self.translate_timer.start()  # 每次输入重启计时器

    def handle_delayed_translation(self):
        text = self.input.toPlainText()

        self.update_translation(text)

    def update_translation(self, text):
        if not text or self.translate_mode == 0:
            self.translation_output.clear()
            return
        translated = []
        translated.append("[EN] " + self.translate_text(text, 'EN'))
        translated.append("[FR] " + self.translate_text(text, 'FR'))
        self.translation_output.setText('\n'.join(translated))

    def translate_text(self, text, target_lang):
        url = 'https://api-free.deepl.com/v2/translate'
        data = {
            'auth_key': DEEPL_API_KEY,
            'text': text,
            'target_lang': target_lang
        }
        try:
            response = requests.post(url, data=data)
            result = response.json()
            return result['translations'][0]['text']
        except Exception as e:
            return f"Error: {e}"

    def toggle_font_size(self):
        sizes = [28, 30, 32, 34]
        idx = sizes.index(self.current_font_size)
        self.current_font_size = sizes[(idx + 1) % len(sizes)]
        self.apply_font_size()

    def apply_font_size(self):
        style = f"font-size: {self.current_font_size}px;"
        self.input.setStyleSheet(style)
        self.output.setStyleSheet(style)
        self.translation_output.setStyleSheet(style)

    
    def toggle_pin(self):
        self.is_pin_on = not self.is_pin_on
        icon_path = "icons/pin-on.png" if self.is_pin_on else "icons/pin-off.png"
        self.btn_pin.setIcon(QIcon(icon_path))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.is_pin_on)
        self.show()

    def toggle_translate(self):
    # 每次按下，在“关闭”与“翻译成英文和法文”间切换
        self.translate_mode = 1 if self.translate_mode == 0 else 0
        icon_path = "icons/translate-on.png" if self.translate_mode == 1 else "icons/translate-off.png"
        self.btn_translate.setIcon(QIcon(icon_path))
        self.convert_to_pinyin()

    def toggle_maximize(self):
        if self.is_maximized:
            self.showNormal()
            self.is_maximized = False
        else:
            self.showMaximized()
            self.is_maximized = True


    def toggle_heteronym(self):
        self.use_heteronym = not self.use_heteronym
        self.convert_to_pinyin()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QColor(200, 200, 200))
        painter.drawRoundedRect(self.rect(), 15, 15)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icons/app_icon.ico"))
    window = PinyinWidget()
    window.setWindowTitle("Pinyin Widget")
    window.show()
    sys.exit(app.exec_())
