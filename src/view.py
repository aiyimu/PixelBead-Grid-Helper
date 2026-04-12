import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QPushButton, QLabel, QFrame, QScrollArea, QFileDialog, QComboBox, QSpinBox, QDialog, QTextEdit, QSlider, QColorDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QSize
from PyQt6.QtGui import QPixmap, QPainter, QPen, QCursor, QShortcut, QKeySequence, QColor, QBrush, QWheelEvent, QMouseEvent
from locales import TRANSLATIONS, LANGUAGES, THEME_NAMES


THEMES = {
    "暗色标准": {
        "window": "#1e1e1e",
        "panel": "#252526",
        "canvas": "#2d2d2d",
        "text": "#cccccc",
        "border": "#404040",
        "button": "#3c3c3c",
        "button_hover": "#4c4c4c",
        "accent": "#007acc"
    },
    "亮色标准": {
        "window": "#ffffff",
        "panel": "#f3f3f3",
        "canvas": "#e8e8e8",
        "text": "#333333",
        "border": "#cccccc",
        "button": "#e0e0e0",
        "button_hover": "#d0d0d0",
        "accent": "#0066cc"
    },
    "暗色像素风": {
        "window": "#1a1a2e",
        "panel": "#16213e",
        "canvas": "#0f3460",
        "text": "#e94560",
        "border": "#533483",
        "button": "#2d132c",
        "button_hover": "#4a1942",
        "accent": "#e94560"
    },
    "亮色像素风": {
        "window": "#fff6e6",
        "panel": "#ffd9b3",
        "canvas": "#ffe4c4",
        "text": "#8b4513",
        "border": "#cd853f",
        "button": "#ffc1a5",
        "button_hover": "#ffb394",
        "accent": "#ff6347"
    },
    "护眼浅绿色": {
        "window": "#e8f5e9",
        "panel": "#c8e6c9",
        "canvas": "#a5d6a7",
        "text": "#2e7d32",
        "border": "#81c784",
        "button": "#a5d6a7",
        "button_hover": "#81c784",
        "accent": "#43a047"
    },
    "护眼暗蓝色": {
        "window": "#1a237e",
        "panel": "#283593",
        "canvas": "#3949ab",
        "text": "#bbdefb",
        "border": "#5c6bc0",
        "button": "#3949ab",
        "button_hover": "#5c6bc0",
        "accent": "#7986cb"
    }
}


class HelpDialog(QDialog):
    def __init__(self, parent=None, language: str = "zh_CN"):
        super().__init__(parent)
        self._language = language
        t = TRANSLATIONS[language]
        self.setWindowTitle(t["help_title"])
        self.setMinimumSize(400, 350)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        t = TRANSLATIONS[self._language]
        help_text.setHtml(t["help_content"])
        layout.addWidget(help_text)


class DistanceDialog(QDialog):
    def __init__(self, parent, distance: int, line1_pos: int, line2_pos: int, language: str = "zh_CN"):
        super().__init__(parent)
        self._language = language
        t = TRANSLATIONS[language]
        self.setWindowTitle(t["distance_dialog_title"])
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        content = QLabel(f"""
        <h2>{t["distance_result"]}</h2>
        <p><b>{t["first_line_pos"]}</b> {line1_pos}</p>
        <p><b>{t["second_line_pos"]}</b> {line2_pos}</p>
        <p style="font-size: 24px; font-weight: bold; color: #0078d4;">
            {t["distance"]}{distance} {t["px"]}
        </p>
        """)
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.setWordWrap(True)
        layout.addWidget(content)
        
        layout.addSpacing(20)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton(t["ok"])
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)


class CanvasWidget(QWidget):
    canvas_clicked = pyqtSignal(int, int)
    line_dragged = pyqtSignal(int, int)
    line_deleted = pyqtSignal(int)
    line_selected = pyqtSignal(int)
    line_toggled = pyqtSignal(int)
    all_deselected = pyqtSignal()
    crop_confirmed = pyqtSignal(int, int, int, int)
    scale_changed = pyqtSignal(float)
    rect_selection_confirmed = pyqtSignal(int, int, int, int)
    delete_selected_requested = pyqtSignal()
    select_all_requested = pyqtSignal()
    deselect_all_requested = pyqtSignal()
    calculate_distance_line_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._grid_lines: list = []
        self._selected_line_ids: list[int] = []
        self._scale_factor: float = 1.0
        self._min_scale: float = 0.1
        self._max_scale: float = 5.0
        self._offset: QPoint = QPoint(0, 0)
        self._pan_offset: QPoint = QPoint(0, 0)
        self._theme = THEMES["暗色标准"]

        self._is_panning: bool = False
        self._last_pan_pos: QPoint = QPoint(0, 0)
        self._is_space_pressed: bool = False

        self._is_adding_line: bool = False
        self._adding_orientation: str | None = None

        self._is_dragging: bool = False
        self._drag_start_pos: QPoint = QPoint(0, 0)
        self._drag_line_original_pos: dict[int, int] = {}
        self._dragging_lines: list[int] = []

        self._is_cropping: bool = False
        self._crop_start_pos: QPoint = QPoint(0, 0)
        self._crop_end_pos: QPoint = QPoint(0, 0)

        self._is_rect_selecting: bool = False
        self._rect_select_start_pos: QPoint = QPoint(0, 0)
        self._rect_select_end_pos: QPoint = QPoint(0, 0)

        self._is_calculating_distance: bool = False
        self._distance_first_line: int | None = None

        self._tool_mode: str = "select"

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._apply_theme()

    def set_theme(self, theme_name: str) -> None:
        self._theme = THEMES.get(theme_name, THEMES["暗色标准"])
        self._apply_theme()

    def _apply_theme(self) -> None:
        self.setStyleSheet(f"background-color: {self._theme['canvas']};")

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._scale_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self.scale_changed.emit(self._scale_factor)
        self.update()

    def fit_to_screen(self) -> None:
        if not self._pixmap:
            return
        widget_size = self.size()
        pixmap_size = self._pixmap.size()
        scale_x = widget_size.width() / pixmap_size.width()
        scale_y = widget_size.height() / pixmap_size.height()
        self._scale_factor = min(scale_x, scale_y) * 0.9
        self._scale_factor = max(self._min_scale, min(self._max_scale, self._scale_factor))
        self._pan_offset = QPoint(0, 0)
        self.scale_changed.emit(self._scale_factor)
        self.update()

    def set_100_percent(self) -> None:
        self._scale_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self.scale_changed.emit(self._scale_factor)
        self.update()

    def zoom_in(self) -> None:
        self._scale_by(1.2, QPoint(int(self.width() / 2), int(self.height() / 2)))

    def zoom_out(self) -> None:
        self._scale_by(0.8, QPoint(int(self.width() / 2), int(self.height() / 2)))

    def _scale_by(self, factor: float, center: QPoint) -> None:
        if not self._pixmap:
            return
        old_scale = self._scale_factor
        new_scale = old_scale * factor
        new_scale = max(self._min_scale, min(self._max_scale, new_scale))
        
        if new_scale != old_scale:
            scaled_size = QSize(
                int(self._pixmap.width() * old_scale),
                int(self._pixmap.height() * old_scale)
            )
            old_x = (self.width() - scaled_size.width()) // 2 + self._pan_offset.x()
            old_y = (self.height() - scaled_size.height()) // 2 + self._pan_offset.y()
            
            self._scale_factor = new_scale
            
            new_scaled_size = QSize(
                int(self._pixmap.width() * new_scale),
                int(self._pixmap.height() * new_scale)
            )
            new_x = (self.width() - new_scaled_size.width()) // 2 + self._pan_offset.x()
            new_y = (self.height() - new_scaled_size.height()) // 2 + self._pan_offset.y()
            
            delta_x = old_x - new_x
            delta_y = old_y - new_y
            self._pan_offset += QPoint(int(delta_x), int(delta_y))
            self._clamp_pan_offset()
            self.scale_changed.emit(self._scale_factor)
            self.update()
    
    def _clamp_pan_offset(self) -> None:
        if not self._pixmap:
            return
        scaled_size = QSize(
            int(self._pixmap.width() * self._scale_factor),
            int(self._pixmap.height() * self._scale_factor)
        )
        max_pan_x = max(0, scaled_size.width() // 2)
        max_pan_y = max(0, scaled_size.height() // 2)
        min_pan_x = -max_pan_x
        min_pan_y = -max_pan_y
        
        new_x = max(min_pan_x, min(max_pan_x, self._pan_offset.x()))
        new_y = max(min_pan_y, min(max_pan_y, self._pan_offset.y()))
        self._pan_offset = QPoint(new_x, new_y)

    def set_grid_lines(self, lines: list) -> None:
        self._grid_lines = lines
        self.update()

    def set_selected_line_ids(self, ids: list[int]) -> None:
        self._selected_line_ids = ids
        self.update()

    def set_adding_mode(self, orientation: str | None) -> None:
        self._is_adding_line = orientation is not None
        self._adding_orientation = orientation
        self._tool_mode = "add" if orientation else "select"
        self._update_cursor()

    def set_cropping_mode(self, is_cropping: bool) -> None:
        self._is_cropping = is_cropping
        if is_cropping:
            self._tool_mode = "crop"
        else:
            self._tool_mode = "select"
        self._update_cursor()

    def set_calculating_distance_mode(self, is_calculating: bool) -> None:
        self._is_calculating_distance = is_calculating
        self._distance_first_line = None
        if is_calculating:
            self._tool_mode = "calculate_distance"
        else:
            self._tool_mode = "select"
        self._update_cursor()

    def set_tool_mode(self, mode: str) -> None:
        self._tool_mode = mode
        self._update_cursor()

    def _update_cursor(self) -> None:
        if self._is_panning:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif self._is_space_pressed:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self._tool_mode == "add" and self._is_adding_line:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self._tool_mode == "crop":
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self._tool_mode == "rect_select":
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self._tool_mode == "calculate_distance":
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            line_id = self._get_line_at(self.mapFromGlobal(self.cursor().pos()))
            if line_id is not None:
                line = self._get_line_by_id(line_id)
                if line:
                    if line.orientation == 'horizontal':
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                    else:
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._pixmap:
            scaled_size = QSize(
                int(self._pixmap.width() * self._scale_factor),
                int(self._pixmap.height() * self._scale_factor)
            )
            scaled_pixmap = self._pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            x = (self.width() - scaled_pixmap.width()) // 2 + self._pan_offset.x()
            y = (self.height() - scaled_pixmap.height()) // 2 + self._pan_offset.y()
            self._offset = QPoint(x, y)
            painter.drawPixmap(x, y, scaled_pixmap)

            for line in self._grid_lines:
                is_selected = line.id in self._selected_line_ids
                
                # 设置线的颜色
                if is_selected:
                    pen_color = QColor(255, 0, 0)
                else:
                    pen_color = line.color
                
                # 设置线的粗细
                thickness = getattr(line, 'thickness', 2)
                if is_selected:
                    pen_width = max(2, int((thickness + 1) * self._scale_factor))
                else:
                    pen_width = max(1, int(thickness * self._scale_factor))
                
                # 设置线的样式
                style = getattr(line, 'style', 'solid')
                if style == 'dashed':
                    pen_style = Qt.PenStyle.DashLine
                elif style == 'dotted':
                    pen_style = Qt.PenStyle.DotLine
                else:
                    pen_style = Qt.PenStyle.SolidLine
                
                pen = QPen(pen_color, pen_width, pen_style)
                painter.setPen(pen)

                if line.orientation == 'horizontal':
                    y_pos = y + int(line.position * self._scale_factor)
                    x_start = x + int(line.start * self._scale_factor)
                    x_end = x + int((line.end if line.end is not None else self._pixmap.width()) * self._scale_factor)
                    painter.drawLine(x_start, y_pos, x_end, y_pos)
                    
                    if is_selected:
                        self._draw_control_points(painter, x_start, y_pos, x_end, y_pos)
                else:
                    x_pos = x + int(line.position * self._scale_factor)
                    y_start = y + int(line.start * self._scale_factor)
                    y_end = y + int((line.end if line.end is not None else self._pixmap.height()) * self._scale_factor)
                    painter.drawLine(x_pos, y_start, x_pos, y_end)
                    
                    if is_selected:
                        self._draw_control_points(painter, x_pos, y_start, x_pos, y_end)

            if self._is_cropping:
                crop_rect = QRect(self._crop_start_pos, self._crop_end_pos).normalized()
                painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(255, 255, 0, 50)))
                painter.drawRect(crop_rect)

            if self._is_rect_selecting:
                rect = QRect(self._rect_select_start_pos, self._rect_select_end_pos).normalized()
                painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(0, 120, 215, 50)))
                painter.drawRect(rect)

    def _draw_control_points(self, painter: QPainter, x1: int, y1: int, x2: int, y2: int) -> None:
        point_size = max(4, int(6 * self._scale_factor))
        half_size = point_size // 2
        
        points = [
            QPoint(x1, y1),
            QPoint((x1 + x2) // 2, (y1 + y2) // 2),
            QPoint(x2, y2)
        ]
        
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        for point in points:
            rect = QRect(point.x() - half_size, point.y() - half_size, point_size, point_size)
            painter.drawRect(rect)

    def wheelEvent(self, event: QWheelEvent) -> None:
        zoom_in = event.angleDelta().y() > 0
        factor = 1.1 if zoom_in else 0.9
        self._scale_by(factor, event.position().toPoint())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and self._is_space_pressed):
            self._is_panning = True
            self._last_pan_pos = event.pos()
            if self._is_space_pressed:
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            if self._tool_mode == "crop" and self._is_cropping and self._pixmap:
                self._crop_start_pos = event.pos()
                self._crop_end_pos = event.pos()
                self.update()
            elif self._tool_mode == "rect_select" and self._pixmap:
                self._is_rect_selecting = True
                self._rect_select_start_pos = event.pos()
                self._rect_select_end_pos = event.pos()
                self.update()
            elif self._tool_mode == "add" and self._is_adding_line and self._pixmap:
                img_x, img_y = self._to_image_coords(event.pos())
                if 0 <= img_x < self._pixmap.width() and 0 <= img_y < self._pixmap.height():
                    if self._adding_orientation == 'horizontal':
                        self.canvas_clicked.emit(img_x, img_y)
                    else:
                        self.canvas_clicked.emit(img_x, img_y)
            elif self._tool_mode == "calculate_distance" and self._pixmap:
                line_id = self._get_line_at(event.pos())
                if line_id is not None:
                    if self._distance_first_line is None:
                        self._distance_first_line = line_id
                        self.calculate_distance_line_selected.emit(line_id)
                    else:
                        self.calculate_distance_line_selected.emit(line_id)
            elif self._tool_mode == "select" and self._pixmap:
                line_id = self._get_line_at(event.pos())
                if line_id is not None:
                    if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                        self.line_toggled.emit(line_id)
                    else:
                        if line_id not in self._selected_line_ids:
                            self.line_selected.emit(line_id)
                        self._is_dragging = True
                        self._drag_start_pos = event.pos()
                        self._dragging_lines = list(self._selected_line_ids)
                        self._drag_line_original_pos = {}
                        for lid in self._dragging_lines:
                            line = self._get_line_by_id(lid)
                            if line:
                                self._drag_line_original_pos[lid] = line.position
                else:
                    self.all_deselected.emit()
                    self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_panning:
            delta = event.pos() - self._last_pan_pos
            self._pan_offset += delta
            self._clamp_pan_offset()
            self._last_pan_pos = event.pos()
            self.update()
        elif self._is_cropping and event.buttons() == Qt.MouseButton.LeftButton:
            self._crop_end_pos = event.pos()
            self.update()
        elif self._is_rect_selecting and event.buttons() == Qt.MouseButton.LeftButton:
            self._rect_select_end_pos = event.pos()
            self.update()
        elif self._is_dragging and self._dragging_lines and self._pixmap:
            img_start_x, img_start_y = self._to_image_coords(self._drag_start_pos)
            img_current_x, img_current_y = self._to_image_coords(event.pos())
            
            for line_id in self._dragging_lines:
                line = self._get_line_by_id(line_id)
                if line and line_id in self._drag_line_original_pos:
                    if line.orientation == 'horizontal':
                        delta = img_current_y - img_start_y
                        new_pos = self._drag_line_original_pos[line_id] + delta
                        new_pos = max(0, min(new_pos, self._pixmap.height()))
                    else:
                        delta = img_current_x - img_start_x
                        new_pos = self._drag_line_original_pos[line_id] + delta
                        new_pos = max(0, min(new_pos, self._pixmap.width()))
                    self.line_dragged.emit(line_id, new_pos)
        else:
            self._update_cursor()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and self._is_panning):
            self._is_panning = False
            self._update_cursor()
        elif event.button() == Qt.MouseButton.LeftButton:
            if self._is_cropping and self._pixmap:
                x1, y1 = self._to_image_coords(self._crop_start_pos)
                x2, y2 = self._to_image_coords(self._crop_end_pos)
                self.crop_confirmed.emit(x1, y1, x2, y2)
            elif self._is_rect_selecting and self._pixmap:
                x1, y1 = self._to_image_coords(self._rect_select_start_pos)
                x2, y2 = self._to_image_coords(self._rect_select_end_pos)
                self.rect_selection_confirmed.emit(x1, y1, x2, y2)
                self._is_rect_selecting = False
            self._is_dragging = False
            self._dragging_lines = []
            self._drag_line_original_pos = {}

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_requested.emit()
        elif event.key() == Qt.Key.Key_Escape:
            if self._is_cropping:
                self._is_cropping = False
                self._crop_start_pos = QPoint(0, 0)
                self._crop_end_pos = QPoint(0, 0)
                self.update()
                self.set_cropping_mode(False)
            elif self._is_rect_selecting:
                self._is_rect_selecting = False
                self._rect_select_start_pos = QPoint(0, 0)
                self._rect_select_end_pos = QPoint(0, 0)
                self.update()
            elif self._is_calculating_distance:
                self.set_calculating_distance_mode(False)
            else:
                self.all_deselected.emit()
        elif event.key() == Qt.Key.Key_Space and not self._is_space_pressed:
            self._is_space_pressed = True
            self._update_cursor()
        elif event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.deselect_all_requested.emit()
            else:
                self.select_all_requested.emit()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._is_space_pressed = False
            self._is_panning = False
            self._update_cursor()
        super().keyReleaseEvent(event)

    def _to_image_coords(self, pos: QPoint) -> tuple[int, int]:
        if not self._pixmap:
            return 0, 0
        scaled_size = QSize(
            int(self._pixmap.width() * self._scale_factor),
            int(self._pixmap.height() * self._scale_factor)
        )
        x = (self.width() - scaled_size.width()) // 2 + self._pan_offset.x()
        y = (self.height() - scaled_size.height()) // 2 + self._pan_offset.y()
        
        img_x = int((pos.x() - x) / self._scale_factor)
        img_y = int((pos.y() - y) / self._scale_factor)
        return img_x, img_y

    def _get_line_at(self, pos: QPoint) -> int | None:
        threshold = max(3, int(5 * self._scale_factor))
        for line in reversed(self._grid_lines):
            if line.orientation == 'horizontal':
                scaled_size = QSize(
                    int(self._pixmap.width() * self._scale_factor),
                    int(self._pixmap.height() * self._scale_factor)
                )
                x = (self.width() - scaled_size.width()) // 2 + self._pan_offset.x()
                y = (self.height() - scaled_size.height()) // 2 + self._pan_offset.y()
                
                y_pos = y + int(line.position * self._scale_factor)
                if abs(pos.y() - y_pos) <= threshold:
                    x_min = x + int(line.start * self._scale_factor)
                    x_max = x + int((line.end if line.end is not None else (self._pixmap.width() if self._pixmap else 0)) * self._scale_factor)
                    if x_min <= pos.x() <= x_max:
                        return line.id
            else:
                scaled_size = QSize(
                    int(self._pixmap.width() * self._scale_factor),
                    int(self._pixmap.height() * self._scale_factor)
                )
                x = (self.width() - scaled_size.width()) // 2 + self._pan_offset.x()
                y = (self.height() - scaled_size.height()) // 2 + self._pan_offset.y()
                
                x_pos = x + int(line.position * self._scale_factor)
                if abs(pos.x() - x_pos) <= threshold:
                    y_min = y + int(line.start * self._scale_factor)
                    y_max = y + int((line.end if line.end is not None else (self._pixmap.height() if self._pixmap else 0)) * self._scale_factor)
                    if y_min <= pos.y() <= y_max:
                        return line.id
        return None

    def _get_line_by_id(self, line_id: int):
        for line in self._grid_lines:
            if line.id == line_id:
                return line
        return None

    def render_to_pixmap(self) -> QPixmap | None:
        if not self._pixmap:
            return None
        
        result = QPixmap(self._pixmap.size())
        result.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self._pixmap)
        
        for line in self._grid_lines:
            # 设置线的粗细
            thickness = getattr(line, 'thickness', 2)
            
            # 设置线的样式
            style = getattr(line, 'style', 'solid')
            if style == 'dashed':
                pen_style = Qt.PenStyle.DashLine
            elif style == 'dotted':
                pen_style = Qt.PenStyle.DotLine
            else:
                pen_style = Qt.PenStyle.SolidLine
            
            pen = QPen(line.color, thickness, pen_style)
            painter.setPen(pen)
            
            if line.orientation == 'horizontal':
                x_start = line.start
                x_end = line.end if line.end is not None else self._pixmap.width()
                painter.drawLine(x_start, line.position, x_end, line.position)
            else:
                y_start = line.start
                y_end = line.end if line.end is not None else self._pixmap.height()
                painter.drawLine(line.position, y_start, line.position, y_end)
        
        painter.end()
        return result


class MainWindow(QMainWindow):
    open_image_requested = pyqtSignal()
    add_horizontal_line_requested = pyqtSignal()
    add_vertical_line_requested = pyqtSignal()
    delete_line_requested = pyqtSignal()
    theme_changed = pyqtSignal(str)
    fill_horizontal_lines_requested = pyqtSignal()
    fill_vertical_lines_requested = pyqtSignal()
    spacing_changed = pyqtSignal(int)
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    crop_requested = pyqtSignal()
    export_requested = pyqtSignal()
    select_tool_requested = pyqtSignal()
    rect_select_tool_requested = pyqtSignal()
    thickness_changed = pyqtSignal(int)
    color_changed = pyqtSignal(QColor)
    style_changed = pyqtSignal(str)
    calculate_distance_requested = pyqtSignal()
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PixelBead Grid Helper")
        self.setGeometry(100, 100, 1400, 900)
        self._current_pixmap: QPixmap | None = None
        self._current_theme = "亮色标准"
        self._current_language = "zh_CN"
        self._setup_ui()
        self._setup_shortcuts()
        self._apply_theme()
        self._update_ui_texts()

    def _setup_ui(self) -> None:
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        self.open_button = QPushButton("")
        self.open_button.clicked.connect(self._on_open_clicked)
        toolbar.addWidget(self.open_button)
        self.save_button = QPushButton("")
        toolbar.addWidget(self.save_button)
        self.export_button = QPushButton("")
        self.export_button.clicked.connect(self._on_export_clicked)
        toolbar.addWidget(self.export_button)

        toolbar.addSeparator()

        self.undo_button = QPushButton("")
        self.undo_button.clicked.connect(self.undo_requested.emit)
        toolbar.addWidget(self.undo_button)
        self.redo_button = QPushButton("")
        self.redo_button.clicked.connect(self.redo_requested.emit)
        toolbar.addWidget(self.redo_button)
        self.delete_button = QPushButton("")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        toolbar.addWidget(self.delete_button)

        toolbar.addSeparator()

        self.zoom_in_button = QPushButton("")
        self.zoom_in_button.clicked.connect(self._on_zoom_in_clicked)
        toolbar.addWidget(self.zoom_in_button)
        self.zoom_out_button = QPushButton("")
        self.zoom_out_button.clicked.connect(self._on_zoom_out_clicked)
        toolbar.addWidget(self.zoom_out_button)
        self.zoom_100_button = QPushButton("")
        self.zoom_100_button.clicked.connect(self._on_zoom_100_clicked)
        toolbar.addWidget(self.zoom_100_button)
        self.fit_screen_button = QPushButton("")
        self.fit_screen_button.clicked.connect(self._on_zoom_fit_clicked)
        toolbar.addWidget(self.fit_screen_button)

        toolbar.addSeparator()

        self.select_button = QPushButton("")
        self.select_button.clicked.connect(self._on_select_tool_clicked)
        toolbar.addWidget(self.select_button)
        self.rect_select_button = QPushButton("")
        self.rect_select_button.clicked.connect(self._on_rect_select_tool_clicked)
        toolbar.addWidget(self.rect_select_button)
        self.add_h_line_button = QPushButton("")
        self.add_h_line_button.clicked.connect(self._on_add_h_line_clicked)
        toolbar.addWidget(self.add_h_line_button)
        self.add_v_line_button = QPushButton("")
        self.add_v_line_button.clicked.connect(self._on_add_v_line_clicked)
        toolbar.addWidget(self.add_v_line_button)
        self.fill_h_button = QPushButton("")
        self.fill_h_button.clicked.connect(self._on_fill_h_clicked)
        self.fill_h_button.setEnabled(False)
        toolbar.addWidget(self.fill_h_button)
        self.fill_v_button = QPushButton("")
        self.fill_v_button.clicked.connect(self._on_fill_v_clicked)
        self.fill_v_button.setEnabled(False)
        toolbar.addWidget(self.fill_v_button)
        self.crop_button = QPushButton("")
        self.crop_button.clicked.connect(self._on_crop_clicked)
        toolbar.addWidget(self.crop_button)
        self.calculate_distance_button = QPushButton("")
        self.calculate_distance_button.clicked.connect(self._on_calculate_distance_clicked)
        toolbar.addWidget(self.calculate_distance_button)

        toolbar.addSeparator()

        # 语言切换
        self.lang_label = QLabel("")
        toolbar.addWidget(self.lang_label)
        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGES.values())
        self.language_combo.setCurrentText(LANGUAGES[self._current_language])
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        toolbar.addWidget(self.language_combo)

        toolbar.addSeparator()

        self.theme_label = QLabel("")
        toolbar.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        # Initialize with current language theme names
        theme_names = THEME_NAMES[self._current_language]
        self.theme_combo.addItems([theme_names[key] for key in THEMES.keys()])
        self.theme_combo.setCurrentText(theme_names[self._current_theme])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        toolbar.addWidget(self.theme_combo)

        toolbar.addSeparator()

        self.help_button = QPushButton("")
        self.help_button.clicked.connect(self._on_help_clicked)
        toolbar.addWidget(self.help_button)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.canvas = CanvasWidget()
        scroll_area.setWidget(self.canvas)

        main_layout.addWidget(scroll_area, stretch=3)

        toolbox_frame = QFrame()
        toolbox_frame.setObjectName("toolbox")
        toolbox_layout = QVBoxLayout(toolbox_frame)

        self.toolbox_label = QLabel("")
        self.toolbox_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbox_layout.addWidget(self.toolbox_label)

        self.add_h_line_btn2 = QPushButton("")
        self.add_h_line_btn2.clicked.connect(self._on_add_h_line_clicked)
        toolbox_layout.addWidget(self.add_h_line_btn2)

        self.add_v_line_btn2 = QPushButton("")
        self.add_v_line_btn2.clicked.connect(self._on_add_v_line_clicked)
        toolbox_layout.addWidget(self.add_v_line_btn2)

        self.delete_line_btn = QPushButton("")
        self.delete_line_btn.clicked.connect(self._on_delete_line_clicked)
        self.delete_line_btn.setEnabled(False)
        toolbox_layout.addWidget(self.delete_line_btn)

        spacing_layout = QHBoxLayout()
        self.spacing_label = QLabel("")
        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setMinimum(1)
        self.spacing_spinbox.setMaximum(1000)
        self.spacing_spinbox.setValue(10)
        self.spacing_spinbox.valueChanged.connect(self._on_spacing_changed)
        spacing_layout.addWidget(self.spacing_label)
        spacing_layout.addWidget(self.spacing_spinbox)
        toolbox_layout.addLayout(spacing_layout)

        self.fill_h_btn2 = QPushButton("")
        self.fill_h_btn2.clicked.connect(self._on_fill_h_clicked)
        self.fill_h_btn2.setEnabled(False)
        toolbox_layout.addWidget(self.fill_h_btn2)

        self.fill_v_btn2 = QPushButton("")
        self.fill_v_btn2.clicked.connect(self._on_fill_v_clicked)
        self.fill_v_btn2.setEnabled(False)
        toolbox_layout.addWidget(self.fill_v_btn2)

        toolbox_layout.addSpacing(10)

        # 线条属性分组
        self.line_properties_label = QLabel("线条属性")
        self.line_properties_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbox_layout.addWidget(self.line_properties_label)

        # 粗细滑块
        thickness_layout = QHBoxLayout()
        self.thickness_label = QLabel("粗细:")
        self.thickness_slider = QSlider(Qt.Orientation.Horizontal)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(10)
        self.thickness_slider.setValue(2)
        self.thickness_value_label = QLabel("2")
        self.thickness_value_label.setMinimumWidth(20)
        self.thickness_slider.valueChanged.connect(self._on_thickness_changed)
        thickness_layout.addWidget(self.thickness_label)
        thickness_layout.addWidget(self.thickness_slider)
        thickness_layout.addWidget(self.thickness_value_label)
        toolbox_layout.addLayout(thickness_layout)

        # 颜色选择器
        color_layout = QHBoxLayout()
        self.color_label = QLabel("颜色:")
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 30)
        self._update_color_preview(QColor(255, 0, 0))
        self.color_button.clicked.connect(self._on_color_button_clicked)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        toolbox_layout.addLayout(color_layout)

        # 样式下拉框
        style_layout = QHBoxLayout()
        self.style_label = QLabel("样式:")
        self.style_combo = QComboBox()
        self.style_combo.addItems(["实线", "虚线", "点线"])
        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        style_layout.addWidget(self.style_label)
        style_layout.addWidget(self.style_combo)
        toolbox_layout.addLayout(style_layout)

        toolbox_layout.addStretch()

        self.selection_count_label = QLabel("当前选中：0 条线")
        self.selection_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbox_layout.addWidget(self.selection_count_label)

        main_layout.addWidget(toolbox_frame, stretch=1)

    def _setup_shortcuts(self) -> None:
        self.undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        self.undo_shortcut.activated.connect(self.undo_requested.emit)

        self.redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        self.redo_shortcut.activated.connect(self.redo_requested.emit)

    def _on_open_clicked(self) -> None:
        self.open_image_requested.emit()

    def _on_crop_clicked(self) -> None:
        self.crop_requested.emit()

    def _on_export_clicked(self) -> None:
        self.export_requested.emit()

    def _on_zoom_in_clicked(self) -> None:
        self.canvas.zoom_in()

    def _on_zoom_out_clicked(self) -> None:
        self.canvas.zoom_out()

    def _on_zoom_100_clicked(self) -> None:
        self.canvas.set_100_percent()

    def _on_zoom_fit_clicked(self) -> None:
        self.canvas.fit_to_screen()

    def _on_select_tool_clicked(self) -> None:
        self.canvas.set_tool_mode("select")
        self.select_tool_requested.emit()
        self._update_tool_buttons("select")

    def _on_rect_select_tool_clicked(self) -> None:
        self.canvas.set_tool_mode("rect_select")
        self.rect_select_tool_requested.emit()
        self._update_tool_buttons("rect_select")

    def _update_tool_buttons(self, active_tool: str) -> None:
        theme = THEMES[self._current_theme]
        self.select_button.setStyleSheet(f"background-color: {theme['accent']};" if active_tool == "select" else "")
        self.rect_select_button.setStyleSheet(f"background-color: {theme['accent']};" if active_tool == "rect_select" else "")

    def _on_add_h_line_clicked(self) -> None:
        self.add_horizontal_line_requested.emit()

    def _on_add_v_line_clicked(self) -> None:
        self.add_vertical_line_requested.emit()

    def _on_delete_clicked(self) -> None:
        self.delete_line_requested.emit()

    def _on_delete_line_clicked(self) -> None:
        self.delete_line_requested.emit()

    def _on_spacing_changed(self, value: int) -> None:
        self.spacing_changed.emit(value)

    def _on_fill_h_clicked(self) -> None:
        self.fill_horizontal_lines_requested.emit()

    def _on_fill_v_clicked(self) -> None:
        self.fill_vertical_lines_requested.emit()

    def _on_thickness_changed(self, value: int) -> None:
        self.thickness_value_label.setText(str(value))
        self.thickness_changed.emit(value)

    def _on_color_button_clicked(self) -> None:
        current_color = QColor(255, 0, 0)
        t = TRANSLATIONS[self._current_language]
        color = QColorDialog.getColor(current_color, self, t["color"])
        if color.isValid():
            self._update_color_preview(color)
            self.color_changed.emit(color)

    def _update_color_preview(self, color: QColor) -> None:
        self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")

    def _on_style_changed(self, index: int) -> None:
        style_map = {0: "solid", 1: "dashed", 2: "dotted"}
        style = style_map.get(index, "solid")
        self.style_changed.emit(style)

    def _update_ui_texts(self) -> None:
        """Update all UI texts based on current language"""
        t = TRANSLATIONS[self._current_language]
        
        # Update window title
        self.setWindowTitle(t["app_name"])
        
        # Update toolbar button texts
        self.open_button.setText(t["open"])
        self.save_button.setText(t["save"])
        self.export_button.setText(t["export"])
        self.undo_button.setText(t["undo"])
        self.redo_button.setText(t["redo"])
        self.delete_button.setText(t["delete"])
        self.zoom_in_button.setText(t["zoom_in"])
        self.zoom_out_button.setText(t["zoom_out"])
        self.zoom_100_button.setText(t["zoom_100"])
        self.fit_screen_button.setText(t["fit_screen"])
        self.select_button.setText(t["select"])
        self.rect_select_button.setText(t["rect_select"])
        self.add_h_line_button.setText(t["add_h_line"])
        self.add_v_line_button.setText(t["add_v_line"])
        self.fill_h_button.setText(t["fill_h"])
        self.fill_v_button.setText(t["fill_v"])
        self.crop_button.setText(t["crop"])
        self.calculate_distance_button.setText(t["calculate_distance"])
        self.help_button.setText(t["help"])
        
        # Update language and theme labels
        self.lang_label.setText(t.get("language", "Language: "))
        self.theme_label.setText(t["theme"] + ": ")
        
        # Update language combo without triggering signal
        self.language_combo.blockSignals(True)
        # Save current language code before clearing
        current_lang_code = self._current_language
        self.language_combo.clear()
        self.language_combo.addItems(LANGUAGES.values())
        self.language_combo.setCurrentText(LANGUAGES[current_lang_code])
        self.language_combo.blockSignals(False)
        
        # Update right panel texts
        self.add_h_line_btn2.setText(t["add_h_line"])
        self.add_v_line_btn2.setText(t["add_v_line"])
        self.delete_line_btn.setText(t["delete_selected"])
        self.fill_h_btn2.setText(t["fill_h"])
        self.fill_v_btn2.setText(t["fill_v"])
        
        # Update labels
        self.toolbox_label.setText(t["toolbox"])
        self.spacing_label.setText(t["spacing"] + ":")
        self.line_properties_label.setText(t["line_properties"])
        self.thickness_label.setText(t["thickness"] + ":")
        self.color_label.setText(t["color"] + ":")
        self.style_label.setText(t["style"] + ":")
        
        # Update style combo
        self.style_combo.blockSignals(True)
        current_index = self.style_combo.currentIndex()
        self.style_combo.clear()
        self.style_combo.addItems([t["solid"], t["dashed"], t["dotted"]])
        self.style_combo.setCurrentIndex(current_index)
        self.style_combo.blockSignals(False)
        
        # Update theme combo
        self.theme_combo.blockSignals(True)
        theme_names = THEME_NAMES[self._current_language]
        self.theme_combo.clear()
        self.theme_combo.addItems([theme_names[key] for key in THEMES.keys()])
        self.theme_combo.setCurrentText(theme_names[self._current_theme])
        self.theme_combo.blockSignals(False)
        
        # Update selection count label
        self._update_selection_count_display()
    
    def _on_language_changed(self, lang_display: str) -> None:
        # Find language code from display name
        lang_code = next((k for k, v in LANGUAGES.items() if v == lang_display), "zh_CN")
        self._current_language = lang_code
        self.language_changed.emit(lang_code)
        # Update all UI texts
        self._update_ui_texts()
    
    def _on_theme_changed(self, theme_display_name: str) -> None:
        # Find original theme key from display name
        theme_names = THEME_NAMES[self._current_language]
        theme_key = next((k for k, v in theme_names.items() if v == theme_display_name), "暗色标准")
        self._current_theme = theme_key
        self.theme_changed.emit(theme_key)
        self._apply_theme()

    def _on_calculate_distance_clicked(self) -> None:
        self.calculate_distance_requested.emit()

    def set_calculating_distance_mode(self, is_calculating: bool) -> None:
        self.canvas.set_calculating_distance_mode(is_calculating)
        theme = THEMES[self._current_theme]
        if is_calculating:
            self.calculate_distance_button.setStyleSheet(f"background-color: {theme['accent']};")
        else:
            self.calculate_distance_button.setStyleSheet("")

    def show_distance_dialog(self, distance: int, line1_pos: int, line2_pos: int) -> None:
        dialog = DistanceDialog(self, distance, line1_pos, line2_pos, self._current_language)
        dialog.exec()

    def _on_help_clicked(self) -> None:
        dialog = HelpDialog(self, self._current_language)
        dialog.exec()

    def _apply_theme(self) -> None:
        theme = THEMES[self._current_theme]
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['window']};
            }}
            QToolBar {{
                background-color: {theme['panel']};
                border: none;
                spacing: 6px;
                padding: 8px 10px;
            }}
            QToolBar QPushButton {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 8px 14px;
                border-radius: 4px;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QLabel {{
                color: {theme['text']};
            }}
            QComboBox {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 3px 5px;
                border-radius: 3px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {theme['text']};
            }}
            QFrame#toolbox {{
                background-color: {theme['panel']};
                border-left: 1px solid {theme['border']};
            }}
            QSpinBox {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 2px 5px;
                border-radius: 3px;
            }}
            QDialog {{
                background-color: {theme['window']};
            }}
            QTextEdit {{
                background-color: {theme['panel']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
            }}
        """)
        self.canvas.set_theme(self._current_theme)

    def set_delete_button_enabled(self, enabled: bool) -> None:
        self.delete_line_btn.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

    def set_fill_buttons_enabled(self, has_h_line: bool, has_v_line: bool) -> None:
        self.fill_h_button.setEnabled(has_h_line)
        self.fill_h_btn2.setEnabled(has_h_line)
        self.fill_v_button.setEnabled(has_v_line)
        self.fill_v_btn2.setEnabled(has_v_line)

    def set_cropping_mode(self, is_cropping: bool) -> None:
        self.canvas.set_cropping_mode(is_cropping)
        theme = THEMES[self._current_theme]
        if is_cropping:
            self.crop_button.setStyleSheet(f"background-color: {theme['accent']};")
        else:
            self.crop_button.setStyleSheet("")

    def set_selection_count(self, count: int) -> None:
        self._current_selection_count = count
        self._update_selection_count_display()
    
    def _update_selection_count_display(self) -> None:
        """Update selection count label text based on current language"""
        if hasattr(self, '_current_selection_count'):
            count = self._current_selection_count
        else:
            count = 0
        t = TRANSLATIONS[self._current_language]
        self.selection_count_label.setText(t["selection_count"].format(count=count))

    def get_spacing(self) -> int:
        return self.spacing_spinbox.value()

    def set_thickness_value(self, thickness: int) -> None:
        self.thickness_slider.blockSignals(True)
        self.thickness_slider.setValue(thickness)
        self.thickness_value_label.setText(str(thickness))
        self.thickness_slider.blockSignals(False)

    def set_color_preview(self, color: QColor) -> None:
        self._update_color_preview(color)

    def set_style_value(self, index: int) -> None:
        self.style_combo.blockSignals(True)
        self.style_combo.setCurrentIndex(index)
        self.style_combo.blockSignals(False)

    def show_file_dialog(self) -> str | None:
        t = TRANSLATIONS[self._current_language]
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t["open_image"],
            "",
            t["image_files"]
        )
        return file_path if file_path else None

    def show_export_dialog(self) -> str | None:
        t = TRANSLATIONS[self._current_language]
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "output"
        
        # 确保 output 文件夹存在
        output_dir.mkdir(exist_ok=True)
        
        # 默认保存位置为 output 文件夹
        default_path = str(output_dir / "exported_image.png")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t["export_image"],
            default_path,
            f"{t['png_image']};;{t['jpg_image']}"
        )
        return file_path if file_path else None

    def display_image(self, pixmap: QPixmap) -> None:
        self._current_pixmap = pixmap
        self.canvas.set_pixmap(pixmap)
        self.canvas.fit_to_screen()

    def set_canvas_grid_lines(self, lines: list) -> None:
        self.canvas.set_grid_lines(lines)

    def set_canvas_selected_line_ids(self, ids: list[int]) -> None:
        self.canvas.set_selected_line_ids(ids)

    def set_canvas_adding_mode(self, orientation: str | None) -> None:
        self.canvas.set_adding_mode(orientation)
        theme = THEMES[self._current_theme]
        if orientation == 'horizontal':
            self.add_h_line_button.setStyleSheet(f"background-color: {theme['accent']};")
            self.add_h_line_btn2.setStyleSheet(f"background-color: {theme['accent']};")
            self.add_v_line_button.setStyleSheet("")
            self.add_v_line_btn2.setStyleSheet("")
        elif orientation == 'vertical':
            self.add_v_line_button.setStyleSheet(f"background-color: {theme['accent']};")
            self.add_v_line_btn2.setStyleSheet(f"background-color: {theme['accent']};")
            self.add_h_line_button.setStyleSheet("")
            self.add_h_line_btn2.setStyleSheet("")
        else:
            self.add_h_line_button.setStyleSheet("")
            self.add_h_line_btn2.setStyleSheet("")
            self.add_v_line_button.setStyleSheet("")
            self.add_v_line_btn2.setStyleSheet("")

    def refresh_canvas(self) -> None:
        self.canvas.update()

    def get_rendered_pixmap(self) -> QPixmap | None:
        return self.canvas.render_to_pixmap()
