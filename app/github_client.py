"""
GitHub client for fetching PR diffs
"""
import re
import os
from typing import Optional, Tuple
import httpx
from github import Github, GithubException


class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client
        
        Args:
            token: GitHub personal access token (optional, for higher rate limits)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.github = Github(self.token) if self.token else Github()
        
    def parse_pr_url(self, pr_url: str) -> Tuple[str, str, int]:
        """
        Parse GitHub PR URL into components
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            Tuple of (owner, repo, pr_number)
            
        Raises:
            ValueError: If URL format is invalid
        """
        # Match: https://github.com/owner/repo/pull/123
        pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
        match = re.match(pattern, pr_url)
        
        if not match:
            raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
        
        owner, repo, pr_number = match.groups()
        return owner, repo, int(pr_number)
    
    async def fetch_pr_diff(self, pr_url: str) -> str:
        """
        Fetch the unified diff for a GitHub PR
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            Raw unified diff content
            
        Raises:
            ValueError: If PR URL is invalid
            Exception: If API request fails
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        try:
            # Use PyGithub to get PR
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull_request = repository.get_pull(pr_number)
            
            # Fetch diff using httpx (PyGithub doesn't provide direct diff access)
            diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            headers = {
                "Accept": "application/vnd.github.v3.diff"
            }
            
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(diff_url, headers=headers, timeout=30.0)
                response.raise_for_status()
                
            return response.text
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error fetching PR diff: {str(e)}")
    
    async def fetch_pr_metadata(self, pr_url: str) -> dict:
        """
        Fetch metadata about a PR
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            Dictionary with PR metadata
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            
            return {
                "title": pr.title,
                "description": pr.body or "",
                "author": pr.user.login,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "commits": pr.commits,
                "changed_files": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions,
            }
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    def close(self):
        """Close the GitHub client"""
        if self.github:
            self.github.close()
