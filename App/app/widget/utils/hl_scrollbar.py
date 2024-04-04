import collections
from PyQt5.QtWidgets import QScrollBar
from PyQt5.QtWidgets import QStyle
from PyQt5.QtWidgets import QStyleOptionSlider
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QRect


class HLScrollBar(QScrollBar):
    pen_color = QColor(255, 215, 0, 64)
    brush_color = QColor(255, 215, 0, 128)

    def __init__(self, parent=None):
        super(QScrollBar, self).__init__(parent=parent)
        self.__hl = set()

    def paintEvent(self, e):
        super().paintEvent(e)

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(
            QStyle.CC_ScrollBar, opt, QStyle.SC_ScrollBarGroove, self)
        sl = self.style().subControlRect(
            QStyle.CC_ScrollBar, opt, QStyle.SC_ScrollBarSlider, self)

        min_val = self.minimum()
        max_val = self.maximum()

        val_range = max_val - min_val + 1
        if val_range == 1:
            return
        val_diff = (gr.height() - sl.height()) / (val_range - 1)

        qp = QPainter(self)
        qp.setPen(self.pen_color)
        qp.setBrush(self.brush_color)
        rect = QRect(gr)
        rect.setHeight(int(val_diff))
        for val in self.__hl:
            idx = val - min_val
            rect.moveTop(gr.top() + int(val_diff *
                         (idx - 1) + sl.height() // 2))
            qp.drawRect(rect)

    def addHLVal(self, val):
        self.__hl.add(val)

    def discardHLVal(self, val):
        self.__hl.discard(val)

    def clearHLVal(self):
        self.__hl.clear()

    def setHighlight(self, hl):
        if hl == None or not isinstance(hl, collections.Set):
            self.clearHLVal()
        else:
            self.__hl.clear()
            self.__hl.update(hl)
        self.update()
