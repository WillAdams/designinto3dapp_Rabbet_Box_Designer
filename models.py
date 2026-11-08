"""Box dimensions, joinery geometry, previews, and layered DXF generation.

The model uses millimetres and lower-left local coordinates for every flat part.
Preview commands are deliberately renderer-independent tuples; the Flet view maps
those tuples to canvas primitives while the DXF exporter maps the same geometry
into closed polylines, circles, lines, and labels.
"""

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class BoxParameters:
    """User-editable box dimensions and the selected cutting tool."""

    width: float = 300.0
    depth: float = 200.0
    height: float = 100.0
    thickness: float = 8.0
    lid_type: str = "Sliding"
    cutout_tool_diameter: float = 6.35

    def validate(self) -> None:
        """Reject dimensions that would make the panel geometry invalid."""
        if min(self.width, self.depth, self.height, self.thickness) <= 0:
            raise ValueError("All dimensions must be greater than zero.")
        if self.cutout_tool_diameter <= 0:
            raise ValueError("Cutout tool diameter must be greater than zero.")
        if self.width <= 2 * self.thickness or self.depth <= 2 * self.thickness:
            raise ValueError("Width and depth must exceed twice the stock thickness.")
        if self.height <= 3 * self.thickness:
            raise ValueError("Height must exceed three times the stock thickness.")
        if self.lid_type not in {"None", "Sliding"}:
            raise ValueError("Lid type must be None or Sliding.")


@dataclass(frozen=True)
class Part:
    """Flat panel dimensions and centre-lines describing its rabbet cuts."""

    name: str
    width: float
    height: float
    rabbet_lines: tuple[tuple[float, float, float, float], ...]
    rabbet_axis_extension: float | None = None
    rabbet_width: float | None = None


def box_parts(p: BoxParameters) -> list[Part]:
    """Return the box panels and the selected lid, with their joinery lines."""
    p.validate()
    t = p.thickness
    rabbet_width = t / 2
    edge = t / 2 + rabbet_width / 2
    front_height = p.height if p.lid_type == "None" else p.height - t
    front_width = p.width - t

    parts = [
        Part(
            "Bottom", p.width, p.depth,
            (
                (edge, edge, p.width - edge, edge),
                (edge, p.depth - edge, p.width - edge, p.depth - edge),
                (edge, edge, edge, p.depth - edge),
                (p.width - edge, edge, p.width - edge, p.depth - edge),
            ),
        ),
        Part("Front", front_width, front_height, ()),
        Part("Back", front_width, p.height, ()),
        Part("Left side", p.depth, p.height, ()),
        Part("Right side", p.depth, p.height, ()),
    ]

    if p.lid_type == "Sliding":
        parts.append(
            Part(
                "Sliding lid", p.width - t, p.depth - t / 2, (),
                rabbet_axis_extension=0.0,
                rabbet_width=t,
            )
        )
    return parts


def part_outline_offset(p: BoxParameters) -> float:
    """Margin around parts for clearance rectangles and dimension geometry."""
    return max(30.0, 2 * p.thickness)


def flat_layout(p: BoxParameters) -> list[tuple[Part, float, float]]:
    """Arrange panels in three rows with adequate space for annotations."""
    parts = box_parts(p)
    frame = part_outline_offset(p)
    gap = max(20.0, 3 * p.thickness)
    bottom, front, back, left, right = parts[:5]
    bottom_x = frame
    bottom_y = frame
    row2_y = bottom_y + bottom.height + 2 * frame + gap
    row3_y = row2_y + max(front.height, back.height) + 2 * frame + gap
    layout = [
        (bottom, bottom_x, bottom_y),
        (front, frame, row2_y),
        (back, frame + front.width + 2 * frame + gap, row2_y),
        (left, frame, row3_y),
        (right, frame + left.width + 2 * frame + gap, row3_y),
    ]
    if len(parts) > 5:
        lid = parts[5]
        layout.insert(1, (lid, bottom_x + bottom.width + 2 * frame + gap, bottom_y))
    return layout


def preview_geometry(
    p: BoxParameters,
    part_separation: float,
    lid_position: float,
    selected_part: str | None = None,
) -> list[tuple]:
    """Create isometric line-art commands for the box or an isolated part."""
    return _assembled_preview(
        p, max(0.0, part_separation), max(0.0, lid_position), selected_part
    )


def flat_preview_geometry(
    p: BoxParameters, selected_part: str | None = None
) -> list[tuple]:
    """Create layer-tagged flat drawing commands for all or one part."""
    return _flat_preview(p, selected_part)


def drafting_grid(p: BoxParameters, canvas_width: float, canvas_height: float) -> list[tuple]:
    """Create a labelled, 100 mm isometric floor grid sized to the box."""
    maximum = ceil(max(p.width, p.depth, p.height) / 100) * 100
    margin = 34.0
    scale = min(
        (canvas_width - 2 * margin) / maximum,
        (canvas_height - 2 * margin) / maximum,
    )
    extent = maximum * scale
    ox = (canvas_width - extent) / 2
    oy = (canvas_height - extent) / 2
    commands: list[tuple] = []
    for value in range(0, maximum + 1, 100):
        position = value * scale
        commands.append(("grid", ox + position, oy, ox + position, oy + extent))
        commands.append(("grid", ox, oy + position, ox + extent, oy + position))
        commands.append(("grid_label", ox + position + 2, oy + extent - 3, f"{value} mm"))
        if value:
            commands.append(("grid_label", ox + 2, oy + position - 3, f"{value} mm"))
    return commands


def fit_preview(commands: list[tuple], canvas_width: float, canvas_height: float) -> list[tuple]:
    """Fit a renderer-independent command list into a canvas, preserving ratio."""
    points: list[tuple[float, float]] = []
    for command in commands:
        kind = command[0]
        if kind in ("rect", "detail_rect"):
            _, x, y, width, height = command
            points.extend(((x, y), (x + width, y + height)))
        elif kind == "layer_rect":
            _, _layer, x, y, width, height = command
            points.extend(((x, y), (x + width, y + height)))
        elif kind == "layer_circle":
            _, _layer, x, y, radius = command
            points.extend(((x - radius, y - radius), (x + radius, y + radius)))
        elif kind in ("line", "detail", "grid", "hidden", "layer_line"):
            if kind == "layer_line":
                _, _layer, x1, y1, x2, y2 = command
            else:
                _, x1, y1, x2, y2 = command
            points.extend(((x1, y1), (x2, y2)))
        elif kind in ("label", "grid_label", "layer_text"):
            if kind == "layer_text":
                _, _layer, x, y, _text = command
            else:
                _, x, y, _text = command
            points.append((x, y))
    if not points or canvas_width <= 0 or canvas_height <= 0:
        return commands

    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    padding = 48.0
    scale = min(
        (canvas_width - 2 * padding) / max(max_x - min_x, 1),
        (canvas_height - 2 * padding) / max(max_y - min_y, 1),
    )
    offset_x = (canvas_width - (max_x - min_x) * scale) / 2 - min_x * scale
    offset_y = (canvas_height - (max_y - min_y) * scale) / 2 - min_y * scale
    fitted: list[tuple] = []
    for command in commands:
        kind = command[0]
        if kind in ("rect", "detail_rect"):
            _, x, y, width, height = command
            fitted.append((kind, x * scale + offset_x, y * scale + offset_y, width * scale, height * scale))
        elif kind == "layer_rect":
            _, layer, x, y, width, height = command
            fitted.append((kind, layer, x * scale + offset_x, y * scale + offset_y, width * scale, height * scale))
        elif kind == "layer_circle":
            _, layer, x, y, radius = command
            fitted.append((kind, layer, x * scale + offset_x, y * scale + offset_y, radius * scale))
        elif kind in ("line", "detail", "grid", "hidden"):
            _, x1, y1, x2, y2 = command
            fitted.append((kind, x1 * scale + offset_x, y1 * scale + offset_y, x2 * scale + offset_x, y2 * scale + offset_y))
        elif kind == "layer_line":
            _, layer, x1, y1, x2, y2 = command
            fitted.append((kind, layer, x1 * scale + offset_x, y1 * scale + offset_y, x2 * scale + offset_x, y2 * scale + offset_y))
        elif kind == "layer_text":
            _, layer, x, y, text = command
            fitted.append((kind, layer, x * scale + offset_x, y * scale + offset_y, text))
        else:
            _, x, y, text = command
            fitted.append((kind, x * scale + offset_x, y * scale + offset_y, text))
    return fitted


def _bottom_nested_rectangles(
    part: Part, thickness: float, cutout_tool_diameter: float
) -> tuple[tuple, ...]:
    """Return the bottom's nested contours and its centered cut-line perimeter."""
    outer_width = part.width - thickness + 2 * cutout_tool_diameter
    outer_height = part.height - thickness + 2 * cutout_tool_diameter
    outer_x = (part.width - outer_width) / 2
    outer_y = (part.height - outer_height) / 2
    return (
        ("RABBETS", outer_x, outer_y, outer_width, outer_height),
        (
            "OUTLINES", thickness / 2, thickness / 2,
            part.width - thickness, part.height - thickness,
        ),
        (
            "CUT_LINES", thickness / 2, thickness / 2,
            part.width - thickness, part.height - thickness,
        ),
        (
            "RABBETS", thickness, thickness,
            part.width - 2 * thickness, part.height - 2 * thickness,
        ),
    )


def _sliding_front_rabbet_rectangles(
    part: Part, thickness: float, cutout_tool_diameter: float
) -> tuple[tuple[float, float, float, float], ...]:
    """Return closed front Rabbet regions in lower-left part coordinates.

    The pair consists of a half-stock bottom band and a top-aligned rectangle
    whose height is one stock thickness shorter than the panel. A third Rabbet
    contour increases each dimension by two tool diameters total,
    leaving one diameter beyond each edge.
    """
    return (
        (0.0, 0.0, part.width, thickness / 2),
        (0.0, thickness, part.width, part.height - thickness),
        (
            -cutout_tool_diameter,
            -cutout_tool_diameter,
            part.width + 2 * cutout_tool_diameter,
            part.height + 2 * cutout_tool_diameter,
        ),
    )


def _sliding_back_rabbet_rectangles(
    part: Part, thickness: float, cutout_tool_diameter: float
) -> tuple[tuple[float, float, float, float], ...]:
    """Return the Sliding Back's cutter margin and three horizontal Rabbet regions."""
    return (
        (
            -cutout_tool_diameter,
            -cutout_tool_diameter,
            part.width + 2 * cutout_tool_diameter,
            part.height + 2 * cutout_tool_diameter,
        ),
        (0.0, 0.0, part.width, thickness / 2),
        (0.0, thickness, part.width, part.height - 2 * thickness),
        (0.0, part.height - thickness / 2, part.width, thickness / 2),
    )


def _sliding_lid_rabbet_rectangles(
    part: Part, thickness: float, cutout_tool_diameter: float
) -> tuple[tuple[float, float, float, float], ...]:
    """Return the lid's bottom-aligned inner Rabbet and cutter-margin rectangle."""
    return (
        (
            -cutout_tool_diameter,
            -cutout_tool_diameter,
            part.width + 2 * cutout_tool_diameter,
            part.height + 2 * cutout_tool_diameter,
        ),
        (
            thickness / 2,
            0.0,
            part.width - thickness,
            part.height - thickness / 2,
        ),
    )


def _side_rabbet_rectangles(
    part: Part,
    thickness: float,
    cutout_tool_diameter: float,
    lid_type: str,
) -> tuple[tuple[float, float, float, float], ...]:
    """Return side-panel Rabbet regions, with a mirrored top band only for Sliding."""
    inset_x = thickness
    cutter_margin = (
        -cutout_tool_diameter,
        -cutout_tool_diameter,
        part.width + 2 * cutout_tool_diameter,
        part.height + 2 * cutout_tool_diameter,
    )
    bottom_band = (inset_x, 0.0, part.width - 2 * thickness, thickness / 2)
    if lid_type == "None":
        # The taller middle region is vertically centred; the asymmetric upper band is omitted.
        central_height = part.height - thickness
        central = (
            inset_x,
            (part.height - central_height) / 2,
            part.width - 2 * thickness,
            central_height,
        )
        return cutter_margin, bottom_band, central

    top_x = thickness if part.name == "Right side" else 0.0
    return (
        cutter_margin,
        (top_x, part.height - thickness / 2, part.width - thickness, thickness / 2),
        bottom_band,
        (inset_x, thickness, part.width - 2 * thickness, part.height - 2 * thickness),
    )


def _flat_preview(p: BoxParameters, selected_part: str | None = None) -> list[tuple]:
    """Emit part boundaries, joinery, labels, and dimensions as layered primitives."""
    commands: list[tuple] = []
    layout = flat_layout(p)
    if selected_part is not None:
        layout = [entry for entry in layout if entry[0].name == selected_part]
    if not layout:
        return commands

    frame = part_outline_offset(p)
    max_x = max(x + part.width + frame for part, x, _ in layout)
    max_y = max(y + part.height + frame for part, _, y in layout)
    scale = min(700 / max(max_x, 1), 400 / max(max_y, 1))
    for part, x, y in layout:
        px = 35 + x * scale
        py = 35 + y * scale
        width = part.width * scale
        height = part.height * scale
        clearance = frame * scale
        commands.append(("layer_rect", "OUTLINES", px - clearance, py - clearance, width + 2 * clearance, height + 2 * clearance))
        if part.name == "Bottom":
            for layer, rx, ry, rw, rh in _bottom_nested_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                commands.append((
                    "layer_rect", layer, px + rx * scale,
                    py + (part.height - ry - rh) * scale,
                    rw * scale, rh * scale,
                ))
        else:
            commands.append(("layer_rect", "CUT_LINES", px, py, width, height))
        commands.append(("layer_text", "DIMENSIONS", px + 4, py + 14, f"{part.name}: {part.width:.1f} x {part.height:.1f} mm"))

        offset = 10 * scale
        commands.extend([
            ("layer_line", "DIMENSIONS", px, py + height + offset, px + width, py + height + offset),
            ("layer_line", "DIMENSIONS", px, py + height, px, py + height + offset + 3 * scale),
            ("layer_line", "DIMENSIONS", px + width, py + height, px + width, py + height + offset + 3 * scale),
            ("layer_text", "DIMENSIONS", px + width / 2, py + height + offset + 5 * scale, f"{part.width:.1f} mm"),
            ("layer_line", "DIMENSIONS", px - offset, py, px - offset, py + height),
            ("layer_line", "DIMENSIONS", px, py, px - offset - 3 * scale, py),
            ("layer_line", "DIMENSIONS", px, py + height, px - offset - 3 * scale, py + height),
            ("layer_text", "DIMENSIONS", px - offset - 15 * scale, py + height / 2, f"{part.height:.1f} mm"),
        ])

        rabbet_width = p.thickness / 2 if part.rabbet_width is None else part.rabbet_width
        extension = p.thickness if part.rabbet_axis_extension is None else part.rabbet_axis_extension
        if part.name == "Sliding lid":
            for rx, ry, rw, rh in _sliding_lid_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                commands.append((
                    "layer_rect", "RABBETS", px + rx * scale,
                    py + (part.height - ry - rh) * scale,
                    rw * scale, rh * scale,
                ))
            # Through-hole on the lid: 1.5T diameter, centred across its
            # width and T inward from its front (lower local-y) edge.
            commands.append((
                "layer_circle", "CUT_LINES", px + width / 2,
                py + (part.height - p.thickness) * scale,
                0.75 * p.thickness * scale,
            ))
        elif part.name == "Front" and p.lid_type == "Sliding":
            for rx, ry, rw, rh in _sliding_front_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                commands.append((
                    "layer_rect", "RABBETS", px + rx * scale,
                    py + (part.height - ry - rh) * scale,
                    rw * scale, rh * scale,
                ))
        elif part.name in {"Front", "Back"} and p.lid_type == "None":
            for rx, ry, rw, rh in _sliding_front_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                commands.append((
                    "layer_rect", "RABBETS", px + rx * scale,
                    py + (part.height - ry - rh) * scale,
                    rw * scale, rh * scale,
                ))
        elif part.name == "Back" and p.lid_type == "Sliding":
            for rx, ry, rw, rh in _sliding_back_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                commands.append((
                    "layer_rect", "RABBETS", px + rx * scale,
                    py + (part.height - ry - rh) * scale,
                    rw * scale, rh * scale,
                ))
        elif part.name in ("Left side", "Right side"):
            for rx, ry, rw, rh in _side_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter, p.lid_type
            ):
                commands.append((
                    "layer_rect", "RABBETS", px + rx * scale,
                    py + (part.height - ry - rh) * scale,
                    rw * scale, rh * scale,
                ))
        elif part.name != "Bottom":
            for x1, y1, x2, y2 in part.rabbet_lines:
                rx, ry, rw, rh = _rabbet_region(x1, y1, x2, y2, rabbet_width, extension)
                commands.append((
                    "layer_rect", "RABBETS", px + rx * scale,
                    py + (part.height - ry - rh) * scale,
                    rw * scale, rh * scale,
                ))
    return commands


def _iso_point(u: float, v: float, z: float = 0.0) -> tuple[float, float]:
    """Project box coordinates onto a 30-degree isometric drafting plane."""
    return (u - v) * 0.866, (u + v) * 0.5 - z


def _isometric_grid(p: BoxParameters) -> list[tuple]:
    """Draw a light floor grid extending approximately 100 mm around the box."""
    margin = 100
    min_u, max_u = -margin, p.width + margin
    min_v, max_v = -margin, p.depth + margin
    commands: list[tuple] = []
    for value in range(min_u, ceil(max_u / 100) * 100 + 1, 100):
        x1, y1 = _iso_point(value, min_v)
        x2, y2 = _iso_point(value, max_v)
        commands.append(("grid", x1, y1, x2, y2))
        commands.append(("grid_label", x1 + 3, y1 + 10, f"{value} mm"))
    for value in range(min_v, ceil(max_v / 100) * 100 + 1, 100):
        x1, y1 = _iso_point(min_u, value)
        x2, y2 = _iso_point(max_u, value)
        commands.append(("grid", x1, y1, x2, y2))
    return commands


def _quadrilateral(points: list[tuple[float, float]], kind: str = "line") -> list[tuple]:
    return [
        (kind, *points[index], *points[(index + 1) % len(points)])
        for index in range(len(points))
    ]


def _solid_prism(
    minimum_u: float,
    maximum_u: float,
    minimum_v: float,
    maximum_v: float,
    minimum_z: float,
    maximum_z: float,
) -> list[tuple]:
    """Return visible black and hidden gray edges for a rectangular board."""
    lower_front = _iso_point(minimum_u, minimum_v, minimum_z)
    lower_right = _iso_point(maximum_u, minimum_v, minimum_z)
    lower_back = _iso_point(maximum_u, maximum_v, minimum_z)
    lower_left = _iso_point(minimum_u, maximum_v, minimum_z)
    upper_front = _iso_point(minimum_u, minimum_v, maximum_z)
    upper_right = _iso_point(maximum_u, minimum_v, maximum_z)
    upper_back = _iso_point(maximum_u, maximum_v, maximum_z)
    upper_left = _iso_point(minimum_u, maximum_v, maximum_z)
    commands = _quadrilateral([upper_front, upper_right, upper_back, upper_left])
    commands.extend([
        ("line", *lower_front, *lower_right),
        ("line", *lower_front, *lower_left),
        ("line", *lower_front, *upper_front),
        ("line", *lower_right, *upper_right),
        ("line", *lower_left, *upper_left),
        ("hidden", *lower_right, *lower_back),
        ("hidden", *lower_left, *lower_back),
        ("hidden", *lower_back, *upper_back),
    ])
    return commands


def _assembled_preview(
    p: BoxParameters,
    part_separation: float,
    lid_position: float,
    selected_part: str | None = None,
) -> list[tuple]:
    """Draw the assembled/exploded view, or isolate one panel."""
    t = p.thickness
    gap = min(max(part_separation, 0.0), 10 * t) * 0.35
    travel = min(max(lid_position, 0.0), p.depth + 10 * t)
    front_height = p.height if p.lid_type == "None" else p.height - t
    front_u_min = t / 2
    front_u_max = p.width - t / 2
    back_height = p.height
    back_u_min = t / 2
    back_u_max = p.width - t / 2
    commands = _isometric_grid(p)
    solids = [
        ("Bottom", (0, p.width, 0, p.depth, 0, t)),
        ("Front", (front_u_min, front_u_max, p.depth - t + gap, p.depth + gap, 0, front_height)),
        ("Back", (back_u_min, back_u_max, -gap, t - gap, 0, back_height)),
        ("Left side", (-gap, t - gap, t, p.depth - t, 0, p.height)),
        ("Right side", (p.width - t + gap, p.width + gap, t, p.depth - t, 0, p.height)),
    ]
    for name, bounds in solids:
        if selected_part is None or name == selected_part:
            commands.extend(_solid_prism(*bounds))

    if p.lid_type == "Sliding":
        lid_name = "Sliding lid"
        if selected_part is None or selected_part == lid_name:
            commands.extend(_solid_prism(
                t, p.width - t, t + travel, p.depth - t + travel,
                p.height, p.height + t,
            ))
    return commands


def _line(layer: str, x1: float, y1: float, x2: float, y2: float) -> list[str]:
    return ["0", "LINE", "8", layer, "10", f"{x1:.3f}", "20", f"{y1:.3f}", "11", f"{x2:.3f}", "21", f"{y2:.3f}"]


def _rect(layer: str, x: float, y: float, width: float, height: float) -> list[str]:
    points = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    codes = ["0", "LWPOLYLINE", "8", layer, "90", "4", "70", "1"]
    for px, py in points:
        codes.extend(["10", f"{px:.3f}", "20", f"{py:.3f}"])
    return codes


def _circle(layer: str, x: float, y: float, radius: float) -> list[str]:
    """Serialize a DXF circle using its centre and radius in millimetres."""
    return [
        "0", "CIRCLE", "8", layer,
        "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0.000",
        "40", f"{radius:.3f}",
    ]


def _text(layer: str, x: float, y: float, value: str, height: float = 5.0) -> list[str]:
    return ["0", "TEXT", "8", layer, "10", f"{x:.3f}", "20", f"{y:.3f}", "40", f"{height:.3f}", "1", value]


def _rabbet_region(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    rabbet_width: float,
    extension: float,
) -> tuple[float, float, float, float]:
    """Turn a horizontal or vertical centre-line into a closed cut region."""
    half = rabbet_width / 2
    if y1 == y2:
        return min(x1, x2) - extension, y1 - half, abs(x2 - x1) + 2 * extension, rabbet_width
    return x1 - half, min(y1, y2) - extension, rabbet_width, abs(y2 - y1) + 2 * extension


def _part_dimensions(part: Part, x: float, y: float) -> list[str]:
    """Write width/height witness lines and labels to the dimensions layer."""
    offset = 10.0
    codes = _line("DIMENSIONS", x, y - offset, x + part.width, y - offset)
    codes += _line("DIMENSIONS", x, y, x, y - offset - 3)
    codes += _line("DIMENSIONS", x + part.width, y, x + part.width, y - offset - 3)
    codes += _text("DIMENSIONS", x + part.width / 2, y - offset - 5, f"{part.width:.1f} mm", 4.0)
    codes += _line("DIMENSIONS", x - offset, y, x - offset, y + part.height)
    codes += _line("DIMENSIONS", x, y, x - offset - 3, y)
    codes += _line("DIMENSIONS", x, y + part.height, x - offset - 3, y + part.height)
    codes += _text("DIMENSIONS", x - offset - 15, y + part.height / 2, f"{part.height:.1f} mm", 4.0)
    return codes


def dxf_document(p: BoxParameters) -> str:
    """Serialize the parts, joinery, and annotations as layered R2000 DXF."""
    layout = flat_layout(p)
    frame = part_outline_offset(p)
    layers = [("OUTLINES", 7), ("RABBETS", 1), ("CUT_LINES", 3), ("DIMENSIONS", 5)]
    codes = [
        "0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
        "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", str(len(layers)),
    ]
    for layer, color in layers:
        codes.extend(["0", "LAYER", "2", layer, "70", "0", "62", str(color), "6", "CONTINUOUS"])
    codes.extend(["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"])

    for part, x, y in layout:
        codes += _rect("OUTLINES", x - frame, y - frame, part.width + 2 * frame, part.height + 2 * frame)
        if part.name == "Bottom":
            for layer, rx, ry, rw, rh in _bottom_nested_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                codes += _rect(layer, x + rx, y + ry, rw, rh)
        else:
            codes += _rect("OUTLINES", x, y, part.width, part.height)
            codes += _rect("CUT_LINES", x, y, part.width, part.height)
        codes += _text("DIMENSIONS", x, y - 18, f"{part.name}: {part.width:.1f} x {part.height:.1f} mm")
        codes += _part_dimensions(part, x, y)

        extension = p.thickness if part.rabbet_axis_extension is None else part.rabbet_axis_extension
        rabbet_width = p.thickness / 2 if part.rabbet_width is None else part.rabbet_width
        if part.name == "Sliding lid":
            for rx, ry, rw, rh in _sliding_lid_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                codes += _rect("RABBETS", x + rx, y + ry, rw, rh)
            # 1.5T diameter finger hole, centred across the lid and T from
            # its front edge; use CUT_LINES so it exports as a through-cut.
            codes += _circle(
                "CUT_LINES", x + part.width / 2, y + p.thickness,
                0.75 * p.thickness,
            )
        elif part.name == "Front" and p.lid_type == "Sliding":
            for rx, ry, rw, rh in _sliding_front_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                codes += _rect("RABBETS", x + rx, y + ry, rw, rh)
        elif part.name in {"Front", "Back"} and p.lid_type == "None":
            for rx, ry, rw, rh in _sliding_front_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                codes += _rect("RABBETS", x + rx, y + ry, rw, rh)
        elif part.name == "Back" and p.lid_type == "Sliding":
            for rx, ry, rw, rh in _sliding_back_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter
            ):
                codes += _rect("RABBETS", x + rx, y + ry, rw, rh)
        elif part.name in ("Left side", "Right side"):
            for rx, ry, rw, rh in _side_rabbet_rectangles(
                part, p.thickness, p.cutout_tool_diameter, p.lid_type
            ):
                codes += _rect("RABBETS", x + rx, y + ry, rw, rh)
        elif part.name != "Bottom":
            for x1, y1, x2, y2 in part.rabbet_lines:
                rx, ry, rw, rh = _rabbet_region(x1, y1, x2, y2, rabbet_width, extension)
                codes += _rect("RABBETS", x + rx, y + ry, rw, rh)
    codes.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(codes) + "\n"
