from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from PIL import Image
from PyQt6.QtGui import QPixmap, QImage, QColor, QPainter


@dataclass
class GridLine:
    id: int = field(default_factory=lambda: GridLine._next_id())
    orientation: str = 'horizontal'  # 'horizontal' or 'vertical'
    position: int = 0
    color: QColor = field(default_factory=lambda: QColor(255, 0, 0))
    start: int = 0
    end: Optional[int] = None
    thickness: int = 2
    style: str = 'solid'  # 'solid', 'dashed', 'dotted'

    _id_counter: int = 0

    @classmethod
    def _next_id(cls) -> int:
        cls._id_counter += 1
        return cls._id_counter

    def copy(self) -> 'GridLine':
        return GridLine(
            id=self.id,
            orientation=self.orientation,
            position=self.position,
            color=QColor(self.color),
            start=self.start,
            end=self.end,
            thickness=self.thickness,
            style=self.style
        )


class ImageModel:
    def __init__(self):
        self._pil_image: Image.Image | None = None
        self._qpixmap: QPixmap | None = None
        self._image_path: str | None = None
        self._grid_lines: list[GridLine] = []
        self._history: list[list[GridLine]] = []
        self._history_index: int = -1
        self._max_history: int = 50
        self._selected_line_ids: List[int] = []
        self._default_thickness: int = 2
        self._default_color: QColor = QColor(255, 0, 0)
        self._default_style: str = 'solid'

    @property
    def pil_image(self) -> Image.Image | None:
        return self._pil_image

    @property
    def qpixmap(self) -> QPixmap | None:
        return self._qpixmap

    @property
    def image_path(self) -> str | None:
        return self._image_path

    @property
    def grid_lines(self) -> list[GridLine]:
        return self._grid_lines

    def load_image(self, file_path: str) -> bool:
        try:
            self._pil_image = Image.open(file_path)
            self._image_path = file_path
            self._convert_to_qpixmap()
            self._grid_lines.clear()
            self._history.clear()
            self._history_index = -1
            return True
        except Exception:
            return False

    def _convert_to_qpixmap(self) -> None:
        if self._pil_image is None:
            return
        pil_image = self._pil_image

        if pil_image.mode == "RGB":
            qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height,
                            pil_image.width * 3, QImage.Format.Format_RGB888)
        elif pil_image.mode == "RGBA":
            qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height,
                            pil_image.width * 4, QImage.Format.Format_RGBA8888)
        else:
            pil_image = pil_image.convert("RGBA")
            qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height,
                            pil_image.width * 4, QImage.Format.Format_RGBA8888)

        self._qpixmap = QPixmap.fromImage(qimage)

    def _save_state(self) -> None:
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]

        state = [line.copy() for line in self._grid_lines]
        self._history.append(state)

        if len(self._history) > self._max_history:
            self._history.pop(0)
        else:
            self._history_index += 1

    def can_undo(self) -> bool:
        return self._history_index > 0

    def can_redo(self) -> bool:
        return self._history_index < len(self._history) - 1

    def undo(self) -> bool:
        if not self.can_undo():
            return False
        self._history_index -= 1
        self._restore_state(self._history[self._history_index])
        return True

    def redo(self) -> bool:
        if not self.can_redo():
            return False
        self._history_index += 1
        self._restore_state(self._history[self._history_index])
        return True

    def _restore_state(self, state: list[GridLine]) -> None:
        self._grid_lines = [line.copy() for line in state]

    def add_grid_line(self, orientation: str, position: int, color: QColor | None = None, start: int = 0, end: Optional[int] = None, thickness: int | None = None, style: str | None = None) -> GridLine:
        self._save_state()
        line = GridLine(
            orientation=orientation,
            position=position,
            color=color if color is not None else self._default_color,
            start=start,
            end=end,
            thickness=thickness if thickness is not None else self._default_thickness,
            style=style if style is not None else self._default_style
        )
        self._grid_lines.append(line)
        return line

    @property
    def default_thickness(self) -> int:
        return self._default_thickness

    @default_thickness.setter
    def default_thickness(self, value: int) -> None:
        self._default_thickness = max(1, min(10, value))

    @property
    def default_color(self) -> QColor:
        return self._default_color

    @default_color.setter
    def default_color(self, value: QColor) -> None:
        self._default_color = value

    @property
    def default_style(self) -> str:
        return self._default_style

    @default_style.setter
    def default_style(self, value: str) -> None:
        self._default_style = value

    def update_selected_lines_thickness(self, thickness: int) -> None:
        if not self._selected_line_ids:
            return
        self._save_state()
        for line_id in self._selected_line_ids:
            line = self.get_grid_line(line_id)
            if line:
                line.thickness = max(1, min(10, thickness))

    def update_selected_lines_color(self, color: QColor) -> None:
        if not self._selected_line_ids:
            return
        self._save_state()
        for line_id in self._selected_line_ids:
            line = self.get_grid_line(line_id)
            if line:
                line.color = color

    def update_selected_lines_style(self, style: str) -> None:
        if not self._selected_line_ids:
            return
        self._save_state()
        for line_id in self._selected_line_ids:
            line = self.get_grid_line(line_id)
            if line:
                line.style = style

    def remove_grid_line(self, line_id: int) -> bool:
        line = self.get_grid_line(line_id)
        if line:
            self._save_state()
            for i, l in enumerate(self._grid_lines):
                if l.id == line_id:
                    del self._grid_lines[i]
                    return True
        return False

    def update_grid_line_position(self, line_id: int, new_position: int) -> bool:
        line = self.get_grid_line(line_id)
        if line and line.position != new_position:
            self._save_state()
            line.position = new_position
            return True
        return False

    def get_grid_line(self, line_id: int) -> GridLine | None:
        for line in self._grid_lines:
            if line.id == line_id:
                return line
        return None

    def batch_add_lines(self, lines: list[GridLine]) -> None:
        self._save_state()
        for line in lines:
            self._grid_lines.append(line)

    def apply_crop(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self._save_state()
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)

        new_lines = []
        for line in self._grid_lines:
            if line.orientation == 'horizontal':
                line_start = line.start
                line_end = line.end if line.end is not None else (self._pil_image.width if self._pil_image else 0)
                
                # 如果线的 y 坐标不在裁剪框内，保留整条线
                if line.position < min_y or line.position > max_y:
                    new_lines.append(line.copy())
                else:
                    # 线的 y 坐标在裁剪框内，检查是否与裁剪框的 x 范围相交
                    # 如果不相交，保留整条线
                    if line_end <= min_x or line_start >= max_x:
                        new_lines.append(line.copy())
                    else:
                        # 相交，分成两段
                        # 左边部分（裁剪框左侧）
                        if line_start < min_x:
                            new_line_left = line.copy()
                            new_line_left.start = line_start
                            new_line_left.end = min_x
                            new_lines.append(new_line_left)
                        # 右边部分（裁剪框右侧）
                        if line_end > max_x:
                            new_line_right = line.copy()
                            new_line_right.start = max_x
                            new_line_right.end = line_end
                            new_lines.append(new_line_right)
            else:
                line_start = line.start
                line_end = line.end if line.end is not None else (self._pil_image.height if self._pil_image else 0)
                
                # 如果线的 x 坐标不在裁剪框内，保留整条线
                if line.position < min_x or line.position > max_x:
                    new_lines.append(line.copy())
                else:
                    # 线的 x 坐标在裁剪框内，检查是否与裁剪框的 y 范围相交
                    # 如果不相交，保留整条线
                    if line_end <= min_y or line_start >= max_y:
                        new_lines.append(line.copy())
                    else:
                        # 相交，分成两段
                        # 上边部分（裁剪框上侧）
                        if line_start < min_y:
                            new_line_top = line.copy()
                            new_line_top.start = line_start
                            new_line_top.end = min_y
                            new_lines.append(new_line_top)
                        # 下边部分（裁剪框下侧）
                        if line_end > max_y:
                            new_line_bottom = line.copy()
                            new_line_bottom.start = max_y
                            new_line_bottom.end = line_end
                            new_lines.append(new_line_bottom)
        
        self._grid_lines = new_lines

    @property
    def selected_line_ids(self) -> List[int]:
        return self._selected_line_ids

    def select_line(self, line_id: int) -> None:
        if line_id not in self._selected_line_ids:
            self._selected_line_ids.append(line_id)

    def deselect_line(self, line_id: int) -> None:
        if line_id in self._selected_line_ids:
            self._selected_line_ids.remove(line_id)

    def toggle_line_selection(self, line_id: int) -> None:
        if line_id in self._selected_line_ids:
            self._selected_line_ids.remove(line_id)
        else:
            self._selected_line_ids.append(line_id)

    def select_all(self) -> None:
        self._selected_line_ids = [line.id for line in self._grid_lines]

    def deselect_all(self) -> None:
        self._selected_line_ids = []

    def is_line_selected(self, line_id: int) -> bool:
        return line_id in self._selected_line_ids

    def delete_selected_lines(self) -> int:
        if not self._selected_line_ids:
            return 0
        self._save_state()
        count = 0
        new_lines = []
        for line in self._grid_lines:
            if line.id not in self._selected_line_ids:
                new_lines.append(line)
            else:
                count += 1
        self._grid_lines = new_lines
        self._selected_line_ids = []
        return count

    def get_lines_in_rect(self, x1: int, y1: int, x2: int, y2: int) -> List[int]:
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)
        
        result = []
        for line in self._grid_lines:
            if line.orientation == 'horizontal':
                line_start = line.start
                line_end = line.end if line.end is not None else (self._pil_image.width if self._pil_image else 0)
                
                if min_y <= line.position <= max_y:
                    if not (line_end < min_x or line_start > max_x):
                        result.append(line.id)
            else:
                line_start = line.start
                line_end = line.end if line.end is not None else (self._pil_image.height if self._pil_image else 0)
                
                if min_x <= line.position <= max_x:
                    if not (line_end < min_y or line_start > max_y):
                        result.append(line.id)
        return result
