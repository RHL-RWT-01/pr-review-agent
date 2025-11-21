"""
Style Agent: Checks code style and best practices
"""
from typing import List
from app.schemas import ReviewComment
from app.agents.base import run_agent
from app.prompts import STYLE_SYSTEM_PROMPT, get_user_prompt


async def style_agent(diff: str, context: str = "") -> List[ReviewComment]:
    """
    Analyze code changes for style and best practices
    """
    user_prompt = get_user_prompt(diff, context, "style issues and best practices")
    
    return await run_agent(
        agent_name="style",
        system_prompt=STYLE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,
        default_severity="low"
    )
