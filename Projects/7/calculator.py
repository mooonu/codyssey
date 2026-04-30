import sys
import os
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '../6'))

from PyQt6.QtGui import QFont
from calculator import Calculator as BaseCalculator

MAX_VALUE = 1e15


class Calculator(BaseCalculator):
    def __init__(self):
        super().__init__()

    def add(self):
        self._set_operator('+')

    def subtract(self):
        self._set_operator('-')

    def multiply(self):
        self._set_operator('×')

    def divide(self):
        self._set_operator('÷')

    def reset(self):
        self._clear()

    def negative_positive(self):
        self._toggle_sign()

    def percent(self):
        self._percent()

    def equal(self):
        self._calculate()

    def _on_click(self, text):
        if text.isdigit():
            self._input_digit(text)
        elif text == '.':
            self._input_dot()
        elif text == 'AC':
            self.reset()
        elif text == '+/-':
            self.negative_positive()
        elif text == '%':
            self.percent()
        elif text == '+':
            self.add()
        elif text == '-':
            self.subtract()
        elif text == '×':
            self.multiply()
        elif text == '÷':
            self.divide()
        elif text == '=':
            self.equal()

    def _compute(self, a, b, op):
        try:
            if op == '+':
                result = a + b
            elif op == '-':
                result = a - b
            elif op == '×':
                result = a * b
            elif op == '÷':
                if b == 0:
                    self._show_error('0으로 나눌 수 없음')
                    return None
                result = a / b
            else:
                return None

            if math.isinf(result) or math.isnan(result):
                self._show_error('범위 초과')
                return None

            if abs(result) >= MAX_VALUE:
                self._show_error('범위 초과')
                return None

            return result

        except OverflowError:
            self._show_error('범위 초과')
            return None

    def _format_number(self, value):
        if math.isinf(value) or math.isnan(value):
            return 'Error'

        if abs(value) >= MAX_VALUE:
            return 'Error'

        # 소수점 6자리 초과 시 반올림
        rounded = round(value, 6)

        if rounded == int(rounded):
            return str(int(rounded))

        # 후행 0 제거
        return f'{rounded:.6f}'.rstrip('0')

    def _update_display(self, text):
        length = len(text)
        if length <= 3:
            size = 60
        elif length <= 6:
            size = 50
        elif length <= 9:
            size = 36
        elif length <= 12:
            size = 28
        else:
            size = 20

        self.display.setFont(QFont('Arial', size, QFont.Weight.Light))
        self.display.setText(text if text else '0')

    def _show_error(self, message):
        self._update_display(message)
        self.current_input = ''
        self.previous_input = ''
        self.operator = None
        self.reset_next = True


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec())
