from PyQt5.QtWidgets import QWidget, QLabel, QCheckBox, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

class LandCardWidget(QWidget):
    checked = pyqtSignal(object, bool)  # передаём self и состояние

    def __init__(self, image_url, title, location, price, date, area=None, price_per_unit=None):
        super().__init__()

        self.title = title
        self.location = location
        self.price = price
        self.area = area
        self.price_per_unit = price_per_unit
        self.date = date


        self.price_per_unit = price_per_unit
        self.is_selected = False

        layout = QHBoxLayout(self)
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox)

        text_layout = QVBoxLayout()
        title_label = QLabel(f"<b>{title}</b>")
        location_label = QLabel(location)
        text_layout.addWidget(title_label)
        text_layout.addWidget(location_label)

        price_block = QVBoxLayout()
        price_label = QLabel(f"<b>{price}</b>")
        area_text = f"{round(area, 2)} соток" if area else "—"
        area_label = QLabel(area_text)
        unit_price_text = f"{round(price_per_unit):,} сум/сотка".replace(",", " ") if price_per_unit else "—"
        price_per_unit_label = QLabel(unit_price_text)

        price_block.addWidget(price_label)
        price_block.addWidget(area_label)
        price_block.addWidget(price_per_unit_label)

        layout.addLayout(text_layout)
        layout.addLayout(price_block)
        self.setLayout(layout)

    def on_checkbox_changed(self, state):
        self.checked.emit(self, state == Qt.Checked)

    def highlight(self, color: str):
        if color == "green":
            self.setStyleSheet("background-color: #d0ffd0;")  # светло-зелёный
        elif color == "violet":
            self.setStyleSheet("background-color: #e6ccff;")  # светло-жёлтый
        else:
            self.setStyleSheet("")

    def set_dimmed(self, is_dimmed: bool):
        if is_dimmed:
            self.setStyleSheet(self.styleSheet() + "opacity: 0.4;")  # визуально тускло
            self.checkbox.setEnabled(False)
        else:
            self.setStyleSheet(self.styleSheet().replace("opacity: 0.4;", ""))
            self.checkbox.setEnabled(True)
