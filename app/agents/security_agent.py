"""
Security Agent: Identifies security vulnerabilities and risks
"""
from typing import List
from app.schemas import ReviewComment
from app.agents.base import run_agent
from app.prompts import SECURITY_SYSTEM_PROMPT, get_user_prompt


async def security_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for security vulnerabilities
    """
    user_prompt = get_user_prompt(diff, context, "security vulnerabilities")
    
    return await run_agent(
        agent_name="security",
        system_prompt=SECURITY_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        default_severity="high"
    )
