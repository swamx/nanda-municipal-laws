# Documentation Index

Municipal Legal Intelligence Service — built for the MIT Hackathon. A lightweight FastAPI service that indexes real NYC municipal law text (NYC Administrative Code + NYC Health Code) in MongoDB and exposes deterministic, citation-backed retrieval — search, exact section lookup, cross-reference resolution, and penalty/permit filtering — for consumption by any autonomous agent or chatbot.

- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design, data model, and the key design decisions (and constraints) behind them
- [API.md](./API.md) — full endpoint reference with curl examples and sample responses
- [DEPLOYMENT.md](./DEPLOYMENT.md) — MongoDB Atlas + Vercel free-tier deployment steps, environment variables, prod-readiness notes
- [DATA_SOURCE.md](./DATA_SOURCE.md) — where the law text comes from, its license, current coverage, and how to extend it

See the repo root [README.md](../README.md) for a quick-start (install, seed, run, test) and the root [SKILL.md](../SKILL.md) for the agent-facing API reference — endpoints, curl examples, and exactly how a calling agent should compose its final answer from this API's citations.
