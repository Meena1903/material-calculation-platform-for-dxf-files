# BuildIQ AI — Automated Pile Foundation Takeoff Engine

> **Technical Assessment Submission**: Automated Pile Foundation Takeoff, Concrete Volumetrics, Bar Bending Schedule (BBS) Steel Tonnage, and Manpower Productivity Estimation from CAD (`.DXF`) and Blueprint (`.PDF`) Drawings.

---

## 1. Approach

Our approach integrates **Computer Vision**, **Multimodal LLMs (NVIDIA NIM)**, and **CAD Computational Geometry** into a decoupled, production-grade pipeline:

1. **Dual Ingestion**: Ingests CAD vector drawings (`.DXF`) for precise spatial coordinate data and high-resolution blueprint PDFs (`.PDF`) for visual schedule verification.
2. **HD Region-of-Interest (ROI) Cropping**: Uses `PyMuPDF` at 300 DPI to isolate schedule tables and cross-section details, preventing token dilution and downsampling loss in vision models.
3. **Multimodal Schema Extraction**: NVIDIA NIM Vision APIs (`meta/llama-3.2-90b-vision-instruct` / `mistralai/pixtral-12b-2409`) localize and transcribe tabular data into strictly validated **Pydantic schemas**.
4. **100% Deterministic Python Engineering Core**: All volumetric extrusions, unit weights via IS 1786 ($d^2/162.28$), and labor estimations execute **exclusively in native Python**, eliminating LLM hallucination and mathematical drift.
5. **Interactive Full-Stack Interface**: A React + TypeScript dashboard with a 2D HTML5 Canvas CAD viewer, BBS inspector, Recharts analytics, and one-click export for `output_takeoff.json` and `output_boq.csv`.

---

## 2. Architecture

```
                                SYSTEM ARCHITECTURE
                                
   +-----------------------+              +-----------------------+
   | CAD Vector DXF File   |              | High-Res PDF Drawing  |
   +-----------+-----------+              +-----------+-----------+
               |                                      |
               v                                      v
   +-----------------------+              +-----------------------+
   |  CAD Vector Parser    |              |  PyMuPDF HD Cropper   |
   | (ezdxf geometry,      |              | (ROI Slicing: Table,  |
   |  circles, text, tags) |              |  Cross-Sections @300DPI|
   +-----------+-----------+              +-----------+-----------+
               |                                      |
               |                                      v
               |                          +-----------------------+
               |                          | NVIDIA NIM Vision API |
               |                          | (Llama-3.2-Vision /   |
               |                          |  Pixtral-12B / NeVA)  |
               |                          +-----------+-----------+
               |                                      |
               |                                      v
               |                          +-----------------------+
               |                          | Pydantic Schema       |
               |                          | Validation Layer      |
               |                          +-----------+-----------+
               |                                      |
               +------------------+-------------------+
                                  |
                                  v
                  +-------------------------------+
                  |  CRITICAL ENGINEERING CORE    |
                  |  100% Native Python 3.14      |
                  |  Mathematical Calculations    |
                  |  (calculator.py - IS 1786)   |
                  +---------------+---------------+
                                  |
       +--------------------------+--------------------------+
       |                          |                          |
       v                          v                          v
+--------------+           +--------------+           +--------------+
| Concrete RMC |           | Steel BBS    |           | Manpower     |
| Volume (m³)  |           | Tonnage (MT) |           | Productivity |
| (V = π·r²·L) |           | (d²/162.28)  |           | (Man-Days)   |
+--------------+           +--------------+           +--------------+
       |                          |                          |
       +--------------------------+--------------------------+
                                  |
                                  v
                   +------------------------------+
                   | Output Artifacts & Delivery  |
                   | - output_takeoff.json        |
                   | - output_boq.csv             |
                   | - React + TS Interactive App |
                   +------------------------------+
```

### Module Structure:
- `backend/app/services/calculator.py`: 100% deterministic native Python civil engineering calculations.
- `backend/app/services/dxf_parser.py`: Vector CAD entity, block insert, and circle parsing with `ezdxf`.
- `backend/app/services/pdf_vision_parser.py`: High-DPI rasterization and ROI crop generation.
- `backend/app/services/nvidia_nim_extractor.py`: NVIDIA NIM API multimodal client with Pydantic validation.
- `backend/app/services/extractor.py`: Pipeline orchestrator unifying CAD vectors and visual schemas.
- `backend/app/services/exporter.py`: Exporter for `output_takeoff.json`, `output_boq.csv`, and submission ZIP.
- `frontend/src/`: React 18 + TypeScript + Tailwind CSS dashboard with 2D Canvas CAD visualizer and BBS drawer.

---

## 3. Critical Engineering Constraint Compliance

> **Mandatory Constraint**: LLMs/Vision models are **ONLY** used for visual parsing, table localization, and schema extraction (structured via Pydantic). **100% of the mathematical formulas, volumetric extrusions, and unit weight calculations execute in native Python.**

### Enforcement:
- The vision model receives an image crop and returns raw schema strings (e.g. tag: `"P50"`, dia: `500`, depth: `35`, count: `29`).
- `calculator.py` takes these validated numbers and executes deterministic arithmetic without any LLM in the numerical loop.

---

## 4. Civil Engineering Formulas & Mathematical Basis

### A. Concrete (RMC) Volumetric Takeoff
For circular piles of diameter $d$ (mm) and depth $L$ (m):
- **Radius**:
  $$r = \frac{d}{2000} \text{ m}$$
- **Volume per Pile**:
  $$V_{\text{pile}} = \pi \times r^2 \times L = \frac{\pi \times (d/1000)^2}{4} \times L \quad (\text{m}^3)$$
- **Total Theoretical Volume**:
  $$V_{\text{total}} = \sum_{i=1}^{N} V_{\text{pile}, i} \quad (\text{m}^3)$$
- **Volume with 5% Wastage / Overbreak Allowance**:
  $$V_{\text{boq}} = V_{\text{total}} \times 1.05 \quad (\text{m}^3)$$

### B. Steel Reinforcement (BBS) Tonnage (IS 1786 / SP 34)
- **Unit Weight Formula**:
  $$w = \frac{d^2}{162.28} \text{ kg/m} \quad (\text{where } d \text{ is bar diameter in mm})$$
  *(Derived from nominal steel density $\rho = 7850\text{ kg/m}^3$)*

- **Main Longitudinal Reinforcement**:
  $$L_{\text{cut}} = L_{\text{pile}} + 1.0\text{m (Anchorage } L_d \text{ into pile cap)}$$
  $$W_{\text{main}} = n_{\text{bars}} \times L_{\text{cut}} \times \left(\frac{d_{\text{main}}^2}{162.28}\right) \text{ kg}$$

- **Helical / Spiral Ties (8mm dia @ 180mm c/c)**:
  $$D_{\text{cage}} = D_{\text{pile}} - 2 \times 0.05\text{m (clear cover)}$$
  $$L_{\text{turn}} = \sqrt{(\pi D_{\text{cage}})^2 + 0.18^2}$$
  $$L_{\text{spiral}} = \left(\frac{L_{\text{pile}}}{0.18} + 2\right) \times L_{\text{turn}}$$
  $$W_{\text{spiral}} = L_{\text{spiral}} \times \left(\frac{8^2}{162.28}\right) \text{ kg}$$

- **Spacer / Stiffener Rings (12mm dia @ 1500mm c/c)**:
  $$N_{\text{spacers}} = \left\lfloor \frac{L_{\text{pile}}}{1.5} \right\rfloor + 1$$
  $$L_{\text{ring}} = \pi D_{\text{cage}} + 0.15\text{m}$$
  $$W_{\text{spacers}} = N_{\text{spacers}} \times L_{\text{ring}} \times \left(\frac{12^2}{162.28}\right) \text{ kg}$$

- **Metric Ton Conversion**:
  $$\text{Total Steel Tonnage (MT)} = \frac{\sum W_{\text{steel}}}{1000.0}$$

### C. Manpower Productivity Estimation
- **Piling & Concreting**: $0.25 \text{ Man-Days/m}^3 \rightarrow 0.25 \times 1350.491 = \mathbf{337.62\text{ Man-Days}}$
- **Rebar Fabrication**: $2.50 \text{ Man-Days/MT} \rightarrow 2.50 \times 63.4164 = \mathbf{158.54\text{ Man-Days}}$
- **Pile Head Chipping**: $0.50 \text{ Man-Days/pile} \rightarrow 0.50 \times 83 = \mathbf{41.50\text{ Man-Days}}$
- **Total Man-Days**: $337.62 + 158.54 + 41.50 = \mathbf{537.66\text{ Man-Days}}$

---

## 5. Ground Truth Verification & Takeoff Results

Audited against `sample files/PILE LAYOUT AND DETAILS (27.09.2024) 1.dxf` & `.pdf`:

| Pile Tag | Diameter (mm) | Depth (m) | Capacity (T) | Cap Config | Pile Count | Unit Vol (m³) | Total Vol (m³) | Steel (MT) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P50** | 500 mm | 35 m | 60 T | 29 caps × 1 | **29** | 6.872 m³ | 199.294 m³ | 11.1326 MT |
| **P70A** | 700 mm | 35 m | 90 T | 2 caps × 1 | **2** | 13.470 m³ | 26.939 m³ | 1.2889 MT |
| **P90** | 900 mm | 45 m | 225 T | 1 cap × 1 | **1** | 28.628 m³ | 28.628 m³ | 1.2530 MT |
| **2P70** | 700 mm | 45 m | 90 T | 5 caps × 2 | **10** | 17.318 m³ | 173.180 m³ | 8.2470 MT |
| **2P80** | 800 mm | 45 m | 150 T | 8 caps × 2 | **16** | 22.619 m³ | 361.912 m³ | 16.1528 MT |
| **2P90** | 900 mm | 45 m | 225 T | 4 caps × 2 | **8** | 28.628 m³ | 229.022 m³ | 10.0240 MT |
| **3P80** | 800 mm | 45 m | 150 T | 1 cap × 3 | **3** | 22.619 m³ | 67.858 m³ | 3.0287 MT |
| **4P80** | 800 mm | 45 m | 150 T | 1 cap × 4 | **4** | 22.619 m³ | 90.478 m³ | 4.0382 MT |
| **10P70** | 700 mm | 45 m | 90 T | 1 cap × 10 | **10** | 17.318 m³ | 173.180 m³ | 8.2470 MT |
| **TOTAL** | — | — | — | — | **83 Nos** | — | **1,350.491 m³** | **63.4164 MT** |

---

## 6. Handling of Geometry, HD Crops & Known Edge Cases

### A. High-Definition Region-of-Interest (ROI) Cropping:
Blueprints often measure $36 \times 48\text{ inches}$ (Arch E) with small schedules occupying $<10\%$ of the canvas. Slicing the full page into an LLM causes blurry downsampling.
- **Solution**: `pdf_vision_parser.py` extracts 300 DPI sub-region crops:
  1. `schedule_table`: Targeted bounding box on the tabular pile schedule.
  2. `rebar_sections`: Targeted crop on rebar callouts and clear cover details.
  3. `overview`: Global sheet overview.

### B. AutoCAD Dynamic Blocks (`*U` & `*D` Anonymous Blocks):
In AutoCAD, dynamic blocks and dimension blocks receive anonymous names like `*U25`, `*U51`, `*D285`. Standard block iteration misses them.
- **Solution**: `dxf_parser.py` recursively inspects all block definitions in the DXF block table, extracting child circles, texts, and attribute definitions (`ATTDEF`).

### C. Text Formatting Control Codes:
AutoCAD embeds formatting codes directly into text strings (e.g. `\C7;` for color, `%%U` for underline, `\P` for paragraph break, `%%C` or `\U+2205` for diameter symbol Ø).
- **Solution**: A regex normalization filter cleans control codes while reliably mapping `%%C` and `dia` to diameter attributes.

### D. Group Multiplier Expressions:
Drawings express multi-pile groups using mathematical notation (e.g. `08x2=16` for `2P80`, `05x2=10` for `2P70`, `01x10=10` for `10P70`).
- **Solution**: An expression parser extracts both the cap count ($N_{\text{caps}}$) and group multiplier ($m$), computing total individual piles as $N_{\text{total}} = N_{\text{caps}} \times m$.

### E. Mixed Diameter Longitudinal Rebar:
Some pile types use multiple bar sizes within the same cage (e.g. `P90` contains $5\times\varnothing 20\text{mm} + 5\times\varnothing 16\text{mm}$).
- **Solution**: The BBS calculator supports composite rebar arrays per pile, applying the exact $d^2/162.28$ unit weight to each subset before summation.

### F. Network / API Key Offline Fallback:
If the NVIDIA NIM API key is unavailable or rate-limited, the engine automatically falls back to deterministic CAD vector spatial parsing without crashing.

---

## 7. Setup & Execution Guide

### Automated Setup Scripts:
- **Windows**: Run `buildiq_engine\scripts\setup_windows.bat` or `.\scripts\setup_windows.ps1`
- **Ubuntu / Linux**: `chmod +x buildiq_engine/scripts/setup_ubuntu.sh && ./buildiq_engine/scripts/setup_ubuntu.sh`
- **macOS**: `chmod +x buildiq_engine/scripts/setup_mac.sh && ./buildiq_engine/scripts/setup_mac.sh`

### Manual Run:
```bash
# 1. Start Backend (FastAPI on Port 8000)
cd buildiq_engine/backend
..\..\.venv\Scripts\python app\main.py

# 2. Start Frontend (React on Port 5173)
cd buildiq_engine/frontend
npm run dev
```

---

## 8. Output Deliverables

1. **`output_takeoff.json`**: Complete structured JSON containing pile inventory, concrete volumes, BBS steel breakdown, and manpower.
2. **`output_boq.csv`**: Civil engineering standard Bill of Quantities spreadsheet formatted with item codes, descriptions, units, rates, and amounts in INR.
3. **`BuildIQ_Meena_Assessment.zip`**: Complete source code, tests, schemas, requirements, and artifacts.
