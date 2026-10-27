# Graph Report - google-maps-free-scraper  (2026-10-27)

## Corpus Check
- 23 files · ~24,444 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 168 nodes · 248 edges · 17 communities (14 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b943c363`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.js
- painel.js
- SETUP — Google Maps Scraper Kit
- Google Maps Scraper Kit
- Google Maps Scraper
- scrape.py
- Contexto operacional do Google Maps Free Scraper
- scrape_neighborhood.py
- scrape.sh script
- capture_neighborhood.sh
- capture_supabase_leads.py
- capture_niche.sh

## God Nodes (most connected - your core abstractions)
1. `Google Maps Scraper` - 12 edges
2. `refreshJobs()` - 9 edges
3. `openResults()` - 9 edges
4. `SETUP — Google Maps Scraper Kit` - 9 edges
5. `refreshJobs()` - 8 edges
6. `openResults()` - 8 edges
7. `renderResults()` - 8 edges
8. `Contexto operacional do Google Maps Free Scraper` - 8 edges
9. `CLAUDE.md — Google Maps Scraper Kit` - 8 edges
10. `Google Maps Scraper Kit` - 8 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (17 total, 3 thin omitted)

### Community 0 - "app.js"
Cohesion: 0.11
Nodes (33): ago(), checkLocation(), closeResults(), deleteJob(), distance(), drawArea(), fetchCount(), fetchRows() (+25 more)

### Community 1 - "painel.js"
Cohesion: 0.12
Nodes (30): ago(), checkLocation(), closeResults(), deleteJob(), distance(), ensureResultsMap(), fetchRows(), geocode() (+22 more)

### Community 2 - "SETUP — Google Maps Scraper Kit"
Cohesion: 0.09
Nodes (19): Attribution, CLAUDE.md — Google Maps Scraper Kit, Hard facts you must not get wrong, Rate limits — warn, don't block, Setup, Slash commands, What this project is, When the user asks to scrape businesses / get a list of places / lead-gen data (+11 more)

### Community 3 - "Google Maps Scraper Kit"
Cohesion: 0.12
Nodes (14): Credits & Attribution, Upstream license (reproduced as required by MIT), Upstream project, Busca focada por bairro, Credits & license, Google Maps Scraper Kit, Hermes workflow, Invoking it in Claude Code (+6 more)

### Community 4 - "Google Maps Scraper"
Cohesion: 0.14
Nodes (14): Best practices (from the upstream docs), Google Maps Scraper, Mental model, Neighborhood mode, Other endpoints, ⭐ Output ONLY money-useful lead fields (default), Rate limits, bans & proxies (read before large jobs), Safety & guardrails (+6 more)

### Community 5 - "scrape.py"
Cohesion: 0.29
Nodes (7): collect_keywords(), enrich_socials(), geocode(), main(), Add instagram/facebook/linkedin to each lead by scanning its website. Zero LLM…, City/place name -> ('lat','lon') strings via Nominatim, or None., req()

### Community 6 - "Contexto operacional do Google Maps Free Scraper"
Cohesion: 0.22
Nodes (8): Cartographer e REA, Contexto operacional do Google Maps Free Scraper, Graphify obrigatório, Mapa técnico, Objetivo, Regra de decisão, Segurança e operação, Verificação

### Community 7 - "scrape_neighborhood.py"
Cohesion: 0.62
Nodes (6): api(), geocode(), job(), main(), norm(), row_key()

### Community 15 - "capture_supabase_leads.py"
Cohesion: 0.70
Nodes (4): call(), load_env(), main(), report()

## Knowledge Gaps
- **51 isolated node(s):** `RFC-4180`, `RFC-4180`, `capture_neighborhood.sh script`, `capture_niche.sh script`, `scrape.sh script` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Google Maps Scraper` connect `Google Maps Scraper` to `SETUP — Google Maps Scraper Kit`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **What connects `RFC-4180`, `RFC-4180`, `capture_neighborhood.sh script` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.10931174089068826 - nodes in this community are weakly interconnected._
- **Should `painel.js` be split into smaller, more focused modules?**
  _Cohesion score 0.1226890756302521 - nodes in this community are weakly interconnected._
- **Should `SETUP — Google Maps Scraper Kit` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `Google Maps Scraper Kit` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Should `Google Maps Scraper` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._