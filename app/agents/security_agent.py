"""
Security Agent: Identifies security vulnerabilities and risks
"""
import os
from typing import List
from openai import AsyncOpenAI
from app.schemas import ReviewComment


async def security_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for security vulnerabilities
    
    Args:
        diff: Code diff to analyze
        context: Additional context about the changes
        
    Returns:
        List of review comments
    """
    client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    
    system_prompt = """You are a security expert reviewing code changes for vulnerabilities.
Focus on:
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) risks
- Authentication and authorization issues
- Insecure data storage or transmission
- Hardcoded credentials or secrets
- Input validation issues
- CSRF vulnerabilities
- Insecure deserialization
- Path traversal issues
- Cryptographic weaknesses

Prioritize actual security vulnerabilities over theoretical concerns.

Provide specific, actionable feedback. For each issue found, specify:
- The file and approximate line number
- The severity (high, medium, low)
- A clear description of the security risk
- A suggested mitigation

Format your response as JSON array with objects containing: file, line, severity, message, suggestion"""

    user_prompt = f"""Review this code diff for security vulnerabilities:

{diff}

{f"Context: {context}" if context else ""}

Return a JSON array of security issues found. If no issues, return an empty array []."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
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
                agent="security",
                severity=issue.get('severity', 'high'),
                file=issue.get('file', 'unknown'),
                line=issue.get('line'),
                message=issue.get('message', ''),
                suggestion=issue.get('suggestion')
            ))
        
        return comments
        
    except Exception as e:
        print(f"Security agent error: {str(e)}")
        return []
