"""
Logic Agent: Reviews code logic, correctness, and potential bugs
"""
import os
from typing import List
from openai import AsyncOpenAI
from app.schemas import ReviewComment


async def logic_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for logical errors and potential bugs
    
    Args:
        diff: Code diff to analyze
        context: Additional context about the changes
        
    Returns:
        List of review comments
    """
    client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    
    system_prompt = """You are a senior software engineer reviewing code changes for logical correctness.
Focus on:
- Logic errors and potential bugs
- Edge cases not being handled
- Incorrect algorithms or data structures
- Off-by-one errors
- Null/undefined reference issues
- Race conditions or concurrency issues
- Incorrect assumptions

Provide specific, actionable feedback. For each issue found, specify:
- The file and approximate line number
- The severity (high, medium, low)
- A clear description of the problem
- A suggested fix

Format your response as JSON array with objects containing: file, line, severity, message, suggestion"""

    user_prompt = f"""Review this code diff for logical errors and bugs:

{diff}

{f"Context: {context}" if context else ""}

Return a JSON array of issues found. If no issues, return an empty array []."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        # Parse the response
        import json
        result = json.loads(content)
        
        # Handle different response formats
        issues = result if isinstance(result, list) else result.get('issues', [])
        
        comments = []
        for issue in issues:
            comments.append(ReviewComment(
                agent="logic",
                severity=issue.get('severity', 'medium'),
                file=issue.get('file', 'unknown'),
                line=issue.get('line'),
                message=issue.get('message', ''),
                suggestion=issue.get('suggestion')
            ))
        
        return comments
        
    except Exception as e:
        print(f"Logic agent error: {str(e)}")
        return []
