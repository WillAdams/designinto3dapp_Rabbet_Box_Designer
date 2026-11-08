# Rabbet Box Designer — literate geometry guide

This guide describes how the box parameters become panels, preview drawings, and a browser-downloadable DXF. The program keeps the dimension and joinery calculations independent of Flet: `models.py` creates millimetre-based geometry commands, and `views/designer.py` lays those commands out in the interface and paints them on canvases.

## Program map and data flow

| Module | Responsibility |
| --- | --- |
| `main.py` | Sets up the page and mounts the designer workspace and starts Flet. |
| `models.py` | Validates parameters; defines parts and cut regions; arranges, projects, and fits previews; writes the layered DXF. It does not import Flet. |
| `views/designer.py` | Builds the panes and controls, translates neutral drawing commands to Flet canvas shapes, refreshes the previews, and initiates the browser file download. |

The drawing pipeline is **parameters → panel dimensions and rabbet regions → view-specific drawing commands → canvas or DXF entities**. The same geometry helpers feed both the flat preview and DXF exporter so the two stay aligned.

##  3D model files

## Parameters and derived dimensions

`BoxParameters` is an immutable dataclass; all dimensions are millimetres.

| Field | Symbol | Meaning | Default |
| --- | --- | --- | ---: |
| `width` | `W` | Outside left-to-right width | 300 mm |
| `depth` | `D` | Outside front-to-back depth | 200 mm |
| `height` | `H` | Nominal height of the side panels | 100 mm |
| `thickness` | `T` | Stock thickness | 8 mm |
| `cutout_tool_diameter` | `C` | Tool diameter used for cutter-aware Rabbet outlines | 6.35 mm |
| `lid_type` | — | `None` or `Sliding` | Sliding |

Validation requires positive values, `W > 2T`, `D > 2T`, and `H > 3T`. The cutter diameter must also be positive. The dimension inputs refresh on blur or Enter, and the width/depth/height nudge buttons refresh immediately.

Useful derived values are:

```text
inner width                 Iw = W - 2T
inner depth                 Id = D - 2T
panel width between sides   Fw = W - T
Sliding front height        Hf = H - T
None front/back height      Hn = H
standard rabbet width       R = T / 2
bottom outer region         (W - T + 2C) × (D - T + 2C)
Sliding lid cut-line        (W - T) × (D - T/2)
Sliding lid inner region    (W - 2T) × (D - T)
```

## Parts and joinery regions

`box_parts(p)` always returns Bottom, Front, Back, Left side, and Right side. It appends a sixth part—the Sliding lid—only when the type is Sliding. `Part` stores a name, its flat cut-line dimensions, and any centre-lines or region overrides used by the drawings.

| Part | Flat cut-line size | Flat-view geometry |
| --- | --- | --- |
| **Bottom** | `W × D` | The same bottom is used for both lid types. Its `RABBETS` layer has a centered outer contour `(W-T+2C) × (D-T+2C)` and inner contour `(W-2T) × (D-2T)`. Between them, the `OUTLINES` and `CUT_LINES` contours are centered at `(W-T) × (D-T)`. |
| **Front — Sliding** | `(W-T) × (H-T)` | The lower Rabbet rectangle is the full part width and `T/2` high. A second full-width rectangle is top-aligned and `H-2T` high. The surrounding Rabbet rectangle extends by `C` on each side. |
| **Front — None** | `(W-T) × H` | Same width and lower-edge Rabbet placement as Sliding, with the panel increased in height by `T`. The bottom band remains `T/2` high; the top-aligned rectangle consequently becomes `H-T` high. Its surrounding Rabbet rectangle extends by `C` on each side. |
| **Back — Sliding** | `(W-T) × H` | Full-height panel. The surrounding Rabbet rectangle extends by `C` on each side; three full-width Rabbet regions are drawn: bottom and top bands `T/2` high, with a middle region `H-2T` high. |
| **Back — None** | `(W-T) × H` | A copy of the None Front: same dimensions, lower band, top-aligned region, and surrounding Rabbet rectangle. |
| **Left / Right side — Sliding** | `D × H` each | The flat geometry is mirrored between the pair. Each has a surrounding rectangle extended by `C` on every side, a bottom band `T/2` high, a top asymmetric band `T/2` high, and a centered region `(D-2T) × (H-2T)`. The top band is shortened by `T` and is aligned to the front edge. |
| **Left / Right side — None** | `D × H` each | The surrounding rectangle and bottom band remain. The Sliding-only upper asymmetric band is omitted. The centered region keeps the same depth, `D-2T`, and is increased in height by `T` to `H-T`. |
| **Sliding lid** | `(W-T) × (D-T/2)` | Present only for Sliding. Its Rabbet layer contains a bottom-aligned inner rectangle `(W-2T) × (D-T)` and a surrounding rectangle with a `C` margin on every side. A circular finger hole is centred across the width and `T` inward from the front edge; its diameter is `1.5T`. |

The None Front and Back use `_sliding_front_rabbet_rectangles()` with their taller part dimensions: this preserves the same bottom reference and lets the upper rectangular region grow with the panel. For side panels `_side_rabbet_rectangles()` selects the None or Sliding region recipe. The Front/Back do not add a sliding lid receiver when Lid type is None.

### Centre-lines, rabbets, and rebates

A rabbet is a step cut into a face; a rebate is a step-like indentation along an edge or end. In the model, `_rabbet_region()` converts centre-lines to closed rectangular regions: the rectangle width is `T/2`, with an axial extension of `T` at each endpoint unless a part overrides it. The Sliding lid has edge rebates on its left, right, and rear perimeter; its outline and its receiving grooves are displayed as closed regions in the flat drawing. The view is descriptive geometry, not a boolean model of removed wood or a machining-depth specification.

The custom helpers `_bottom_nested_rectangles()`, `_sliding_front_rabbet_rectangles()`, `_sliding_back_rabbet_rectangles()`, `_sliding_lid_rabbet_rectangles()`, and `_side_rabbet_rectangles()` describe the larger closed regions directly. For front and side outer rectangles the tool margin is `C` per edge; these cutter-aware boundaries are not generic cutter-radius compensation.

## Neutral commands and fitting

The model emits renderer-independent tuples. `layer_rect`, `layer_line`, and `layer_text` carry a DXF layer name; `line` and `hidden` describe the isometric box; `grid` and `grid_label` describe its floor grid. `fit_preview()` calculates the command bounds and uses one uniform scale plus a centering translation to fit the available canvas without distorting the geometry. The initial commands are created during workspace initialization; resize events recalculate the fit.

## Assembled / exploded view

`preview_geometry()` delegates to `_assembled_preview()`. `_iso_point(u, v, z)` projects the box coordinates onto a drafting plane:

```text
screen_x = 0.866 × (u - v)
screen_y = 0.5 × (u + v) - z
```

The first two terms give the floor axes their isometric directions; increasing `z` moves upward on screen. `_solid_prism()` projects each panel as a rectangular prism, drawing visible edges in black and occluded edges in medium gray. This is a wireframe assembly guide: it does not subtract the rabbet cuts from the solids.

| Panel | Width-axis range | Depth-axis range | Height range |
| --- | --- | --- | --- |
| Bottom | `0 .. W` | `0 .. D` | `0 .. T` |
| Front | `T/2 .. W-T/2` | `D-T+gap .. D+gap` | `0 .. H` for None; `0 .. H-T` for Sliding |
| Back | `T/2 .. W-T/2` | `-gap .. T-gap` | `0 .. H` |
| Left side | `-gap .. T-gap` | `T .. D-T` | `0 .. H` |
| Right side | `W-T+gap .. W+gap` | `T .. D-T` | `0 .. H` |
| Sliding lid | `T .. W-T` | `T+travel .. D-T+travel` | `H .. H+T` |

The front and back are placed between the side panels. `gap` is the separation slider's stock-thickness value multiplied by `T` and by a restrained visual factor of `0.35`; this preserves the slider's `0..10T` range without making the panels fly apart. The Sliding lid travels in the depth direction from `0` to `D+10T`. None draws no lid, and the lid-position slider is inactive.

`_isometric_grid()` places a pale 100 mm drafting grid on `z=0`, the plane supporting the box bottom, with its footprint extended around the box. It is projected by `_iso_point()` just like the panels and is drawn before the box edges so the box remains legible.

## Flat / cutting layout

`flat_layout()` places the bottom and optional lid in the first row, front and back in the second, and the side pair in the third. It uses a deterministic gap of `max(20 mm, 3T)` and the clearance frame from `part_outline_offset()`; this is a non-overlapping drawing layout, not an optimized sheet-nesting algorithm.

`_flat_preview()` emits the surrounding clearance outline, actual panel perimeter, dimension witnesses and labels, then the part's Rabbet regions. The Sliding lid additionally shows its circular finger hole on the green CUT_LINES layer. Bottom geometry is deliberately specialized and consists of four nested contours, including the CUT_LINES perimeter. Front and Back branch on lid type; the None Back intentionally calls the same geometry helper as the None Front. The two side panels use the same helper with a mirrored top-band alignment. Every Rabbet region is a closed rectangle. Dimension and clearance commands are included in the fitting bounds, so the complete layout scales to the pane.

The preview uses DXF-equivalent colors: `OUTLINES` black, `RABBETS` red, `CUT_LINES` green, and `DIMENSIONS` blue. This pane has no grid. The black clearance boxes are layout aids and are separate from the panel cut-lines.

## Layered DXF export

`dxf_document()` writes an ASCII R2000 DXF, declares millimetre units (`$INSUNITS=4`), and places all panels in the same arrangement as the flat preview. Its layers are:

| Layer | Contents |
| --- | --- |
| `OUTLINES` | Clearance rectangles around parts, ordinary panel perimeters, and the Bottom's intermediate contour. |
| `RABBETS` | Closed Rabbet/rebate regions, including the Bottom contours, front/back/side joinery and Sliding lid regions. |
| `CUT_LINES` | Closed panel cut perimeters; the Bottom perimeter is `(W-T) × (D-T)`. For the Sliding lid, also includes a through-cut finger-hole circle of diameter `1.5T`, centred at `(lid width/2, T)` in the lid's local coordinates. |
| `DIMENSIONS` | Part-name/size labels, dimension witness lines, and width/height labels. |

Each rectangle is an explicitly closed `LWPOLYLINE`. Layer colors use DXF indices: black 7, red 1, green 3, and blue 5. The export is geometry for a downstream CAD/CAM workflow, not a full CAM program: it does not include kerf, leads, tabs, sheet boundaries, cut ordering, or machining depth. Interpret each closed region according to the intended pocket or contour operation.

## Interface and interactions

`DesignerWorkspace` owns parameter controls, the isometric and flat canvases, pane-collapse state, explanatory text, and the file picker. The Parameters, Assembled / Exploded, and Flat / Cutting Layout headings collapse their panes into narrow restore bars. When both drawings are collapsed, the guide pane occupies the remaining space; the Parameters pane retains its established width when the drawing panes are collapsed.

The Parameters pane includes width, depth, height, thickness, Lid type (`None` / `Sliding`), part selection, cutout-tool diameter, and DXF download. `All` is the default part selection; selecting Front, Back, either side, Top, or Bottom isolates that part in both previews. Top means the Sliding lid, and has no geometry for None. Export always includes all parts for the selected lid type. The assembled pane provides part separation and lid travel sliders. The browser downloads the generated DXF without requiring server-side file storage.

In `_shapes()`, each tagged model command maps to the corresponding Flet canvas shape and layer color. `_set_previews()` regenerates model commands after a valid parameter or selection change, then fits each command list to its own canvas. Its commented `view_color_overrides` and `flat_color_overrides` mappings demonstrate how to override an individual preview primitive color without changing the DXF layer colors.

## Extension points

- Change dimension validation or panel sizes in `BoxParameters` and `box_parts()`.
- Change the sheet arrangement in `flat_layout()`.
- Change the region geometry in the named bottom/front/back/lid/side helpers.
- Change isometric placement, projection, hidden edges, or floor grid in `_assembled_preview()`, `_solid_prism()`, `_iso_point()`, and `_isometric_grid()`.
- Add a drawing command in the model preview functions, then map it in `DesignerWorkspace._shapes()`.
- Change DXF layer mapping or entity serialization in `dxf_document()` and its small `_line()`, `_rect()`, `_text()`, and `_rabbet_region()` writers.

The central invariant is that panel dimensions and joinery calculations belong to `models.py`; the preview and DXF exporter are separate renderers of that shared geometry rather than independent box calculators.
