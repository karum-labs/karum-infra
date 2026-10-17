# Karum: The Autonomous Retail Expansion & Stockist Intelligence Agent for Brands

**Karum** is an agentic B2B retail distribution and site-selection platform built for the **Qloo Agentic Hackathon 2026**. Operated by emerging and scaling consumer brands (Food & Beverage, Craft Spirits, Specialty CPG, Apparel, and Lifestyle), Karum closes the gap between a brand and physical retail. 

Given a brand's identity (or composite cultural vibe) and a target city, Karum queries Qloo's Taste Graph to decode the cultural and demographic DNA of every block and venue. It tells a brand **which independent stores, bars, and cafes ("doors") to pitch to stock their product**, **where to open their own flagship store or weekend pop-up**, **which non-competing boutiques to partner with for brand activations**, and **which accounts to skip**. It then uses Vertex AI with live Google Search Grounding to audit each venue's live menu or shelf inventory for competitors, calculates an optimized field-sales route via Google Maps Routes, and drafts hyper-personalized B2B sales scripts and displacement battlecards for every shopkeeper.

---

## TL;DR — Executive Summary

- **What We Are Building:** **Karum**, a multi-mode physical expansion agent for brands. It combines Qloo's cross-domain entity correlation (`Brand` $\rightarrow$ `Places`), locality heatmaps (`urn:heatmap`), taste tags (`urn:tag`), and explainability signals (`feature.explainability=true`) with live web menu verification (Vertex AI Google Search Grounding) and spatial route optimization (Google Maps Platform).
- **Who Operates the Platform:** Emerging and growth-stage brands, field sales reps, wholesale account executives, and retail expansion directors.
- **Why We Pivoted from Landlord-Only to Brand-Operated:** Qloo's strongest, battle-tested primitive is mapping a **Brand or Composite Entity Signal $\rightarrow$ Ranked Physical Places & Locality Heatmaps** within a city. Building for the brand unlocks both **Wholesale Door Scouting** (selling into existing shops/bars) and **Flagship/Pop-Up Site Scouting** (opening the brand's own storefront) with low technical risk and immediate B2B revenue impact.
- **Hackathon Moat & Positioning:** 
  - **Qloo Indispensability:** $10/10$ (Without Qloo, an LLM simply lists popular Yelp bars or generic commercial streets without knowing whether the venue's patrons culturally align with the brand).
  - **2026 Field Differentiation:** Avoids crowded 2026 hackathon lanes like live-music venue booking (*Booker*, *Advance*, *Undercard*), synthetic focus groups (*Quorum*), creator sponsorships (*Cold-Open*, *Deal Desk*), and consumer relocation (*TasteBridge*, *Home2Here*).
  - **Zero Out-of-Pocket Cost:** Runs entirely on the hackathon's Qloo API key ($10,000$ requests/month quota) and the **$300 Google Cloud Trial Credit** (covering serverless Vertex AI Gemini 2.5 Flash, Google Search Grounding, Google Places API, Google Routes API, and Cloud Run hosting).

---

## 1. Hackathon Strategy, Rules & Judge Fit

### 1.1 Verified Hackathon Rules & Constraints
| Dimension | Verified Constraint | Karum Compliance Strategy |
| :--- | :--- | :--- |
| **Submission Deadline** | Oct 30, 2026 @ 11:45pm EDT | Freeze features by Oct 27; deploy public no-login Flutter Web build by Oct 28. |
| **Judging Window** | Nov 2, 2026 $\rightarrow$ Nov 16, 2026 | Cloud Run services and pre-warmed cache stay live through Nov 23. |
| **Prizes** | $\$25,000$ total ($1\text{st}: \$15,000$, $2\text{nd}: \$6,000$, $3\text{rd}: \$4,000$) | Positioned as a venture-ready B2B SaaS product, not a toy consumer chatbot. |
| **Live Demo Mandate** | Judges test the hosted app directly; demo videos are optional | Instant 1-click pre-warmed brand scenarios on the landing screen; zero login wall. |
| **Qloo API Environment** | `https://hackathon.api.qloo.com` via `X-Api-Key` header | Strict server-side key isolation inside `service-taste` with persistent response caching. |
| **Open Source Requirement** | Public repositories with visible OSS license in GitHub About | MIT License across all 5 repositories (`infra`, `client`, `server`, `service-taste`, `service-ai`). |

### 1.2 Designing for the 2026 Judging Panel
Only one judge is a Qloo engineer; the rest are investors, entertainment executives, and operators:
- **Jason Calacanis (Angel Investor) & Todd Boehly (Eldridge Industries):** Evaluate **Potential Impact** and unit economics. Karum automates field sales and retail site selection—a workflow where brands spend tens of thousands of dollars on brokers and field reps.
- **Mike Diolosa (Qloo CTO):** Evaluates **Technological Implementation**. Karum chains 6+ distinct Qloo primitives (Entity Resolution, Cross-Domain Place Ranking, Locality Heatmaps, Taste Tag Extraction, Per-Result Explainability, and Audience Comparison) inside a deterministic gRPC microservice architecture.
- **Michael Abrams (EVP Strategy, Live Nation) & Cedric the Entertainer:** Appreciate hospitality, beverage programs, cultural curation, and physical venue dynamics.
- **Nicole Seligman (OpenAI Board):** Looks for grounded, non-hallucinated agentic workflows where every LLM claim is backed by traceable cultural data and live web citations.

### 1.3 Lessons Applied from 2025 Winners
1. **Put Qloo inside a high-stakes B2B revenue decision** (*GeoTaste*, *Alloy*, *Resonance AI*): Landing 30 wholesale retail accounts or signing a pop-up lease is worth $\$50,000+$ in annual recurring revenue for an emerging brand.
2. **Make Negative Space a first-class feature** (*Zesty*): Tell the brand **"Doors to Skip / Do Not Pitch"**—stores that look trendy on paper but whose patrons have low cultural affinity or whose shelves are already locked into competing craft contracts.
3. **Include an "LLM-Only vs. Karum" Counterfactual Toggle** (*Advance 2026 pattern*): Prove on-screen that a standard LLM gives generic tourist traps while Karum surfaces high-converting neighborhood stockists.

---

## 2. Product Vision & The 5 Core Brand Use Cases

In Karum, **the Brand operates the platform**. When a brand logs into Karum, it defines its identity either by resolving its existing Qloo Brand Entity or—if it is a brand-new startup not yet in Qloo's graph—by constructing a **Composite Cultural Seed** (combining $2\text{–}4$ reference brands, genres, or lifestyle tags that represent its target customer, e.g., *"Oatly" + "Aesop" + "Indie Rock" + "Natural Wine"*).

Karum then executes five high-value commercial workflows:

### Use Case 1: Wholesale Stockist & "Door Scouting" (Primary Mode)
- **The Problem:** An emerging craft beverage, specialty food, or CPG brand wants to get stocked in independent bars, cafes, restaurants, or specialty boutiques in a new city. Field sales reps waste $70\%$ of their time walking into doors whose clientele doesn't match the product.
- **How Karum Works:**
  1. Queries Qloo `/v2/insights` (`Brand/Seed` $\rightarrow$ `urn:entity:place`) within the target city's coordinates to rank venues whose patrons share the highest behavioral affinity with the brand.
  2. Resolves operational data (address, opening hours, website) via **Google Places API**.
  3. Uses **Vertex AI with Google Search Grounding** to inspect the venue's live online menu, delivery listings, and social footprint to check if they already carry the brand or a direct competitor.
  4. Generates a turn-by-turn field sales route via **Google Routes API** and writes a tailored pitch for the shopkeeper/beverage director citing Qloo's shared cultural tags.

### Use Case 2: Flagship Store & Pop-Up Site Scouting
- **The Problem:** The brand wants to set up its own physical flagship store, seasonal showroom, or weekend tasting pop-up, and needs to know which micro-neighborhood or street corridor has the highest concentration of its target audience.
- **How Karum Works:**
  1. Queries Qloo's Locality Heatmap (`filter.type=urn:heatmap`) using the brand's entity/tag signals across the target city.
  2. Identifies the top 3 high-affinity spatial clusters (hex grids / blocks).
  3. Pulls the "Anchor Neighbors" in those clusters via Qloo to explain the block's persona (e.g., *"This 3-block corridor in Silver Lake over-indexes by $94\%$ on your brand profile due to adjacent patrons of Venue A, B, and C"*).
  4. Outputs a **Site Selection Brief** comparing foot-traffic taste fit and demographic skew across candidate neighborhoods.

### Use Case 3: Competitor "Conquesting" (Shelf Displacement)
- **The Problem:** Retail shelf space and backbars are finite. Often, the best prospective store is currently stocking a legacy, mass-market competitor whose brand ethos no longer matches the neighborhood's evolving taste.
- **How Karum Works:**
  1. Identifies high-affinity venues via Qloo where **Vertex AI Search Grounding** detects an incumbent competitor on the menu (e.g., a craft espresso bar still using a generic commercial syrup or legacy energy drink).
  2. Runs Qloo's `/v2/analysis/compare` between the venue's taste profile, the legacy incumbent brand, and the user's emerging brand.
  3. Generates a **"Displacement Battlecard"** showing the shopkeeper mathematically why their patrons align better with the emerging brand than the incumbent product they currently stock.

### Use Case 4: Cross-Category Collabs & "Shop-in-Shop" Activations
- **The Problem:** Emerging brands grow fastest through cultural co-marketing with non-competing retail spaces (e.g., a botanical non-alcoholic aperitif hosting a tasting inside an independent menswear store, vinyl shop, or ceramic studio).
- **How Karum Works:**
  1. Queries Qloo `/v2/insights` using the brand signal but restricts `filter.tags` to non-food retail categories (apparel, bookstores, art galleries, fitness studios, design shops).
  2. Ranks non-competing lifestyle venues by audience overlap and drafts a **Co-Branded Activation Proposal** explaining why both businesses share the exact same customer base.

### Use Case 5: Hyper-Local SKU Assortment & Field Marketing
- **The Problem:** Brands typically sell a portfolio of multiple SKUs (e.g., a beverage brand with a Spicy Ginger variant, a Yuzu Citrus variant, and a Classic Botanical variant). Different neighborhoods within the same city have distinct palate preferences.
- **How Karum Works:**
  1. Extracts the specific Qloo taste tags (`filter.type=urn:tag`) for each target store's micro-catchment.
  2. Maps those local tags to the brand's SKU catalog so the sales rep pitches the exact SKU most likely to sell at that specific door.

---

## 3. Counterfactual Proof: Why Qloo is Indispensable

Query: *"We are 'sola', an emerging artisanal yuzu-mezcal aperitif (vibe: Madre Mezcal + Aesop + Vinyl Culture). Which 10 doors in Austin, TX should our rep visit today, and what should they pitch?"*

| Approach | What It Outputs | Why It Fails / Succeeds |
| :--- | :--- | :--- |
| **A. Plain LLM (Gemini / GPT alone)** | Lists the 10 most famous bars in Austin from generic travel blogs (e.g., Midnight Cowboy, The Roosevelt Room). | **Fails:** Zero awareness of whether those specific venues' audiences align with yuzu/botanical/vinyl subcultures; recommends tourist traps and steakhouses alongside craft lounges. |
| **B. LLM + Web Search Only** | Scrapes "best mezcal bars in Austin" articles and lists bars that already have 50 mezcals on the shelf. | **Fails:** Recommends oversaturated accounts where another mezcal brand has zero margin leverage, while missing high-affinity neighborhood cafes, listening bars, and restaurants that *should* carry an agave aperitif. |
| **C. Vector Text Embeddings** | Matches venues whose text reviews contain words like "yuzu" or "mezcal". | **Fails:** Text similarity cannot infer cross-domain behavioral taste (e.g., knowing that patrons of a specific East Austin bistro also love Aesop and independent cinema). |
| **D. Karum (Qloo + Search Grounding + Maps)** | 1. **Qloo** ranks Austin venues by cross-domain behavioral affinity to the brand's cultural seed + extracts shared lifestyle tags.<br>2. **Search Grounding** audits each bar's live menu to flag whether they are open for an aperitif slot or locked into a competitor.<br>3. **Zesty-style Negative Space** flags 3 famous bars to **Skip** due to low taste fit or heavy category saturation.<br>4. **Maps Routes** sequences the day's field route. | **Succeeds:** Delivers verifiable cultural correlation, live shelf intelligence, route logistics, and an evidence-backed sales script. |

---

## 4. Multi-Repository Architecture & Technology Stack

To keep the architecture modular, scalable, and clean for multi-person parallel development, the codebase is split into **five decoupled repositories** without hardcoded product-name prefixes.

### 4.1 Repository Topology

```
├── infra/                  # Central source of truth: Protobufs, Code-Gen, Docker, Cloud Run
│   ├── proto/
│   │   ├── taste/v1/       # taste.proto (Go <-> service-taste gRPC contract)
│   │   └── agent/v1/       # agent.proto (Go <-> service-ai gRPC contract)
│   ├── docker/             # docker-compose.yml for full local stack orchestration
│   ├── deploy/             # Google Cloud Run YAML manifests & deployment scripts
│   └── Makefile            # protoc compilation targeting server, service-taste, service-ai
│
├── client/                 # Frontend: Flutter (Web primary for judges + Mobile/Desktop)
├── server/                 # Core API Gateway & Orchestrator: Go + Gin + gRPC Client + Maps
├── service-taste/          # Microservice 1: Python (FastAPI + gRPC) -> Qloo API & Caching
└── service-ai/             # Microservice 2: Python (FastAPI + gRPC) -> Vertex AI & Search Grounding
```

---

### 4.2 Detailed Component Breakdown

#### 1. `infra` (Contracts & DevOps Repository)
- **Role:** Houses the `.proto` interface definitions, local multi-container environment, and Cloud Run deployment configurations.
- **Tech:** Protocol Buffers (`proto3`), `protoc`, Docker Compose, GitHub Actions.

#### 2. `client` (Frontend Repository)
- **Framework:** **Flutter** (Dart 3.x), compiled to **Flutter Web** for frictionless judge access (and native iOS/Android/macOS ready).
- **Key Packages:**
  - `flutter_bloc` or `flutter_riverpod`: Reactive state management for streaming agent traces and map states.
  - `google_maps_flutter` / `flutter_map`: Renders interactive store pins, Qloo affinity heatmaps, and turn-by-turn field sales polylines.
  - `dio`: REST HTTP client with streaming/SSE support for real-time agent progress updates from the Go gateway.

#### 3. `server` (Core Backend & API Gateway Repository)
- **Framework:** **Go 1.22+** with **Gin (`github.com/gin-gonic/gin`)**.
- **Role:** 
  - Exposes REST/SSE endpoints to the Flutter client.
  - Orchestrates concurrent gRPC calls to `service-taste` and `service-ai`.
  - Calls **Google Maps Places API (New)** to enrich Qloo venues with verified street addresses, operating status, phone numbers, and website URLs.
  - Calls **Google Maps Routes API** (`optimizeWaypointOrder: true`) to compute the optimal physical visit order for the sales rep.
  - Generates downloadable PDF Sales Run-Sheets and Site Selection Memos.
- **Key Libraries:** `google.golang.org/grpc`, `google.golang.org/protobuf`, `googlemaps.github.io/maps`.

#### 4. `service-taste` (Qloo Cultural Intelligence Microservice)
- **Framework:** **Python 3.11+** running a **gRPC Server** (`grpcio`) alongside **FastAPI** (for `/health`, Swagger inspection, and direct debugging).
- **Role:** Dedicated abstraction layer for all Qloo Taste Graph operations.
  - Resolves brand names, neighbor venues, and lifestyle tags into canonical Qloo URNs.
  - Executes cross-domain `Brand` $\rightarrow$ `Places` queries, `urn:heatmap` spatial grids, `urn:demographics` checks, and `/v2/analysis/compare` overlap calculations.
  - Normalizes scores and caches responses in SQLite/Redis by parameter hash so repeated demo runs never exhaust the $10,000\text{ req/mo}$ hackathon quota.
- **Key Libraries:** `httpx` (async REST calls to Qloo), `pydantic`, `grpcio`, `grpcio-tools`.

#### 5. `service-ai` (Vertex AI & Live Web Grounding Microservice)
- **Framework:** **Python 3.11+** running **gRPC** + **FastAPI**.
- **Role:** The reasoning, live verification, and copywriting engine.
  - Uses the official **`google-genai` SDK** authenticated via **Vertex AI (`vertexai=True`)** on `gemini-2.5-flash`.
  - Attaches native **Google Search Grounding** (`types.Tool(google_search=types.GoogleSearch())`) to audit live venue menus, cocktail lists, and retail shelves for incumbent competitors.
  - Synthesizes Qloo's explainability tags + live menu findings into tailored B2B outreach emails, door-knocking scripts, SKU recommendations, and LLM-only counterfactual baselines.
- **Key Libraries:** `google-genai`, `pydantic`, `grpcio`.

---

### 4.3 End-to-End System Flow

```
[ Flutter Client (`client`) ]
       │
       │  1. POST /api/v1/scout (Brand Seed, Target City, Mode: DoorScout | Flagship | Collab)
       ▼
[ Go + Gin Gateway (`server`) ]
       │
       ├──► 2. gRPC: GetCulturalTargets() ──► [ `service-taste` (Python) ]
       │                                            ├── Resolves Brand / Seed Entities (`/search`, `/v2/tags`)
       │                                            ├── Queries `/v2/insights` (Places + Explainability + Tags)
       │                                            ├── Queries `/v2/insights` (`urn:heatmap` & `urn:demographics`)
       │                                            └── Returns Ranked Doors + Skip List + Cultural DNA
       │
       ├──► 3. REST: Google Maps Places API (New)
       │       └── Verifies store is OPEN, fetches exact address, website URL, & coordinates
       │
       ├──► 4. gRPC: AuditAndDraftPitches() ─► [ `service-ai` (Python) ]
       │                                            ├── Calls Gemini 2.5 Flash + Google Search Grounding
       │                                            ├── Inspects venue's live menu / stockists for competitors
       │                                            ├── Recommends specific Brand SKU per venue
       │                                            └── Drafts custom B2B pitch + Displacement Battlecard
       │
       ├──► 5. REST: Google Maps Routes API
       │       └── Computes optimal multi-stop walking/driving sequence across qualified doors
       │
       ▼  6. Streams trace events & returns complete Campaign Payload + PDF Run-Sheet
[ Flutter Client (`client`) ]
```

---

### 4.4 Shared gRPC Contracts (`infra/proto`)

#### `infra/proto/taste/v1/taste.proto`
```protobuf
syntax = "proto3";

package taste.v1;

option go_package = "github.com/org/infra/gen/go/taste/v1;tastev1";

service TasteService {
  rpc ResolveBrandSeed (ResolveSeedRequest) returns (ResolveSeedResponse);
  rpc ScoutDoors (ScoutDoorsRequest) returns (ScoutDoorsResponse);
  rpc GetLocalityHeatmap (HeatmapRequest) returns (HeatmapResponse);
}

message ResolveSeedRequest {
  string brand_query = 1;
  repeated string fallback_vibe_queries = 2;
}

message EntityRef {
  string entity_id = 1;
  string name = 2;
  string subtype = 3;
}

message ResolveSeedResponse {
  repeated EntityRef resolved_entities = 1;
  repeated string resolved_tag_ids = 2;
}

message ScoutDoorsRequest {
  repeated string seed_entity_ids = 1;
  repeated string seed_tag_ids = 2;
  double latitude = 3;
  double longitude = 4;
  int32 radius_meters = 5;
  string target_category_tag = 6; // e.g., urn:tag:genre:place:bar or retail boutique
}

message ContributingSignal {
  string entity_id = 1;
  string name = 2;
  double weight = 3;
}

message DoorCandidate {
  string qloo_entity_id = 1;
  string name = 2;
  double latitude = 3;
  double longitude = 4;
  double affinity_score = 5;
  repeated string shared_taste_tags = 6;
  repeated ContributingSignal explainability_signals = 7;
  bool is_negative_space_skip = 8;
  string skip_reason = 9;
}

message ScoutDoorsResponse {
  repeated DoorCandidate recommended_doors = 1;
  repeated DoorCandidate doors_to_skip = 2;
  map<string, double> demographic_age_skew = 3;
}

message HeatmapRequest {
  repeated string seed_entity_ids = 1;
  double latitude = 2;
  double longitude = 3;
  int32 radius_meters = 4;
}

message HeatmapPoint {
  double latitude = 1;
  double longitude = 2;
  double intensity = 3;
}

message HeatmapResponse {
  repeated HeatmapPoint points = 1;
}
```

#### `infra/proto/agent/v1/agent.proto`
```protobuf
syntax = "proto3";

package agent.v1;

option go_package = "github.com/org/infra/gen/go/agent/v1;agentv1";

service AgentService {
  rpc VerifyDoorAndGeneratePitch (DoorPitchRequest) returns (DoorPitchResponse);
  rpc GenerateLlmBaseline (BaselineRequest) returns (BaselineResponse);
}

message DoorPitchRequest {
  string brand_name = 1;
  string brand_description = 2;
  repeated string brand_skus = 3;
  string venue_name = 4;
  string venue_address = 5;
  string venue_website = 6;
  double affinity_score = 7;
  repeated string shared_taste_tags = 8;
  string campaign_mode = 9; // "WHOLESALE", "CONQUEST", "COLLAB", "FLAGSHIP"
}

message DoorPitchResponse {
  bool menu_verified = 1;
  bool stocks_incumbent_competitor = 2;
  string detected_competitors = 3;
  string menu_summary = 4;
  string recommended_sku = 5;
  string tailored_pitch_script = 6;
  string displacement_battlecard = 7;
  repeated string grounding_source_urls = 8;
}

message BaselineRequest {
  string brand_name = 1;
  string brand_description = 2;
  string city = 3;
}

message BaselineResponse {
  repeated string generic_llm_venues = 1;
  string generic_reasoning = 2;
}
```

---

### 4.5 Cloud & Billing Budget ($300 GCP Trial Credit)

Every paid cloud dependency runs inside a single Google Cloud Project linked to the **$300 Free Trial Billing Account**:

| Service | GCP / External Product | Authentication Method | Estimated Hackathon Spend |
| :--- | :--- | :--- | :--- |
| **Cultural Graph** | Qloo Hackathon API | `X-Api-Key` header (`10,000` req/mo quota) | **$0.00** (Free Hackathon Key) |
| **Agent Brain** | Vertex AI (`gemini-2.5-flash`) | Application Default Credentials (ADC) / Service Account | **$\approx \$1.50$** (Serverless token billing) |
| **Live Web Scraping** | Vertex AI Search Grounding | Native `google_search` tool in `google-genai` | **$\approx \$2.00$** (Covered by Free Tier / Trial Credit) |
| **Venue Metadata** | Google Maps Places API (New) | GCP Maps API Key | **$\approx \$3.00$** (Covered by Maps Credit / Trial Credit) |
| **Route Optimization** | Google Maps Routes API | GCP Maps API Key | **$\approx \$1.50$** (Covered by Trial Credit) |
| **Container Hosting** | Google Cloud Run | GCP IAM | **$\approx \$0.00$** (Within 2M free monthly requests) |
| **Total Out-of-Pocket** | — | — | **$\$0.00$** (Uses $< \$10$ of the $\$300$ GCP Trial) |

---

## 5. Qloo API Architecture & Scoring Rubric

### 5.1 Verified Qloo API Call Sequence (`service-taste`)
All requests target `https://hackathon.api.qloo.com` with `X-Api-Key`:

1. **Brand & Composite Vibe Resolution:**
   - `GET /search?query=<brand_or_vibe_entity>&types=urn:entity:brand,urn:entity:place,urn:entity:artist&take=5`
   - Resolves the user's brand (or reference brands like *Aesop*, *Oatly*, *Madre Mezcal*) into Qloo Entity UUIDs.
2. **Lifestyle & Category Tag Resolution:**
   - `GET /v2/tags?filter.query=<keyword>&feature.typo_tolerance=true`
   - Maps product descriptors (e.g., `"craft cocktails"`, `"organic"`, `"specialty coffee"`, `"indie"`) to canonical Qloo Tag URNs.
3. **Cross-Domain Door Ranking (The Core Engine):**
   - `GET /v2/insights?filter.type=urn:entity:place&signal.interests.entities=<seed_ids>&signal.interests.tags=<tag_ids>&filter.location=POINT(<lon> <lat>)&filter.location.radius=<meters>&filter.tags=<venue_category_tag>&feature.explainability=true&take=25`
   - *Critical Syntax Rule:* `/v2/insights` requires WKT `POINT(<lon> <lat>)` (longitude first) and an explicit `filter.location.radius` in meters.
   - Returns ranked target doors along with per-venue explainability weights (`feature.explainability=true`).
4. **Local Taste Fingerprint per Door / Block:**
   - `GET /v2/insights?filter.type=urn:tag&signal.interests.entities=<venue_id>&take=10`
   - Extracts the readable cultural descriptors that define that specific venue's crowd (used for SKU matching and pitch hooks).
5. **Locality Heatmap (For Flagship & Pop-Up Site Scouting):**
   - `GET /v2/insights?filter.type=urn:heatmap&signal.interests.entities=<seed_ids>&filter.location=POINT(<lon> <lat>)&filter.location.radius=10000`
   - Returns spatial coordinates and affinity intensity weights to render the cultural density overlay on the Flutter map.
6. **Audience Demographic Verification:**
   - `GET /v2/insights?filter.type=urn:demographics&signal.interests.entities=<venue_ids>`
   - Returns age/gender distribution buckets to confirm the venue's crowd matches the brand's target buyer demographic.
7. **Competitor vs. Brand Overlap (`/v2/analysis/compare`):**
   - `GET /v2/analysis/compare?a.signal.interests.entities=<venue_id>,<emerging_brand_id>&b.signal.interests.entities=<venue_id>,<incumbent_competitor_id>`
   - Quantifies why the emerging brand is a stronger cultural fit for the venue than the legacy competitor detected on their menu.

---

### 5.2 The 3-Part Karum Door Score
Rather than showing an opaque number, Karum computes a transparent composite score $S_{\text{door}} \in [0, 100]$ broken into three sub-bars on every card:

$$S_{\text{door}} = 0.50 \cdot A_{\text{taste}} + 0.30 \cdot O_{\text{shelf}} + 0.20 \cdot D_{\text{demo}} - P_{\text{saturation}}$$

1. **Cultural Affinity Fit ($A_{\text{taste}}$):** Qloo affinity score between the Brand Seed and the Venue entity, shown as a percentile inside the returned shortlist (raw affinity bands shift with seed type — brand seeds sat near 0.85, place seeds near 0.97 on 17 Oct — so raw values are not comparable across campaigns), with `feature.explainability` signal weights attached.
2. **Shelf / Menu Opportunity ($O_{\text{shelf}}$):** Derived from Vertex AI Search Grounding. High score if the venue carries complementary categories (e.g., craft cocktails, small-batch goods) without an exclusive lock from a direct craft twin; triggers Conquest Mode if they only stock a legacy mass-market incumbent.
3. **Demographic & Locality Alignment ($D_{\text{demo}}$):** Alignment between the venue's `urn:demographics` age buckets and the brand's target cohort, plus neighborhood heatmap intensity.
4. **Saturation / Mismatch Penalty ($P_{\text{saturation}}$):** Pushes a venue into the **"Doors to Skip"** column when its Qloo affinity falls below the returned shortlist's floor (computed per campaign — an absolute cutoff never fires, 17 Oct evidence) or when live menu verification shows the venue already stocks $4+$ direct niche competitors.

---

## 6. User Interface & 3-Minute Judge Demo

### 6.1 Flutter Web UI Layout
1. **Top Mode Switcher & Preset Bar:**
   - Instant 1-click sample buttons for judges:
     - *Sample 1 (Austin, TX):* **"Sola Yuzu Mezcal"** (Wholesale Bar & Restaurant Door Scout)
     - *Sample 2 (Brooklyn, NY):* **"Kinto-Style Minimalist Ceramics & Matcha"** (Flagship Pop-Up Site Scout + Boutique Collab Scout)
     - *Sample 3 (Mumbai, Colaba):* **"Subko-Style Specialty Craft Cacao & Coffee"** (Stockist & Cafe Partner Scout)
   - Mode pills: `Wholesale Doors` | `Flagship & Pop-Up Scout` | `Brand Collabs`
2. **Left Panel — Brand Seed Builder & Live Agent Trace:**
   - Brand input + Qloo autocomplete chip selector for Composite Vibe Seeds and SKU list.
   - Streaming real-time execution log showing each microservice hop:
     - `[service-taste] Resolved 3 cultural seed entities via Qloo /search`
     - `[service-taste] Ranked 22 Austin venues via Qloo /v2/insights (POINT -97.7431 30.2672)`
     - `[server] Verified opening hours & URLs via Google Places API`
     - `[service-ai] Audited live menus via Vertex AI Google Search Grounding (8 citations)`
     - `[server] Optimized 6-stop field sales route via Google Routes API (14.2 mins drive)`
3. **Center Canvas — Interactive Map (Pins + Heatmap + Route Polyline):**
   - Toggles between **Field Sales Route View** (numbered stop pins connected by driving/walking polylines), **Cultural Heatmap View** (`urn:heatmap` density layer for Flagship scouting), and **Skip Pins** (red markers for venues to avoid).
4. **Right Drawer — Ranked Door Cards, "Doors to Skip", & Evidence Drawer:**
   - **Recommended Doors (Top 6):** Shows the 3 sub-score bars, recommended SKU badge, live menu finding with clickable Google Search citation links, and a 1-click **"View Pitch & Battlecard"** modal.
   - **"How We Know" Evidence Drawer:** Displays the exact Qloo API request parameters, `feature.explainability` entity weights, and shared `urn:tag` badges.
   - **"Doors to Skip" Tab (Negative Space):** Highlights popular venues that a naive sales rep would waste time visiting, explaining why Qloo + Grounding rejected them.
   - **"LLM-Only Baseline" Toggle:** Side-by-side comparison proving how a generic ungrounded LLM fails on the exact same prompt.

---

### 6.2 The 3-Minute Judge Demo Script

- **0:00 – 0:25 (The Hook & Problem):**
  - *"Emerging brands die on the shelf—not because their product is bad, but because their sales reps knock on the wrong doors and open pop-ups on the wrong blocks. Today, brands guess using Yelp lists. Karum uses Qloo's Taste Graph and live Google Search Grounding to tell a brand exactly which shopkeepers' customers already love their vibe, what is on their menu right now, and how to pitch them."*
- **0:25 – 0:55 (Brand Seed & Live Agent Trace):**
  - Click **Try Sample: Sola Yuzu Mezcal in Austin, TX**.
  - Show the composite cultural seed (*Aesop + Ilegal Mezcal + Khruangbin* — the 17 Oct probe's Qloo-verified seed; Madre Mezcal is absent from Qloo coverage) and 3 SKUs.
  - Watch the live trace stream across `service-taste` (Qloo), `server` (Google Places/Routes), and `service-ai` (Vertex AI Search Grounding).
- **0:55 – 1:40 (The Magic Moment — Door Cards + Menu Grounding + Negative Space):**
  - Click **Door #1** (top of the locked preset's bar list — Mezcalería Tobalá in the 17 Oct probe, $86\%$ Qloo affinity). Open the **Evidence Drawer**: show the Qloo cultural affinity, the shared tags (`craft_cocktails`, `indie_rock`, `sustainable_design`), and the live menu verification with real web URLs confirming their Oaxacan cocktail focus and recommends pitching *SKU #2 (Yuzu Blanco)*.
  - Click the **"Doors to Skip"** tab: show the famous Sixth Street venues a plain LLM recommended (The Blind Pig Pub, Maggie Mae's in the 17 Oct probe — both score below every returned door), flagged in red by Karum because Qloo shows low relative affinity and Search Grounding shows a locked corporate distributor menu.
- **1:40 – 2:15 (Counterfactual & Sales Action):**
  - Toggle **"Compare with Plain LLM"** to show the generic tourist list side-by-side against Karum's culturally grounded route.
  - Click **"Generate Pitch & Run-Sheet"**: preview the tailored email/script citing Qloo's shared audience insights and the optimized 6-stop Google Maps sales route.
- **2:15 – 2:50 (Mode Switch: Flagship & Collab Scout):**
  - Toggle to **Flagship & Pop-Up Scout**. The Qloo `urn:heatmap` lights up East 6th / Cesar Chavez as the #1 micro-corridor for a weekend pop-up, alongside 3 non-competing apparel/vinyl shops (`Brand Collabs` mode) to co-host the tasting.
- **2:50 – 3:00 (Close):**
  - *"From first stockist to first flagship store, Karum turns Qloo's cultural graph into revenue."*

**Seed & door check (17 Oct 2026):** the names above track the verified Qloo probe. Madre Mezcal does not resolve in Qloo (brand-typed and any-type searches miss; only same-name places elsewhere) — Ilegal Mezcal, Aesop, and Khruangbin all resolve. The bar-filtered door list tops out at Mezcalería Tobalá (0.859), Midnight Cowboy, Clark's Oyster Bar; without the category tag the ranking is taste-anchor-shaped (Franklin Barbecue, Uncommon Objects, Cathedral of Junk), and Sixth Street bars (Blind Pig 0.812, Maggie Mae's 0.816) score below every returned door (pool floor 0.828) — the skip-list story. Re-render the script's names and percentages from the locked preset before the demo.

---

## 7. Implementation Roadmap & Team Split (Oct 17 $\rightarrow$ Oct 30, 2026)

| Phase | Dates | Owner / Repo | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Phase 1: Contracts & Infra** | Oct 17 – Oct 18 | Both (`infra`) | Finalize `taste.proto` and `agent.proto`; write `Makefile` for Go & Python stub generation; set up `docker-compose.yml`. |
| **Phase 2: Qloo Microservice** | Oct 18 – Oct 21 | Backend / Qloo (`service-taste`) | Implement `/search`, `/v2/tags`, `/v2/insights` (Places, Tags, Heatmap, Demographics), `feature.explainability=true`, and SQLite parameter-hash caching. |
| **Phase 3: Vertex AI & Grounding** | Oct 18 – Oct 21 | AI / Agent (`service-ai`) | Implement `google-genai` client (`vertexai=True`, `gemini-2.5-flash`) with `GoogleSearch` tool; build structured Pydantic output parsers for menu verification, SKU selection, and pitch drafting. |
| **Phase 4: Go Gateway & Maps** | Oct 21 – Oct 23 | Backend (`server`) | Build Gin REST API, wire gRPC clients to `service-taste` and `service-ai`, integrate Google Places API (New) and Google Routes API waypoint optimization. |
| **Phase 5: Flutter Web UI** | Oct 21 – Oct 26 | Frontend (`client`) | Build brand seed selector, streaming trace log, interactive map (route polylines + heatmap), door cards with 3 sub-score bars, evidence drawer, "Doors to Skip", and LLM comparison toggle. |
| **Phase 6: Pre-Warm & Cloud Run** | Oct 26 – Oct 28 | Both (`infra` / all) | Pre-warm 3 demo cities (Austin, Brooklyn, Mumbai Colaba) into cache; deploy `server`, `service-taste`, `service-ai`, and `client` to Google Cloud Run; verify MIT licenses on all 5 GitHub repos. |
| **Phase 7: Polish & Submit** | Oct 28 – Oct 29 | Both | Final end-to-end latency check ($<8\text{s}$ live, $<1\text{s}$ cached presets), write Devpost submission mapped to the 4 judging criteria, submit 24 hours ahead of deadline. |