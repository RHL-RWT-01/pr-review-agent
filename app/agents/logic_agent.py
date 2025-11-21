"""
Logic Agent: Reviews code logic, correctness, and potential bugs
"""
from typing import List
from app.schemas import ReviewComment
from app.agents.base import run_agent
from app.prompts import LOGIC_SYSTEM_PROMPT, get_user_prompt


async def logic_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for logical errors and potential bugs
    """
    user_prompt = get_user_prompt(diff, context, "logical errors and bugs")
    
    return await run_agent(
        agent_name="logic",
        system_prompt=LOGIC_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        default_severity="medium"
    )
