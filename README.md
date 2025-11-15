# PR Review Agent

Backend service that performs automated code reviews using a multi-agent AI system.

## Features

- **Multi-Agent Review System**: Specialized agents for different aspects:

  - **Logic Agent**: Reviews code logic, correctness, and potential bugs
  - **Security Agent**: Identifies security vulnerabilities and risks
  - **Performance Agent**: Analyzes performance implications
  - **Style Agent**: Checks code style and best practices

- **Flexible Input**: Accept GitHub PR URLs or raw diffs
- **Structured Output**: Returns JSON-formatted review comments suitable for GitHub API

## Setup

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   Create a `.env` file in the root directory:

   ```
   OPEN_ROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_MODEL=deepseek/deepseek-chat-v3.1:free  # Optional, defaults to DeepSeek V3.1 (FREE)
   GITHUB_TOKEN=your_github_token_here  # Optional, for fetching PRs
   ```

3. **Run the server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Usage

### Review a GitHub PR

```bash
curl -X POST http://localhost:8000/review/pr \
  -H "Content-Type: application/json" \
  -d '{
    "pr_url": "https://github.com/owner/repo/pull/123"
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Response Format

```json
{
  "status": "success",
  "review": {
    "summary": "Overall review summary",
    "comments": [
      {
        "agent": "security",
        "severity": "high",
        "file": "app/auth.py",
        "line": 42,
        "message": "Potential SQL injection vulnerability",
        "suggestion": "Use parameterized queries instead"
      }
    ],
    "stats": {
      "total_comments": 5,
      "by_severity": {
        "high": 1,
        "medium": 2,
        "low": 2
      }
    }
  }
}
```

## Architecture

- **FastAPI**: HTTP API framework
- **Multi-Agent Orchestration**: Independent specialist agents run in parallel
- **OpenRouter + DeepSeek Integration**: Uses DeepSeek V3.1 (FREE, 671B parameters) for intelligent code analysis
- **Extensible Design**: Easy to add new agents or customize existing ones

## Environment Variables

- `OPEN_ROUTER_API_KEY` (required): Your OpenRouter API key
- `OPENROUTER_MODEL` (optional): Model to use (default: deepseek/deepseek-chat-v3.1:free)
- `GITHUB_TOKEN` GitHub personal access token for fetching PRs
- `MAX_DIFF_SIZE` (optional): Maximum diff size in characters (default: 100000)



