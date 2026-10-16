# Qloo Agentic Hackathon 2026: Build "Karum", a Tenant-Mix Agent That Tells Landlords What an Empty Storefront Should Become

Build **Karum**, an agent for retail landlords, leasing brokers and mall operators. You give it one vacant unit and its neighbours. It reads the taste of the surrounding block from Qloo, scores candidate tenant brands on two things, catchment fit and co-tenancy complement, and then writes the leasing memo and the outreach. The decision is a multi-year lease, not a dinner choice. It depends on Qloo's locality, place and cross-domain brand signals. And neither the 2025 winners nor the 2026 entries I could find attempted it.

## TL;DR
- **What to build:** Karum, a "what should this vacancy become?" leasing agent. It combines Qloo's place, brand, tag and location signals to rank tenants by catchment fit and by complement with existing neighbours, then produces an evidence-backed memo and outreach. Qloo Indispensability 9/10, Previous-Hackathon Similarity 5/10 (closest is GeoTaste), judge score 80/100.
- **Why this and not the usual ideas:** the 2025 winners (GeoTaste 1st; Alloy, Resonance AI and Zesty as honorable mentions) all put Qloo inside a business decision rather than a consumer recommendation. The 2026 field is already filling up. On GitHub I found entries for venue booking (Booker, Advance, Undercard), synthetic focus groups (Quorum), partnership discovery (Cold-Open, Deal Desk), café marketing (Hayy), relocation (TasteBridge, Home2Here) and MCP wrappers. Avoid all of these.
- **The main risk, and how to manage it:** spend the first 3–4 days with the hackathon key confirming place and brand coverage and location filtering for 3 demo cities. If Qloo cannot separate two neighbourhoods' taste profiles in a way a judge can see, kill Karum and fall back to the Tier-A runner-up (an independent-retailer buying agent).

---

## Key Findings

**1. The rules reward Qloo-dependence, a finished product and real-problem credibility.** The organisers state the anti-pattern plainly: "If your submission would work the same without Qloo, you're building the wrong thing." There are four judging criteria:
- Technological Implementation: "How thoroughly and skillfully does the project use Qloo?"
- Design: "a complete, coherent product experience, not just a technical proof of concept"
- Potential Impact: "a credible, specific case for solving a real problem for a real audience"
- Quality of the Idea: "a creative, non-obvious use of Qloo."

**2. Judges will try the app themselves.** Submissions need a live, externally hosted demo, a public repository, a text description and an open-source licence visible in the repo's About section. "Demo videos are not required. Instead of asking for a recording, we're requiring something judges can actually use." So the cold-start experience a judge has in the first minute matters more than a polished video.

**3. Most of the panel is not engineers.** The judges are:
- Jason Calacanis (angel investor)
- Mike Diolosa (Qloo CTO)
- Nicole Seligman (OpenAI board)
- Todd Boehly (Eldridge Industries; sports and real-assets investor)
- Cedric the Entertainer
- Michael Abrams (EVP Strategic Initiatives, Live Nation Entertainment)

Only one is a Qloo technologist. A winning project has to read as a business to investors and operators, and as a deep Qloo integration to the CTO.

**4. Prior winners show that "decision support for money-bearing decisions" wins.** The 2025 Qloo LLM Hackathon drew 2,893 participants and 344 gallery submissions:
- 1st place: GeoTaste ($10,000), a location-to-business-insight consultant agent.
- Honorable mentions ($5,000 each): Alloy, Resonance AI and Zesty.
  - Alloy is cultural due diligence for M&A.
  - Resonance AI writes culturally authentic political messaging.
  - Zesty is an "unrecommendation engine."

Three of the four are B2B decision tools. The fourth, Zesty, wins by inverting the default product assumption.

**5. Date discrepancy you should know about.** The brief says the previous hackathon ran July 1 to August 1, **2026**. Devpost lists the Qloo LLM Hackathon as **Jul 1 – Aug 1, 2025**, with winners announced August 25, and the Alloy repo says it was "built for the 2025 Qloo LLM Hackathon." I treat it as the 2025 event. This changes nothing in the analysis, but your write-up should say "2025."

**6. The 2026 field is already moving into B2B, and copying it is the biggest strategic risk.** Public GitHub repos tagged for the current event include:
- Live music: Booker (venue booking), Advance (tour advance for promoters) and Undercard (support-act audit).
- Quorum ("a focus group in a box").
- Cold-Open (partnership leads) and Deal Desk (creator sponsorship inbox).
- Hayy (café marketing) and CulturePilot (market decisions).
- Relocation: TasteBridge and Home2Here.
- TasteLoop, TasteRoute, Common Ground, TasteShip, and several Qloo MCP servers.

With a Live Nation executive on the panel, music booking will be the most crowded B2B lane.

---

## Details

### 1. Hackathon facts (verified vs. unverified)

| Item | Finding | Status |
|---|---|---|
| Submission window | Starts Sept 30, 2026, 9:00am EDT; deadline **Oct 30, 2026 @ 11:45pm EDT** | Verified (rules, 16 Oct 2026) |
| Prizes | $25,000 cash: 1st $15,000, 2nd $6,000, 3rd $4,000 | Verified |
| Eligibility | Above age of majority; all countries except standard exceptions | Verified |
| Build requirement | Integrate the Qloo API and either work as an agentic tool, use an agent framework, or wire Qloo into an existing agent | Verified |
| Submission | Live hosted demo, public repo (GitHub/GitLab/Bitbucket) with all source and run instructions, text description, open-source licence visible in repo About; no video required | Verified |
| Participants | 303 when first fetched; **1,545 on 16 Oct 2026** | Verified (Devpost) |
| API access | Hackathon key via the Qloo developer guide form; entrants report it works only against `https://hackathon.api.qloo.com` with an `X-Api-Key` header and takes "a few business days" | Entrant-reported |
| Judging period / announcement | **Judging Nov 2, 2026 12:00pm → Nov 16, 2026 11:45pm EDT; winners on or around Nov 23.** Judges must get free access to the project until judging ends — which matches the entrant keeping access "until 2026-11-17" | Verified (rules, 16 Oct 2026) |
| Team size | **No team-size cap appears anywhere in the 2026 rules** — only that a team appoints one Representative. (The 2025 rules capped teams at four.) | Verified (rules, 16 Oct 2026) |
| New vs. existing project | **The Qloo integration must be new** — a pre-existing project must have gained its Qloo integration after Sept 30, 2026, and the submission must explain how it was significantly updated during the window | Verified (rules, 16 Oct 2026) |

**Rules read in full — 16 Oct 2026** (`qloo.devpost.com/rules` retrieved; the earlier "could not retrieve it" blocker is closed). Remaining constraints from the text: submissions must be the entrant's original work with no prior financial or preferential support from Qloo; judges must have free access to the hosted demo through Nov 16, 2026; the repo must be public with an open-source licence file detectable in the About section; all submission materials must be in English; and no API-key usage terms appear beyond obtaining the key via the developer-guide form. Everything previously open in this table is now verified above.

### 2. How Qloo works, and what each capability unlocks

**What the Taste Graph is.** Qloo describes "250M+ entities across music, film, dining, fashion, and more" in the hackathon brief. Its corporate materials cite larger catalogue figures (575M+ entities); treat those as marketing-level numbers. Third-party coverage describes recommendations derived from "co-occurrences between lifestyle entities and anonymized behavioral signals," with no personal identity data. Qloo's own capabilities page describes three properties:
- One combined read of a set of interests: "each addition re-reads the whole, rather than stacking on the last answer."
- Crossing category boundaries: "Qloo carries an affinity from music to hotels, or from fashion to dining."
- Locality reads at block, neighbourhood, city and country scale. These include a heatmap, which Qloo says requires a place-genre signal such as `urn:tag:genre:place:restaurant`.

**How it differs from the alternatives:**
- **Semantic similarity and embeddings:** an embedding says Brian Eno is *like* other ambient artists because the text describing them is alike. Qloo says people who like Brian Eno and Jil Sander *also go to* specific Copenhagen restaurants. That is a behavioural co-occurrence across unrelated categories, which no text corpus encodes.
- **LLM reasoning:** an LLM produces plausible cultural stereotypes from its training text. Qloo returns ranked real-world entities with affinity scores tied to location.
- **Traditional recommenders:** these work inside one catalogue and need user history. Qloo starts from a single signal and returns results across domains.
- **Demographic targeting:** this infers taste from age and gender. Qloo infers it from taste itself, and can output demographics as a *result* of taste.

**API surface relevant to the hackathon** (from entrant repos and Qloo docs snippets; confirm against `docs.qloo.com` with your key):

| Capability | How it is called | Product capability it unlocks |
|---|---|---|
| Entity resolution | `GET /search` (its `types` enum differs from Insights `filter.type` — Karum uses `urn:entity:place` and `urn:entity:brand`; see [QLOO_APIS.md](QLOO_APIS.md) §1); `GET /entities?entity_ids=` | Turn messy user input ("that taco place on Red River") into a canonical, auditable ID. This is the basis for explainability |
| Tag resolution | `GET /v2/tags?filter.query=` | Turn vague concepts ("natural wine", "minimalist") into graph-native signals |
| Audiences | `GET /v2/audiences` — ⚠️ OpenAPI `deprecated: true`; take segments from Insights output instead (see [QLOO_APIS.md](QLOO_APIS.md) §4) | Start from a named segment instead of seed entities |
| Core inference | `GET /v2/insights` with `filter.type=urn:entity:…` and `signal.interests.entities` / `signal.interests.tags` | Cross-domain ranking: "people who like X → which brands, places, artists" |
| Tag-based filtering | `filter.tags=urn:tag:genre:…` | Restrict outputs to a category (e.g., only restaurants or only retail) while ranking by taste |
| Location | **Verified 16 Oct 2026:** `filter.location=<lat>,<lon>` + `filter.location.radius=<metres>` on Insights (`filter.radius=<miles>` on `/search`); `filter.location.query` takes locality names only | Ask "what fits *here*." This is the core of any site-selection product — exact recipes in [QLOO_APIS.md](QLOO_APIS.md) §3.1 and §3.5 |
| Demographic output | `filter.type=urn:demographics` | Infer the age/gender skew of an entity's audience, so the demographic is the result of taste rather than the input |
| Taste description | `filter.type=urn:tag` | "What defines this set or location": readable descriptors for explanations |
| Heatmap / locality | **Verified 16 Oct 2026:** `filter.type=urn:heatmap` inside `/v2/insights`, needs a location plus any entity/tag signal (`urn:tag:genre:place:restaurant` is a good choice, not a requirement) | Visual map of where a taste concentrates. This is the strongest demo asset — see [QLOO_APIS.md](QLOO_APIS.md) §3.7 |
| Comparison | **Verified 16 Oct 2026:** `GET /v2/analysis/compare` with `a.` / `b.signal.interests.entities` | Overlap and difference between two entity sets (e.g., current tenants vs. candidate) |
| Popularity / trends / exclusions / diversification | Qloo says results "can be weighted by factors such as regionalization and real-time popularity"; TechCrunch quotes adjustable "novel vs expected" weighting | Separate "safe" from "emerging" picks and exclude what is already present. **Verified 16 Oct 2026:** `filter.popularity.min/max`, `bias.trends`, `filter.exclude.tags` (+ `operator.filter.exclude.tags`), and `diversify.by=subtype` (tags only) are documented — see [QLOO_APIS.md](QLOO_APIS.md) |

Entrant repos report real coverage gaps. Undercard notes "Qloo coverage is limited in this hackathon environment: some artists cannot be found … or ranked." Plan for misses from the start, and label every miss as a miss rather than guessing.

### 3. What we can extract from the 2025 hackathon (competitive dataset)

**Method and limits:** I categorised every project visible on two gallery pages (about 48 of 344), plus the four winners, the developer write-ups surfaced in search, and 2026 repos. This is a sample, not a census. Before committing, finish the census during Phase 1 using the 15 gallery pages.

| Domain | 2025 projects observed | Density |
|---|---|---|
| Travel / itineraries | Appmuseme, Qlootra, TasteTrip AI, Wander Wise, Voya (astrology travel), Lokalo, TasteJourney (creator travel) | Crowded |
| Cultural DNA / self-discovery | CultureAI, Taste Mirror, Taste Compass, Culturo, DriftSense | Crowded |
| General concierge / lifestyle | Serendipity Engine, cultural-recommendation-app, CultureHub, Cultural Compass, Qlue, MyNakama, Sustainable Lifestyle Assistant | Crowded |
| Movies / books / media | QlooMoodFlix, Gastrotrip, Cultura (webcam emotion), PersonaReads | Crowded |
| Fashion / shopping | Taste Taylor, BrandLink, Qloo Fashion AI, cultureQ (coupons) | Crowded |
| Group / social | Duddle, CultureCircle (Harmony Score), Vybr (roommates), resonance engine | Semi-crowded |
| Marketing / brand strategy | Marketly, AdBuddy.ai, CULTURAL_MATCH_AI, TAVA venture architect, Product Discovery & Market Insights | Semi-crowded |
| Creative generation | Griot (manga), Cue Beats (film brief), Aethos (image prompts), StoryMap | Semi-crowded |
| Location / business intelligence | **GeoTaste (winner)** | Underexplored, and won |
| Deal / M&A diligence | **Alloy (winner)** | White space, and won |
| Political / civic messaging | **Resonance AI (winner)** | White space, and won |
| Anti-recommendation | **Zesty (winner)**, Qloo Fashion AI "Anti-Recommendations" | Underexplored, and won |
| Other / off-theme | Rescueeye-Global (disaster), AI ambulance detection, Tyohaar (festivals), KALA | Noise |

The pattern is clear. Most submissions are consumer recommenders wrapped around an LLM, and every winner sits in a sparse category.

### 4. The winners analysed

- **GeoTaste (1st).** "Transforms location into business insights… market analysis, competitive intelligence and interactive visualizations." It stood out for three reasons:
  - It answers an expensive question (where and what to open) that people normally pay consultants for.
  - Location is where Qloo's data is hardest for an LLM to fake: an LLM knows "Brooklyn is hip" but not which tastes concentrate within 500 m.
  - Maps make the result visible.

  A generic AI consultant writes market-research prose. GeoTaste grounds it in place-level affinity.
- **Resonance AI.** "Political intelligence that creates culturally authentic campaign messaging." Here the agent's job is *translation*. It turns a constituency's taste profile into the language and references of messaging. The payoff is concrete: an expensive, high-stakes audience (campaigns) gets an output it can use the same day. The core move is taste-as-audience-understanding where no first-party data exists.
- **Zesty.** "The Unrecommendation Engine that flips your feed." The product-thinking insight is that sometimes the valuable output is what to move *away* from: a filter-bubble escape, or a deliberate contrast. It shows judges that the team understood the graph well enough to invert it. The transferable lesson is that **negative space is a feature**. "What not to do" is often worth more than "what to do."
- **Alloy.** "De-risking multi-billion dollar deals by replacing gut-feel with a data-driven Cultural Compatibility Score," built as a ReAct agent on Gemini with Qloo and Tavily search. Cultural compatibility becomes a business decision because post-merger culture clash destroys value, and today it is judged by intuition. Alloy moved Qloo from consumers to boardrooms and quantified something considered unquantifiable. The pattern transfers to any "will these two things fit?" decision: co-tenancy, co-branding, sponsorship, hiring venues for brands.

I could not open the winners' individual Devpost pages, so their exact endpoint usage is not verified. The descriptions above come from gallery taglines and the Alloy repository.

### 5. What the winners had in common

| Winning Pattern | Evidence | Why It Matters | Can We Generalize It? |
|---|---|---|---|
| A business decision, not a recommendation | GeoTaste, Alloy, Resonance AI | Investor and operator judges score Impact on economic stakes | Yes: pick a decision worth at least $10k |
| Qloo replaces "gut feel" | Alloy states it outright | Gives a credible "why Qloo" story | Yes |
| A score or compatibility number | Alloy's Cultural Compatibility Score; CultureCircle's Harmony Score (non-winner) | Makes the output quotable and comparable | Yes, but the score must be explainable |
| Location as the hard-to-fake signal | GeoTaste | LLMs have weak, stereotyped local knowledge | Yes: strongest Qloo moat for demos |
| An inverted product assumption | Zesty | Signals real product thinking | Yes: add a "do not do" output |
| A specific, named buyer | M&A firms, campaigns, businesses | Makes Potential Impact credible | Yes |
| A visual payoff | GeoTaste's "interactive visualizations" | Judges remember maps and scores | Yes |
| Agentic orchestration over several sources | Alloy's ReAct agent with Qloo and web search | Matches 2026's "agentic" requirement | Yes, and 2026 requires it |

**What "winning Qloo thinking" looks like:** take a decision currently made on intuition about people. Make Qloo's cross-domain or locality signal the evidence. Output a defensible score plus a concrete action, show the evidence chain, and include what *not* to do.

### 6. Hidden demand and high-value decisions

Retail leasing has the shape of a strong problem. A guide for district managers notes that "final leasing decisions are typically left to individual property owners," and that managers "are often without sufficient resources and guidance." Industry trade press says "platforms have emerged… to help better match retail landlords with the right brands," and that "a shared customer base, rather than a more traditional, one-size-fits-all shopping center layout, can boost overall consumer traffic and spending." Percentage-rent leases "incentivize landlords to select a complementary mix of tenants," which means landlords directly profit from getting tenant mix right.

Existing tools lean on footfall and demographics ("foot traffic sensors, Wi-Fi analytics, and anonymized mobile data"). They describe *who walks by*, not *what those people culturally want*. That gap is the missing Qloo layer.

For contrast, music-side tools charge for far lower-stakes help: Booking-Agent.io sells venue and talent-buyer data at "$49.99/month."

**India wedge (assessed and rejected as the primary angle):** malls with vacancy and a crowded D2C-brand expansion market make tenant mix a real Indian problem. However, I could not verify Qloo's place and brand coverage in Indian Tier-2 cities, and I could not retrieve current vacancy data. Use one Indian demo city (e.g., Bengaluru's Indiranagar) only if Phase 1 coverage tests pass. Lead the demo with a city where coverage is proven (NYC, London or Austin).

### 7. Raw idea pool (48 ideas, compressed)

Format: idea, then decision or customer, then verdict.

**Location and real estate**
1. Karum, vacant-unit tenant mix for landlords: **Tier A**
2. Mall re-merchandising plan for a whole floor: merged into Karum v2
3. Pop-up slot programmer for short-term retail space: Tier B (thin wallet)
4. Food-hall stall curation: Tier B (folded into Karum)
5. High-street BID "missing tenants" report for councils: Karum variant
6. Franchise territory picker: reject (GeoTaste overlap ~8)
7. Hotel ground-floor and lobby programming: **Tier A**
8. Coworking amenity programming: reject (low stakes)
9. Real-estate listing copy by buyer taste: reject (decorative)
10. Neighbourhood relocation for families: reject (TasteBridge and Home2Here exist)

**Retail and merchandising**
11. Indie bookstore and record-store buying agent: **Tier A**
12. Boutique brand-assortment buyer: Tier B (SKU coverage gap)
13. Museum gift-shop assortment: Tier B
14. Airport retail concept selection: reject (needs enterprise access)
15. D2C "which city next" expansion: reject (GeoTaste overlap)
16. Wine-list builder for restaurants: reject (entity coverage unknown)
17. Menu concept for a new neighbourhood: reject (GeoTaste and Hayy overlap)

**Media and entertainment**
18. Indie film platform-release planner: **Tier A**
19. Festival lineup builder: Tier B (2026 music lane crowded)
20. Venue booking: reject (Booker exists)
21. Tour routing and openers: reject (Advance and Undercard exist)
22. Podcast guest booking: Tier B
23. Streaming catalogue acquisition fit for a regional platform: Tier B (data-heavy)
24. Book cover and positioning comps for publishers: Tier B
25. Soundtrack licensing short-list for ads: Tier B

**Brand and marketing**
26. Sponsorship fit: reject (Cold-Open and Deal Desk exist)
27. Synthetic focus group: reject (Quorum exists)
28. Co-branding collab finder: reject (Cold-Open overlap)
29. Brand-safety "cultural clash" pre-flight for ads: Tier B
30. Influencer–brand fit: reject (crowded)
31. Localization of global campaigns: reject (Resonance AI pattern; CULTURAL_MATCH_AI exists)
32. Political messaging: reject (copy of a winner)

**Events and hospitality**
33. Corporate offsite programming: Tier B
34. Indian wedding sangeet and menu planning: Tier B (coverage risk)
35. Conference side-event planning: reject (low novelty)
36. Senior-living activity and dining: reject (Qloo's own example prompt; "Resonance" 2026 targets it)
37. Hotel guest pre-arrival personalization: reject (concierge, crowded)

**Agent economy**
38. Taste-veto layer for shopping agents (MCP): Tier B (MCP crowded; weak user value alone)
39. Agent-to-agent "taste passport": reject (no concrete buyer yet)
40. Agent-readable catalogue enrichment for SMB listings: Tier B
41. Gift agent: reject (crowded)
42. Group-decision agent: reject (Duddle, CultureCircle, Common Ground)

**Other**
43. Rare-disease community matching: reject (Qloo is decorative)
44. Lighting-style advisor: reject (organiser's example; Qloo weak)
45. Hiring and culture fit: reject (ethics; decorative)
46. Dating: reject (crowded, ethics)
47. Education reading lists: reject (low stakes)
48. Unrecommendation for merchants ("what not to stock"): merged into Karum and the buying agent as the negative-space feature

### 8. Counterfactual test for Karum

Query: "Vacant 1,200 sq ft unit at [address], neighbours: [natural-wine bar], [record store], [ramen shop]. What should go here?"

- **A. LLM only:** "A café, boutique fitness studio, or plant shop would complement the area." The answer is generic, could apply to any trendy block, and gives no evidence.
- **B. LLM + Search:** it adds which chains are expanding and the local rent levels. That is factual, but it still guesses at taste fit, and trend articles bias it toward whatever is in the news.
- **C. LLM + Embeddings:** it finds brands whose *descriptions* resemble the neighbours, such as other wine bars. That creates **cannibalisation**, the exact mistake tenant mix tries to avoid.
- **D. LLM + Qloo:** it resolves the three neighbours as Qloo places, reads which brands and place categories the neighbours' audiences *also* show affinity for, and filters to categories absent within the radius. It ranks candidates by fit with the catchment plus complement with the neighbours, minus overlap with them. It can produce a non-obvious pick, such as a specific eyewear or outdoor brand, alongside the tag evidence and a "do not lease" list. This shape is the one Qloo's own example shows: a West Village Italian restaurant whose cross-domain relationships include "Warby Parker." **D is the only version that can tell an owner which of two plausible tenants the block's audience will choose, and why.**

---

# EXECUTIVE VERDICT
**Best Idea:** Karum, the vacancy-to-tenant leasing agent for landlords, brokers and mall operators.
**One-Line Pitch:** Karum reads what a block's people actually love and tells a landlord which tenant to sign, which ones to avoid, and why, then drafts the pitch to land them.
**Qloo Indispensability:** 9/10
**Qloo Novelty:** 7/10
**Previous-Hackathon Similarity:** 5/10
**Solo Startability:** 4/5
**Two-Person Startability:** 5/5
**Judge Score:** 80/100
**Business Potential:** 8/10
**Novelty:** 7/10
**Demo Wow Factor:** 8/10
**Technical Risk:** Medium

# TOP 10 IDEAS (comparison table)

| # | Idea | Tier | Qloo Tech (20) | Agentic (15) | Novelty (15) | Problem (15) | Demo (15) | Business (10) | Design (5) | Feasibility (5) | **Total /100** | Indisp. /10 | Similarity /10 | Solo /5 | Duo /5 | Tech Risk /10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Karum**, tenant-mix leasing agent | A | 17 | 11 | 11 | 13 | 12 | 8 | 4 | 4 | **80** | 9 | 5 (GeoTaste) | 4 | 5 | 5 |
| 2 | **Shelfwise**, indie bookstore/record-store buying agent (location-aware "what to stock / what to cut") | A | 15 | 11 | 12 | 10 | 10 | 5 | 4 | 5 | **72** | 8 | 2 (PersonaReads is consumer) | 5 | 5 | 4 |
| 3 | **Rollout**, indie film platform-release planner (cities, theatres, comp titles, partner brands) | A | 15 | 11 | 10 | 11 | 11 | 6 | 3 | 3 | **70** | 8 | 4 (Advance 2026 does this for tours) | 3 | 4 | 6 |
| 4 | **House Program**, boutique-hotel ground-floor and lobby programming | A | 14 | 10 | 11 | 10 | 11 | 6 | 4 | 4 | **70** | 8 | 4 (GeoTaste) | 4 | 5 | 5 |
| 5 | **Taste Veto**, preference-guard layer for shopping agents (MCP plus a demo agent) | A/B | 13 | 13 | 8 | 8 | 8 | 5 | 3 | 4 | **62** | 8 | 3 (2026 MCPs exist) | 4 | 5 | 5 |
| 6 | Festival lineup builder | B | 14 | 10 | 6 | 11 | 11 | 6 | 4 | 3 | 65 | 8 | 3 (2025), but 2026 lane has Booker/Advance/Undercard | 3 | 4 | 5 |
| 7 | Ad "cultural clash" pre-flight checker | B | 12 | 9 | 9 | 10 | 9 | 6 | 3 | 4 | 62 | 7 | 4 (Resonance AI) | 4 | 5 | 6 |
| 8 | Publisher comp-titles and positioning agent | B | 13 | 9 | 10 | 8 | 8 | 5 | 3 | 4 | 60 | 8 | 2 | 4 | 5 | 4 |
| 9 | Indian wedding sangeet / menu programmer | B | 11 | 10 | 10 | 9 | 10 | 6 | 4 | 3 | 63 | 7 | 1 | 3 | 4 | 8 (coverage) |
| 10 | Corporate offsite programmer | B | 11 | 10 | 7 | 8 | 9 | 6 | 4 | 4 | 59 | 7 | 4 (CultureCircle) | 4 | 5 | 4 |

Indispensability below 8 (ideas 7, 9 and 10) disqualifies an idea from the final shortlist under your rule. They stay here only as reference points.

**Rejected (reasons):** venue booking, tour routing, sponsorship, focus groups and relocation all already exist in the 2026 field. Political messaging and M&A culture scoring copy winners. Travel, cultural DNA, movies, fashion, gifting, dating and group planning are crowded in 2025, and Qloo is near-decorative in them. Rare disease and lighting are cases where Qloo is decoration. Airport retail and streaming acquisition need enterprise data.

# PREVIOUS QLOO HACKATHON — WHAT WE LEARNED (strongest patterns from the July-August competition)

(The prior event ran Jul 1 – Aug 1, **2025**, per Devpost.)

1. **Every winner answered "what should a business or organisation do?"** None answered "what should I watch?" Three of four are B2B. Zesty won by inverting the recommender itself.
2. **Location is Qloo's strongest demo moat.** The grand prize went to the location project. LLMs are weakest at block-level taste and Qloo is strongest there.
3. **Scores beat prose.** Alloy's Cultural Compatibility Score turned culture into a number a dealmaker can act on.
4. **Negative space impresses.** Zesty's "unrecommendation" showed the team understood the graph well enough to invert it.
5. **Name the buyer.** M&A firms, campaigns and businesses. Nobody won with "for everyone."
6. **The bar has risen for 2026.** The new criteria add Design ("complete, coherent product experience") and require judges to *use* the app. A strong idea with a thin UI will lose to a slightly weaker idea that feels like a product.
7. **The 2026 competition has learned from the 2025 winners.** Many entrants are already building B2B "taste-grounded decision" tools, with evidence panels and LLM-vs-Qloo baselines (Advance benchmarks Qloo against "an LLM alone" on 115 real tours). Novelty now has to come from choosing a decision nobody else picked.

# CROWDED AREAS TO AVOID

**DO NOT BUILD THIS UNLESS RADICALLY DIFFERENT:**
- Personalized travel itineraries or trip companions (Appmuseme, Qlootra, TasteTrip, Wander Wise, Lokalo, Voya, TasteJourney)
- Cultural DNA, taste-identity or "know yourself" apps (CultureAI, Taste Mirror, Taste Compass, Culturo)
- General lifestyle concierges or "conversational AI with taste" (Serendipity Engine, Qlue, CultureHub, Cultural Compass; TasteLoop and TasteRoute in 2026)
- Movie, music or book recommenders, including mood-based ones (QlooMoodFlix, Cultura, PersonaReads)
- Fashion and shopping stylists (Taste Taylor, BrandLink, Qloo Fashion AI)
- Group harmony and friend-planning (Duddle, CultureCircle; Common Ground in 2026)
- Roommate, dating or social matching (Vybr)
- Generic AI marketing-campaign generators (Marketly, AdBuddy, CULTURAL_MATCH_AI)
- Creative generators with "cultural context" (Griot, Cue Beats, Aethos)
- **2026-specific:** live-music venue booking, tour advance and openers (Booker, Advance, Undercard); synthetic focus groups (Quorum); brand-partnership and sponsorship leads (Cold-Open, Deal Desk); SMB café marketing (Hayy); relocation and "belonging" planners (TasteBridge, Home2Here); bare Qloo MCP servers
- Copies of the winners: location consulting for a new business (GeoTaste), culturally authentic political messaging (Resonance AI), M&A culture scoring (Alloy), feed inversion (Zesty)

# QLOO WHITE SPACE (most promising underexplored opportunities)

1. **Co-tenancy and tenant mix (fixed space, many candidates).** This is the inverse of GeoTaste. Nobody was found doing "which brand should fill *this* unit, given its neighbours."
2. **Inventory and assortment for independent retailers.** These are buy and cut decisions. Books and artists are well-covered Qloo entity types, and nobody built for the *seller*.
3. **Release and rollout planning for film and books.** It is a market-sequencing decision. Only touring music is being attempted in 2026.
4. **Hospitality ground-floor programming.** Hotels choosing F&B partners, retail pop-ups and music programming for a specific location and guest mix.
5. **Agent-side preference guarding.** A "taste veto" that stops a purchasing agent from buying something that conflicts with its principal's taste profile. This is real agent-economy value, but only once a concrete purchasing agent sits on top.

The connecting idea across all five is that **compatibility between a fixed physical or catalogue context and a set of candidates** remains unclaimed. That is the generalised Alloy pattern applied outside M&A, at a price point small operators can afford.

# THE IDEA I SHOULD BUILD (full product specification)

### Product name
**Karum.**

### One-line pitch
"Karum reads what a block's people actually love and tells a landlord which tenant to sign, which ones to avoid, and why, then drafts the pitch to land them."

### The problem
A vacant storefront costs the owner rent every month. Choosing the wrong tenant locks in a weak lease for years and can drag down neighbours' sales (and percentage rent). Today the decision rests on broker intuition, the highest bidder, and footfall and demographic data that say who walks by but not what those people want. District managers are "often without sufficient resources and guidance."

### The target customer
- **Primary:** small and mid-size retail landlords and independent leasing brokers (1–30 storefronts) who cannot afford enterprise location-analytics contracts.
- **Secondary:** business improvement districts and town-centre managers.
- **Later:** mall operators.

### Why current solutions fail
- Footfall and demographic platforms describe volume and demographic composition, not cultural preference.
- Broker intuition does not scale and cannot be shown to an owner or a brand's expansion team.
- LLMs give stereotyped, block-agnostic advice and tend to suggest whatever already exists nearby, which leads to cannibalisation.

### The insight
The best tenant is not the one most *similar* to the neighbours. It is the one the neighbours' customers also love but cannot currently get within walking distance. That is a cross-domain affinity question constrained by location, which is exactly what Qloo's graph answers.

### Why Qloo is essential
Every core step depends on Qloo:
- Resolving the neighbours as real places.
- Reading the cross-domain affinities of their audiences.
- Reading the taste concentration of the catchment.
- Scoring candidates.
- Producing descriptive tags for the explanation.

Remove Qloo and the product collapses to the generic LLM answer in counterfactual A.

### The agent workflow
1. **User intent:** "Fill unit 4B at [address]; current neighbours X, Y, Z; size and rent band; optional brand shortlist or 'surprise me'."
2. **Context gathering:** the agent asks at most two clarifying questions (budget tier; food and beverage allowed?). It geocodes the address.
3. **Entity resolution:** `/search` with `types=urn:entity:place` for each neighbour, and `urn:entity:brand` for shortlist brands. Ambiguous matches are shown to the user for one-click confirmation.
4. **Tag resolution:** `/v2/tags` maps constraints ("no F&B", "fitness", "eyewear") to tag IDs.
5. **Qloo queries** (see the call sequence below): catchment fingerprint, neighbour-audience affinities, candidate scoring, presence check.
6. **Result interpretation:** normalise affinities, then compute three sub-scores:
   - **Catchment fit:** candidate affinity under the location signal.
   - **Co-tenancy complement:** affinity of the neighbours' audiences for the candidate.
   - **Cannibalisation penalty:** same category already present within the radius.
7. **Agent reasoning:** the LLM reasons only over the returned entities and tags. It checks for contradictions (high fit but a category already saturated), and runs follow-up probes when a candidate is borderline. Running probes on its own initiative is what makes it an agent rather than a form.
8. **Decision:** a ranked shortlist of 5 candidates, 3 "do not lease" warnings, and one recommended pick.
9. **Explanation:** a "How we know" panel for each candidate. It lists every Qloo call, its parameters and result count, which neighbour audiences carried the affinity, and the descriptive tags. Inferences are clearly separated from Qloo outputs.
10. **Action:** generates (a) a one-page leasing memo PDF for the owner, (b) a tailored outreach email per brand citing the audience evidence, and (c) a listing blurb rewritten for the top candidate category. It can also save the analysis and re-run monthly ("watch this vacancy").

### Qloo API architecture (verified against docs.qloo.com — see [QLOO_APIS.md](QLOO_APIS.md) for the full reference; spike items still open are marked)
1. `GET /search?query=<neighbour>&types=urn:entity:place&filter.location=<lat>,<lon>&filter.radius=<miles>&take=5`, once per neighbour, giving neighbour IDs biased to the vacancy point. **Note: `/search` radius is in miles (`filter.radius`), Insights radius is in metres (`filter.location.radius`).**
2. `GET /v2/insights?filter.type=urn:tag&signal.interests.entities=<neighbour IDs>`, the "block taste" descriptors.
3. `GET /v2/insights?filter.type=urn:entity:brand&signal.interests.entities=<neighbour IDs>&<location>&feature.explainability=true`, the brands the neighbours' audiences show affinity for. This is the candidate generator, and the explainability payload feeds the evidence drawer directly. **Spike: Qloo's entity-type guide omits location params for `brand` while the location use case advertises them — settle whether `filter.location=POINT(<lon> <lat>)`, `signal.location`, or a locality query actually narrows results (fallback: `filter.location.query=<locality>`).**
4. `GET /v2/insights?filter.type=urn:entity:place&filter.tags=<candidate category tag>&filter.location=<lat>,<lon>&filter.location.radius=<metres>`, which checks whether that category already exists nearby (cannibalisation).
5. `GET /v2/insights?filter.type=urn:demographics&signal.interests.entities=<top candidates>`, the audience-skew sanity check against the catchment. **Spike: `urn:demographics` is documented on the use-case page but missing from the hackathon guide's supported-`filter.type` list (403 risk).**
6. Optional: the heatmap via `filter.type=urn:heatmap` with a signal — any entity or tag works; `urn:tag:genre:place:restaurant` is the sensible choice for Karum but not a hard requirement — to render where affinity concentrates around the unit.
7. Optional: `GET /v2/analysis/compare?a.signal.interests.entities=<neighbour IDs>&b.signal.interests.entities=<candidate>` for the "your neighbours vs. this candidate" overlap chart.

**Standing rules:** never `/recs` or `/recommendations` (legacy, forbidden); unsupported parameters are silently ignored, so every call must be asserted non-empty in tests; fixture JSON must be redacted — Qloo forbids raw responses in public repos and Devpost requires public repos.

### Full example session
- **User:** "Unit at 1xx Bedford Ave, Brooklyn. Neighbours: a natural-wine bar, a vinyl shop, a ramen counter. 900 sq ft, no kitchen. Who should I sign?"
- **Agent:** resolves the three places (shows the matches, and the user confirms). It asks "Mid or premium rent tier?", and the user answers premium.
- **Qloo:** block descriptors return tags (illustratively, "indie", "craft", "design-forward"). The brand affinity query returns a ranked brand list across eyewear, outdoor apparel, stationery, skincare and so on. The presence check finds two coffee shops and one bike shop within the radius.
- **Agent:** drops coffee (saturated) and bikes (present). It probes further: "Skincare ranks high but has one competitor; re-query with the skincare tag under this location." It then ranks the shortlist.
- **Result:** "Recommended: an independent eyewear brand (catchment fit 0.9x, complement 0.8x, no competitor within 500 m). Do not lease: a third coffee concept (cannibalisation), a mass-market fast-fashion chain (low affinity with neighbours' audiences)." Memo and outreach emails follow, with every number traceable. (Values here are illustrative; the demo must show live outputs.)

### The "magic moment"
The judge types three real neighbouring venues on a block they know. Karum rejects the obvious answer the judge was thinking of (another café) with the reason "already saturated within 400 m." It then surfaces a non-food brand, such as an eyewear or stationery label, and shows the chain of evidence: these three venues' audiences, the affinity for that brand, and its absence nearby. The judge's reaction should be: *"A normal LLM would have said 'café'."* A side-by-side "LLM-only answer" panel makes the contrast explicit.

### User interface
1. **Start screen:** address field, "add neighbours" (autocomplete via `/search`), constraints chips. A "Try a sample block" button lets judges start without effort.
2. **Live agent trace:** a streaming timeline of tool calls ("Resolving neighbours… Reading block taste… Checking saturation…").
3. **Map view:** the unit pin, neighbour pins, competitor pins and an optional heatmap overlay.
4. **Shortlist board:** five candidate cards, each with three sub-score bars, top shared tags and an "evidence" drawer.
5. **"Do not lease" column:** red cards with the reason. This is the Zesty-pattern negative space.
6. **LLM-only comparison toggle:** what a plain LLM said for the same prompt.
7. **Outputs:** memo PDF, per-brand outreach email (copy or send via mailto), listing blurb.
8. **Saved vacancies:** re-run and diff ("affinity for X rose since last month").

### Before vs. after
- **Before (generic LLM):** "Consider a café, boutique fitness or a plant shop." No evidence, the same answer for every hip block, and it recommends competitors of the existing tenants.
- **After (Karum):** a ranked, block-specific shortlist with saturation checks, a co-tenancy rationale traced to real venues' audiences, a list of what to avoid, and ready-to-send outreach.

### Technical architecture (deliberately simple)

> **Superseded — the build uses Flutter web.** This Next.js sketch was the pre-build idea. The settled stack is a **Flutter web client** (the judge target; the same screens also run on desktop), a Go + Gin API gateway, and Python gRPC microservices across five repos. The memo PDF is server-rendered by the gateway (no react-pdf), map tiles are drawn directly in the Flutter client, and deployment is Cloud Run, not Vercel. The full record is in [DECISIONS.md](DECISIONS.md) §2 and [TECH.md](TECH.md). The bullets below are kept only as the original brief.

- **Frontend:** ~~Next.js (App Router) with Tailwind, MapLibre GL using free OSM/CARTO tiles, and react-pdf for the memo.~~ **Flutter web** draws OSM/CARTO tiles in-app; the memo PDF is rendered server-side.
- **Backend:** ~~Next.js route handlers (or a single FastAPI service if you prefer Python).~~ Go + Gin API gateway plus the Python microservices; the Qloo key stays server-side only.
- **Model:** any tool-calling LLM (Claude, GPT or Gemini), with a deterministic "autopilot" fallback strategy for when the LLM fails. TasteBridge uses this same pattern.
- **Agent framework:** a hand-rolled tool loop. Avoid heavy frameworks. (The Vercel AI SDK from the original sketch does not apply to the Go/Python backend.)
- **Qloo:** a typed client with retries. Every call is logged into a trace object sent to the UI.
- **Database:** SQLite or Supabase Postgres for saved vacancies and cached Qloo responses.
- **External APIs:** a geocoder (Nominatim or Mapbox free tier); optional email via Resend.
- **Deployment:** Cloud Run, with a static host for the Flutter web build. Keep a public, no-login demo mode, because judges need unrestricted access.
- **Authentication:** none for the demo; magic-link login for saved vacancies.
- **Caching:** cache Qloo responses by parameter hash for 24h, and pre-warm the sample blocks.
- **Monitoring:** Cloud Run logs plus a `/health` endpoint that reports Qloo live or fallback mode. Per-IP rate limiting.

# 3-MINUTE JUDGE DEMO (exact sequence of interactions)

1. **0:00–0:20 (problem):** the landing card reads "A wrong tenant is a 5–10 year mistake. Brokers guess. Karum reads the block." Click **Try sample: Bedford Ave, Brooklyn**.
2. **0:20–0:50 (resolution):** three neighbours auto-resolve with Qloo IDs and categories. The judge sees the confirmations. Optionally swap in a venue the judge knows.
3. **0:50–1:30 (agent at work):** the trace streams through block taste tags, the brand-affinity query, the saturation check, and a probe follow-up. The map fills with neighbours and competitors.
4. **1:30–2:10 (magic moment):** the shortlist appears. The "Do not lease: third coffee concept, saturated within 400 m" card sits next to the #1 non-obvious brand. Open its evidence drawer: neighbour audiences → affinity → no competitor nearby.
5. **2:10–2:30 (counterfactual):** toggle the "LLM-only answer" to show the generic "café, fitness, plants."
6. **2:30–2:50 (action):** click **Generate memo**, then **Draft outreach to Brand #1**. The PDF and email appear, each citing the evidence.
7. **2:50–3:00 (close):** "Every vacancy in the world has this question. Karum answers it with what people actually love."

Also offer a second sample block in another city, plus a free-entry mode, so judges who explore beyond the script still get results.

# MVP BUILD PLAN (concrete implementation roadmap)

**Must build**
- Neighbour resolution with confirmation
- Block taste tags
- Brand-affinity candidate generation under a location filter
- Category saturation check
- Three-part score and ranking
- "Do not lease" list
- Evidence drawer and call trace
- Map with pins
- LLM-only comparison panel
- Memo PDF and outreach email
- Two pre-warmed sample blocks
- Public hosting, MIT licence, README with architecture and honesty rules

**Should build**
- Heatmap overlay (if available with the hackathon key)
- Demographic sanity check
- Agent follow-up probes
- Saved vacancies
- Leave-one-out evaluation page: hide a real, highly rated existing tenant and see whether Karum ranks its category above the LLM's picks. This copies Advance's credibility move and gives you a quantitative Impact claim.

**Nice to have**
- Monthly re-run diff alerts
- A brand-side view ("which vacancies fit my brand")
- An MCP endpoint so other agents can call Karum

**Absolutely do not build**
- Login walls on the demo
- Payments
- Footfall data integrations
- Scraping listings sites
- Multi-floor mall planner
- Mobile app
- Custom ML models
- Any feature that shows undocumented Qloo parameters you haven't tested

**30-day plan (Oct 4 → Oct 30; the key request takes a few business days, so request it today)**

| Phase | Days | Deliverable |
|---|---|---|
| 1. Qloo/API experimentation | Oct 4–8 | Request the key immediately; use fixtures while waiting. Coverage notebook: for 3 cities × 5 blocks, test place resolution, brand insights with location, tag outputs, heatmap availability. **Kill/go gate on Oct 8** |
| 2. Core prototype | Oct 8–12 | Scoring pipeline as a CLI: address and neighbours in, ranked JSON with evidence out |
| 3. Agent workflow | Oct 12–16 | LLM tool loop, probes, deterministic fallback, trace object |
| 4. Frontend/UX | Oct 14–21 | Start screen, trace timeline, map, shortlist board, do-not-lease column, evidence drawer |
| 5. Integration | Oct 21–23 | Memo PDF, outreach email, LLM-only panel, caching, saved vacancies |
| 6. Testing | Oct 23–25 | Leave-one-out eval on about 20 blocks; edge cases (unresolved venue, empty results); rate limits |
| 7. Deployment | Oct 25–26 | Production deploy, env secrets, health endpoint, licence in repo About |
| 8. Demo optimisation | Oct 26–28 | Pre-warm samples, copywriting, 60-second onboarding, accessibility pass |
| 9. Final submission | Oct 28–29 | Devpost description mapped to the four criteria, screenshots, eval results. Submit **24h before** the deadline |

**Solo vs. two-person**
- **Solo (minimum):** the single-city sample plus free entry; brand-affinity, saturation and tags only; shortlist, evidence, LLM comparison, memo. Skip the heatmap, saved vacancies and eval page.
- **Two people:**
  - **Person 1 (Qloo + agent):** coverage tests, Qloo client, scoring, agent loop, probes, eval, caching.
  - **Person 2 (product):** UI, map, cards, PDF and email generation, onboarding, deployment, Devpost copy.
  - They sync on the trace schema on day 2.

**Effort estimate (two-person days):** frontend 6, backend 3, agent orchestration 3, Qloo integration 3, integrations (geocoder, PDF, email) 2, data acquisition 0.5 (sample blocks only), infrastructure 1, testing 2, deployment 0.5, polish 3. That is about 24 person-days, which fits.

**Monetization (estimates, not validated)**
- **Who pays and why:** independent landlords and leasing brokers. A month of vacancy on a small storefront typically costs more than any plausible report price, and brokers can use the memo to win listings.
- **Pricing hypothesis:** $49–$149 per vacancy report; a broker plan at $199–$499/month; BID or council licences.
- **First customer:** a local broker with 3–10 active listings, reached through LinkedIn or commercial-real-estate (CRE) Twitter, given the hackathon demo free in exchange for feedback.
- **Path:**
  - First $100: two paid reports from broker contacts.
  - First $1,000: ten brokers or one BID pilot.
  - First $10,000: about 20 broker subscriptions, or 3 small-mall operators.
- **Expansion:** mall operators, food-hall operators, brand expansion teams (the reverse marketplace), and India mall operators if coverage holds.

**Defensibility (Qloo is not the moat)**
- A domain-specific scoring rubric (fit, complement, cannibalisation) calibrated over time against real lease outcomes that users report.
- A saved-vacancy history that turns into a two-sided match: brands looking for space, landlords looking for brands. This creates network effects.
- Workflow lock-in: the memo and outreach become part of the broker's pitch process.
- Broker distribution relationships.

A weekend rebuild with Qloo plus an LLM would give the first screen, not the calibrated rubric, the outcome data or the two-sided marketplace.

**Technical risks and mitigations**
- **Place and brand coverage gaps:** gate on Phase 1 tests; choose demo cities by coverage; label misses explicitly.
- **Location-filter granularity (city vs. radius):** test radius behaviour early. If only city-level works, use neighbour-entity signals as the "block" proxy.
- **Heatmap not available on the hackathon key:** make it optional, and use pins plus the competitor radius instead.
- **Agent reliability:** use a deterministic fallback pipeline; constrain the LLM to returned entities; add schema validation.
- **Latency (5–8 Qloo calls):** run calls in parallel, cache, pre-warm samples, and stream the trace so waiting feels like progress.
- **Brand results skew to big chains, or brands without retail presence:** use the documented popularity bands (`filter.popularity.min/max`) and a "has physical retail" heuristic, or let the user paste a candidate list.
- **Cost:** LLM tokens are small. Rate-limit per IP.
- **User comprehension:** keep three sub-scores with plain-English labels rather than one opaque number.

# WHY THIS COULD WIN (directly mapped to the judging criteria)

- **Technological Implementation:** it uses five or more distinct Qloo capabilities in one reasoning chain (place resolution, tag output, cross-domain brand affinity under location, category presence checks, demographics, and optionally heatmap and compare), plus agent probes, a fallback, an evidence trace and a leave-one-out evaluation. That is clearly a "working, non-trivial implementation."
- **Design:** it is a complete flow from address to memo to outreach, has a map-centred UI, needs zero setup for judges, and keeps the outputs a broker would actually send.
- **Potential Impact:** it names a buyer (landlords and brokers), states the economic stakes (multi-year leases and vacancy carrying costs), shows how incumbents fail (footfall without taste), and provides an evaluation that quantifies the gain over LLM-only.
- **Quality of the Idea:** it is non-obvious. It inverts GeoTaste (a fixed space choosing among many brands, instead of one business choosing a place), applies Alloy's compatibility logic to co-tenancy, and adopts Zesty's negative space ("do not lease").
- **Judge fit:**
  - Boehly and Calacanis invest in real assets and businesses, so they see a market.
  - Diolosa sees deep, honest API use.
  - Abrams sees venue-economics thinking.
  - Seligman sees responsible, evidence-traced agent behaviour.
- **Versus each winner:**
  - **GeoTaste:** Karum adds co-tenancy, cannibalisation, a concrete action (outreach) and an evaluation.
  - **Resonance AI:** Karum has a commercial buyer and measurable outcomes.
  - **Zesty:** Karum puts negative space inside a monetisable decision.
  - **Alloy:** Karum addresses a far larger, more frequent and cheaper-to-serve decision, with spatial evidence that is easier to verify.

# WHY THIS COULD FAIL (brutally honest)

- **Too close to GeoTaste for some judges.** Mitigation: lead the pitch with "fixed space, many candidates, co-tenancy," and never say "business consultant."
- **Qloo brand outputs may not map to brands with physical retail, or that would plausibly lease 900 sq ft.** If top results are global megabrands or online-only labels, the magic moment dies.
- **Location precision may be city-level only on the hackathon key,** which would weaken the "block" story.
- **Another 2026 entrant may build retail site or tenant tools.** CulturePilot ("better market decisions") and others are adjacent, and I could only see public GitHub, not Devpost drafts.
- **Real estate is unglamorous next to music and entertainment** for judges like Cedric the Entertainer. The demo must feel vivid (map, surprising pick, strong "do not lease" line).
- **Willingness to pay is untested.** Small landlords are notoriously cheap, and the pricing above is a hypothesis.
- ~~**I could not read the 2026 rules page or full Qloo docs.**~~ **Closed 16 Oct 2026:** the rules were read in full (no team cap; the Qloo integration must be new; judging Nov 2–16) and the API surface is mapped in [QLOO_APIS.md](QLOO_APIS.md). What remains unverified is spike behaviour — parameter acceptance, radius granularity, quota — plus key-delivery timing.

**Kill criteria (abandon by Oct 8–10 if any is true):**
1. For at least 3 of 5 test blocks, Qloo's brand or place outputs under location do not change meaningfully when the neighbours change. That would mean Qloo is not adding block-specific signal.
2. Fewer than 70% of real neighbourhood venues resolve via `/search` in the demo cities.
3. Top candidate brands are mostly non-retail or implausible for small units, even after filtering.
4. The leave-one-out test does not beat LLM-only on at least 12 of 20 blocks.
5. Median end-to-end latency stays above 20s after caching and parallelisation.
6. Three non-technical testers cannot explain the recommendation after 60 seconds.
7. The rules page prohibits the approach.

**Fallback:** switch to **Shelfwise**, the independent bookstore and record-store buying agent. It uses the same architecture (resolve entities, then affinity under location, then presence and saturation, then "stock / cut" lists) on book and artist entities, which may have stronger coverage.

**Long-term product:**
- **Hackathon MVP:** a single-vacancy report.
- **v1:** a broker workspace with saved vacancies, monthly diffs and branded memos.
- **v2:** a brand-side view and matching marketplace (brands get pinged when a high-fit vacancy appears), plus outcome capture (signed? sales?) that calibrates the rubric.
- **Startup:** a "cultural tenant-mix" layer sold to mall operators and BIDs, integrated alongside footfall vendors rather than competing with them, with an India mall-operator wedge if coverage holds.

# FINAL RECOMMENDATION (decisive)

Build **Karum**. Request the Qloo hackathon key today and read the official rules page tonight. Spend Oct 4–8 on the coverage notebook and treat the Oct 8 kill/go gate as binding. If it passes, build exactly the Must-Build list, with the "do not lease" card and the LLM-only comparison as the centrepiece of the magic moment. Ship a public, no-login demo with two pre-warmed blocks by Oct 26, and submit by Oct 29.

Stay out of music booking, focus groups, sponsorship and relocation; the 2026 field already has entries there. If the gate fails, pivot to Shelfwise the same day without re-planning. The architecture carries over.

The narrative to tell judges:
- **Problem:** vacant storefronts are filled by guesswork.
- **Insight:** the right tenant is what the neighbours' customers love but cannot currently buy on that block.
- **Why Qloo:** only a cross-domain, location-aware taste graph can see that.
- **Why an agent:** it resolves, probes, rejects, decides and then acts.
- **Why now:** landlords are re-tenanting in a post-anchor retail market, and agents can now produce the memo and the outreach.
- **Why you:** a two-person team can ship this in 24 person-days.
- **Why it matters:** every vacancy on every high street has this question.
