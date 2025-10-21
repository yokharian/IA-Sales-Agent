## Product Requirements Document (PRD)

Summary: build tools for a LangChain-based AI agent that (1) recommends cars from a CSV catalog based on customer preferences and (2) calculates financing plans (down payment, car price, 10% interest, terms 3–6 years). MVP focused on quick LLM integration, reproducibility, and regression tests.

## 1. Goals

- Deliver a set of tools (LangChain tools + pipelines) that:
  - Filter and recommend vehicles from a CSV catalog with tolerance for input errors (typos, incomplete brand/model).
  - Calculate and present financing plans clearly and verifiably.
- Minimize hallucinations using RAG + verification rules.
- Be integrable as an agent in LangChain and expose an API for consumption (WhatsApp/web bot).

## 2. Scope (MVP)

Includes:

- Ingest and normalize CSV into a datastore (Postgres).
- Vectorize descriptions for semantic search (FAISS / Chroma).
- LangChain tools:
  - catalog_search_tool(preferences) → top-N matches (structured).
  - finance_calc_tool(price, down_payment, term_years) → amortization schedule + monthly payment.
  - fact_check_tool(response, source_records) → verifies key numbers against DB.
- Prompt templates and chains (retrieval + synthesis) with guardrails to avoid inventions.
- Test-suite with golden set and CSV examples.

Does not include advanced UI or multi-region deployment (roadmap will cover these).

## 3. Functional requirements

FR1 - CSV ingestion:

- Parse the CSV (headers as provided) and normalize fields: make/model lowercased, strip accents, map Sí/No to booleans.
- Store records in Postgres and update the vector DB with embeddings of text (make+model+version+year+specs).

FR2 - Search and recommendation:

- Endpoint/tool that receives preferences (min/max budget, make(s), model(s), max km, features like bluetooth, car_play, size) and returns top 5 matches with:
  - similarity score (0–1),
  - key fields (stock_id, price, make, model, year, km, version, features),
  - brief justification (1–2 sentences) based on record attributes.
- Must tolerate typographical errors via fuzzy match + semantic retrieval.

FR3 - Financing calculation:

- Tool that accepts price and down_payment and calculates:
  - principal_financed = price - down_payment
  - nominal annual rate = 10% (fixed)
  - terms in months = 36, 48, 60, 72 (3–6 years; include 36–72 months)
  - monthly payment per term (fixed-rate loan amortization) and total paid.
  - show a summary table per term and a simplified amortization schedule for a selected term.
- Validations: down_payment ≤ price; return a clear error if invalid.

FR4 - Verification and hallucination mitigation:

- Always include the data source for numeric facts (stock_id or "internal catalog").
- Do not allow the agent to invent prices or features: any claim about a vehicle must come from the DB; if information is missing, return "Not available".
- Implement fact_check_tool that compares generated responses with the DB and flags inconsistencies.

FR5 - API and LangChain integration:

- Expose tools compatible with LangChain's Agent API (tool signatures + docs).

FR6 - Logging and observability:

- Log tool inputs/outputs (no PII).
- Metrics: tool latency, error rate, mismatches detected by fact_check.

## 4. Non-functional requirements

- Performance: p99 latency for tool calls < 1s (excluding LLM calls); target LLM roundtrip < 1.5s.
- Scalability: horizontal via containers.
- Security: secrets in Vault; DB connections over TLS.
- Testability: unit/integration tests for parsers, fuzzy-match, calculations, and fact_check.
- Reproducibility: Docker scripts + docker-compose for local setup; README with setup.

## 5. Data model (summary)

- vehicles (Postgres):
  - stock_id (PK), make, model, year, version, km, price (float), features (jsonb: bluetooth, car_play), dims (json), raw_row (json)
- embeddings index: id -> vector (FAISS/Chroma) with metadata linking to vehicles.

Example normalized row for the first CSV entry:

- stock_id: 243587
- make: volkswagen
- model: touareg
- year: 2018
- price: 461999.0
- km: 77400
- features.bluetooth: true
- raw_row: {...}

## 6. UX / Output examples (templates)

- Recommendation short format: "I recommend: [make model year version] (stock [id]) — Price: $X — km: Y — Reason: [match reason]."
- Financing summary table with columns: term (years), monthly_payment, total_paid, total_interest.

## 7. APIs / Tools (contracts)

Tool: catalog_search_tool(preferences: dict) -> List[VehicleResult]

- preferences keys: budget_min, budget_max, make, model, km_max, features[], sort_by
- returns top-5 with similarity_score and source_stock_id.

Tool: finance_calc_tool(price: float, down_payment: float) -> FinanceSummary

- returns list of {term_years, months, monthly_payment, total_paid, interest_paid} for 3–6 years.

Tool: fact_check_tool(generated_text: str, referenced_ids: List[int]) -> FactCheckResult

- validates numeric claims against DB; returns list of mismatches.

API endpoints mirror these tools with JSON.

## 8. Acceptance criteria

- Given the provided CSV, the system ingests and indexes all rows; sample query "busco Touareg 2018 con bluetooth y presupuesto 500k" returns stock_id 243587 in top-3 with correct price and features.
- finance_calc_tool(price=461999, down_payment=46199) returns monthly payments for 36, 48, 60, 72 months and totals; principal and interest calculations validated by unit tests.
- fact_check_tool flags a generated claim if it differs >0.1% from DB price.

## 9. Testing strategy

- Unit tests: CSV parser, normalization, fuzzy matcher, finance math (edge cases: zero down payment, down_payment == price).
- Integration tests: end-to-end LangChain chain with a mocked deterministic LLM; verify tool invocation and final response.
- Regression/golden tests: a set of representative queries (~200, including typos) and assert tool outputs within tolerances.
- Load tests: index 100k records and measure search latency.

## 10. Roadmap (quarters)

Q1 (MVP, 6 weeks): CSV ingestion, Postgres + vector index, catalog_search_tool, finance_calc_tool, unit tests, README + docker-compose.
Q2: LangChain agent integration, RAG chains, fact_check_tool, Twilio webhook demo, staging deploy.
Q3: Monitoring, feature flags, managed vector DB, privacy audits, performance tuning.
Q4: Multi-language support, advanced recommendation ranking (ML model), A/B tests with human agents.

## 11. Risks & mitigations

- Hallucinations: RAG + fact_check; disallow free-form LLM assertions about DB facts.
- Poor fuzzy matches: combine token-based fuzzy (Levenshtein) + embedding similarity with thresholds.
- Numeric rounding errors: canonicalize currency/decimals; tests for financial math.

## 12. Effort estimate (person-weeks)

- MVP: 6–8 pw (1 infra eng, 1 backend eng, 0.5 ML/data eng, 0.5 QA)
- Full product (Q1–Q3): 20–30 pw.

## 13. Deliverables

- Repository with code: ingestor, tools, LangChain agent examples, tests, docker-compose.
- README for reproducibility and Twilio demo.
- Golden test dataset and test runner.
- Postgres + vector index schema and sample data (from CSV).

Date: October 20, 2025.
