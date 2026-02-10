# Herd MCP Server

Model Context Protocol server for Herd operational tracking and team coordination.

## Setup

### 1. Install Dependencies

```bash
cd .herd/mcp
pip install -e .
```

### 2. Seed the Database

Run the seed script to populate agent definitions and model pricing:

```bash
python3 scripts/seed_db.py
```

This will create `.herd/herd.duckdb` with all agent and model definitions.

### 3. Configure MCP in Agent .mcp.json

Add the Herd MCP server to your Claude Code `.mcp.json` file:

```json
{
  "mcpServers": {
    "herd": {
      "command": "python3",
      "args": ["-m", "herd_mcp"],
      "env": {
        "HERD_AGENT_NAME": "grunt",
        "HERD_DB_PATH": ".herd/herd.duckdb"
      }
    }
  }
}
```

**Important**: Set `HERD_AGENT_NAME` to your agent's code:
- `mini-mao` - Scrum Master
- `grunt` - Backend Developer
- `pikasso` - Frontend Developer
- `wardenstein` - QA Engineer
- `shakesquill` - Technical Writer

### 4. Restart Claude Code

After adding the MCP server configuration, restart Claude Code to load the tools.

## Available Tools

- `herd_log` - Post messages to Slack and log activity
- `herd_status` - Get current status of agents, sprint, and blockers
- `herd_spawn` - Spawn new agent instances
- `herd_assign` - Assign tickets to agents
- `herd_transition` - Transition ticket status
- `herd_review` - Submit code reviews
- `herd_metrics` - Query operational metrics
- `herd_catchup` - Get summary of recent activity
- `herd_decommission` - Permanently decommission an agent
- `herd_standdown` - Temporarily stand down an agent

## Identity Resolution

The MCP server uses the `HERD_AGENT_NAME` environment variable to determine which agent is making requests. This maps to:

1. **agent_code** in `agent_def` table
2. **agent_instance_code** in `agent_instance` table (created on first use)

If no active instance exists, the server automatically creates one when tools are first called.

## Database Schema

The database has 23 tables tracking:
- **Entity Definitions**: initiatives, projects, agents, models, sprints, tickets
- **Versioned Content**: craft, personality, skillset versions
- **Instance Tracking**: agent instances with their configurations
- **Activity Ledgers**: lifecycle, ticket, PR, review, and token activity

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
ruff check src/ tests/
black --check src/ tests/
```

## Permissions

The MCP server requires:
- **Read/Write** access to `.herd/herd.duckdb`
- **Network** access to Slack API (for `herd_log` tool)
- **Environment** variable `HERD_AGENT_NAME` set

## Troubleshooting

**Tools not appearing in Claude Code:**
1. Check `.mcp.json` syntax is valid JSON
2. Verify `python3 -m herd_mcp` runs without errors
3. Check Claude Code logs for MCP server errors
4. Restart Claude Code

**Identity not resolving:**
1. Ensure `HERD_AGENT_NAME` is set in `.mcp.json`
2. Run `python3 scripts/seed_db.py` to ensure agent definitions exist
3. Check that agent_code matches your HERD_AGENT_NAME exactly

**Database errors:**
1. Ensure `.herd/` directory exists
2. Run `python3 scripts/seed_db.py` to initialize schema
3. Check file permissions on `.herd/herd.duckdb`
