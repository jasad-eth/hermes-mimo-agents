# 🤖 Hermes-MiMo Multi-Agent Workflow Engine

<p align="center">
  <strong>Multi-agent orchestration powered by Xiaomi MiMo LLM</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Xiaomi%20MiMo-v2.5-orange.svg" alt="MiMo v2.5">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
</p>

---

## Overview

Hermes-MiMo is a lightweight multi-agent orchestration framework that coordinates specialized AI agents through structured message passing, task decomposition, and intelligent routing — all running on **Xiaomi MiMo's high-performance inference API**.

Built for developers who want to compose complex AI workflows from modular, single-purpose agents.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Orchestrator                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Planner  │  │  Coder   │  │ Reviewer │  ...      │
│  │  Agent   │  │  Agent   │  │  Agent   │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│       └──────────────┼──────────────┘                │
│                      │                               │
│              ┌───────▼───────┐                       │
│              │  MiMo v2.5    │                       │
│              │  API Backend  │                       │
│              └───────────────┘                       │
└─────────────────────────────────────────────────────┘
```

## Key Features

- **🎯 Specialized Agents** — Coder, Reviewer, Researcher, Planner — each with optimized system prompts and temperature settings
- **🔄 5 Workflow Modes** — Sequential, Parallel, Pipeline, Debate, Hierarchical
- **🧠 Smart Task Routing** — Auto-routes tasks to the best-fit agent based on role matching
- **📊 Structured Results** — Every task produces a typed `TaskResult` with timing, artifacts, and metadata
- **🔁 Retry & Recovery** — Automatic retry with configurable max attempts
- **💬 Inter-Agent Communication** — Agents can send messages and share context
- **📈 Observable** — Event logging, stats tracking, and token usage monitoring

## Quick Start

```bash
# Clone
git clone https://github.com/jasad-eth/hermes-mimo-agents.git
cd hermes-mimo-agents

# Install
pip install -e .

# Set API key
export MIMO_API_KEY="your-xiaomi-mimo-api-key"

# Run demo
python examples/code_review_demo.py
```

## Usage

### Basic: Register Agents & Run Workflow

```python
import asyncio
from src.utils.mimo_client import MiMoClient
from src.core.orchestrator import Orchestrator
from src.agents import CoderAgent, ReviewerAgent, PlannerAgent

async def main():
    async with MiMoClient(api_key="your-key") as mimo:
        orch = Orchestrator(mimo_client=mimo)

        # Register specialized agents
        orch.register_agent(CoderAgent())
        orch.register_agent(ReviewerAgent())
        orch.register_agent(PlannerAgent())

        # Use pre-built workflows
        from src.workflows import code_review_workflow

        result = await code_review_workflow(
            orchestrator=orch,
            feature_description="Rate limiter with Redis-backed token bucket",
            language="python",
        )

        print(result["final_code"])

asyncio.run(main())
```

### Custom Workflow: Multi-Agent Debate

```python
# Agents debate a topic and converge on a conclusion
result = await orch.run_debate(
    topic="GraphQL vs REST for microservices?",
    agents=["coder", "reviewer", "researcher"],
    rounds=3,
)

print(result.summary)  # Synthesized conclusion
```

### Pipeline: Research → Plan → Build

```python
from src.workflows import research_and_build_workflow

result = await research_and_build_workflow(
    orchestrator=orch,
    goal="Build a real-time collaborative editor with CRDT",
    constraints="Must work offline, TypeScript, < 50KB bundle",
)
```

## Workflow Modes

| Mode | Use Case | How It Works |
|------|----------|--------------|
| **Sequential** | Linear tasks | Tasks run one by one, context passes forward |
| **Parallel** | Independent tasks | Tasks run concurrently, results aggregated |
| **Pipeline** | Multi-stage processing | Stage output feeds into next stage |
| **Debate** | Decision making | Multiple agents argue, then synthesize |
| **Hierarchical** | Complex projects | Lead agent delegates to specialists |

## Project Structure

```
hermes-mimo-agents/
├── src/
│   ├── core/
│   │   ├── orchestrator.py   # Brain: coordinates agents & workflows
│   │   ├── agent.py          # Agent: autonomous unit with LLM backbone
│   │   ├── task.py           # Task: unit of work with status tracking
│   │   └── message.py        # Message: inter-agent communication
│   ├── agents/
│   │   ├── coder.py          # Code generation & debugging
│   │   ├── reviewer.py       # Code review & security analysis
│   │   ├── researcher.py     # Technical research & analysis
│   │   └── planner.py        # Task decomposition & planning
│   ├── workflows/
│   │   ├── code_review_workflow.py
│   │   ├── feature_workflow.py
│   │   └── research_workflow.py
│   └── utils/
│       └── mimo_client.py    # Async MiMo API client
├── examples/
│   ├── code_review_demo.py
│   └── debate_demo.py
├── pyproject.toml
└── README.md
```

## AI Tools & Models Used

| Tool/Model | Purpose |
|------------|---------|
| **Xiaomi MiMo v2.5 Pro** | Primary LLM backbone for all agents |
| **Hermes Agent** | Development workflow orchestration |
| **Claude Code** | Code generation assistance |
| **Python 3.10+** | Runtime with async/await |
| **httpx** | Async HTTP client for MiMo API |

## Configuration

Agents are highly configurable:

```python
from src.core.agent import AgentConfig

custom_agent = AgentConfig(
    name="security-auditor",
    role="security specialist",
    system_prompt="You are a penetration tester...",
    model="MiMo-v2.5-pro",
    temperature=0.2,        # Lower = more deterministic
    max_tokens=4096,
    tools=["vulnerability_scanning", "code_analysis"],
)
```

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a PR

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ using <a href="https://mimo.xiaomi.com/">Xiaomi MiMo</a>
</p>
