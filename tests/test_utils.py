"""
Tests for utility functions
"""
import pytest
from app.utils import parse_unified_diff, chunk_diff, extract_added_lines, is_code_file

def test_parse_unified_diff():
    diff = """diff --git a/app/main.py b/app/main.py
index 1234567..890abcd 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,5 +1,6 @@
 import os
-from fastapi import FastAPI
+from fastapi import FastAPI, Request
+from slowapi import Limiter
 
 app = FastAPI()
"""
    hunks = parse_unified_diff(diff)
    assert len(hunks) == 1
    assert hunks[0].file_path == "app/main.py"
    assert hunks[0].old_start == 1
    assert hunks[0].new_start == 1
    assert "from slowapi import Limiter" in hunks[0].content

def test_chunk_diff_small():
    diff = "small diff"
    chunks = chunk_diff(diff, max_chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == "small diff"

def test_is_code_file():
    assert is_code_file("test.py") is True
    assert is_code_file("test.js") is True
    assert is_code_file("test.txt") is False
    assert is_code_file("image.png") is False
