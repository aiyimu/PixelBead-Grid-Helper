from model import ImageModel, GridLine
from view import MainWindow
from PyQt6.QtGui import QColor


class Controller:
    def __init__(self, model: ImageModel, view: MainWindow):
        self._model = model
        self._view = view
        self._adding_orientation: str | None = None
        self._is_dragging: bool = False
        self._is_cropping: bool = False
        self._is_calculating_distance: bool = False
        self._distance_first_line_id: int | None = None
        self._connect_signals()

    def _connect_signals(self) -> None:
        self._view.open_image_requested.connect(self._on_open_image)
        self._view.file_dropped.connect(self._on_file_dropped)
        self._view.add_horizontal_line_requested.connect(self._on_add_h_line)
        self._view.add_vertical_line_requested.connect(self._on_add_v_line)
        self._view.delete_line_requested.connect(self._on_delete_selected_lines)
        self._view.fill_horizontal_lines_requested.connect(self._on_fill_h_lines)
        self._view.fill_vertical_lines_requested.connect(self._on_fill_v_lines)
        self._view.undo_requested.connect(self._on_undo)
        self._view.redo_requested.connect(self._on_redo)
        self._view.crop_requested.connect(self._on_crop)
        self._view.export_requested.connect(self._on_export)
        self._view.canvas.canvas_clicked.connect(self._on_canvas_clicked)
        self._view.canvas.line_dragged.connect(self._on_line_dragged)
        self._view.canvas.line_selected.connect(self._on_line_selected)
        self._view.canvas.line_toggled.connect(self._on_line_toggled)
        self._view.canvas.all_deselected.connect(self._on_all_deselected)
        self._view.canvas.crop_confirmed.connect(self._on_crop_confirmed)
        self._view.canvas.rect_selection_confirmed.connect(self._on_rect_selection_confirmed)
        self._view.canvas.delete_selected_requested.connect(self._on_delete_selected_lines)
        self._view.canvas.select_all_requested.connect(self._on_select_all)
        self._view.canvas.deselect_all_requested.connect(self._on_deselect_all)
        self._view.select_tool_requested.connect(self._on_select_tool)
        self._view.rect_select_tool_requested.connect(self._on_rect_select_tool)
        self._view.thickness_changed.connect(self._on_thickness_changed)
        self._view.color_changed.connect(self._on_color_changed)
        self._view.style_changed.connect(self._on_style_changed)
        self._view.calculate_distance_requested.connect(self._on_calculate_distance)
        self._view.canvas.calculate_distance_line_selected.connect(self._on_calculate_distance_line_selected)

    def _on_open_image(self) -> None:
        file_path = self._view.show_file_dialog()
        if file_path and self._model.load_image(file_path):
            self._model.deselect_all()
            self._view.display_image(self._model.qpixmap)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
            self._adding_orientation = None
            self._view.set_canvas_adding_mode(None)
            self._update_selection_ui()

    def _on_file_dropped(self, file_path: str) -> None:
        """Handle file dropped on canvas"""
        if file_path and self._model.load_image(file_path):
            self._model.deselect_all()
            self._view.display_image(self._model.qpixmap)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
            self._adding_orientation = None
            self._view.set_canvas_adding_mode(None)
            self._update_selection_ui()

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
        line = self._model.get_grid_line(line_id)
        if line:
            line.position = new_pos
            self._view.set_canvas_grid_lines(self._model.grid_lines)

    def _on_line_selected(self, line_id: int) -> None:
        self._model.deselect_all()
        self._model.select_line(line_id)
        self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
        self._update_selection_ui()

    def _on_line_toggled(self, line_id: int) -> None:
        self._model.toggle_line_selection(line_id)
        self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
        self._update_selection_ui()

    def _on_all_deselected(self) -> None:
        if self._is_dragging:
            self._model._save_state()
            self._is_dragging = False
        self._model.deselect_all()
        self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
        self._update_selection_ui()

    def _on_rect_selection_confirmed(self, x1: int, y1: int, x2: int, y2: int) -> None:
        line_ids = self._model.get_lines_in_rect(x1, y1, x2, y2)
        self._model.deselect_all()
        for line_id in line_ids:
            self._model.select_line(line_id)
        self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
        self._update_selection_ui()

    def _on_select_all(self) -> None:
        self._model.select_all()
        self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
        self._update_selection_ui()

    def _on_deselect_all(self) -> None:
        self._model.deselect_all()
        self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
        self._update_selection_ui()

    def _on_delete_selected_lines(self) -> None:
        count = self._model.delete_selected_lines()
        if count > 0:
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
            self._update_selection_ui()

    def _update_selection_ui(self) -> None:
        has_selection = len(self._model.selected_line_ids) > 0
        self._view.set_delete_button_enabled(has_selection)
        self._view.set_selection_count(len(self._model.selected_line_ids))
        
        has_h = False
        has_v = False
        if len(self._model.selected_line_ids) == 1:
            line = self._model.get_grid_line(self._model.selected_line_ids[0])
            if line:
                if line.orientation == 'horizontal':
                    has_h = True
                else:
                    has_v = True
                self._view.set_thickness_value(line.thickness)
                self._view.set_color_preview(line.color)
                style_map = {"solid": 0, "dashed": 1, "dotted": 2}
                self._view.set_style_value(style_map.get(line.style, 0))
        self._view.set_fill_buttons_enabled(has_h, has_v)

    def _on_thickness_changed(self, thickness: int) -> None:
        if self._model.selected_line_ids:
            self._model.update_selected_lines_thickness(thickness)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
        else:
            self._model.default_thickness = thickness

    def _on_color_changed(self, color: QColor) -> None:
        if self._model.selected_line_ids:
            self._model.update_selected_lines_color(color)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
        else:
            self._model.default_color = color

    def _on_style_changed(self, style: str) -> None:
        if self._model.selected_line_ids:
            self._model.update_selected_lines_style(style)
            self._view.set_canvas_grid_lines(self._model.grid_lines)
        else:
            self._model.default_style = style

    def _on_select_tool(self) -> None:
        self._view._update_tool_buttons("select")

    def _on_rect_select_tool(self) -> None:
        self._view._update_tool_buttons("rect_select")

    def _on_undo(self) -> None:
        if self._model.undo():
            self._model.deselect_all()
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
            self._update_selection_ui()

    def _on_redo(self) -> None:
        if self._model.redo():
            self._model.deselect_all()
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
            self._update_selection_ui()

    def _on_crop(self) -> None:
        if self._model.pil_image is None:
            return
        self._is_cropping = not self._is_cropping
        self._view.set_cropping_mode(self._is_cropping)
        if not self._is_cropping:
            self._update_selection_ui()

    def _on_crop_confirmed(self, x1: int, y1: int, x2: int, y2: int) -> None:
        if self._is_cropping:
            self._model.apply_crop(x1, y1, x2, y2)
            self._model.deselect_all()
            self._view.set_canvas_grid_lines(self._model.grid_lines)
            self._view.set_canvas_selected_line_ids(self._model.selected_line_ids)
            self._is_cropping = False
            self._view.set_cropping_mode(False)
            self._update_selection_ui()

    def _on_export(self) -> None:
        if self._model.pil_image is None:
            return
        file_path = self._view.show_export_dialog()
        if file_path:
            pixmap = self._view.get_rendered_pixmap()
            if pixmap:
                pixmap.save(file_path)

    def _on_fill_h_lines(self) -> None:
        if len(self._model.selected_line_ids) != 1:
            return
        line = self._model.get_grid_line(self._model.selected_line_ids[0])
        if not line or line.orientation != 'horizontal':
            return
        if self._model.pil_image is None:
            return

        spacing = self._view.get_spacing()
        base_pos = line.position
        img_height = self._model.pil_image.height

        existing_positions = set()
        for l in self._model.grid_lines:
            if l.orientation == 'horizontal':
                existing_positions.add(l.position)

        new_lines = []
        pos = base_pos - spacing
        while pos >= 0:
            if pos not in existing_positions:
                new_line = GridLine(
                    orientation='horizontal',
                    position=pos,
                    color=line.color,
                    thickness=line.thickness,
                    style=line.style
                )
                new_lines.append(new_line)
            pos -= spacing

        pos = base_pos + spacing
        while pos <= img_height:
            if pos not in existing_positions:
                new_line = GridLine(
                    orientation='horizontal',
                    position=pos,
                    color=line.color,
                    thickness=line.thickness,
                    style=line.style
                )
                new_lines.append(new_line)
            pos += spacing

        if new_lines:
            self._model.batch_add_lines(new_lines)
            self._view.set_canvas_grid_lines(self._model.grid_lines)

    def _on_fill_v_lines(self) -> None:
        if len(self._model.selected_line_ids) != 1:
            return
        line = self._model.get_grid_line(self._model.selected_line_ids[0])
        if not line or line.orientation != 'vertical':
            return
        if self._model.pil_image is None:
            return

        spacing = self._view.get_spacing()
        base_pos = line.position
        img_width = self._model.pil_image.width

        existing_positions = set()
        for l in self._model.grid_lines:
            if l.orientation == 'vertical':
                existing_positions.add(l.position)

        new_lines = []
        pos = base_pos - spacing
        while pos >= 0:
            if pos not in existing_positions:
                new_line = GridLine(
                    orientation='vertical',
                    position=pos,
                    color=line.color,
                    thickness=line.thickness,
                    style=line.style
                )
                new_lines.append(new_line)
            pos -= spacing

        pos = base_pos + spacing
        while pos <= img_width:
            if pos not in existing_positions:
                new_line = GridLine(
                    orientation='vertical',
                    position=pos,
                    color=line.color,
                    thickness=line.thickness,
                    style=line.style
                )
                new_lines.append(new_line)
            pos += spacing

        if new_lines:
            self._model.batch_add_lines(new_lines)
            self._view.set_canvas_grid_lines(self._model.grid_lines)

    def _on_calculate_distance(self) -> None:
        if self._model.pil_image is None:
            return
        self._is_calculating_distance = True
        self._distance_first_line_id = None
        self._view.set_calculating_distance_mode(True)

    def _on_calculate_distance_line_selected(self, line_id: int) -> None:
        if not self._is_calculating_distance:
            return
        
        line = self._model.get_grid_line(line_id)
        if not line:
            return
        
        if self._distance_first_line_id is None:
            # 第一条线选中
            self._distance_first_line_id = line_id
        else:
            # 第二条线选中，计算距离
            first_line = self._model.get_grid_line(self._distance_first_line_id)
            if first_line and first_line.orientation == line.orientation:
                # 两条线平行，计算距离
                distance = abs(line.position - first_line.position)
                self._view.show_distance_dialog(distance, first_line.position, line.position)
            # 重置状态
            self._is_calculating_distance = False
            self._distance_first_line_id = None
            self._view.set_calculating_distance_mode(False)
