"""
Style Agent: Checks code style and best practices
"""
import os
from typing import List
from openai import AsyncOpenAI
from app.schemas import ReviewComment


async def style_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for style and best practices
    
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
    
    system_prompt = """You are a code quality expert reviewing code changes for style and best practices.
Focus on:
- Code readability and clarity
- Naming conventions
- Code duplication (DRY principle)
- Function/method length and complexity
- Missing documentation or comments
- Inconsistent formatting
- SOLID principles violations
- Design patterns misuse
- Error handling patterns
- Testing best practices

Be constructive and focus on significant issues, not nitpicks.

Provide specific, actionable feedback. For each issue found, specify:
- The file and approximate line number
- The severity (high, medium, low)
- A clear description of the style/practice concern
- A suggested improvement

Format your response as JSON array with objects containing: file, line, severity, message, suggestion"""

    user_prompt = f"""Review this code diff for style issues and best practices:

{diff}

{f"Context: {context}" if context else ""}

Return a JSON array of style/practice issues found. If no issues, return an empty array [].

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no code blocks."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4
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
                agent="style",
                severity=issue.get('severity', 'low'),
                file=issue.get('file', 'unknown'),
                line=issue.get('line'),
                message=issue.get('message', ''),
                suggestion=issue.get('suggestion')
            ))
        
        return comments
        
    except Exception as e:
        print(f"Style agent error: {str(e)}")
        return []
