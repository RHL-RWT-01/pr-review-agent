"""
Utility functions for parsing diffs and chunking
"""
import re
from typing import List, Dict, Tuple, Optional


class DiffHunk:
    """Represents a single changed hunk in a diff"""
    def __init__(self, file_path: str, old_start: int, old_count: int, 
                 new_start: int, new_count: int, content: str):
        self.file_path = file_path
        self.old_start = old_start
        self.old_count = old_count
        self.new_start = new_start
        self.new_count = new_count
        self.content = content
        
    def __repr__(self):
        return f"DiffHunk({self.file_path}, lines {self.new_start}-{self.new_start + self.new_count})"


def parse_unified_diff(diff: str) -> List[DiffHunk]:
    """
    Parse a unified diff into structured hunks
    
    Args:
        diff: Raw unified diff string
        
    Returns:
        List of DiffHunk objects
    """
    hunks = []
    current_file = None
    
    lines = diff.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Match file headers (diff --git a/file b/file)
        if line.startswith('diff --git'):
            # Next lines should have --- and +++ with file paths
            i += 1
            continue
            
        # Match old file marker (--- a/file)
        if line.startswith('---'):
            i += 1
            continue
            
        # Match new file marker (+++ b/file)
        if line.startswith('+++'):
            match = re.match(r'\+\+\+ b/(.*)', line)
            if match:
                current_file = match.group(1)
            i += 1
            continue
            
        # Match hunk headers (@@ -old_start,old_count +new_start,new_count @@)
        if line.startswith('@@'):
            match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
            if match and current_file:
                old_start = int(match.group(1))
                old_count = int(match.group(2) or 1)
                new_start = int(match.group(3))
                new_count = int(match.group(4) or 1)
                
                # Collect hunk content
                hunk_lines = [line]
                i += 1
                while i < len(lines) and not lines[i].startswith('@@') and not lines[i].startswith('diff'):
                    hunk_lines.append(lines[i])
                    i += 1
                    
                hunk_content = '\n'.join(hunk_lines)
                hunks.append(DiffHunk(current_file, old_start, old_count, 
                                     new_start, new_count, hunk_content))
                continue
        
        i += 1
    
    return hunks


def chunk_diff(diff: str, max_chunk_size: int = 4000) -> List[str]:
    """
    Split a large diff into smaller chunks for processing
    
    Args:
        diff: Raw diff content
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of diff chunks
    """
    if len(diff) <= max_chunk_size:
        return [diff]
    
    hunks = parse_unified_diff(diff)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for hunk in hunks:
        hunk_str = f"File: {hunk.file_path}\n{hunk.content}\n\n"
        hunk_size = len(hunk_str)
        
        if current_size + hunk_size > max_chunk_size and current_chunk:
            # Start a new chunk
            chunks.append('\n'.join(current_chunk))
            current_chunk = [hunk_str]
            current_size = hunk_size
        else:
            current_chunk.append(hunk_str)
            current_size += hunk_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks


def extract_added_lines(diff: str) -> Dict[str, List[Tuple[int, str]]]:
    """
    Extract only the added lines from a diff
    
    Args:
        diff: Raw diff content
        
    Returns:
        Dictionary mapping file paths to list of (line_number, content) tuples
    """
    hunks = parse_unified_diff(diff)
    added_lines = {}
    
    for hunk in hunks:
        if hunk.file_path not in added_lines:
            added_lines[hunk.file_path] = []
        
        lines = hunk.content.split('\n')
        current_line = hunk.new_start
        
        for line in lines[1:]:  # Skip the @@ header
            if line.startswith('+') and not line.startswith('+++'):
                added_lines[hunk.file_path].append((current_line, line[1:]))
                current_line += 1
            elif not line.startswith('-'):
                current_line += 1
    
    return added_lines


def format_diff_for_display(diff: str, max_length: int = 500) -> str:
    """
    Format diff for readable display, truncating if necessary
    
    Args:
        diff: Raw diff content
        max_length: Maximum length to display
        
    Returns:
        Formatted diff string
    """
    if len(diff) <= max_length:
        return diff
    
    return diff[:max_length] + f"\n... (truncated, {len(diff)} total characters)"


def get_file_extension(file_path: str) -> Optional[str]:
    """Extract file extension from path"""
    if '.' in file_path:
        return file_path.rsplit('.', 1)[1].lower()
    return None


def is_code_file(file_path: str) -> bool:
    """Check if a file is a code file based on extension"""
    code_extensions = {
        'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'h', 'hpp',
        'cs', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala', 'sh',
        'sql', 'html', 'css', 'scss', 'sass', 'vue', 'svelte'
    }
    ext = get_file_extension(file_path)
    return ext in code_extensions if ext else False
