"""Flet workspace for the rabbet box designer."""

import flet as ft
from flet import canvas as cv

from models import (
    BoxParameters,
    dxf_document,
    fit_preview,
    flat_preview_geometry,
    preview_geometry,
)


class DesignerWorkspace(ft.Column):
    def __init__(self, page: ft.Page):
        self._page = page
        self._picker = ft.FilePicker()
        self._page.services.append(self._picker)
        self._parameters = BoxParameters()
        self._selected_part: str | None = None
        self._page.on_resize = self._on_page_resize

        self._lid_type_selector = ft.Dropdown(
            label="Lid type",
            value=self._parameters.lid_type,
            options=[
                ft.DropdownOption(key="None", text="None"),
                ft.DropdownOption(key="Sliding", text="Sliding"),
            ],
            color=ft.Colors.BLACK,
            fill_color=ft.Colors.WHITE,
            on_select=self._select_lid_type,
            on_focus=lambda event: self._set_explanation(
                "Choose None for the open-box panel arrangement, or Sliding to include the sliding lid."
            ),
        )
        self._part_selector = ft.Dropdown(
            label="Display part",
            value="all",
            options=[
                ft.DropdownOption(key="all", text="All"),
                ft.DropdownOption(key="front", text="Front"),
                ft.DropdownOption(key="back", text="Back"),
                ft.DropdownOption(key="left-side", text="Left-side"),
                ft.DropdownOption(key="right-side", text="Right-side"),
                ft.DropdownOption(key="top", text="Top"),
                ft.DropdownOption(key="bottom", text="Bottom"),
            ],
            color=ft.Colors.BLACK,
            fill_color=ft.Colors.WHITE,
            on_select=self._select_part,
            on_focus=lambda event: self._set_explanation(
                "Choose All to show the full box, or isolate a panel. Top selects the sliding lid, or shows no geometry when Lid type is None."
            ),
        )

        self._cutout_tool_selector = ft.Dropdown(
            label="Cutout tool diameter",
            value=6.7,
            options=[
                ft.DropdownOption(key=3.3, text="3mm"),
                ft.DropdownOption(key=3.5, text="3.175mm (1/8″)"),
                ft.DropdownOption(key=6.6, text="6mm"),
                ft.DropdownOption(key=6.7, text="6.35mm (1/4″)"),
                ft.DropdownOption(key=8.8, text="8mm (5/16″)"),
            ],
            color=ft.Colors.BLACK,
            fill_color=ft.Colors.WHITE,
            on_select=self._refresh,
            on_focus=lambda event: self._set_explanation(
                "Set the cutter diameter used to enlarge the bottom panel's outer Rabbet contour."
            ),
        )

        self._width, self._width_control = self._dimension_field(
            "Box width", "300", nudges=True
        )
        self._depth, self._depth_control = self._dimension_field(
            "Box depth", "200", nudges=True
        )
        self._height, self._height_control = self._dimension_field(
            "Box height", "100", nudges=True
        )
        self._thickness, self._thickness_control = self._dimension_field(
            "Stock thickness", "8"
        )

        self._separation_text = ft.Text("Part separation: 0 mm", color=ft.Colors.BLACK)
        self._separation = ft.Slider(
            min=0,
            max=10,
            divisions=100,
            value=0,
            on_change=self._refresh,
            on_focus=lambda event: self._set_explanation(
                "Part separation controls how far the box components move apart in the assembled / exploded view. The range is 0–10 stock thicknesses."
            ),
        )
        self._lid_position_text = ft.Text("Lid position: 0 mm", color=ft.Colors.BLACK)
        self._lid_position = ft.Slider(
            min=0,
            max=self._lid_travel_limit(),
            divisions=100,
            value=0,
            on_change=self._refresh,
            on_focus=lambda event: self._set_explanation(self._lid_position_help()),
        )

        self._canvas_height = self._preview_height(self._page.height or 720)
        self._view_canvas_width = 400.0
        self._view_canvas_height = self._canvas_height
        self._flat_canvas_width = 400.0
        self._flat_canvas_height = self._canvas_height
        self._view_canvas = cv.Canvas(
            height=self._canvas_height,
            shapes=[],
            expand=True,
            on_resize=lambda event: self._on_canvas_resize(event, "view"),
        )
        self._flat_canvas = cv.Canvas(
            height=self._canvas_height,
            shapes=[],
            expand=True,
            on_resize=lambda event: self._on_canvas_resize(event, "flat"),
        )
        self._layers_text = ft.Text(
            self._layer_list_text(),
            color=ft.Colors.BLACK,
            no_wrap=False,
        )
        self._status = ft.Text("", color=ft.Colors.BLACK)
        self._show_parameters = True
        self._show_assembled = True
        self._show_flat = True
        self._normal_parameter_width: float | None = None
        self._normal_parameter_reference_width: float | None = None
        self._explanation = ft.Text(
            "Focus a parameter or slider to see what it controls.",
            color=ft.Colors.BLACK,
        )
        self._explanation_pane = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("CONTROL GUIDE", color=ft.Colors.BLACK),
                    self._explanation,
                ],
                expand=True,
            ),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_500),
            expand=1,
        )

        self._parameters_pane = ft.Container(
            content=ft.Column(
                controls=[
                    ft.TextButton(
                        content="PARAMETERS",
                        icon=ft.Icons.TUNE,
                        tooltip="Collapse Parameters",
                        on_click=self._toggle_parameters,
                    ),
                    self._width_control,
                    self._depth_control,
                    self._height_control,
                    self._thickness_control,
                    self._lid_type_selector,
                    self._part_selector,
                    self._cutout_tool_selector,                    
                    ft.Divider(),
                    ft.TextButton(
                        content="Sliding box option discussed in this YouTube video",
                        url="https://www.youtube.com/watch?v=V93xDM3lXsM",
                    ),
                    ft.TextButton(
                        content=".c2d template available on Cutrocket",
                        url="https://cutrocket.com/p/x3snfnc9k1mx8",
                    ),
                    self._layers_text,
                    ft.Button(
                        content="Export layered DXF",
                        icon=ft.Icons.FILE_DOWNLOAD,
                        on_click=self._export_dxf,
                    ),
                    self._status,
                    ft.Container(expand=True),
                    ft.Row(
                        controls=[
                            ft.Text("A ", color=ft.Colors.BLACK),
                            ft.TextButton(
                                content="Design into 3D",
                                url="https://willadams.gitbook.io/design-into-3d",
                            ),
                            ft.Text(" ", color=ft.Colors.BLACK),
                            ft.TextButton(
                                content="Project",
                                url="https://willadams.gitbook.io/design-into-3d/3d-project",
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                expand=True,
            ),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_500),
            expand=1,
        )
        self._assembled_pane = ft.Container(
            content=ft.Column(
                controls=[
                    ft.TextButton(
                        content="ASSEMBLED / EXPLODED",
                        icon=ft.Icons.INVENTORY_2,
                        tooltip="Collapse Assembled / Exploded view",
                        on_click=self._toggle_assembled,
                    ),
                    ft.Container(
                        content=self._view_canvas,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.Border.all(1, ft.Colors.GREY_500),
                        expand=True,
                    ),
                    self._separation_text,
                    self._separation,
                    self._lid_position_text,
                    self._lid_position,
                ],
                expand=True,
            ),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_500),
            expand=1,
        )
        self._flat_pane = ft.Container(
            content=ft.Column(
                controls=[
                    ft.TextButton(
                        content="FLAT / CUTTING LAYOUT",
                        icon=ft.Icons.CARPENTER,
                        tooltip="Collapse Flat / Cutting Layout",
                        on_click=self._toggle_flat,
                    ),
                    ft.Container(
                        content=self._flat_canvas,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.Border.all(1, ft.Colors.GREY_500),
                        expand=True,
                    ),
                    ft.Text(
                        "Dimensions are in millimetres; part outlines include clearance boxes.",
                        color=ft.Colors.BLACK,
                    ),
                ],
                expand=True,
            ),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_500),
            expand=1,
        )

        super().__init__(controls=[], expand=True)
        self._set_layout()
        self._set_slider_labels()
        self._set_previews()

    def _set_explanation(self, text: str) -> None:
        self._explanation.value = text
        self.update()

    def _toggle_parameters(self, _event) -> None:
        self._show_parameters = not self._show_parameters
        self._finish_layout_change()

    def _toggle_assembled(self, _event) -> None:
        self._show_assembled = not self._show_assembled
        self._finish_layout_change()

    def _toggle_flat(self, _event) -> None:
        self._show_flat = not self._show_flat
        self._finish_layout_change()

    def _finish_layout_change(self) -> None:
        if not any((self._show_parameters, self._show_assembled, self._show_flat)):
            self._show_parameters = True
        self._set_layout()
        self.update()

    def _collapsed_button(self, label: str, icon, callback):
        return ft.Container(
            width=42,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_500),
            content=ft.Column(
                controls=[
                    ft.IconButton(
                        icon=icon,
                        tooltip=f"Restore {label}",
                        icon_color=ft.Colors.BLACK,
                        on_click=callback,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _set_layout(self) -> None:
        """Rebuild the three-pane row with expanded panes and restore bars."""
        items = []
        if self._show_parameters:
            if self._show_assembled and self._show_flat:
                # In the normal three-pane layout, equal flex establishes the
                # reference size which is captured from the preview canvas.
                self._parameters_pane.width = None
                self._parameters_pane.expand = 1
            elif self._normal_parameter_width is not None:
                # Pin the Parameters pane to its measured normal width; the
                # remaining visible pane(s) absorb the collapsed pane space.
                width = self._normal_parameter_width
                if self._normal_parameter_reference_width and self._page.width:
                    width *= self._page.width / self._normal_parameter_reference_width
                self._parameters_pane.width = width
                self._parameters_pane.expand = None
            else:
                self._parameters_pane.width = None
                self._parameters_pane.expand = 1
            items.append(self._parameters_pane)
        else:
            items.append(
                self._collapsed_button(
                    "Parameters", ft.Icons.TUNE, self._toggle_parameters
                )
            )

        if self._show_assembled:
            self._assembled_pane.expand = 1
            items.append(self._assembled_pane)
        else:
            items.append(
                self._collapsed_button(
                    "Assembled / Exploded", ft.Icons.INVENTORY_2, self._toggle_assembled
                )
            )

        if self._show_flat:
            self._flat_pane.expand = 1
            items.append(self._flat_pane)
        else:
            items.append(
                self._collapsed_button(
                    "Flat / Cutting Layout", ft.Icons.CARPENTER, self._toggle_flat
                )
            )

        if self._show_parameters and not self._show_assembled and not self._show_flat:
            # The guide fills all space not reserved for Parameters; both
            # collapsed view restore bars stay narrow.
            self._explanation_pane.expand = 1
            items = [
                self._parameters_pane,
                self._explanation_pane,
                self._collapsed_button(
                    "Assembled / Exploded", ft.Icons.INVENTORY_2, self._toggle_assembled
                ),
                self._collapsed_button(
                    "Flat / Cutting Layout", ft.Icons.CARPENTER, self._toggle_flat
                ),
            ]

        self.controls = [
            ft.Row(
                controls=items,
                expand=True,
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        ]

    @staticmethod
    def _preview_height(page_height: float) -> float:
        """Leave enough vertical room for each pane's controls."""
        return max(220.0, min(450.0, page_height - 220.0))

    def _lid_travel_limit(self) -> float:
        if self._parameters.lid_type == "Sliding":
            return self._parameters.depth + 10 * self._parameters.thickness
        return 0.0

    def _lid_position_help(self) -> str:
        if self._parameters.lid_type == "Sliding":
            return "Lid position moves the sliding lid from closed (0 mm) through the box depth plus ten stock thicknesses."
        return "The lid-position control is inactive because Lid type is None."

    def _on_page_resize(self, event) -> None:
        self._canvas_height = self._preview_height(event.height)
        self._set_layout()
        self._view_canvas.height = self._canvas_height
        self._flat_canvas.height = self._canvas_height
        self._set_previews()
        self.update()

    def _dimension_field(self, label: str, value: str, nudges: bool = False):
        explanation = {
            "Box width": "Outside width of the box, in millimetres. The side panels determine this overall dimension.",
            "Box depth": "Outside front-to-back depth of the box, in millimetres.",
            "Box height": "Outside height of the assembled box, in millimetres.",
            "Stock thickness": "Thickness of the board stock. Rabbet widths are derived from this value.",
        }.get(label, "Edit this box dimension in millimetres.")
        field = ft.TextField(
            label=label,
            value=value,
            color=ft.Colors.BLACK,
            bgcolor=ft.Colors.WHITE,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_blur=self._refresh,
            on_submit=self._refresh,
            on_focus=lambda event: self._set_explanation(explanation),
            expand=True,
        )
        controls = [field]
        if nudges:
            controls.append(
                ft.Column(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.KEYBOARD_ARROW_UP,
                            icon_size=12,
                            width=16,
                            height=16,
                            padding=ft.Padding.zero(),
                            on_click=lambda event: self._nudge(field, 1),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                            icon_size=12,
                            width=16,
                            height=16,
                            padding=ft.Padding.zero(),
                            on_click=lambda event: self._nudge(field, -1),
                        ),
                    ],
                    spacing=0,
                    tight=True,
                )
            )
        else:
            controls.append(ft.Container(width=16))
        return field, ft.Row(
            controls=controls,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _nudge(self, field: ft.TextField, amount: float) -> None:
        try:
            field.value = f"{max(1, float(field.value or 0) + amount):g}"
        except ValueError:
            field.value = "1"
        self._refresh(None)

    def _read_parameters(self) -> BoxParameters:
        return BoxParameters(
            width=float(self._width.value or 0),
            depth=float(self._depth.value or 0),
            height=float(self._height.value or 0),
            thickness=float(self._thickness.value or 0),
            lid_type=self._lid_type_selector.value or "Sliding",
            cutout_tool_diameter=float(self._cutout_tool_selector.value or 6.35),
        )

    def _select_lid_type(self, event) -> None:
        self._lid_position.value = 0
        self._refresh(event)

    def _part_name_for_selection(self, value: str | None) -> str | None:
        if value in (None, "all"):
            return None
        names = {
            "front": "Front",
            "back": "Back",
            "left-side": "Left side",
            "right-side": "Right side",
            "bottom": "Bottom",
        }
        if value == "top":
            if self._parameters.lid_type == "Sliding":
                return "Sliding lid"
            return "Lid (none)"
        return names.get(value)

    def _select_part(self, event) -> None:
        self._selected_part = self._part_name_for_selection(event.control.value)
        self._set_previews()
        self.update()

    def _layer_list_text(self) -> str:
        layers = ["OUTLINES", "RABBETS", "CUT_LINES", "DIMENSIONS"]
        return "Layers:\n" + "\n".join(layers)

    def _refresh(self, _event) -> None:
        try:
            self._parameters = self._read_parameters()
            self._parameters.validate()
            self._selected_part = self._part_name_for_selection(self._part_selector.value)
            self._lid_position.max = max(1.0, self._lid_travel_limit())
            self._lid_position.disabled = self._parameters.lid_type == "None"
            if float(self._lid_position.value or 0) > self._lid_travel_limit():
                self._lid_position.value = self._lid_travel_limit()
            for field in (self._width, self._depth, self._height, self._thickness):
                field.error_text = None
            self._status.value = ""
            self._set_slider_labels()
            self._set_previews()
        except ValueError as error:
            self._status.value = f"Check dimensions: {error}"
        self.update()

    def _set_slider_labels(self) -> None:
        separation = float(self._separation.value or 0) * self._parameters.thickness
        lid_position = float(self._lid_position.value or 0)
        self._separation_text.value = f"Part separation: {separation:g} mm"
        if self._parameters.lid_type == "Sliding":
            self._lid_position_text.value = (
                f"Lid position: {lid_position:g} mm / {self._lid_travel_limit():g} mm"
            )
        else:
            self._lid_position_text.value = "Lid position: unavailable (no lid)"

    def _on_canvas_resize(self, event, canvas_name: str) -> None:
        if event.width < 100 or event.height < 100:
            return
        if canvas_name == "view":
            self._view_canvas_width = event.width
            self._view_canvas_height = event.height
            if self._show_parameters and self._show_assembled and self._show_flat:
                # The assembled canvas is inset by the pane's 16px padding and
                # 1px border on each side; use it to record the true pane width.
                self._normal_parameter_width = event.width + 34.0
                self._normal_parameter_reference_width = self._page.width
        else:
            self._flat_canvas_width = event.width
            self._flat_canvas_height = event.height
        self._set_previews()
        self.update()

    def _set_previews(self) -> None:
        separation = float(self._separation.value or 0) * self._parameters.thickness
        lid_position = float(self._lid_position.value or 0)
        view_commands = fit_preview(
            preview_geometry(
                self._parameters,
                separation,
                lid_position,
                self._selected_part,
            ),
            self._view_canvas_width,
            self._view_canvas_height,
        )
        flat_commands = fit_preview(
            flat_preview_geometry(self._parameters, self._selected_part),
            self._flat_canvas_width,
            self._flat_canvas_height,
        )
        # Optional per-primitive colors for the assembled / exploded drawing.
        # Keys are zero-based positions in view_commands; entries affect only
        # that individual line, rectangle, or text primitive. Uncomment and
        # edit the sample mapping to enable overrides (indices follow the
        # generated command order and can change when part selection changes).
        view_color_overrides = {}
        # view_color_overrides = {0: ft.Colors.RED, 1: ft.Colors.BLUE}
        self._view_canvas.shapes = self._shapes(view_commands, view_color_overrides)

        # Optional per-primitive colors for the flat / cutting layout, using
        # its independent command indexes and override mapping.
        flat_color_overrides = {}
        # flat_color_overrides = {0: ft.Colors.RED, 1: ft.Colors.BLUE}
        self._flat_canvas.shapes = self._shapes(flat_commands, flat_color_overrides)

    @staticmethod
    def _shapes(
        commands: list[tuple], color_overrides: dict | None = None
    ) -> list[cv.Shape]:
        shapes: list[cv.Shape] = []
        layer_colors = {
            "OUTLINES": ft.Colors.BLACK,
            "RABBETS": ft.Colors.RED,
            "CUT_LINES": ft.Colors.GREEN,
            "DIMENSIONS": ft.Colors.BLUE,
        }
        color_overrides = color_overrides or {}
        for command_index, command in enumerate(commands):
            kind, *values = command
            if kind in {"rect", "detail_rect"}:
                x, y, width, height = values
                shapes.append(
                    cv.Rect(
                        x,
                        y,
                        width,
                        height,
                        paint=ft.Paint(
                            color=color_overrides.get(command_index),
                            style=ft.PaintingStyle.STROKE,
                            stroke_width=2 if kind == "rect" else 1,
                        ),
                    )
                )
            elif kind == "layer_rect":
                layer, x, y, width, height = values
                shapes.append(
                    cv.Rect(
                        x,
                        y,
                        width,
                        height,
                        paint=ft.Paint(
                            color=color_overrides.get(command_index, layer_colors[layer]),
                            style=ft.PaintingStyle.STROKE,
                            stroke_width=2 if layer == "CUT_LINES" else 1,
                        ),
                    )
                )
            elif kind == "layer_circle":
                layer, x, y, radius = values
                shapes.append(
                    cv.Circle(
                        x,
                        y,
                        radius,
                        paint=ft.Paint(
                            color=color_overrides.get(command_index, layer_colors[layer]),
                            style=ft.PaintingStyle.STROKE,
                            stroke_width=1,
                        ),
                    )
                )
            elif kind in {"line", "detail", "grid", "hidden"}:
                x1, y1, x2, y2 = values
                line_color = color_overrides.get(
                    command_index,
                    ft.Colors.GREY_300
                    if kind == "grid"
                    else ft.Colors.GREY_600
                    if kind == "hidden"
                    else ft.Colors.BLACK,
                )
                shapes.append(
                    cv.Line(
                        x1,
                        y1,
                        x2,
                        y2,
                        paint=ft.Paint(
                            color=line_color,
                            stroke_width=2 if kind == "line" else 1,
                        ),
                    )
                )
            elif kind == "layer_line":
                layer, x1, y1, x2, y2 = values
                shapes.append(
                    cv.Line(
                        x1,
                        y1,
                        x2,
                        y2,
                        paint=ft.Paint(
                            color=color_overrides.get(command_index, layer_colors[layer]),
                            stroke_width=1,
                        ),
                    )
                )
            elif kind in {"label", "grid_label"}:
                x, y, text = values
                shapes.append(
                    cv.Text(
                        x,
                        y,
                        text,
                        style=ft.TextStyle(
                            size=11,
                            color=color_overrides.get(
                                command_index,
                                ft.Colors.GREY_300 if kind == "grid_label" else ft.Colors.BLACK,
                            ),
                        ),
                    )
                )
            elif kind == "layer_text":
                layer, x, y, text = values
                shapes.append(
                    cv.Text(
                        x,
                        y,
                        text,
                        style=ft.TextStyle(
                            size=11,
                            color=color_overrides.get(command_index, layer_colors[layer]),
                        ),
                    )
                )
        return shapes

    async def _export_dxf(self, _event) -> None:
        try:
            self._parameters = self._read_parameters()
            self._parameters.validate()
            filename = (
                f"rabbet_box_W{self._parameters.width:g}_"
                f"D{self._parameters.depth:g}_H{self._parameters.height:g}_"
                f"T{self._parameters.thickness:g}_{self._parameters.lid_type}.dxf"
            )
            await self._picker.save_file(
                file_name=filename,
                allowed_extensions=["dxf"],
                file_type=ft.FilePickerFileType.CUSTOM,
                src_bytes=dxf_document(self._parameters).encode("ascii"),
            )
            self._status.value = "DXF download ready: outlines, rabbets, cut-lines, and dimensions."
        except ValueError as error:
            self._status.value = f"Check dimensions before export: {error}"
        self.update()
