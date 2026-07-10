# MCP transport for the Municipal Law Skill

A thin [MCP](https://modelcontextprotocol.io/) server wrapping the same public HTTP contract documented in the root [SKILL.md](../SKILL.md) - six tools (`is_action_allowed`, `search_municipal_law`, `get_section`, `get_related_sections`, `find_penalties`, `find_permits`), each a direct call to the deployed REST API. It reimplements no retrieval/action-evaluation logic; it exists so an MCP-native client (Claude Desktop, Claude Code, etc.) can reach this skill without going through raw HTTP.

Local-only, like [`local_agent/`](../local_agent/README.md): not part of the deployed FastAPI app, excluded from the Vercel deployment via [`.vercelignore`](../.vercelignore).

## Install

```bash
pip install -r mcp_server/requirements.txt
```

## Run

```bash
python -m mcp_server.server
```

Runs over stdio, pointed at the live deployment (`https://nanda-municipal-laws.vercel.app`) by default. Override with `MCP_API_BASE_URL` (in the environment or a `.env.mcp` file) to point at a local dev server instead:

```bash
echo "MCP_API_BASE_URL=http://localhost:8000" > .env.mcp
```

## Connect an MCP client

```bash
claude mcp add municipal-law -- python -m mcp_server.server
```

Or, generic MCP client config:

```jsonc
{
  "mcpServers": {
    "municipal-law": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/nanda-municipal-laws"
    }
  }
}
```

## Tests

```bash
python -m pytest mcp_server/tests -v
```

Exercises the real MCP tool functions against the real FastAPI app + retrieval logic, with the shared `ApiClient` pointed at an in-process `TestClient` (see [`mcp_server/tests/conftest.py`](tests/conftest.py)) instead of the network - no live deployment, no live Mongo, same pattern as `local_agent/tests`.
