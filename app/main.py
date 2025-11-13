"""
FastAPI application and endpoints for PR review agent
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.schemas import (
    PRReviewRequest,
    DiffReviewRequest,
    ReviewResponse,
    HealthResponse
)
from app.github_client import GitHubClient
from app.orchestrator import review_diff


# Load environment variables
load_dotenv()

# Validate required environment variables
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("OPENAI_API_KEY environment variable is required")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    print("PR Review Agent starting up...")
    print(f"   Model: {os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')}")
    print(f"   GitHub Token: {'Set' if os.getenv('GITHUB_TOKEN') else 'Not set'}")
    
    yield
    
    # Shutdown
    print("PR Review Agent shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="PR Review Agent",
    description="AI-powered code review system with specialized agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "PR Review Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "review_pr": "/review/pr",
            "review_diff": "/review/diff"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/review/pr", response_model=ReviewResponse)
async def review_github_pr(request: PRReviewRequest):
    """
    Review a GitHub pull request
    
    Args:
        request: PR review request with GitHub PR URL
        
    Returns:
        Review results with comments from all agents
    """
    try:
        # Initialize GitHub client
        github_client = GitHubClient()
        
        # Fetch PR diff
        print(f"Fetching PR: {request.pr_url}")
        diff = await github_client.fetch_pr_diff(request.pr_url)
        
        # Check diff size
        max_diff_size = int(os.getenv('MAX_DIFF_SIZE', 100000))
        if len(diff) > max_diff_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"PR diff too large ({len(diff)} chars, max {max_diff_size})"
            )
        
        # Fetch PR metadata for context
        try:
            metadata = await github_client.fetch_pr_metadata(request.pr_url)
            context = f"PR: {metadata['title']}\nDescription: {metadata['description']}"
        except Exception as e:
            print(f"Could not fetch PR metadata: {e}")
            context = ""
        
        github_client.close()
        
        # Run review
        print(f"Running multi-agent review...")
        review_result = await review_diff(diff, context)
        
        print(f"Review complete: {review_result.stats.total_comments} comments")
        
        return ReviewResponse(
            status="success",
            review=review_result
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error reviewing PR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review PR: {str(e)}"
        )


@app.post("/review/diff", response_model=ReviewResponse)
async def review_raw_diff(request: DiffReviewRequest):
    """
    Review a raw diff
    
    Args:
        request: Diff review request with raw diff content
        
    Returns:
        Review results with comments from all agents
    """
    try:
        # Validate diff
        if not request.diff or not request.diff.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diff content is required"
            )
        
        # Check diff size
        max_diff_size = int(os.getenv('MAX_DIFF_SIZE', 100000))
        if len(request.diff) > max_diff_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Diff too large ({len(request.diff)} chars, max {max_diff_size})"
            )
        
        print(f"Running multi-agent review on raw diff...")
        
        # Run review
        review_result = await review_diff(request.diff, request.context or "")
        
        print(f"Review complete: {review_result.stats.total_comments} comments")
        
        return ReviewResponse(
            status="success",
            review=review_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reviewing diff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review diff: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
