"""
Performance Agent: Analyzes performance implications
"""
from typing import List
from app.schemas import ReviewComment
from app.agents.base import run_agent
from app.prompts import PERF_SYSTEM_PROMPT, get_user_prompt


async def perf_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for performance issues
    """
    user_prompt = get_user_prompt(diff, context, "performance issues")
    
    return await run_agent(
        agent_name="performance",
        system_prompt=PERF_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        default_severity="medium"
    )
