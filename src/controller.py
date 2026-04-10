from model import ImageModel, GridLine
from view import MainWindow


class Controller:
    def __init__(self, model: ImageModel, view: MainWindow):
        self._model = model
        self._view = view
        self._adding_orientation: str | None = None
        self._selected_line: GridLine | None = None
        self._is_dragging: bool = False
        self._is_cropping: bool = False
        self._connect_signals()

    def _connect_signals(self) -> None:
        self._view.open_image_requested.connect(self._on_open_image)
        self._view.add_horizontal_line_requested.connect(self._on_add_h_line)
        self._view.add_vertical_line_requested.connect(self._on_add_v_line)
        self._view.delete_line_requested.connect(self._on_delete_button_clicked)
        self._view.fill_horizontal_lines_requested.connect(self._on_fill_h_lines)
        self._view.fill_vertical_lines_requested.connect(self._on_fill_v_lines)
        self._view.undo_requested.connect(self._on_undo)
        self._view.redo_requested.connect(self._on_redo)
        self._view.crop_requested.connect(self._on_crop)
        self._view.export_requested.connect(self._on_export)
        self._view.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self._view.canvas.line_dragged.connect(self._on_line_dragged)
        self._view.canvas.line_deleted.connect(self._on_line_deleted)
        self._view.canvas.line_selected.connect(self._on_line_selected)
        self._view.canvas.line_unselected.connect(self._on_line_unselected)
        self._view.canvas.crop_confirmed.connect(self._on_crop_confirmed)

    def _on_open_image(self) -> None:
        file_path = self._view.show_file_dialog()
        if file_path and self._model.load_image(file_path):
            self._view.display_image(self._model.qpixmap)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._adding_orientation = None
            self._view.set_canvas_adding_mode(None)
            self._view.set_delete_button_enabled(False)
            self._view.set_fill_buttons_enabled(False, False)
            self._selected_line = None

    def _on_add_h_line(self) -> None:
        if self._model.pil_image is None:
            return
        if self._adding_orientation == 'horizontal':
            self._adding_orientation = None
        else:
            self._adding_orientation = 'horizontal'
        self._view.set_canvas_adding_mode(self._adding_orientation)

    def _on_add_v_line(self) -> None:
        if self._model.pil_image is None:
            return
        if self._adding_orientation == 'vertical':
            self._adding_orientation = None
        else:
            self._adding_orientation = 'vertical'
        self._view.set_canvas_adding_mode(self._adding_orientation)

    def _on_canvas_clicked(self, x: int, y: int) -> None:
        if self._adding_orientation:
            if self._adding_orientation == 'horizontal':
                self._model.add_grid_line('horizontal', y)
            else:
                self._model.add_grid_line('vertical', x)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._adding_orientation = None
            self._view.set_canvas_adding_mode(None)

    def _on_line_dragged(self, line_id: int, new_pos: int) -> None:
        if not self._is_dragging:
            self._is_dragging = True
        line = self._model.get_grid_line(line_id)
        if line:
            line.position = new_pos
            self._view.set_canvas_grid_lines(self._model.grid_lines)

    def _on_line_deleted(self, line_id: int) -> None:
        self._model.remove_grid_line(line_id)
        self._view.set_canvas_grid_lines(self._model.grid_lines)
        self._view.set_delete_button_enabled(False)
        self._selected_line = None
        self._update_fill_buttons_state()

    def _on_delete_button_clicked(self) -> None:
        line_id = self._view.canvas.get_selected_line_id()
        if line_id is not None:
            self._model.remove_grid_line(line_id)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._view.set_delete_button_enabled(False)
            self._selected_line = None
            self._update_fill_buttons_state()

    def _on_line_selected(self, line_id: int) -> None:
        if self._is_dragging:
            self._model.update_grid_line_position(line_id, self._model.get_grid_line(line_id).position)
            self._is_dragging = False
        self._view.set_delete_button_enabled(True)
        self._selected_line = self._model.get_grid_line(line_id)
        self._update_fill_buttons_state()

    def _on_line_unselected(self) -> None:
        if self._is_dragging:
            self._is_dragging = False
        self._view.set_delete_button_enabled(False)
        self._selected_line = None
        self._update_fill_buttons_state()

    def _update_fill_buttons_state(self) -> None:
        has_h = False
        has_v = False
        if self._selected_line:
            if self._selected_line.orientation == 'horizontal':
                has_h = True
            else:
                has_v = True
        self._view.set_fill_buttons_enabled(has_h, has_v)

    def _on_undo(self) -> None:
        if self._model.undo():
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._selected_line = None
            self._view.set_delete_button_enabled(False)
            self._update_fill_buttons_state()

    def _on_redo(self) -> None:
        if self._model.redo():
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._selected_line = None
            self._view.set_delete_button_enabled(False)
            self._update_fill_buttons_state()

    def _on_crop(self) -> None:
        if self._model.pil_image is None:
            return
        self._is_cropping = not self._is_cropping
        self._view.set_cropping_mode(self._is_cropping)
        if not self._is_cropping:
            self._selected_line = None
            self._view.set_delete_button_enabled(False)
            self._update_fill_buttons_state()

    def _on_crop_confirmed(self, x1: int, y1: int, x2: int, y2: int) -> None:
        if self._is_cropping:
            self._model.apply_crop(x1, y1, x2, y2)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._is_cropping = False
            self._view.set_cropping_mode(False)
            self._selected_line = None
            self._view.set_delete_button_enabled(False)
            self._update_fill_buttons_state()

    def _on_export(self) -> None:
        if self._model.pil_image is None:
            return
        file_path = self._view.show_export_dialog()
        if file_path:
            pixmap = self._view.get_rendered_pixmap()
            if pixmap:
                pixmap.save(file_path)

    def _on_fill_h_lines(self) -> None:
        if not self._selected_line or self._selected_line.orientation != 'horizontal':
            return
        if self._model.pil_image is None:
            return

        spacing = self._view.get_spacing()
        base_pos = self._selected_line.position
        line_color = self._selected_line.color
        img_height = self._model.pil_image.height

        existing_positions = set()
        for line in self._model.grid_lines:
            if line.orientation == 'horizontal':
                existing_positions.add(line.position)

        new_lines = []
        pos = base_pos - spacing
        while pos >= 0:
            if pos not in existing_positions:
                new_line = GridLine(orientation='horizontal', position=pos, color=line_color)
                new_lines.append(new_line)
            pos -= spacing

        pos = base_pos + spacing
        while pos <= img_height:
            if pos not in existing_positions:
                new_line = GridLine(orientation='horizontal', position=pos, color=line_color)
                new_lines.append(new_line)
            pos += spacing

        if new_lines:
            self._model.batch_add_lines(new_lines)
            self._view.set_canvas_grid_lines(self._model.grid_lines)

    def _on_fill_v_lines(self) -> None:
        if not self._selected_line or self._selected_line.orientation != 'vertical':
            return
        if self._model.pil_image is None:
            return

        spacing = self._view.get_spacing()
        base_pos = self._selected_line.position
        line_color = self._selected_line.color
        img_width = self._model.pil_image.width

        existing_positions = set()
        for line in self._model.grid_lines:
            if line.orientation == 'vertical':
                existing_positions.add(line.position)

        new_lines = []
        pos = base_pos - spacing
        while pos >= 0:
            if pos not in existing_positions:
                new_line = GridLine(orientation='vertical', position=pos, color=line_color)
                new_lines.append(new_line)
            pos -= spacing

        pos = base_pos + spacing
        while pos <= img_width:
            if pos not in existing_positions:
                new_line = GridLine(orientation='vertical', position=pos, color=line_color)
                new_lines.append(new_line)
            pos += spacing

        if new_lines:
            self._model.batch_add_lines(new_lines)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
