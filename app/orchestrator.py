"""
Multi-agent orchestration: runs specialist agents and aggregates results
"""
import asyncio
from typing import List
from app.schemas import ReviewComment, ReviewResult, ReviewStats
from app.agents import logic_agent, security_agent, perf_agent, style_agent
from app.utils import chunk_diff


async def orchestrate_review(diff: str, context: str = "") -> ReviewResult:
    """
    Orchestrate the multi-agent review process
    
    Args:
        diff: Code diff to review
        context: Additional context about the changes
        
    Returns:
        Aggregated review results from all agents
    """
    # Check if diff is too large and needs chunking
    max_diff_size = 15000  # Characters per agent
    chunks = chunk_diff(diff, max_diff_size) if len(diff) > max_diff_size else [diff]
    
    all_comments = []
    
    # Process each chunk
    for chunk in chunks:
        # Run all agents in parallel for this chunk
        results = await asyncio.gather(
            logic_agent(chunk, context),
            security_agent(chunk, context),
            perf_agent(chunk, context),
            style_agent(chunk, context),
            return_exceptions=True
        )
        
        # Collect comments, handling any exceptions
        for result in results:
            if isinstance(result, Exception):
                print(f"Agent error: {str(result)}")
                continue
            all_comments.extend(result)
    
    # Deduplicate similar comments
    unique_comments = _deduplicate_comments(all_comments)
    
    # Sort by severity and file
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    unique_comments.sort(key=lambda c: (severity_order.get(c.severity, 3), c.file, c.line or 0))
    
    # Generate statistics
    stats = _calculate_stats(unique_comments)
    
    # Generate summary
    summary = _generate_summary(unique_comments, stats)
    
    return ReviewResult(
        summary=summary,
        comments=unique_comments,
        stats=stats
    )


def _deduplicate_comments(comments: List[ReviewComment]) -> List[ReviewComment]:
    """
    Remove duplicate or very similar comments
    
    Args:
        comments: List of review comments
        
    Returns:
        Deduplicated list of comments
    """
    unique = []
    seen = set()
    
    for comment in comments:
        # Create a key based on file, line, and message similarity
        key = (comment.file, comment.line, comment.message[:100])
        
        if key not in seen:
            seen.add(key)
            unique.append(comment)
    
    return unique


def _calculate_stats(comments: List[ReviewComment]) -> ReviewStats:
    """
    Calculate statistics about the review
    
    Args:
        comments: List of review comments
        
    Returns:
        Review statistics
    """
    by_severity = {}
    by_agent = {}
    
    for comment in comments:
        # Count by severity
        by_severity[comment.severity] = by_severity.get(comment.severity, 0) + 1
        
        # Count by agent
        by_agent[comment.agent] = by_agent.get(comment.agent, 0) + 1
    
    return ReviewStats(
        total_comments=len(comments),
        by_severity=by_severity,
        by_agent=by_agent
    )


def _generate_summary(comments: List[ReviewComment], stats: ReviewStats) -> str:
    """
    Generate a human-readable summary of the review
    
    Args:
        comments: List of review comments
        stats: Review statistics
        
    Returns:
        Summary text
    """
    if not comments:
        return "Code review complete. No significant issues found."
    
    high_count = stats.by_severity.get('high', 0)
    medium_count = stats.by_severity.get('medium', 0)
    low_count = stats.by_severity.get('low', 0)
    
    summary_parts = [
        f"Code review complete. Found {stats.total_comments} issue(s):"
    ]
    
    if high_count > 0:
        summary_parts.append(f"  {high_count} high severity")
    if medium_count > 0:
        summary_parts.append(f"  {medium_count} medium severity")
    if low_count > 0:
        summary_parts.append(f"  {low_count} low severity")
    
    summary_parts.append("\nKey findings:")
    
    # Add top 3 high severity issues
    high_severity = [c for c in comments if c.severity == 'high'][:3]
    for comment in high_severity:
        summary_parts.append(f"  - [{comment.agent}] {comment.file}: {comment.message[:80]}...")
    
    return "\n".join(summary_parts)


async def review_diff(diff: str, context: str = "") -> ReviewResult:
    """
    Main entry point for reviewing a diff
    
    Args:
        diff: Code diff to review
        context: Additional context
        
    Returns:
        Review result
    """
    return await orchestrate_review(diff, context)
