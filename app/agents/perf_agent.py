"""
Performance Agent: Analyzes performance implications
"""
import os
from typing import List
from openai import AsyncOpenAI
from app.schemas import ReviewComment


async def perf_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for performance issues
    
    Args:
        diff: Code diff to analyze
        context: Additional context about the changes
        
    Returns:
        List of review comments
    """
    # Use OpenRouter API with DeepSeek (OpenAI-compatible)
    client = AsyncOpenAI(
        api_key=os.getenv('OPEN_ROUTER_API_KEY'),
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/pr-review-agent",
            "X-Title": "PR Review Agent"
        }
    )
    model = os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3.1:free')
    
    system_prompt = """You are a performance optimization expert reviewing code changes.
Focus on:
- Inefficient algorithms (O(n²) when O(n) is possible)
- Unnecessary database queries (N+1 queries)
- Memory leaks or excessive memory usage
- Blocking operations that could be async
- Unnecessary loops or iterations
- Inefficient data structures
- Missing caching opportunities
- Heavy computations in hot paths
- Redundant API calls

Focus on significant performance issues, not micro-optimizations.

Provide specific, actionable feedback. For each issue found, specify:
- The file and approximate line number
- The severity (high, medium, low)
- A clear description of the performance concern
- A suggested optimization

Format your response as JSON array with objects containing: file, line, severity, message, suggestion"""

    user_prompt = f"""Review this code diff for performance issues:

{diff}

{f"Context: {context}" if context else ""}

Return a JSON array of performance issues found. If no issues, return an empty array [].

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no code blocks."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # Parse the response - handle markdown code blocks if present
        import json
        import re
        
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```'):
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        
        result = json.loads(content)
        
        # Handle different response formats
        issues = result if isinstance(result, list) else result.get('issues', [])
        
        comments = []
        for issue in issues:
            comments.append(ReviewComment(
                agent="performance",
                severity=issue.get('severity', 'medium'),
                file=issue.get('file', 'unknown'),
                line=issue.get('line'),
                message=issue.get('message', ''),
                suggestion=issue.get('suggestion')
            ))
        
        return comments
        
    except Exception as e:
        print(f"Performance agent error: {str(e)}")
        return []
