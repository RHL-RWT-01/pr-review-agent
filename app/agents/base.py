"""
Base agent functionality with retry logic and error handling.
"""
import os
import json
import re
import logging
from typing import List, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.schemas import ReviewComment

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((Exception)) # Retry on most exceptions including JSON parse errors
)
async def run_agent(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    default_severity: str = "medium"
) -> List[ReviewComment]:
    """
    Run a specialized agent with retries and error handling.
    """
    try:
        client = AsyncOpenAI(
            api_key=os.getenv('OPEN_ROUTER_API_KEY'),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/pr-review-agent",
                "X-Title": "PR Review Agent"
            }
        )
        model = os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3.1:free')
        
        logger.info(f"Running {agent_name} agent...")
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )
        
        content = response.choices[0].message.content
        
        # Clean up content (remove markdown)
        content = content.strip()
        if content.startswith('```'):
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
            
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for {agent_name}: {e}. Content: {content[:100]}...")
            raise e # Trigger retry
            
        # Handle different response formats
        issues = result if isinstance(result, list) else result.get('issues', [])
        
        comments = []
        for issue in issues:
            comments.append(ReviewComment(
                agent=agent_name,
                severity=issue.get('severity', default_severity),
                file=issue.get('file', 'unknown'),
                line=issue.get('line'),
                message=issue.get('message', ''),
                suggestion=issue.get('suggestion')
            ))
            
        return comments
        
    except Exception as e:
        logger.error(f"{agent_name} agent failed after retries: {str(e)}")
        raise e
