# CAD for AI Applications — Beginner Cheat Sheet

> **Goal:** Understand enough CAD/DXF terminology and structure to build an AI application that can read drawings, identify construction elements, extract quantities, and reason about them.
>
> **Context:** This is especially focused on construction drawings such as pile layouts, pile caps, grade beams, dimensions, annotations, and takeoff.

---

# 1. CAD in One Minute

**CAD = Computer-Aided Design.**

A CAD drawing is not necessarily an image.

A CAD file can contain **structured geometric objects** such as:

- Lines
- Circles
- Arcs
- Polylines
- Splines
- Text
- Dimensions
- Hatches
- Blocks
- Layers

This is extremely important for an AI application.

### Image vs CAD

**PDF/Image:**
```text
pixels → OCR/vision → meaning
```

**CAD/DXF:**
```text
geometric entities + metadata → parse → geometry + meaning
```

A CAD file can tell you that something is a **CIRCLE** with:

```text
center = (1000, 2000)
radius = 300
layer = "PILE"
```

That is much more reliable than trying to detect the circle from pixels.

---

# 2. The CAD Mental Model

Think of a CAD drawing as:

```text
DRAWING
│
├── Layers
│   ├── PILE
│   ├── PILECAP
│   ├── GRADE_BEAM
│   └── DIMENSION
│
├── Entities
│   ├── CIRCLE
│   ├── LINE
│   ├── LWPOLYLINE
│   ├── ARC
│   ├── TEXT
│   ├── DIMENSION
│   └── INSERT
│
├── Blocks
│   └── reusable symbols/components
│
└── Layout / Model Space
```

### Remember

**Layer = category/organization**

**Entity = actual drawing object**

**Block = reusable group/symbol**

---

# 3. Coordinate System

CAD objects normally have coordinates.

For 2D CAD:

```text
(x, y)
```

Example:

```text
Circle center = (1250, 3000)
```

For 3D CAD:

```text
(x, y, z)
```

Example:

```text
Point = (1250, 3000, 150)
```

### Important

The coordinate system tells you **where** something is.

It does NOT automatically tell you **what** something means.

A circle at `(1000, 2000)` could be:

- A pile
- A column
- A hole
- A symbol
- A detail
- Something else

You need layers, blocks, nearby text, dimensions, and drawing context to determine meaning.

---

# 4. Units

CAD drawings may use:

- mm
- cm
- m
- inches
- feet

A value of:

```text
300
```

could mean:

```text
300 mm
300 cm
300 m
300 inches
```

depending on the drawing.

### Never assume units.

Your application should ideally determine or receive:

```text
drawing units
scale
measurement system
```

### Common construction convention

Many structural drawings use **millimetres (mm)**.

Example:

```text
PILE DIA = 600
```

usually means:

```text
600 mm diameter
```

but verify from the drawing/title block/project standards.

---

# 5. Main CAD Entity Types

These are the entities you should know first.

---

## 5.1 LINE

A straight line between two points.

```text
LINE
start = (x1, y1)
end   = (x2, y2)
```

Example:

```text
start = (0, 0)
end   = (1000, 0)
```

Length:

```text
L = √((x2-x1)² + (y2-y1)²)
```

### Construction uses

Lines may represent:

- Grid lines
- Walls
- Beam edges
- Pile cap edges
- Centerlines
- Property boundaries
- Detail lines

---

# 6. CIRCLE

A circle is defined primarily by:

```text
center
radius
```

Example:

```text
center = (5000, 3000)
radius = 300
```

Diameter:

```text
D = 2 × radius
```

So:

```text
radius = 300 mm
diameter = 600 mm
```

### In a pile drawing

A circle may represent a **pile**.

For example:

```text
CIRCLE
center = (5000, 3000)
radius = 300
```

could mean:

```text
PILE
DIA = 600 mm
LOCATION = (5000, 3000)
```

### But be careful

**Circle ≠ automatically pile.**

Your AI should combine:

```text
geometry
+ layer
+ nearby text
+ dimensions
+ blocks
+ context
```

to classify it.

---

# 7. ARC

An arc is only part of a circle.

Typical properties:

```text
center
radius
start angle
end angle
```

Example:

```text
center = (0, 0)
radius = 1000
start angle = 0°
end angle = 90°
```

This represents a quarter-circle.

### Construction uses

- Curved walls
- Curved beams
- Road geometry
- Circular details
- Structural details

---

# 8. POLYLINE / LWPOLYLINE

A polyline is a connected sequence of points/segments.

Example:

```text
P1 → P2 → P3 → P4
```

It can represent:

```text
┌──────────┐
│          │
│          │
└──────────┘
```

A **closed polyline** can define an area.

### Construction uses

- Pile cap boundaries
- Grade beam boundaries
- Walls
- Slabs
- Footings
- Irregular shapes

### Important

A polyline may contain:

- Straight segments
- Curved segments (bulges/arcs)
- Width
- Closed/open state

---

# 9. SPLINE

A spline is a smooth mathematical curve.

Think:

```text
polyline:
_/\/\_

spline:
~~~~~~
```

Used when smooth curves are required.

For a basic takeoff engine, SPLINE may be less important than:

```text
LINE
CIRCLE
ARC
LWPOLYLINE
```

but you should still recognize it.

---

# 10. ELLIPSE

An ellipse is like a stretched circle.

Example:

```text
     ______
   /        \
  |          |
   \________/
```

Typical information includes:

- Center
- Major axis
- Ratio/minor axis information
- Start/end parameters

Used for:

- Curved details
- Mechanical details
- Symbols
- Drafting geometry

---

# 11. HATCH

A hatch is a fill/pattern applied to an area.

Example:

```text
///////////
///////////
///////////
```

It can indicate:

- Concrete
- Earth
- Sectioned material
- Masonry
- Insulation
- Other construction materials

### Important

A hatch is generally **not the boundary itself**.

Think:

```text
BOUNDARY → defines area
HATCH    → visually fills/patterns area
```

---

# 12. TEXT

CAD drawings contain text objects.

Examples:

```text
PILE P1
DIA 600
TYPICAL
GRADE BEAM
300x600
```

Text can be extremely valuable to an AI system.

It provides **semantic meaning** to otherwise ambiguous geometry.

---

# 13. MTEXT

MTEXT = multiline text.

Example:

```text
PILE CAP
PC-01
1800 x 1800 x 600
```

It can contain formatting and multiple lines.

For extraction:

```text
TEXT + MTEXT
```

should normally be treated as a text/annotation family.

---

# 14. DIMENSION

A dimension represents a measured value.

Example:

```text
<----------- 3000 ----------->
```

A dimension can contain:

- Measurement
- Extension lines
- Dimension line
- Arrowheads
- Text
- Geometry references

Examples:

```text
3000
600
1500
250
```

### Very important for takeoff

Dimensions can tell your AI:

```text
distance between piles
pile diameter
pile cap size
beam width
beam depth
offsets
grid spacing
```

### Do not blindly trust visible text

A dimension's actual geometry and measurement data can be more useful than OCR of the displayed number.

---

# 15. LEADER / MULTILEADER

A leader connects annotation text to a location.

Example:

```text
PILE P1
     \
      \
       ●
```

Meaning:

```text
text → points to object
```

Useful for identifying:

- Notes
- Pile types
- Beam types
- Structural details
- Material specifications

---

# 16. BLOCK

A block is a reusable collection of CAD objects.

Think of it as a **template/component**.

For example:

```text
BLOCK: PILE_SYMBOL
    ├── Circle
    ├── Cross
    └── Text
```

Instead of drawing that symbol manually 100 times, CAD can insert the same block repeatedly.

Those inserted instances are often represented by:

```text
INSERT
```

### Why blocks matter for AI

A block name can contain strong semantic clues:

```text
PILE
PILE_600
COLUMN
GRID
PCAP
GB
```

So your parser should inspect:

```text
INSERT
→ block name
→ block definition
→ attributes
→ insertion point
→ scale
→ rotation
```

---

# 17. ATTRIB / ATTDEF

Blocks can contain attributes.

Example:

```text
Block = PILE
Attribute:
TYPE = P1
DIA  = 600
```

### ATTDEF

Defines an attribute inside a block.

### ATTRIB

Stores the actual attribute value for an inserted block.

These can be extremely useful because they may contain structured information directly.

---

# 18. LAYERS

Layers are one of the most important CAD concepts.

A drawing might have:

```text
PILE
PILE-CAP
GRADE-BEAM
GRID
TEXT
DIMENSIONS
WALL
COLUMN
```

An entity belongs to a layer.

Example:

```text
Entity:
    type = CIRCLE
    layer = PILE
```

This gives your AI a strong classification signal.

### But:

Do not assume layer names are standardized.

One project may use:

```text
PILE
```

Another:

```text
S-PILE
```

Another:

```text
STR_PILES
```

Another:

```text
FOUNDATION-PILE
```

Your application should learn/configure layer mappings rather than hard-code one naming convention.

---

# 19. MODEL SPACE vs PAPER SPACE

CAD drawings can have different spaces.

### Model Space

Where the actual design geometry is usually created.

Think:

```text
REAL DRAWING
```

### Paper Space / Layout

Used for sheets, viewports, title blocks, printing, etc.

Think:

```text
PRINTED SHEET
```

A viewport can show a portion of Model Space at a particular scale.

---

# 20. BLOCK vs ENTITY

This distinction is important.

### Entity

One drawing object:

```text
CIRCLE
LINE
TEXT
```

### Block

A reusable collection:

```text
PILE SYMBOL
├── CIRCLE
├── CROSS
└── TEXT
```

### INSERT

An instance of a block placed into the drawing.

Think:

```text
Block Definition
       ↓
     INSERT
       ↓
actual occurrence in drawing
```

---

# 21. DXF

**DXF = Drawing Exchange Format.**

It is a CAD file format commonly used to exchange drawing data.

For an AI application, DXF is useful because it can expose structured CAD information.

A simplified DXF idea:

```text
ENTITY
  ↓
TYPE
  ↓
PROPERTIES
  ↓
GEOMETRY
  ↓
METADATA
```

---

# 22. Basic DXF Entity Structure

A DXF file contains **group codes**.

You may see something conceptually like:

```text
0
CIRCLE
8
PILE
10
5000
20
3000
40
300
```

Meaning approximately:

```text
0  → entity type
CIRCLE → entity is a circle

8  → layer
PILE → layer name

10 → X coordinate
5000 → X

20 → Y coordinate
3000 → Y

40 → radius
300 → radius
```

### Important group codes to remember

| Code | Common meaning |
|---|---|
| `0` | Entity type |
| `8` | Layer |
| `10` | X coordinate |
| `20` | Y coordinate |
| `30` | Z coordinate |
| `40` | Radius / other numeric value depending on entity |
| `1` | Text/value in many contexts |
| `2` | Name, such as block name, depending on entity |

**Do not assume a group code always means the same thing. Its meaning depends on the entity/context.**

---

# 23. Important CAD Data Types — Quick List

Memorize these first:

```text
LINE
CIRCLE
ARC
LWPOLYLINE
POLYLINE
SPLINE
ELLIPSE
HATCH
TEXT
MTEXT
DIMENSION
LEADER
MULTILEADER
INSERT
ATTRIB
ATTDEF
```

For a beginner, the priority is:

```text
★★★★★ CIRCLE
★★★★★ LINE
★★★★★ LWPOLYLINE
★★★★★ TEXT / MTEXT
★★★★★ DIMENSION
★★★★★ INSERT / BLOCK
★★★★☆ ARC
★★★★☆ HATCH
★★★☆☆ SPLINE
★★★☆☆ ELLIPSE
★★★☆☆ ATTRIB
```

---

# 24. Geometry vs Semantics

This is one of the most important concepts for your AI application.

## Geometry

Answers:

> **What shape and where?**

Example:

```text
CIRCLE
center = (5000, 3000)
radius = 300
```

## Semantics

Answers:

> **What does it mean?**

Example:

```text
PILE
type = P1
diameter = 600 mm
```

CAD often gives you geometry directly, but meaning may need to be inferred.

---

# 25. How AI Can Understand a Pile

Suppose your parser finds:

```text
CIRCLE
center = (5000, 3000)
radius = 300
layer = PILE
```

Nearby text says:

```text
P1
```

A dimension says:

```text
600
```

Your AI can construct:

```json
{
  "element": "pile",
  "type": "P1",
  "center": [5000, 3000],
  "diameter": 600,
  "radius": 300,
  "layer": "PILE"
}
```

This is much more useful than simply saying:

```text
I found a circle.
```

---

# 26. Spatial Relationships

CAD AI needs to understand **relationships**, not only individual objects.

Examples:

```text
Pile A
    ↓
inside
    ↓
Pile Cap
```

or:

```text
Pile A
    ↓
3000 mm from
    ↓
Pile B
```

or:

```text
Dimension
    ↓
measures
    ↓
Pile-to-pile distance
```

Important spatial relationships include:

- Inside
- Outside
- Touching
- Intersecting
- Near
- Parallel
- Perpendicular
- Connected
- Aligned
- Centered
- Offset from

---

# 27. Bounding Box

A bounding box is a simple rectangle surrounding an object.

```text
┌──────────────────┐
│      OBJECT      │
│                  │
└──────────────────┘
```

Typically:

```text
min_x
min_y
max_x
max_y
```

Useful for:

- Spatial searches
- Collision/intersection checks
- Finding nearby annotations
- Grouping objects
- Detecting objects inside regions

---

# 28. Distance

For two points:

```text
P1 = (x1, y1)
P2 = (x2, y2)
```

Distance:

```text
d = √((x2-x1)² + (y2-y1)²)
```

This is fundamental for CAD processing.

Example:

```text
Pile 1 = (0, 0)
Pile 2 = (3000, 0)

distance = 3000 mm
```

---

# 29. Point-in-Polygon

A very useful operation.

Question:

> Is this pile inside this pile cap?

Conceptually:

```text
PILE ●

┌───────────────┐
│               │
│      ●        │
│               │
└───────────────┘
     PILE CAP
```

Your application can perform:

```text
point_in_polygon(pile_center, pile_cap_boundary)
```

If true:

```text
pile belongs to pile cap
```

---

# 30. Intersection

Two objects may intersect.

Example:

```text
────────────
     │
     │
     │
```

Questions your application may ask:

```text
Does beam intersect pile cap?
Does wall intersect beam?
Does dimension cross an object?
```

Geometry libraries can help calculate these relationships.

---

# 31. Typical Construction Takeoff Pipeline

A useful mental model for your project:

```text
CAD FILE
   ↓
Parse DXF
   ↓
Extract entities
   ↓
Normalize geometry
   ↓
Extract text/dimensions
   ↓
Identify layers
   ↓
Identify blocks
   ↓
Build spatial relationships
   ↓
Classify construction elements
   ↓
Group elements
   ↓
Calculate quantities
   ↓
Validate
   ↓
AI-generated takeoff
```

---

# 32. Example: Automated Pile Takeoff

Input:

```text
DXF
```

Parser finds:

```text
35 circles
12 text objects
18 dimensions
4 polylines
```

AI/geometry engine determines:

```text
30 circles = piles
5 circles = other symbols
```

Then:

```text
P1 → 20 piles
P2 → 10 piles
```

Output:

```text
Pile Type | Diameter | Quantity
----------|----------|---------
P1        | 600 mm   | 20
P2        | 750 mm   | 10
```

---

# 33. Why You Should NOT Use an LLM for Everything

A common architecture mistake is:

```text
CAD → LLM → answer
```

Instead:

```text
CAD
 ↓
CAD parser
 ↓
Geometry engine
 ↓
Structured data
 ↓
Rules + spatial reasoning
 ↓
LLM
 ↓
Natural-language explanation
```

### Let deterministic code handle:

- Coordinates
- Distances
- Areas
- Lengths
- Intersections
- Counts
- Geometry
- Bounding boxes
- Point-in-polygon
- Exact dimensions

### Let AI/LLM handle:

- Ambiguous labels
- Drawing interpretation
- Mapping different naming conventions
- Contextual reasoning
- Natural-language questions
- Explaining results

---

# 34. Example Internal Representation

Your application could normalize CAD entities into something like:

```json
{
  "id": "entity_001",
  "type": "circle",
  "layer": "PILE",
  "geometry": {
    "center": [5000, 3000],
    "radius": 300
  },
  "metadata": {
    "source": "drawing.dxf"
  }
}
```

Then classify it:

```json
{
  "element_type": "pile",
  "pile_type": "P1",
  "diameter_mm": 600,
  "center": [5000, 3000]
}
```

This separation is valuable:

```text
RAW CAD DATA
      ↓
NORMALIZED CAD DATA
      ↓
SEMANTIC CONSTRUCTION DATA
```

---

# 35. Useful Python Libraries

For Python CAD processing, know these names:

### ezdxf

A popular Python library for reading/writing DXF.

Think:

```text
DXF → Python objects
```

### Shapely

Useful for 2D computational geometry.

Think:

```text
geometry → distance/intersection/contains/etc.
```

### NumPy

Useful for numerical operations and coordinate manipulation.

### OpenCV

Useful when you also need to process:

- Rendered CAD images
- PDFs
- Raster drawings
- Computer vision

### OCR

Useful for text that is only available visually.

Examples:

```text
Tesseract / Pytesseract
```

---

# 36. Hybrid CAD + Vision Architecture

Real-world drawings may contain information that isn't cleanly available as CAD entities.

A robust system can use:

```text
             CAD FILE
                │
        ┌───────┴────────┐
        ↓                ↓
   DXF Parser       Render/Image
        ↓                ↓
   Geometry          OCR/Vision
        ↓                ↓
        └───────┬────────┘
                ↓
        Information Fusion
                ↓
          AI Reasoning
                ↓
           Takeoff
```

This is often better than relying on only CAD parsing or only computer vision.

---

# 37. CAD Terms You Should Know

| Term | Simple meaning |
|---|---|
| CAD | Computer-Aided Design |
| DXF | CAD exchange file format |
| DWG | Common native AutoCAD drawing format |
| Entity | Individual CAD object |
| Layer | Organizational category |
| Block | Reusable group/component |
| INSERT | Instance of a block |
| Model Space | Main drawing/design area |
| Paper Space | Layout/printing area |
| Viewport | Window showing model space |
| Coordinate | Object position |
| Origin | Coordinate reference point |
| Polyline | Connected sequence of segments |
| Hatch | Filled/patterned area |
| Annotation | Text/dimensions/notes |
| Dimension | Measurement annotation |
| Scale | Relationship between drawing and real-world size |
| X/Y/Z | Coordinate axes |

---

# 38. Construction Terms You Will Encounter

For pile foundation drawings:

### Pile

Deep foundation element transferring load into the ground.

Typical CAD representation:

```text
CIRCLE
```

### Pile Cap

Concrete element connecting one or more piles and supporting a column/load.

Typical representation:

```text
POLYLINE + HATCH + TEXT + DIMENSIONS
```

### Grade Beam

Beam connecting foundations/pile caps.

Typical representation:

```text
LWPOLYLINE / LINE + TEXT + DIMENSIONS
```

### Grid

Reference system for locating structural elements.

Example:

```text
       1       2       3
       │       │       │
A ─────┼───────┼───────┼────
       │       │       │
B ─────┼───────┼───────┼────
```

### Column

Vertical structural member.

### Footing

Foundation element supporting a column/wall/load.

---

# 39. What to Extract From a Construction CAD File

For an automated takeoff engine, think in these categories:

## Geometry

```text
coordinates
length
width
height
radius
diameter
area
perimeter
```

## Identity

```text
element type
element ID
block name
layer
handle
```

## Annotation

```text
text
dimensions
leaders
notes
labels
```

## Relationships

```text
inside
connected
near
intersects
aligned
belongs_to
```

## Quantities

```text
count
length
area
volume
```

---

# 40. A Useful Entity Schema

A generic normalized object could look like:

```json
{
  "id": "E001",
  "cad_type": "CIRCLE",
  "layer": "PILE",
  "geometry": {
    "center": [5000, 3000],
    "radius": 300
  },
  "semantic_type": "PILE",
  "properties": {
    "diameter_mm": 600,
    "pile_type": "P1"
  },
  "source": {
    "file": "foundation.dxf"
  }
}
```

The key idea:

```text
cad_type ≠ semantic_type
```

Example:

```text
cad_type     = CIRCLE
semantic_type = PILE
```

---

# 41. Confidence

AI classification should ideally have confidence.

Example:

```json
{
  "cad_type": "CIRCLE",
  "semantic_type": "PILE",
  "confidence": 0.97
}
```

Possible reasoning:

```text
Layer = PILE             +0.40
Diameter = 600 mm        +0.20
Nearby text = P1         +0.20
Inside pile-cap boundary +0.10
Known symbol pattern     +0.07
```

The exact scoring system depends on your application.

---

# 42. Validation

Never let the AI blindly produce the final takeoff.

Add validation.

Example:

```text
Detected:
30 piles

Expected from schedule:
30 piles

→ PASS
```

Or:

```text
Detected:
28 piles

Schedule:
30 piles

→ REVIEW REQUIRED
```

Useful validation rules:

```text
pile count
pile diameter
pile spacing
pile-cap association
beam length
duplicate detection
missing labels
dimension consistency
```

---

# 43. The Most Important Mental Model

When you see a CAD drawing, ask:

### 1. WHAT?

```text
CIRCLE?
LINE?
POLYLINE?
TEXT?
DIMENSION?
BLOCK?
```

### 2. WHERE?

```text
(x, y, z)
```

### 3. WHICH CATEGORY?

```text
layer
block
```

### 4. WHAT DOES IT MEAN?

```text
pile?
beam?
column?
pile cap?
grid?
```

### 5. WHAT IS IT RELATED TO?

```text
inside pile cap?
connected to beam?
near column?
aligned with grid?
```

### 6. WHAT CAN I CALCULATE?

```text
count
length
area
distance
quantity
```

---

# 44. One-Page Memory Sheet

```text
CAD
│
├── ENTITY = drawing object
│   ├── LINE
│   ├── CIRCLE
│   ├── ARC
│   ├── POLYLINE
│   ├── SPLINE
│   ├── ELLIPSE
│   ├── HATCH
│   ├── TEXT
│   ├── MTEXT
│   ├── DIMENSION
│   ├── LEADER
│   └── INSERT
│
├── LAYER = organization/category
│
├── BLOCK = reusable component
│
├── COORDINATES = WHERE
│   ├── X
│   ├── Y
│   └── Z
│
├── GEOMETRY = SHAPE
│
└── SEMANTICS = MEANING
```

### For pile takeoff:

```text
CIRCLE
  ↓
center + radius
  ↓
diameter
  ↓
layer + text + context
  ↓
PILE
  ↓
pile type
  ↓
group/count
  ↓
validate
  ↓
takeoff
```

---

# 45. What to Learn First

Do NOT try to learn all of CAD at once.

Use this order:

### Level 1 — Must know

```text
CAD
DXF
Entity
Layer
Coordinate
CIRCLE
LINE
POLYLINE
TEXT
DIMENSION
BLOCK
```

### Level 2 — Very useful

```text
ARC
HATCH
LEADER
MULTILEADER
INSERT
ATTRIB
Model Space
Paper Space
Bounding Box
```

### Level 3 — Geometry programming

```text
distance
intersection
contains
point-in-polygon
nearest-neighbor
clustering
area
perimeter
```

### Level 4 — AI application

```text
entity classification
spatial reasoning
text-to-geometry association
semantic normalization
confidence scoring
validation
takeoff generation
```

---

# 46. Final Cheat Code

When looking at any CAD entity, remember:

> **TYPE + WHERE + LAYER + CONTEXT = MEANING**

For example:

```text
CIRCLE
+
(5000, 3000)
+
LAYER = PILE
+
TEXT = P1
+
DIA = 600
```

becomes:

```text
PILE P1
600 mm diameter
at (5000, 3000)
```

That transformation — **raw CAD → structured geometry → semantic construction object → quantity** — is the core idea you need for an AI-powered CAD takeoff system.
