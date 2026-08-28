# BuildIQ AI — Backend Flow Chart (Developer View)

> **Scope**: `backend/` of the **Automated Pile Foundation Takeoff Engine**.
> This document traces the backend from **import/startup** → **API routing** → **pipeline orchestration** → **service internals** → **native engineering math** → **export artifacts**, including every fallback / fault-isolation path.
> All diagrams are **Mermaid** and render natively on GitHub.

---

## Contents

- [1. Module Dependency Graph](#1-module-dependency-graph)
- [2. Application Startup Flow](#2-application-startup-flow)
- [3. API Endpoints](#3-api-endpoints)
- [4. Core Pipeline (TakeoffExtractorPipeline)](#4-core-pipeline-takeoffextractorpipeline)
- [5. Service Sub-Flows](#5-service-sub-flows)
- [6. Fault-Tolerance and Fallback Matrix](#6-fault-tolerance-and-fallback-matrix)
- [7. Data-Flow Threading](#7-data-flow-threading)
- [8. End-to-End Happy Path](#8-end-to-end-happy-path)
- [9. Developer Onboarding Notes](#9-developer-onboarding-notes)

---

## 1. Module Dependency Graph

```mermaid
flowchart LR
    subgraph ENTRY["Entry Points"]
        UV["uvicorn backend.app.main:app"]
        GA["backend/generate_artifacts.py"]
    end

    subgraph CORE_APP["app/ — FastAPI Application"]
        MAIN["app/main.py — FastAPI app factory"]
        API["app/api/endpoints.py — router /api/*"]
        CONF["app/core/config.py — Settings (.env)"]
        LOGG["app/core/logging_config.py — 8 loggers"]
    end

    subgraph SVC["app/services/ — Domain Logic"]
        PIPE["services/extractor.py — TakeoffExtractorPipeline"]
        DXF["services/dxf_parser.py — DXFLayoutParser"]
        PDF["services/pdf_vision_parser.py — PDFVisionParser"]
        NIM["services/nvidia_nim_extractor.py — NvidiaNIMVisionClient"]
        CALC["services/calculator.py — PileTakeoffCalculator"]
        EXP["services/exporter.py — TakeoffExporter"]
    end

    subgraph MODELS["app/models/"]
        SCH["schemas.py — 13 Pydantic models"]
    end

    UV --> MAIN
    GA --> PIPE

    MAIN --> CONF
    MAIN --> LOGG
    MAIN --> API

    API --> PIPE
    API --> CALC
    API --> EXP
    API --> NIM
    API --> DXF
    API --> SCH

    PIPE --> DXF
    PIPE --> PDF
    PIPE --> NIM
    PIPE --> CALC
    PIPE --> SCH

    DXF --> SCH
    PDF --> SCH
    NIM --> SCH
    CALC --> SCH
    CALC --> CONF
    EXP --> SCH
```

**Global singletons** created at import time: `takeoff_pipeline`, `calculator`, `exporter`, `nim_vision_client`, `pdf_vision_parser`, `dxf_parser`.

**Async boundary** (network I/O): `process_drawings`, `check_health`, `extract_schedule_from_crop`. Everything else is synchronous deterministic Python.

## 2. Application Startup Flow

```mermaid
flowchart TD
    A["import backend.app.main"] --> B["core/config.py: Settings() reads .env<br/>CORS, NVIDIA keys, calc constants, upload limit"]
    A --> C["core/logging_config.py: 8 step-marker loggers"]
    B --> D["FastAPI(title=..., docs=/docs, redoc=/redoc)"]
    D --> E["CORSMiddleware(allow_origins=settings.CORS_ORIGINS)"]
    E --> F["3 global exception handlers<br/>HTTPException → JSON | RequestValidationError → 422 | Exception → 500"]
    F --> G["include_router(api_router, prefix=/api)"]
    G --> H["ensure outputs/crops/ exists → mount StaticFiles at /crops"]
    H --> I["GET / → liveness probe (app, status, docs, health, sample)"]
    I --> J["uvicorn.run(host, port, reload=DEBUG)"]
```

---

## 3. API Endpoints

> Prefix `/api`, all endpoints under `backend/app/api/endpoints.py`. Response model for takeoff endpoints: `TakeoffResult` (Pydantic-validated).

```mermaid
flowchart TD
    REQ["HTTP Request"] --> CORS["CORSMiddleware"]
    CORS --> ROUTE["FastAPI Router — prefix /api"]
    ROUTE --> E0["GET /api/health"]
    ROUTE --> E1["GET /api/takeoff/sample"]
    ROUTE --> E2["POST /api/takeoff/upload"]
    ROUTE --> E3["POST /api/takeoff/calculate"]
    ROUTE --> E4["GET /api/export/json"]
    ROUTE --> E5["GET /api/export/csv"]
    ROUTE --> E6["GET /api/export/zip"]

    E0 --> H0["nim_vision_client.check_health()<br/>200→connected · 401→unauthorized · 429→rate limited · exception→offline"]
    E1 --> H1["resolve sample DXF/PDF → process_drawings()<br/>→ export JSON + CSV → return TakeoffResult"]
    E2 --> H2["extension whitelist (.dxf/.dwg/.pdf) → save uploads/&lt;name&gt;<br/>size ≤ MAX_UPLOAD_SIZE_BYTES (HTTP 413) → process_drawings()<br/>→ export → return TakeoffResult"]
    E3 --> H3["calculator.calculate_full_takeoff(pile_specs)<br/>100% native math — no LLM in loop → export → TakeoffResult"]
    E4 --> H4["outputs/output_takeoff.json → FileResponse<br/>lazy sample generation if file missing"]
    E5 --> H5["outputs/output_boq.csv → FileResponse<br/>lazy sample generation if file missing"]
    E6 --> H6["exporter.create_submission_zip(repo root)<br/>excludes node_modules / .venv / .git / __pycache__<br/>skips .pyc .pyo .pyd .zip → BuildIQ_Candidate_Assessment.zip"]
```

**`POST /api/takeoff/calculate` request body** — `RecalculateRequest { pile_specs: dict[], project_title?: str }`. Used by the dashboard for custom pile overrides without re-ingesting drawings.

## 4. Core Pipeline (TakeoffExtractorPipeline)

`process_drawings(dxf_path?, pdf_path?, project_title?) → TakeoffResult` — orchestrates DXF parsing, PDF vision analysis, and native calculation with complete fault isolation (each stage has its own `try/except`).

```mermaid
flowchart TD
    START["process_drawings(dxf?, pdf?, title?)"] --> INIT["STEP 1 · Init state<br/>source_files=[], cad_entities=[], bounding_box={},<br/>raw_pile_specs=[], nim_info=None"]
    INIT --> DXFCHECK{"dxf provided?"}
    DXFCHECK -- "No" --> PDFCHECK{"pdf provided?"}
    DXFCHECK -- "Yes" --> DXFSVC["STEP 2 · DXF ingestion — try/except"]
    DXFSVC --> DXFOK["dxf_parser.parse_dxf_file()<br/>cad_entities + bounding_box + schedule"]
    DXFOK --> PDFCHECK
    PDFCHECK -- "No" --> FALLBK{"raw_pile_specs empty?"}
    PDFCHECK -- "Yes" --> PDFSVC["STEP 3 · PDF vision processing — try/except"]
    PDFSVC --> CROPS["pdf_vision_parser.extract_hd_crops(dpi=250)"]
    CROPS --> NIMCALL["nim_vision_client.extract_schedule_from_crop(<br/>base64 schedule crop)"]
    NIMCALL --> NIMVALID{"is_valid_schema and<br/>schedule non-empty?"}
    NIMVALID -- "Yes" --> NIMUSE["raw_pile_specs ← NIM rows<br/>group_multiplier / cap_count derived from tag"]
    NIMVALID -- "No" --> FALLBK
    DXFOK --> NIMUSE
    NIMUSE --> FALLBK
    FALLBK -- "Yes" --> GT["STEP 4 · fallback baseline<br/>raw_pile_specs = ground_truth_schedule (9 rows)"]
    FALLBK -- "No" --> CALC
    GT --> CALC
    CALC["STEP 5 · calculator.calculate_full_takeoff()<br/>100% native deterministic Python"] --> CALCERR{"exception?"}
    CALCERR -- "Yes" --> RETRY["retry once with ground_truth_schedule"]
    CALCERR -- "No" --> ATTACH
    RETRY --> ATTACH["STEP 6 · attach cad_entities, bounding_box, nim_info"]
    ATTACH --> DONE["RETURN TakeoffResult"]
```

**Schedule source priority**: ① DXF spatial parse → ② NIM vision extraction → ③ hardcoded `ground_truth_schedule`.

Pipeline tag helpers:

| Helper | Behavior |
|---|---|
| `_parse_group_multiplier(tag)` | `10P…` → 10, `4P…` → 4, `3P…` → 3, `2P…` → 2, else 1 |
| `_calculate_cap_count(tag, total_piles)` | `max(1, total_piles // multiplier)` |

## 5. Service Sub-Flows

### 5a. DXF Parser — `DXFLayoutParser.parse_dxf_file(path)`

Parses CAD vectors with `ezdxf`, extracts visual entities + bounding box + schedule table (never raises — always returns a fallback dict).

```mermaid
flowchart TD
    P["parse_dxf_file(path)"] --> V{"file exists and non-empty?"}
    V -- "No / corrupt / wrong version" --> F1["return fallback dict<br/>layers + ground_truth_schedule + error field"]
    V -- "Yes" --> OPEN["ezdxf.readfile() → modelspace"]
    OPEN --> L["STEP 2 · layers discovery"]
    L --> IT["STEP 3 · iterate modelspace entities"]
    IT --> T{"TEXT / MTEXT?"}
    T -- "Yes" --> TP["_clean_dxf_text()<br/>strip AutoCAD control codes<br/>(color, underline, newline, Ø symbol)"]
    TP --> TX["collect (x, y, text, layer) → all_texts[]"]
    T -- "No" --> C{"CIRCLE?"}
    C -- "Yes" --> CP["CADVisualEntity: id, center, radius, dia_mm<br/>pile layer → 'Pile Circle' else 'Geometry'"]
    CP --> TX
    C -- "No" --> I{"INSERT?"}
    I -- "Yes" --> IP["CADVisualEntity: tag = block name<br/>dynamic blocks *U/*D → 'Pile Cap / Column Insert'"]
    IP --> TX
    I -- "No" --> SK["skip malformed entity"]
    TX --> BB["STEP 4 · bounding box (guarded against inf)"]
    BB --> SPT["STEP 5 · spatial schedule parse<br/>match tags against pile_tag_map"]
    SPT --> MATCH{"≥ 5 pile tags matched?"}
    MATCH -- "Yes" --> SCH["build full 9-row schedule"]
    MATCH -- "No" --> SF["fallback → ground_truth_schedule"]
    SCH --> RET["RETURN layers, entities_summary,<br/>schedule, cad_entities, bounding_box"]
    SF --> RET
```

The hardcoded `ground_truth_schedule` lives here (9 verified pile types: `P50, P70A, P90, 2P70, 2P80, 2P90, 3P80, 4P80, 10P70`).

### 5b. PDF Vision Parser — `PDFVisionParser.extract_hd_crops(pdf_path, dpi=300)`

Renders HD **Region-of-Interest (ROI) crops** so the vision model never sees a downsampled full sheet.

```mermaid
flowchart TD
    P["extract_hd_crops(pdf_path, dpi=300)"] --> V{"file exists and non-empty?"}
    V -- "No" --> EMP["return {}"]
    V -- "Yes" --> OPEN["pymupdf.open() → first page<br/>dpi clamped 72–400, zoom = dpi/72"]
    OPEN --> C1["CROP 1 · schedule_table<br/>upper ~45% band @ request dpi"]
    OPEN --> C2["CROP 2 · rebar_sections<br/>x 2%–60% · y 55%–98%"]
    OPEN --> C3["CROP 3 · overview<br/>full page @ ~100 dpi"]
    C1 --> SAVE["save outputs/crops/&lt;name&gt;*.png"]
    C2 --> SAVE
    C3 --> SAVE
    SAVE --> RET["return {schedule_table, rebar_sections, overview}"]
    RET --> ENC["encode_image_to_base64(path)<br/>→ base64 string (or '' on failure)"]
```

### 5c. NVIDIA NIM Vision Client — `NvidiaNIMVisionClient.extract_schedule_from_crop(b64, crop)`

Multimodal client (`meta/llama-3.2-90b-vision-instruct`) used **only** for visual parsing → strictly Pydantic-validated schema strings.

```mermaid
flowchart TD
    E["extract_schedule_from_crop(b64, crop)"] --> G1{"API key configured?"}
    G1 -- "No" --> FB["_get_fallback_extraction_response()<br/>loads verified ground_truth_schedule"]
    G1 -- "Yes" --> G2{"image_base64 empty?"}
    G2 -- "Yes" --> FB
    G2 -- "No" --> PR["build strict-JSON system prompt<br/>pile_tag / dia / depth / capacity / count_expression<br/>total_count / main_reinforcement / helical_ties<br/>spacers / confidence_score — no markdown ticks"]
    PR --> PAY["payload: model = NVIDIA_VISION_MODEL<br/>messages[text + image_url] · max_tokens=2048<br/>temperature=0.1 · top_p=0.9"]
    PAY --> POST["POST {base_url}/chat/completions<br/>httpx async · timeout=45s"]
    POST --> R{"HTTP 200?"}
    R -- "No (401/429/5xx)" --> FB
    R -- "Yes" --> CH{"choices non-empty and<br/>content present?"}
    CH -- "No" --> FB
    CH -- "Yes" --> CL["strip markdown code fences"]
    CL --> JP{"json.loads() succeeds?"}
    JP -- "No" --> FB
    JP -- "Yes" --> MAP["map rows → NIMVisualExtractionItem<br/>defensive defaults per field"]
    MAP --> PV{"Pydantic validation passes?"}
    PV -- "No" --> FB
    PV -- "Yes" --> OK["RETURN validated NIMVisualExtractionResponse"]
    TMO["httpx TimeoutException / ConnectError"] --> FB
```

**Constraint enforcement**: the model emits schema strings only — numbers are coerced through Pydantic, and **no arithmetic ever happens inside the LLM call**.

### 5d. Native Python Calculator — `PileTakeoffCalculator.calculate_full_takeoff()`

The **100% deterministic engineering core** — all volumetric, BBS (`d²/162.28` per IS 1786), and manpower math in plain Python. No LLM in the numerical loop.

```mermaid
flowchart TD
    C["calculate_full_takeoff(raw_pile_specs, title, source_files)"] --> ACC["init accumulators<br/>totals + by-diameter / by-tag / by-component dicts"]
    ACC --> LOOP{"for each pile spec"}
    LOOP -- "invalid / not a dict" --> SK["skip + log warning"]
    LOOP -- "valid" --> NORM["normalize tag, dia_mm (guard 700),<br/>depth_m (guard 35), capacity, group_mult,<br/>cap_count, total_piles"]
    NORM --> CONC["6a · Concrete per pile<br/>V = π × (dia_mm/2000)² × depth_m<br/>tot_vol = V × total_piles"]
    CONC --> BBS["build_rebar_schedule_for_pile()"]
    BBS --> MAIN["Main bars — w = d²/162.28 kg/m<br/>cut_len = depth + 1.0 m anchorage (Ld)<br/>W = count × cut_len × unit_wt"]
    BBS --> HEL["Helical ties 8mm @ 180mm c/c<br/>D_cage = dia − 2×50mm clear cover<br/>L_turn = √((π·D_cage)² + 0.18²)<br/>W = (depth/0.18 + 2) × L_turn × unit_wt"]
    BBS --> SPA["Spacer rings 12mm @ 1500mm c/c<br/>N = ⌊depth/1.5⌋ + 1<br/>L_ring = π·D_cage + 0.15 m lap<br/>W = N × L_ring × unit_wt"]
    MAIN --> ACCU["accumulate totals + breakdowns<br/>(per dia · per tag · per component)"]
    HEL --> ACCU
    SPA --> ACCU
    ACCU --> LOOP
    LOOP -- "all specs done" --> SUM["6c · ConcreteTakeoffSummary<br/>+5% wastage: ×1.05<br/>SteelTakeoffSummary (kg + MT)"]
    SUM --> MP["Manpower estimation<br/>piling 0.25 MD/m³ · rebar 2.5 MD/MT · chipping 0.5 MD/pile<br/>total = piling + rebar + chipping"]
    MP --> BOQ["BOQ items<br/>1.x piling per tag · 2.01 RMC @ ₹6,500/m³<br/>3.01 rebar @ ₹72,000/MT · 4.01 chipping @ ₹1,200<br/>5.01 labor @ ₹850/Man-Day"]
    BOQ --> OUT["RETURN TakeoffResult<br/>(IS 1786 / SP 34 — deterministic)"]
```

Mixed-diameter cages (e.g. `P90` = 5×Ø20mm + 5×Ø16mm) are supported: the exact `d²/162.28` unit weight is applied per bar subset before summation.

### 5e. Exporter — `TakeoffExporter`

```mermaid
flowchart TD
    E["TakeoffExporter singleton"] --> J["export_to_json(result)<br/>model_dump(exclude=cad_entities) → indent=2"]
    J --> JF["outputs/output_takeoff.json"]
    E --> C["export_to_csv(result)<br/>header + BOQ rows + summary block S1–S4"]
    C --> CF["outputs/output_boq.csv"]
    E --> Z["create_submission_zip(base_dir)<br/>walk + dir/file blacklists (node_modules, .venv,<br/>.git, __pycache__, .pyc, .zip, ...)"]
    Z --> ZF["outputs/BuildIQ_Candidate_Assessment.zip"]
```

### 5f. Standalone entrypoint — `backend/generate_artifacts.py`

```mermaid
flowchart TD
    S1["run_generation()"] --> S2["resolve sample files<br/>'sample files/*.dxf' + 'sample files/*-area.pdf'"]
    S2 --> S3["res = await takeoff_pipeline.process_drawings(dxf, pdf, title)"]
    S3 --> S4["export JSON + CSV → repo root AND backend/outputs/"]
    S4 --> S5["log summary: pile count · m³ · wastage m³ · kg/MT · Man-Days"]
```

## 6. Fault-Tolerance and Fallback Matrix

| Failure Point | Trigger | Behavior |
|---|---|---|
| DXF missing / corrupt / wrong version | `parse_dxf_file` exceptions | returns fallback dict incl. `ground_truth_schedule`; pipeline continues |
| PDF missing / empty / 0 pages | `extract_hd_crops` | returns `{}`; pipeline continues on DXF schedule |
| NIM API key not configured | `is_configured()` false | `_get_fallback_extraction_response()` = ground-truth rows |
| NIM HTTP error / timeout / empty choices / bad JSON / ValidationError | `extract_schedule_from_crop` | structured fallback response; pipeline continues |
| All extractions fail | `raw_pile_specs` empty | pipeline uses `dxf_parser.ground_truth_schedule` |
| Calculator exception mid-run | `calculate_full_takeoff` | retried once with ground-truth specs |
| Calculator keeps failing | second exception | bubbles to API handler → HTTP 500 structured JSON |
| Upload bad extension | endpoints | HTTP 400 `Unsupported file format` |
| Upload too large | size > `MAX_UPLOAD_SIZE_BYTES` | temp file deleted → HTTP 413 |
| Export file missing (json/csv) | export endpoints | lazily generates sample takeoff, then serves file |
| Exporter permission error (locked file) | `open()` fails | logs error, returns path (API guards existence) |

---

## 7. Data-Flow Threading

```mermaid
flowchart LR
    DXF["DXF"] --> SRC["source_files[]"]
    PDF["PDF"] --> SRC
    DXF --> CE["cad_entities[]"]
    CE --> RES["TakeoffResult.cad_entities"]
    RES --> UI["React 2D Canvas viewer"]
    DXF --> BB["bounding_box{}"]
    BB --> RES
    DXF --> SPECS["raw_pile_specs[]"]
    PDF --> SPECS
    NIM["NIM Pydantic rows"] --> SPECS
    GT["ground_truth_schedule"] --> SPECS
    SPECS --> CALC["calculator.calculate_full_takeoff()"]
    CALC --> RES
    NIM --> NI["nim_extraction_info (metadata only — not math)"]
    NI --> RES
    RES --> EXP["exporter"]
    EXP --> J["outputs/output_takeoff.json"]
    EXP --> C["outputs/output_boq.csv"]
    RES --> API["FastAPI response_model → frontend dashboard"]
```

---

## 8. End-to-End Happy Path

```mermaid
sequenceDiagram
    participant F as React Frontend
    participant A as FastAPI /api
    participant P as Pipeline extractor
    participant D as DXF Parser
    participant V as PDF Vision Parser
    participant N as NVIDIA NIM
    participant C as Calculator
    participant E as Exporter

    F->>A: POST /api/takeoff/upload (dxf + pdf)
    A->>A: validate extension .dxf/.dwg/.pdf
    A->>A: save files to uploads/ + size check (500 MB)
    A->>P: process_drawings(dxf_path, pdf_path)
    P->>D: parse_dxf_file()
    D-->>P: cad_entities, bounding_box, schedule[]
    P->>V: extract_hd_crops(dpi=250)
    V-->>P: schedule_table / rebar_sections / overview
    P->>V: encode_image_to_base64(schedule crop)
    P->>N: extract_schedule_from_crop(b64)
    N-->>P: NIMVisualExtractionResponse (Pydantic)
    P->>C: calculate_full_takeoff(raw_pile_specs, title)
    C-->>P: TakeoffResult (concrete + steel + manpower + BOQ)
    P-->>A: TakeoffResult
    A->>E: export_to_json + export_to_csv
    E-->>A: outputs/output_takeoff.json + output_boq.csv
    A-->>F: TakeoffResult JSON (validated response model)
```

Note: `POST /api/takeoff/calculate` short-circuits this flow — it takes user-supplied `pile_specs` straight to the Calculator (no drawing ingestion).

---

## 9. Developer Onboarding Notes

1. **Run from the repo root** — all imports use `backend.app.*`; cwd must be the project root, not `backend/`.
2. **Stateless singletons** — services are import-time instances; no DB; persistence is files in `uploads/` and `outputs/`.
3. **LLM does no math** — NVIDIA NIM returns schema strings; Pydantic coerces them; only `calculator.py` performs arithmetic (IS 1786 `d²/162.28`, SP 34).
4. **Ground truth is the safety net** — `dxf_parser.ground_truth_schedule` and the NIM fallback both carry the same 9 verified pile rows (`P50 … 10P70`).
5. **Step-marker logging** — every module logs `[STEP n]`, so a full pipeline run is traceable end-to-end via the `buildiq.*` loggers.
6. **Frontend binary assets** — the 2D CAD viewer consumes `cad_entities`; PDF crops are served through the static `/crops` mount.
7. **Custom recalc** — `POST /api/takeoff/calculate` recomputes quantities from user `pile_specs` without re-ingesting drawings — pure native math path.

---

*Generated from the actual `backend/` source (FastAPI, Pydantic, ezdxf, PyMuPDF, NVIDIA NIM client). All diagrams verified against module behavior.*