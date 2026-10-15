Yes, you can split them into two separate microservices and two distinct repositories: `service-taste` (handling Qloo) and `service-ai` (handling Vertex AI and search grounding). Dividing them this way is standard if two people are working on the backend simultaneously—one focusing on Qloo data wrangling, and the other on LLM prompt engineering and web grounding.

## The 5-Repository Layout

```text
├── infra/            # Shared Protobufs, Docker Compose, and Cloud Run manifests
├── client/           # Flutter web UI (judge target; same screens on desktop — no mobile app)
├── server/           # Go + Gin API Gateway (routes traffic, orchestrates jobs)
├── service-taste/    # Microservice 1: Qloo API integration, caching, & taste scoring
└── service-ai/       # Microservice 2: Vertex AI, Google Search Grounding, & pitch drafting
```

## What Each Microservice Does

### 1. service-taste (The Taste & Correlation Service)

- **Primary tech:** Python (FastAPI/gRPC) or Go.
- **Role:** Acts as the data abstraction layer for Qloo. It isolates Qloo's API quirks, authentication, and rate limits from the rest of your app.

**What it does:**

- **Entity resolution:** Resolves raw user strings (e.g., "Madre Mezcal") into Qloo Entity IDs.
- **Cross-domain querying:** Calls Qloo's Recommendation endpoint to fetch places matching the brand in the target city.
- **Data normalization and scoring:** Extracts affinity scores, strips extraneous metadata, and flattens cultural tags (e.g., `["craft_cocktails", "indie_rock"]`).
- **Caching layer:** Stores Qloo query responses in memory or Redis so repeated test runs do not burn through hackathon API credits.
- **gRPC RPC:** `GetRankedVenues(BrandRequest)` returns `VenueListResponse`.

### 2. service-ai (The Agent & Synthesis Service)

- **Primary tech:** Python (FastAPI/gRPC) using `google-genai` and Pydantic.
- **Role:** Performs live web verification and generates sales deliverables.

**What it does:**

- **Live menu verification:** Calls Gemini 2.5 Flash with Google Search Grounding to check whether target venues already stock the product or direct competitors.
- **Pitch and battlecard generation:** Ingests the venue's menu context alongside Qloo's cultural tags to draft customized sales scripts.
- **Buyer persona mapping:** Infers the beverage director / GM profile for that style of venue.
- **gRPC RPC:** `VerifyAndDraftPitch(PitchRequest)` returns `PitchResponse`.

## End-to-End Execution Flow

```text
[ Flutter Client ]
        │  POST /api/v1/campaigns/generate
        ▼
[ Go Gateway (server) ]
        │
        ├── 1. gRPC call ──► [ service-taste ] ──► Qloo API
        │                     (Returns ranked Austin bars + cultural tags)
        │
        ├── 2. HTTP call ──► Google Places API
        │                     (Enriches bars with addresses, hours, websites)
        │
        ├── 3. gRPC call ──► [ service-ai ] ──► Vertex AI + Search
        │                     (Checks live menus & writes sales pitches)
        │
        ├── 4. HTTP call ──► Google Routes API
        │                     (Computes optimal multi-stop driving path)
        │
        ▼  Returns complete campaign run-sheet
[ Flutter Client ]
```
