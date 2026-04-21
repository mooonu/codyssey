import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.current_input = ''
        self.previous_input = ''
        self.operator = None
        self.reset_next = False
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('Calculator')
        self.setFixedSize(320, 520)
        self.setStyleSheet('background-color: #1c1c1e;')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 20, 10, 10)
        main_layout.setSpacing(0)

        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.display.setFont(QFont('Arial', 60, QFont.Weight.Light))
        self.display.setStyleSheet('color: white; padding: 10px 10px 0px 10px;')
        self.display.setFixedHeight(150)
        main_layout.addWidget(self.display)

        grid = QGridLayout()
        grid.setSpacing(10)

        buttons = [
            ('AC', 0, 0, 'func'), ('+/-', 0, 1, 'func'), ('%', 0, 2, 'func'), ('÷', 0, 3, 'op'),
            ('7',  1, 0, 'num'), ('8',  1, 1, 'num'), ('9',  1, 2, 'num'), ('×', 1, 3, 'op'),
            ('4',  2, 0, 'num'), ('5',  2, 1, 'num'), ('6',  2, 2, 'num'), ('-', 2, 3, 'op'),
            ('1',  3, 0, 'num'), ('2',  3, 1, 'num'), ('3',  3, 2, 'num'), ('+', 3, 3, 'op'),
            ('0',  4, 0, 'zero'), ('.', 4, 2, 'num'), ('=',  4, 3, 'op'),
        ]

        for text, row, col, kind in buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(65)
            btn.setFont(QFont('Arial', 26))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            if kind == 'op':
                btn.setStyleSheet(self._style('#ff9f0a', 'black'))
            elif kind == 'func':
                btn.setStyleSheet(self._style('#636366', 'white'))
            else:
                btn.setStyleSheet(self._style('#3a3a3c', 'white'))

            if text == '0':
                btn.setFixedWidth(145)
                grid.addWidget(btn, row, col, 1, 2)
            else:
                btn.setFixedWidth(65)
                grid.addWidget(btn, row, col)

            btn.clicked.connect(lambda _, t=text: self._on_click(t))

        main_layout.addLayout(grid)
        self.setLayout(main_layout)

    def _style(self, bg, fg):
        return (
            f'QPushButton {{'
            f'  background-color: {bg};'
            f'  color: {fg};'
            f'  border-radius: 32px;'
            f'  border: none;'
            f'}}'
            f'QPushButton:pressed {{'
            f'  background-color: {"#ffc966" if bg == "#ff9f0a" else "#8e8e93" if bg == "#636366" else "#636366"};'
            f'}}'
        )

    def _on_click(self, text):
        if text.isdigit():
            self._input_digit(text)
        elif text == '.':
            self._input_dot()
        elif text == 'AC':
            self._clear()
        elif text == '+/-':
            self._toggle_sign()
        elif text == '%':
            self._percent()
        elif text in ('+', '-', '×', '÷'):
            self._set_operator(text)
        elif text == '=':
            self._calculate()

    def _input_digit(self, digit):
        if self.reset_next:
            self.current_input = ''
            self.reset_next = False
        if self.current_input == '0':
            self.current_input = digit
        else:
            self.current_input += digit
        self._update_display(self.current_input)

    def _input_dot(self):
        if self.reset_next:
            self.current_input = '0'
            self.reset_next = False
        if '.' not in self.current_input:
            self.current_input = (self.current_input or '0') + '.'
        self._update_display(self.current_input)

    def _clear(self):
        self.current_input = ''
        self.previous_input = ''
        self.operator = None
        self.reset_next = False
        self._update_display('0')

    def _toggle_sign(self):
        if self.current_input and self.current_input != '0':
            if self.current_input.startswith('-'):
                self.current_input = self.current_input[1:]
            else:
                self.current_input = '-' + self.current_input
            self._update_display(self.current_input)

    def _percent(self):
        if self.current_input:
            value = float(self.current_input) / 100
            self.current_input = self._format_number(value)
            self._update_display(self.current_input)

    def _set_operator(self, op):
        if self.current_input:
            self.previous_input = self.current_input
            self.reset_next = True
        self.operator = op

    def _calculate(self):
        if not self.previous_input or not self.current_input or not self.operator:
            return

        a = float(self.previous_input)
        b = float(self.current_input)
        result = self._compute(a, b, self.operator)

        if result is None:
            return

        self.current_input = self._format_number(result)
        self.previous_input = ''
        self.operator = None
        self.reset_next = True
        self._update_display(self.current_input)

    def _compute(self, a, b, op):
        if op == '+':
            return a + b
        elif op == '-':
            return a - b
        elif op == '×':
            return a * b
        elif op == '÷':
            if b == 0:
                self._update_display('error')
                self.current_input = ''
                return None
            return a / b
        return None

    def _format_number(self, value):
        if value == int(value):
            return str(int(value))
        return str(value)

    def _update_display(self, text):
        self.display.setText(text if text else '0')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec())
