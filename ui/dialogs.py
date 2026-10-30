# 自繪提示框：showInfo / showConfirm，色票取自 theme.palette()，切換主題後自動套用
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF
from PyQt5.QtWidgets import QDialog, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from ui import theme
from core.i18n import t

ACCENT = "#7a2e2e"
DANGER_FILL = "#b91c1c"
DISCARD_CODE = 2    # 「不儲存」按鈕的結果碼（QDialog.Accepted = 1、Rejected = 0）


class Overlay(QWidget):    # 蓋住主視窗的半透明遮罩
    def __init__(self, host):
        super().__init__(host)
        self.setGeometry(host.rect())

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90 if theme.isDark() else 60))


class IconBadge(QWidget):    # 圓形底 + 線條圖示（check / warn）
    def __init__(self, kind, color):
        super().__init__()
        self.kind = kind
        self.color = QColor(color)
        self.setFixedSize(36, 36)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor(self.color)
        bg.setAlphaF(0.15 if theme.isDark() else 0.10)
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawEllipse(self.rect())

        pen = QPen(self.color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if self.kind == "check":
            p.drawPolyline(QPolygonF([QPointF(11, 18.5), QPointF(16, 23.5), QPointF(25, 13)]))
        else:
            p.drawPolygon(QPolygonF([QPointF(18, 10), QPointF(27, 26), QPointF(9, 26)]))
            p.drawLine(QPointF(18, 15.5), QPointF(18, 20.5))
            p.drawPoint(QPointF(18, 23.2))


class CustomDialog(QDialog):
    def __init__(self, host, title, message, kind, confirmText, showCancel, danger, discardText=None):
        super().__init__(host, Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(420 if discardText else 300)    # 三個按鈕時加寬，避免較長的翻譯被擠壓
        p = theme.palette()
        self.bgColor = QColor(p.cardBg)
        self.borderColor = QColor(p.cardBorder)

        if kind == "warn":
            iconColor = p.danger
        else:
            iconColor = p.ink if theme.isDark() else ACCENT

        titleLabel = QLabel(title)
        titleLabel.setStyleSheet(f"color: {p.ink}; font-size: 15px; font-weight: 600; background: transparent;")
        messageLabel = QLabel(message)
        messageLabel.setWordWrap(True)
        messageLabel.setStyleSheet(f"color: {p.inkSoft}; font-size: 13px; background: transparent;")

        textLayout = QVBoxLayout()
        textLayout.setSpacing(4)
        textLayout.addWidget(titleLabel)
        textLayout.addWidget(messageLabel)
        textLayout.addStretch()

        topLayout = QHBoxLayout()
        topLayout.setSpacing(12)
        topLayout.addWidget(IconBadge(kind, iconColor), 0, Qt.AlignTop)
        topLayout.addLayout(textLayout, 1)

        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(8)
        buttonLayout.addStretch()
        if showCancel:
            cancelButton = QPushButton(t("cancel"))
            cancelButton.setStyleSheet(self.buttonStyle("transparent", p.ink, p.inputBorder, p.hoverBg))
            cancelButton.clicked.connect(self.reject)
            buttonLayout.addWidget(cancelButton)

        if discardText:    # 「不儲存」：透明底、紅字紅框，夾在取消與主要按鈕之間
            discardButton = QPushButton(discardText)
            discardButton.setStyleSheet(self.buttonStyle("transparent", p.danger, p.danger, p.hoverBg))
            discardButton.clicked.connect(lambda: self.done(DISCARD_CODE))
            buttonLayout.addWidget(discardButton)

        fill = DANGER_FILL if danger else ACCENT
        confirmButton = QPushButton(confirmText)
        confirmButton.setStyleSheet(self.buttonStyle(fill, "#ffffff", fill, QColor(fill).lighter(115).name()))
        confirmButton.setDefault(True)
        confirmButton.clicked.connect(self.accept)
        buttonLayout.addWidget(confirmButton)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(18)
        layout.addLayout(topLayout)
        layout.addLayout(buttonLayout)

    def buttonStyle(self, fill, textColor, border, hoverFill):
        return (f"QPushButton {{ background: {fill}; color: {textColor}; border: 1px solid {border};"
                f" border-radius: 7px; padding: 6px 16px; font-size: 13px; }}"
                f"QPushButton:hover {{ background: {hoverFill}; }}")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self.borderColor, 1))
        p.setBrush(self.bgColor)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        host = self.parentWidget()
        center = host.mapToGlobal(host.rect().center())
        self.move(center - self.rect().center())    # 置中於主視窗


def runDialogCode(parent, title, message, kind, confirmText, showCancel, danger, discardText=None):    # 回傳結果碼
    host = parent.window()
    overlay = Overlay(host)
    overlay.show()
    overlay.raise_()
    code = CustomDialog(host, title, message, kind, confirmText, showCancel, danger, discardText).exec_()
    overlay.deleteLater()
    return code


def runDialog(parent, title, message, kind, confirmText, showCancel, danger):
    return runDialogCode(parent, title, message, kind, confirmText, showCancel, danger) == QDialog.Accepted


def showInfo(parent, title, message):
    runDialog(parent, title, message, "check", t("ok"), False, False)


def showConfirm(parent, title, message, confirmText=None, danger=False, kind="warn"):    # 回傳 True 表示按下確認；kind 為 warn（三角警示）或 check（勾勾）
    return runDialog(parent, title, message, kind, confirmText or t("ok"), True, danger)


def showSaveChoice(parent, title, message, saveText, discardText):    # 回傳 "save" / "discard" / "cancel"（Esc 視為 cancel）
    code = runDialogCode(parent, title, message, "warn", saveText, True, False, discardText)
    if code == QDialog.Accepted:
        return "save"
    return "discard" if code == DISCARD_CODE else "cancel"