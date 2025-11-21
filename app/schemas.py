"""
Pydantic schemas for request/response validation
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl


class PRReviewRequest(BaseModel):
    """Request to review a GitHub PR"""
    pr_url: str = Field(..., description="GitHub PR URL (e.g., https://github.com/RHL-RWT-01/civicsync-be/pull/13)")


class ReviewComment(BaseModel):
    """A single review comment from an agent"""
    agent: str = Field(..., description="Agent that generated this comment (logic, security, perf, style)")
    severity: str = Field(..., description="Severity level: high, medium, low")
    file: str = Field(..., description="File path where the issue was found")
    line: Optional[int] = Field(None, description="Line number where the issue occurs")
    message: str = Field(..., description="Description of the issue")
    suggestion: Optional[str] = Field(None, description="Suggested fix or improvement")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")


class ReviewStats(BaseModel):
    """Statistics about the review"""
    total_comments: int
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_agent: Dict[str, int] = Field(default_factory=dict)


class ReviewResult(BaseModel):
    """Complete review result"""
    summary: str = Field(..., description="Overall review summary")
    comments: List[ReviewComment] = Field(default_factory=list)
    stats: ReviewStats
    errors: List[str] = Field(default_factory=list, description="List of errors encountered during review")


class ReviewResponse(BaseModel):
    """API response for review requests"""
    status: str = Field(..., description="Status of the review (success, error)")
    review: Optional[ReviewResult] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "1.0.0"
