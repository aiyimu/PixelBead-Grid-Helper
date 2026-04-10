from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QPushButton, QLabel, QFrame, QScrollArea, QFileDialog, QComboBox, QSpinBox, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QPen, QCursor, QShortcut, QKeySequence, QColor, QBrush


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
    }
}


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键帮助")
        self.setMinimumSize(400, 350)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
            <h3>快捷键列表</h3>
            <ul>
                <li><b>Ctrl + Z</b> - 撤销操作</li>
                <li><b>Ctrl + Y</b> - 重做操作</li>
                <li><b>Delete</b> - 删除选中的线</li>
                <li><b>Esc</b> - 取消裁剪模式</li>
            </ul>
            <h3>操作说明</h3>
            <ul>
                <li>点击"添加横线"/"添加纵线"，然后在图片上点击添加线</li>
                <li>选中线后，可以拖动改变位置</li>
                <li>选中线后，点击"补全横线"/"补全纵线"自动补全</li>
                <li>点击"裁剪"按钮，拖动鼠标画选框，确认裁剪后截断相交的线</li>
                <li>点击"导出"按钮，保存图片+网格线为图片文件</li>
                <li>可以通过"主题"下拉框切换界面风格</li>
            </ul>
        """)
        layout.addWidget(help_text)


class ImageCanvas(QLabel):
    canvas_clicked = pyqtSignal(int, int)
    line_dragged = pyqtSignal(int, int)
    line_deleted = pyqtSignal(int)
    line_selected = pyqtSignal(int)
    line_unselected = pyqtSignal()
    crop_confirmed = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._grid_lines: list = []
        self._scale_factor: float = 1.0
        self._offset: QPoint = QPoint(0, 0)
        self._theme = THEMES["暗色标准"]

        self._is_adding_line: bool = False
        self._adding_orientation: str | None = None

        self._selected_line_id: int | None = None
        self._is_dragging: bool = False
        self._drag_start_pos: QPoint = QPoint(0, 0)
        self._drag_line_original_pos: int = 0

        self._is_cropping: bool = False
        self._crop_start_pos: QPoint = QPoint(0, 0)
        self._crop_end_pos: QPoint = QPoint(0, 0)

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
        self.update()

    def set_grid_lines(self, lines: list) -> None:
        self._grid_lines = lines
        self.update()

    def set_adding_mode(self, orientation: str | None) -> None:
        self._is_adding_line = orientation is not None
        self._adding_orientation = orientation
        if orientation:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self._is_cropping:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_cropping_mode(self, is_cropping: bool) -> None:
        self._is_cropping = is_cropping
        if is_cropping:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif self._is_adding_line:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._pixmap:
            scaled_pixmap = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._scale_factor = scaled_pixmap.width() / self._pixmap.width() if self._pixmap.width() > 0 else 1.0
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            self._offset = QPoint(x, y)
            painter.drawPixmap(x, y, scaled_pixmap)

            for line in self._grid_lines:
                pen = QPen(line.color, 2)
                if line.id == self._selected_line_id:
                    pen.setWidth(3)
                painter.setPen(pen)

                if line.orientation == 'horizontal':
                    y_pos = y + int(line.position * self._scale_factor)
                    x_start = x + int(line.start * self._scale_factor)
                    x_end = x + int((line.end if line.end is not None else scaled_pixmap.width() / self._scale_factor) * self._scale_factor)
                    painter.drawLine(x_start, y_pos, x_end, y_pos)
                else:
                    x_pos = x + int(line.position * self._scale_factor)
                    y_start = y + int(line.start * self._scale_factor)
                    y_end = y + int((line.end if line.end is not None else scaled_pixmap.height() / self._scale_factor) * self._scale_factor)
                    painter.drawLine(x_pos, y_start, x_pos, y_end)

            if self._is_cropping:
                crop_rect = QRect(self._crop_start_pos, self._crop_end_pos).normalized()
                painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(255, 255, 0, 50)))
                painter.drawRect(crop_rect)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_cropping and self._pixmap:
                self._crop_start_pos = event.pos()
                self._crop_end_pos = event.pos()
                self.update()
            elif self._is_adding_line and self._pixmap:
                img_x, img_y = self._to_image_coords(event.pos())
                if 0 <= img_x < self._pixmap.width() and 0 <= img_y < self._pixmap.height():
                    if self._adding_orientation == 'horizontal':
                        self.canvas_clicked.emit(img_x, img_y)
                    else:
                        self.canvas_clicked.emit(img_x, img_y)
            else:
                line_id = self._get_line_at(event.pos())
                if line_id is not None:
                    old_selected = self._selected_line_id
                    self._selected_line_id = line_id
                    self._is_dragging = True
                    self._drag_start_pos = event.pos()
                    line = self._get_line_by_id(line_id)
                    if line:
                        self._drag_line_original_pos = line.position
                    if old_selected != line_id:
                        self.line_selected.emit(line_id)
                    self.update()
                else:
                    if self._selected_line_id is not None:
                        self._selected_line_id = None
                        self.line_unselected.emit()
                        self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._is_cropping and event.buttons() == Qt.MouseButton.LeftButton:
            self._crop_end_pos = event.pos()
            self.update()
        elif self._is_dragging and self._selected_line_id is not None and self._pixmap:
            line = self._get_line_by_id(self._selected_line_id)
            if line:
                delta = event.pos() - self._drag_start_pos
                if line.orientation == 'horizontal':
                    new_pos = self._drag_line_original_pos + int(delta.y() / self._scale_factor)
                    new_pos = max(0, min(new_pos, self._pixmap.height()))
                else:
                    new_pos = self._drag_line_original_pos + int(delta.x() / self._scale_factor)
                    new_pos = max(0, min(new_pos, self._pixmap.width()))
                self.line_dragged.emit(self._selected_line_id, new_pos)
        else:
            line_id = self._get_line_at(event.pos())
            if line_id is not None and not self._is_cropping and not self._is_adding_line:
                line = self._get_line_by_id(line_id)
                if line:
                    if line.orientation == 'horizontal':
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                    else:
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif not self._is_cropping and not self._is_adding_line:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_cropping and self._pixmap:
                x1, y1 = self._to_image_coords(self._crop_start_pos)
                x2, y2 = self._to_image_coords(self._crop_end_pos)
                self.crop_confirmed.emit(x1, y1, x2, y2)
            self._is_dragging = False

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete and self._selected_line_id is not None:
            self.line_deleted.emit(self._selected_line_id)
            self._selected_line_id = None
            self.update()
        elif event.key() == Qt.Key.Key_Escape:
            self._is_cropping = False
            self._crop_start_pos = QPoint(0, 0)
            self._crop_end_pos = QPoint(0, 0)
            self.update()
            self.set_cropping_mode(False)

    def _to_image_coords(self, pos: QPoint) -> tuple[int, int]:
        x = int((pos.x() - self._offset.x()) / self._scale_factor)
        y = int((pos.y() - self._offset.y()) / self._scale_factor)
        return x, y

    def _get_line_at(self, pos: QPoint) -> int | None:
        threshold = 5
        for line in reversed(self._grid_lines):
            if line.orientation == 'horizontal':
                y_pos = self._offset.y() + int(line.position * self._scale_factor)
                if abs(pos.y() - y_pos) <= threshold:
                    x_min = self._offset.x() + int(line.start * self._scale_factor)
                    x_max = self._offset.x() + int((line.end if line.end is not None else (self._pixmap.width() if self._pixmap else 0)) * self._scale_factor)
                    if x_min <= pos.x() <= x_max:
                        return line.id
            else:
                x_pos = self._offset.x() + int(line.position * self._scale_factor)
                if abs(pos.x() - x_pos) <= threshold:
                    y_min = self._offset.y() + int(line.start * self._scale_factor)
                    y_max = self._offset.y() + int((line.end if line.end is not None else (self._pixmap.height() if self._pixmap else 0)) * self._scale_factor)
                    if y_min <= pos.y() <= y_max:
                        return line.id
        return None

    def _get_line_by_id(self, line_id: int):
        for line in self._grid_lines:
            if line.id == line_id:
                return line
        return None

    def get_selected_line_id(self) -> int | None:
        return self._selected_line_id

    def render_to_pixmap(self) -> QPixmap | None:
        if not self._pixmap:
            return None
        
        result = QPixmap(self._pixmap.size())
        result.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self._pixmap)
        
        for line in self._grid_lines:
            pen = QPen(line.color, 2)
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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PixelBead Grid Helper")
        self.setGeometry(100, 100, 1200, 800)
        self._current_pixmap: QPixmap | None = None
        self._current_theme = "暗色标准"
        self._setup_ui()
        self._setup_shortcuts()
        self._apply_theme()

    def _setup_ui(self) -> None:
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        self.open_button = QPushButton("打开")
        self.open_button.clicked.connect(self._on_open_clicked)
        toolbar.addWidget(self.open_button)

        self.crop_button = QPushButton("裁剪")
        self.crop_button.clicked.connect(self._on_crop_clicked)
        toolbar.addWidget(self.crop_button)

        self.export_button = QPushButton("导出")
        self.export_button.clicked.connect(self._on_export_clicked)
        toolbar.addWidget(self.export_button)

        toolbar.addWidget(QPushButton("保存"))
        toolbar.addWidget(QPushButton("撤销"))
        toolbar.addWidget(QPushButton("重做"))

        toolbar.addSeparator()

        theme_label = QLabel("主题: ")
        toolbar.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.setCurrentText(self._current_theme)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        toolbar.addWidget(self.theme_combo)

        toolbar.addSeparator()

        self.help_button = QPushButton("帮助")
        self.help_button.clicked.connect(self._on_help_clicked)
        toolbar.addWidget(self.help_button)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.canvas = ImageCanvas()
        scroll_area.setWidget(self.canvas)

        main_layout.addWidget(scroll_area, stretch=3)

        toolbox_frame = QFrame()
        toolbox_frame.setObjectName("toolbox")
        toolbox_layout = QVBoxLayout(toolbox_frame)

        toolbox_label = QLabel("工具箱")
        toolbox_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbox_layout.addWidget(toolbox_label)

        self.add_h_line_btn = QPushButton("添加横线")
        self.add_h_line_btn.clicked.connect(self._on_add_h_line_clicked)
        toolbox_layout.addWidget(self.add_h_line_btn)

        self.add_v_line_btn = QPushButton("添加纵线")
        self.add_v_line_btn.clicked.connect(self._on_add_v_line_clicked)
        toolbox_layout.addWidget(self.add_v_line_btn)

        self.delete_line_btn = QPushButton("删除选中")
        self.delete_line_btn.clicked.connect(self._on_delete_line_clicked)
        self.delete_line_btn.setEnabled(False)
        toolbox_layout.addWidget(self.delete_line_btn)

        spacing_layout = QHBoxLayout()
        spacing_label = QLabel("间距:")
        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setMinimum(1)
        self.spacing_spinbox.setMaximum(1000)
        self.spacing_spinbox.setValue(10)
        self.spacing_spinbox.valueChanged.connect(self._on_spacing_changed)
        spacing_layout.addWidget(spacing_label)
        spacing_layout.addWidget(self.spacing_spinbox)
        toolbox_layout.addLayout(spacing_layout)

        self.fill_h_btn = QPushButton("补全横线")
        self.fill_h_btn.clicked.connect(self._on_fill_h_clicked)
        self.fill_h_btn.setEnabled(False)
        toolbox_layout.addWidget(self.fill_h_btn)

        self.fill_v_btn = QPushButton("补全纵线")
        self.fill_v_btn.clicked.connect(self._on_fill_v_clicked)
        self.fill_v_btn.setEnabled(False)
        toolbox_layout.addWidget(self.fill_v_btn)

        toolbox_layout.addStretch()

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

    def _on_add_h_line_clicked(self) -> None:
        self.add_horizontal_line_requested.emit()

    def _on_add_v_line_clicked(self) -> None:
        self.add_vertical_line_requested.emit()

    def _on_delete_line_clicked(self) -> None:
        self.delete_line_requested.emit()

    def _on_spacing_changed(self, value: int) -> None:
        self.spacing_changed.emit(value)

    def _on_fill_h_clicked(self) -> None:
        self.fill_horizontal_lines_requested.emit()

    def _on_fill_v_clicked(self) -> None:
        self.fill_vertical_lines_requested.emit()

    def _on_theme_changed(self, theme_name: str) -> None:
        self._current_theme = theme_name
        self.theme_changed.emit(theme_name)
        self._apply_theme()

    def _on_help_clicked(self) -> None:
        dialog = HelpDialog(self)
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
                spacing: 3px;
            }}
            QPushButton {{
                background-color: {theme['button']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 5px 10px;
                border-radius: 3px;
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

    def set_fill_buttons_enabled(self, has_h_line: bool, has_v_line: bool) -> None:
        self.fill_h_btn.setEnabled(has_h_line)
        self.fill_v_btn.setEnabled(has_v_line)

    def set_cropping_mode(self, is_cropping: bool) -> None:
        self.canvas.set_cropping_mode(is_cropping)
        theme = THEMES[self._current_theme]
        if is_cropping:
            self.crop_button.setStyleSheet(f"background-color: {theme['accent']};")
        else:
            self.crop_button.setStyleSheet("")

    def get_spacing(self) -> int:
        return self.spacing_spinbox.value()

    def show_file_dialog(self) -> str | None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有文件 (*)"
        )
        return file_path if file_path else None

    def show_export_dialog(self) -> str | None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出图片",
            "",
            "PNG 图片 (*.png);;JPG 图片 (*.jpg *.jpeg)"
        )
        return file_path if file_path else None

    def display_image(self, pixmap: QPixmap) -> None:
        self._current_pixmap = pixmap
        self.canvas.set_pixmap(pixmap)

    def set_canvas_grid_lines(self, lines: list) -> None:
        self.canvas.set_grid_lines(lines)

    def set_canvas_adding_mode(self, orientation: str | None) -> None:
        self.canvas.set_adding_mode(orientation)
        theme = THEMES[self._current_theme]
        if orientation == 'horizontal':
            self.add_h_line_btn.setStyleSheet(f"background-color: {theme['accent']};")
            self.add_v_line_btn.setStyleSheet("")
        elif orientation == 'vertical':
            self.add_v_line_btn.setStyleSheet(f"background-color: {theme['accent']};")
            self.add_h_line_btn.setStyleSheet("")
        else:
            self.add_h_line_btn.setStyleSheet("")
            self.add_v_line_btn.setStyleSheet("")

    def refresh_canvas(self) -> None:
        self.canvas.update()

    def get_rendered_pixmap(self) -> QPixmap | None:
        return self.canvas.render_to_pixmap()
