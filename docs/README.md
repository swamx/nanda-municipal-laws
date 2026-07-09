# Documentation Index

Municipal Bylaws Knowledge API — built for the MIT Hackathon. A lightweight FastAPI service that indexes real NYC Administrative Code text in MongoDB and exposes keyword search + document/chunk retrieval, for consumption by the `municipal-bylaws-skill` Claude Agent Skill (or any other agent/chatbot).

- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design, data model, and the key design decisions (and constraints) behind them
- [API.md](./API.md) — full endpoint reference with curl examples and sample responses
- [DEPLOYMENT.md](./DEPLOYMENT.md) — MongoDB Atlas + Vercel free-tier deployment steps, environment variables, prod-readiness notes
- [DATA_SOURCE.md](./DATA_SOURCE.md) — where the bylaw text comes from, its license, current coverage, and how to extend it

See the repo root [README.md](../README.md) for a quick-start (install, seed, run, test) and the root [SKILL.md](../SKILL.md) for the agent-facing API reference in hackathon-submission format.
