#!/usr/bin/env python3
"""
Simplified file merger for LLM consumption with essential features.

Key features:
• Hierarchical file organization with clear structure
• File type detection and syntax highlighting hints
• Enhanced metadata for better LLM understanding
• Token estimation and optimization
• Smart truncation for large files
• Space removal options for compactness

Usage:
    python merge_for_llm.py -f src tests --priority-files main.py app.py -o context.txt
"""
import os
import argparse
import pathlib
import re
from datetime import datetime, timezone
from collections import Counter
from typing import List, Dict, Tuple, Optional, Set
import fnmatch  # Add this line


IGNORE_FILES_TO_PARSE = [".gitignore", ".dockerignore", ".gcloudignore", ".containerignore"]

# Configuration
EXCLUDE_DIRS = {
    "node_modules", "venv", ".venv", "__pycache__", ".git", ".idea",
    ".vscode", "dist", "build", ".DS_Store", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", "htmlcov", "logs", "tmp", "temp"
}

# Fine-grained glob patterns (directory-level or deep wildcard)
EXCLUDE_GLOBS = {
    # ShadCN component dump
    "components/ui/**",           # project-root variant
    "**/components/ui/**",        # nested (monorepo / packages / apps/*)

    # Build / dist / caches
    "dist/**", "build/**", ".next/**", ".turbo/**", ".parcel-cache/**",
    "node_modules/**", "vendor/**", ".aws-sam/**", ".serverless/**",
    "__pycache__/**", ".pytest_cache/**", ".mypy_cache/**", ".tox/**",
    ".cache/**", "htmlcov/**", ".nyc_output/**", ".jest/**",

    # Version control internals
    ".git/**", ".hg/**", ".svn/**",
}

EXCLUDE_FILES = {
    "llm_context.txt",  # Special case for output file

    # ── Common config / environment ────────────────────────────────────────────
    ".env.local", ".env.*", ".DS_Store",
    ".gitignore", ".gitattributes", ".editorconfig",
    ".eslint*", ".prettier*",
    ".idea/*",            # JetBrains IDEs
    ".vscode/*",          # VS Code
    ".vs/*",              # Visual Studio
    ".gradle/*",          # Gradle caches

    # ── Logs / temporary / swap / cache ───────────────────────────────────────
    "*.log", "*.tmp", "*.temp", "*.bak",
    "*.swp", "*.swo",                # Vim swap
    "*.pid",
    "*.pyc", "*.pyo",                # Python byte-code
    "*.class",                       # Java/Kotlin byte-code
    "*.db",
    ".cache/*", ".pytest_cache/*", ".mypy_cache/*", ".tox/*",
    ".nyc_output/*", ".jest/*",
    "npm-debug.log*", "yarn-debug.log*", "yarn-error.log*", "pnpm-debug.log*",

    # ── Lock files ────────────────────────────────────────────────────────────
    "pnpm-lock.yaml", "package-lock.json", "yarn.lock",
    "poetry.lock", "Pipfile.lock", "composer.lock",
    "Gemfile.lock", "Cargo.lock",

    # ── Static / binary assets ────────────────────────────────────────────────
    "*.svg", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp",
    "*.ico", "*.bmp", "*.tiff",
    "*.mp4", "*.mp3", "*.wav", "*.ogg",
    "*.woff", "*.woff2", "*.ttf", "*.eot",

    # ── Documentation / metadata ──────────────────────────────────────────────
    "LICENSE", "COPYING",
    "CHANGELOG*", "CONTRIBUTING*", "SECURITY*", "CODEOWNERS",
    "*.md", "*.rst",

    # ── Build / dist artefacts ────────────────────────────────────────────────
    "dist/*", "build/*", "out/*", "coverage/*", "htmlcov/*",
    "target/*", "__pycache__/*",
    ".next/*", ".turbo/*", ".parcel-cache/*",
    "node_modules/*", "vendor/*",
    ".aws-sam/*", ".serverless/*",

    # ── Generated data & archives ─────────────────────────────────────────────
    "*.min.js", "*.map", "*.stats.json", "*.lockb",
    "*.egg", "*.egg-info", ".eggs/*", "*.whl",
    "*.exe", "*.dll", "*.so", "*.dylib",
    "*.a", "*.o", "*.obj",
    "*.jar", "*.war", "*.ear",
    "*.zip", "*.tar", "*.tar.gz", "*.tgz", "*.7z", "*.gz", "*.rar",

    # ── Test snapshots / fixtures ─────────────────────────────────────────────
    "__snapshots__/*", "fixtures/*", "tests/__output__/*",

    # ── Version-control internals ─────────────────────────────────────────────
    ".git/*", ".hg/*", ".svn/*",
}

# File type mappings for better LLM understanding
FILE_TYPES = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.jsx': 'jsx',
    '.tsx': 'tsx', '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.h': 'c',
    '.hpp': 'cpp', '.cs': 'csharp', '.go': 'go', '.rs': 'rust',
    '.rb': 'ruby', '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
    '.scala': 'scala', '.r': 'r', '.m': 'matlab', '.sh': 'bash',
    '.sql': 'sql', '.html': 'html', '.css': 'css', '.scss': 'scss',
    '.sass': 'sass', '.xml': 'xml', '.json': 'json', '.yaml': 'yaml',
    '.yml': 'yaml', '.toml': 'toml', '.ini': 'ini', '.cfg': 'config',
    '.md': 'markdown', '.rst': 'restructuredtext', '.txt': 'text',
    '.dockerfile': 'dockerfile', '.makefile': 'makefile', '.cmake': 'cmake'
}

PRIORITY_PATTERNS = [
    r'main\.(py|js|ts|java|cpp|c)$',
    r'app\.(py|js|ts)$',
    r'index\.(js|ts|html)$',
    r'__init__\.py$',
    r'setup\.(py|cfg)$',
    r'requirements\.txt$',
    r'package\.json$',
    r'pyproject\.toml$',
    r'README\.(md|rst|txt)$',
    r'config\.(py|js|ts|json|yaml|yml)$'
]



def find_ignore_files_recursively(search_paths: List[str]) -> List[str]:
    """Find all ignore files recursively in the given paths."""
    found_ignore_files = []
    
    for search_path in search_paths:
        if os.path.isfile(search_path):
            # Single file - check its directory for ignore files
            search_dir = os.path.dirname(search_path)
        else:
            # Directory
            search_dir = search_path
            
        # Walk through directory recursively
        for root, dirs, files in os.walk(search_dir):
            # Skip excluded directories early
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for ignore_filename in IGNORE_FILES_TO_PARSE:
                ignore_path = os.path.join(root, ignore_filename)
                if os.path.isfile(ignore_path):
                    found_ignore_files.append(ignore_path)
                    
    return found_ignore_files

def parse_ignore_file(ignore_file_path: str) -> Tuple[Set[str], Set[str]]:
    """
    Parse an ignore file and return (directories_to_exclude, files_to_exclude).
    Returns patterns that should be added to EXCLUDE_DIRS and EXCLUDE_FILES.
    """
    dirs_to_exclude = set()
    files_to_exclude = set()
    negation_patterns_found = []
    
    try:
        with open(ignore_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"⚠️  Could not read {ignore_file_path}: {e}")
        return dirs_to_exclude, files_to_exclude
    
    for line in lines:
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
            
        # Track negation patterns for warning
        if line.startswith('!'):
            negation_patterns_found.append(line)
            continue
            
        # Remove trailing slashes for directory detection
        original_pattern = line
        clean_pattern = line.rstrip('/')
        
        # Determine if it's a directory pattern
        is_directory_pattern = (
            original_pattern.endswith('/') or 
            '/' not in clean_pattern or
            clean_pattern in ['node_modules', 'dist', 'build', '__pycache__', '.git', 'venv', '.venv']
        )
        
        if is_directory_pattern:
            # Add to directory exclusions
            if '/' in clean_pattern:
                # Complex path - add the deepest directory
                dirs_to_exclude.add(os.path.basename(clean_pattern))
            else:
                # Simple directory name
                dirs_to_exclude.add(clean_pattern)
        else:
            # Add to file exclusions
            if '*' in clean_pattern or '?' in clean_pattern:
                # Wildcard pattern
                files_to_exclude.add(clean_pattern)
            elif '/' in clean_pattern:
                # Path-based pattern - add the filename
                files_to_exclude.add(os.path.basename(clean_pattern))
            else:
                # Simple filename
                files_to_exclude.add(clean_pattern)
    
    # Warn about negation patterns if found
    if negation_patterns_found:
        print(f"   ⚠️  Note: {len(negation_patterns_found)} negation patterns (!pattern) found but not supported yet")
    
    return dirs_to_exclude, files_to_exclude

def update_exclusions_from_ignore_files(search_paths: List[str]) -> Tuple[Set[str], Set[str]]:
    """
    Find and parse all ignore files, returning additional exclusions.
    Returns (additional_exclude_dirs, additional_exclude_files).
    """
    print("🔍 Searching for ignore files...")
    
    ignore_files = find_ignore_files_recursively(search_paths)
    
    if not ignore_files:
        print("📝 No ignore files found")
        return set(), set()
    
    print(f"📋 Found {len(ignore_files)} ignore files:")
    
    additional_exclude_dirs = set()
    additional_exclude_files = set()
    
    for ignore_file in ignore_files:
        rel_path = os.path.relpath(ignore_file, os.getcwd())
        print(f"   📄 {rel_path}")
        
        dirs, files = parse_ignore_file(ignore_file)
        additional_exclude_dirs.update(dirs)
        additional_exclude_files.update(files)
    
    print(f"✅ Parsed ignore files:")
    print(f"   🗂️  Additional directories to exclude: {len(additional_exclude_dirs)}")
    print(f"   📄 Additional files to exclude: {len(additional_exclude_files)}")
    
    if additional_exclude_dirs:
        print(f"   📁 Directory patterns: {', '.join(sorted(list(additional_exclude_dirs)[:10]))}")
        if len(additional_exclude_dirs) > 10:
            print(f"      ... and {len(additional_exclude_dirs) - 10} more")
    
    if additional_exclude_files:
        print(f"   📄 File patterns: {', '.join(sorted(list(additional_exclude_files)[:10]))}")
        if len(additional_exclude_files) > 10:
            print(f"      ... and {len(additional_exclude_files) - 10} more")
    
    return additional_exclude_dirs, additional_exclude_files


class FileAnalyzer:
    """Analyzes files for better LLM context organization."""
    
    def __init__(self):
        self.file_metrics = {}
    
    def analyze_file(self, filepath: str) -> Dict:
        """Analyze a single file for metadata."""
        try:
            # Check if file is likely binary
            if self._is_binary_file(filepath):
                return {'error': 'Binary file', 'lines': 0, 'bytes': 0}
            
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            return {'error': str(e), 'lines': 0, 'bytes': 0}
        
        lines = content.count('\n') + 1
        # Estimate tokens (rough approximation)
        estimated_tokens = len(content.split()) * 1.3  # Rough estimate
        
        return {
            'lines': lines,
            'estimated_tokens': int(estimated_tokens),
            'is_config': self._is_config_file(filepath),
            'is_test': self._is_test_file(filepath),
            'priority_score': self._calculate_priority(filepath)
        }
    
    def _is_binary_file(self, filepath: str) -> bool:
        """Check if file is likely binary."""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return False
    
    def _is_config_file(self, filepath: str) -> bool:
        """Check if file is a configuration file."""
        config_patterns = [
            r'config', r'settings', r'\.env', r'\.ini', r'\.cfg',
            r'\.toml', r'\.yaml', r'\.yml', r'\.json'
        ]
        filename = os.path.basename(filepath).lower()
        return any(re.search(pattern, filename) for pattern in config_patterns)
    
    def _is_test_file(self, filepath: str) -> bool:
        """Check if file is a test file."""
        test_patterns = [r'test_', r'_test\.', r'/tests?/', r'spec\.']
        return any(re.search(pattern, filepath.lower()) for pattern in test_patterns)
    
    def _calculate_priority(self, filepath: str) -> int:
        """Calculate priority score for file ordering."""
        filename = os.path.basename(filepath).lower()
        score = 0
        
        for i, pattern in enumerate(PRIORITY_PATTERNS):
            if re.search(pattern, filename, re.IGNORECASE):
                score += (len(PRIORITY_PATTERNS) - i) * 10
        
        # Boost for certain directories
        if '/src/' in filepath or '/lib/' in filepath:
            score += 5
        if '/test' in filepath:
            score -= 5  # Lower priority for tests
        
        return score

def smart_file_ordering(file_data: List[Tuple[str, Dict]]) -> List[Tuple[str, Dict]]:
    """Order files intelligently for better LLM understanding."""
    
    # Separate into categories
    config_files = []
    entry_points = []
    core_files = []
    test_files = []
    
    for filepath, metadata in file_data:
        if metadata.get('is_config'):
            config_files.append((filepath, metadata))
        elif metadata.get('priority_score', 0) > 20:
            entry_points.append((filepath, metadata))
        elif metadata.get('is_test'):
            test_files.append((filepath, metadata))
        else:
            core_files.append((filepath, metadata))
    
    # Sort each category
    entry_points.sort(key=lambda x: x[1]['priority_score'], reverse=True)
    config_files.sort(key=lambda x: os.path.basename(x[0]))
    core_files.sort(key=lambda x: x[0])  # Simple alphabetical sort
    test_files.sort(key=lambda x: x[0])
    
    # Combine in logical order
    return entry_points + config_files + core_files + test_files


def generate_enhanced_header(file_data: List[Tuple[str, Dict]], header_fmt: str) -> str:
    """Generate enhanced header with project analysis and clear LLM instructions."""
    
    total_files = len(file_data)
    total_tokens = sum(data.get('estimated_tokens', 0) for _, data in file_data)
    

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace('+00:00', 'Z')
    
    llm_instructions = f"""
############################  LLM_CONTEXT_DIRECTIVE  ############################
## COMPREHENSIVE CODEBASE  – MERGED, AUTHORITATIVE SOURCE OF TRUTH
##  Files        : {total_files}
##  Tokens (≈)   : {total_tokens:,}
##  Generated    : {timestamp}
###############################################################################

You are reading the **one-true, merged code drop** for this project.  
Assume nothing exists outside this file.
━━━━━━━━━━━━━━━━ FILE DELIMITERS ━━━━━━━━━━━━━━━━  
    <<< FILE: path/to/file.ext >>>    …    <<< END FILE >>>
━━━━━━━━━━━━━━━━ FILE ORDER ━━━━━━━━━━━━━━━━  
1. Entry points  
2. Configuration / env  
3. Core implementation (alphabetical)
4. Tests & fixtures  
───────────────────────── HARD RULES (NON-NEGOTIABLE) ─────────────────────────
1. Wrapper integrity – Never delete, nest, or reorder the <<< FILE … >>> /
    <<< END FILE >>> markers. Everything between one pair is that file.
2. **Duplicate filenames** – If a path occurs multiple times, **KEEP ONLY** the
    final occurrence; earlier versions are obsolete and must be ignored.  
    • **Special case:** `llm_context.txt` is itself one of the wrapped files.
    If it appears more than once, **use only the last instance**.
3. **Source-bounded reasoning** – Do **not** hallucinate or invent code.  
    If it is not inside the wrappers, it does not exist.
4. **Quoting & citing** – When referring to code, always name the *exact* file
    path (line numbers optional but helpful).
5. **No structural drift** – Do **not** rename, split, or shuffle files unless
    explicitly told. Preserve imports, comments, and formatting verbatim when
    copying snippets.
6. Scope of edits – Work exclusively on the most recent version of each file.
7. Patch delivery
    • For every edited file, return the entire updated file, wrapped as shown below.
    • Snippets or diffs are not allowed.
    • Explanations alone must not alter code blocks.
    Language-specific wrappers
    ─────────────
    // <<< FILE: path/to/file.ext >>>    …    <<< END FILE >>> (JS, TS, Java, C#, C++, etc.)
    ### <<< FILE: path/to/file.ext >>>    …    <<< END FILE >>>  (Python, etc.)
    <!-- <<< FILE: path/to/file.ext >>>    …    <<< END FILE >>> --> (HTML, etc.)
    /* <<< FILE: path/to/file.ext >>>    …    <<< END FILE >>> */ (CSS / SCSS, etc.)
    -- <<< FILE: path/to/file.ext >>>    …    <<< END FILE >>> -- (SQL, etc.)
    ─────────────
8. Context preservation – If content is omitted for brevity, indicate it with:
    ... [TRUNCATED: X lines] ...
9. Always use Canvas for code blocks, and ensure that the code is formatted
    correctly with proper syntax highlighting for the file type.

──────────────────────────────── END OF RULES ────────────────────────────────
"""

    return llm_instructions

def normalize_path(path: str) -> pathlib.Path:
    """Normalize path for consistent handling."""
    return pathlib.Path(path).resolve()

def get_file_size_safe(filepath: str) -> int:
    """Get file size safely, returning 0 on error."""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

def deduplicate_files(files: List[str]) -> List[str]:
    """Deduplicate files, keeping the last occurrence of each."""
    seen, deduped = set(), []
    for fp in reversed(files):
        abs_path = str(normalize_path(fp))
        if abs_path not in seen:
            seen.add(abs_path)
            deduped.append(fp)
    return list(reversed(deduped))

def is_excluded(path: str) -> bool:
    """
    True if any path segment matches EXCLUDE_DIRS
    OR the path matches any pattern in EXCLUDE_GLOBS.
    """
    p = pathlib.Path(path)
    path_str = str(p).replace('\\', '/')
    
    # Check directory exclusions
    if any(part in EXCLUDE_DIRS for part in p.parts):
        return True
    
    # Check glob patterns with proper matching
    for pattern in EXCLUDE_GLOBS:
        # Convert glob pattern to work with fnmatch
        if '**' in pattern:
            # Handle recursive patterns like "components/ui/**"
            base_pattern = pattern.replace('/**', '').replace('**/', '')
            if base_pattern in path_str:
                return True
        else:
            # Use fnmatch for simpler patterns
            if fnmatch.fnmatch(path_str, pattern):
                return True
    
    return False

def should_exclude_file(filepath: str) -> bool:
    """
    True if filename matches any literal or pattern in EXCLUDE_FILES.
    """
    p = pathlib.Path(filepath)
    fname = p.name
    
    for pattern in EXCLUDE_FILES:
        if pattern.startswith('*') and pattern.endswith('*'):
            # Contains pattern
            if pattern[1:-1] in fname:
                return True
        elif pattern.startswith('*'):
            # Ends with pattern
            if fname.endswith(pattern[1:]):
                return True
        elif pattern.endswith('*'):
            # Starts with pattern
            if fname.startswith(pattern[:-1]):
                return True
        elif pattern.endswith('/*'):
            # Directory pattern
            if pattern[:-2] in str(p.parent):
                return True
        else:
            # Exact match
            if fname == pattern:
                return True
    
    return False

def gather_files_enhanced(paths: List[str], extensions: Optional[List[str]] = None,
                         max_file_size: int = 1024*1024,  # 1MB default
                         priority_files: Optional[List[str]] = None,
                         output_file: Optional[str] = None,
                         respect_ignore_files: bool = True) -> List[str]:
    """Enhanced file gathering with ignore file support."""
    
    # Get additional exclusions from ignore files
    additional_exclude_dirs = set()
    additional_exclude_files = set()
    
    if respect_ignore_files:
        additional_exclude_dirs, additional_exclude_files = update_exclusions_from_ignore_files(paths)
    
    # Combine with existing exclusions
    combined_exclude_dirs = EXCLUDE_DIRS.union(additional_exclude_dirs)
    combined_exclude_files = EXCLUDE_FILES.union(additional_exclude_files)
    
    collected = []
    priority_set = set(str(normalize_path(pf)) for pf in (priority_files or []))
    
    # Convert output file to absolute path for comparison
    output_abs = str(normalize_path(output_file)) if output_file else None
    
    def should_exclude_file_enhanced(filepath: str) -> bool:
        """Enhanced file exclusion check using combined patterns."""
        p = pathlib.Path(filepath)
        fname = p.name
        
        for pattern in combined_exclude_files:
            if pattern.startswith('*') and pattern.endswith('*'):
                # Contains pattern
                if pattern[1:-1] in fname:
                    return True
            elif pattern.startswith('*'):
                # Ends with pattern
                if fname.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                # Starts with pattern
                if fname.startswith(pattern[:-1]):
                    return True
            elif pattern.endswith('/*'):
                # Directory pattern
                if pattern[:-2] in str(p.parent):
                    return True
            else:
                # Exact match or wildcard
                if fnmatch.fnmatch(fname, pattern) or fname == pattern:
                    return True
        
        return False
    
    def is_excluded_enhanced(path: str) -> bool:
        """Enhanced directory exclusion check using combined patterns."""
        p = pathlib.Path(path)
        path_str = str(p).replace('\\', '/')
        
        # Check directory exclusions
        if any(part in combined_exclude_dirs for part in p.parts):
            return True
        
        # Check glob patterns (simplified)
        for pattern in EXCLUDE_GLOBS:
            if pattern.endswith('/**'):
                dir_pattern = pattern[:-3]
                if dir_pattern in path_str:
                    return True
        
        return False
    
    for p in paths:
        if os.path.isfile(p):
            abs_path = str(normalize_path(p))
            
            # Skip if this is the output file itself
            if output_abs and abs_path == output_abs:
                print(f"⚠️  Skipping output file: {p}")
                continue
                
            if not is_excluded_enhanced(p) and not should_exclude_file_enhanced(p):
                if not extensions or any(p.endswith(ext) for ext in extensions):
                    file_size = get_file_size_safe(p)
                    
                    # Check file size unless it's a priority file
                    if abs_path in priority_set or file_size <= max_file_size:
                        collected.append(abs_path)
                    else:
                        print(f"⚠️  Skipping large file: {p} ({file_size} bytes)")
        
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                # Filter directories using enhanced exclusions
                dirs[:] = [d for d in dirs if d not in combined_exclude_dirs]
                
                for fname in files:
                    fp = os.path.join(root, fname)
                    abs_path = str(normalize_path(fp))
                    
                    # Skip if this is the output file itself
                    if output_abs and abs_path == output_abs:
                        continue
                        
                    if not is_excluded_enhanced(fp) and not should_exclude_file_enhanced(fp):
                        if not extensions or any(fp.endswith(ext) for ext in extensions):
                            file_size = get_file_size_safe(fp)
                            
                            if abs_path in priority_set or file_size <= max_file_size:
                                collected.append(abs_path)
                            else:
                                print(f"⚠️  Skipping large file: {fp} ({file_size} bytes)")
    
    # Deduplicate files
    return deduplicate_files(collected)

def truncate_large_content_streaming(filepath: str, max_lines: int = 500) -> Tuple[str, bool]:
    """Smart truncation of large files with streaming to avoid memory issues."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = []
            line_count = 0
            
            # Read up to max_lines to check if truncation is needed
            for line in f:
                lines.append(line.rstrip('\n'))
                line_count += 1
                if line_count > max_lines:
                    break
            
            if line_count <= max_lines:
                return '\n'.join(lines), False
            
            # Need truncation - keep beginning and end
            keep_start = max_lines // 2
            keep_end = max_lines // 2
            
            # Read remaining lines to get the end
            remaining_lines = []
            for line in f:
                remaining_lines.append(line.rstrip('\n'))
                line_count += 1
            
            if len(remaining_lines) > keep_end:
                end_lines = remaining_lines[-keep_end:]
            else:
                end_lines = remaining_lines
            
            truncated_lines = (
                lines[:keep_start] +
                [f"... [TRUNCATED: {line_count - max_lines} lines omitted for brevity] ..."] +
                end_lines
            )
            
            return '\n'.join(truncated_lines), True
            
    except Exception as e:
        return f"# ERROR: Could not read file - {e}", False

def write_file_content(filepath: str, metadata: Dict, out_file, max_lines_per_file: int) -> Tuple[int, bool]:
    """Write a single file's content with metadata."""
    rel_path = os.path.relpath(filepath, start=os.getcwd())
    file_type = metadata.get('file_type', 'text')
    
    # Enhanced file header with metadata
    out_file.write(f"<<< FILE: {rel_path} >>>\n")
    out_file.write(f"# Metadata: type={file_type}, lines={metadata.get('lines', 0)}, "
                   f"tokens≈{metadata.get('estimated_tokens', 0)}\n")
    out_file.write(f"# {'─' * 60}\n")
    
    lines_written = 3  # Header lines
    was_truncated = False
    
    try:
        content, was_truncated = truncate_large_content_streaming(filepath, max_lines_per_file)
              
        out_file.write(content)
        lines_written += content.count('\n')
        
        if not content.endswith('\n'):
            out_file.write('\n')
            lines_written += 1
            
    except Exception as e:
        out_file.write(f"# ERROR: Could not read file - {e}\n")
        lines_written += 1
    
    out_file.write("<<< END FILE >>>\n\n")
    lines_written += 2
    
    return lines_written, was_truncated

def write_table_of_contents(file_data: List[Tuple[str, Dict]], out_file) -> int:
    """Write enhanced table of contents."""
    out_file.write("### PROJECT STRUCTURE & ANALYSIS\n")
    out_file.write("IDX │ FILE PATH                                                │ TYPE       │ LINES │ TOKENS │ PRIORITY\n")
    out_file.write("────┼──────────────────────────────────────────────────────────┼────────────┼───────┼────────┼─────────\n")
    
    lines_written = 3
    
    for i, (filepath, metadata) in enumerate(file_data, 1):
        rel_path = os.path.relpath(filepath, start=os.getcwd())
        file_type = metadata.get('file_type', 'unknown')
        lines = metadata.get('lines', 0)
        tokens = metadata.get('estimated_tokens', 0)
        priority = metadata.get('priority_score', 0)
        
        out_file.write(f"{i:3d} │ {rel_path[:56].ljust(56)} │ {file_type[:10].ljust(10)} │ {lines:5d} │ {tokens:6d} │ {priority:7d}\n")
        lines_written += 1
    
    out_file.write("\n")
    lines_written += 1
    
    return lines_written

def write_enhanced_output(file_data: List[Tuple[str, Dict]], output_path: str,
                         header_fmt: str,                          max_lines_per_file: int = 1000, include_toc: bool = True) -> Dict:
    """Write enhanced output with metadata and smart formatting."""
    
    header = generate_enhanced_header(file_data, header_fmt)
    total_files = len(file_data)
    total_lines_written = 0
    total_truncated = 0
    
    with open(output_path, 'w', encoding='utf-8') as out:
        # Write header
        out.write(header + "\n\n")
        total_lines_written += header.count('\n') + 2
        
        # Write enhanced table of contents (optional)
        if include_toc:
            toc_lines = write_table_of_contents(file_data, out)
            total_lines_written += toc_lines
        else:
            out.write("# Table of Contents omitted to save context space\n\n")
            total_lines_written += 2
        
        # Write file contents
        for filepath, metadata in file_data:
            file_lines, was_truncated = write_file_content(
                filepath, metadata, out,  max_lines_per_file
            )
            total_lines_written += file_lines
            if was_truncated:
                total_truncated += 1
        
        # Enhanced end marker
        out.write("<<< END OF MERGED CONTEXT >>>\n")
        out.write(f"# Summary: {total_files} files processed, {total_truncated} truncated\n")
        total_lines_written += 2
    
    return {
        'files_processed': total_files,
        'lines_written': total_lines_written,
        'files_truncated': total_truncated,
        'output_size': get_file_size_safe(output_path)
    }

def main():
    parser = argparse.ArgumentParser(
        description="Simplified file merger for optimal LLM consumption",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python merge_for_llm.py -f src/ --priority-files main.py app.py
  python merge_for_llm.py -f . --ext .py .js --max-size 500000
  python merge_for_llm.py -f src/ --remove-spaces conservative
  python merge_for_llm.py -f . --remove-spaces aggressive --no-toc
        """
    )
    
    parser.add_argument('-f', '--folders', nargs='+', required=True,
                        help='Folders and files to process')
    parser.add_argument('--ext', '--extensions', nargs='+',
                        help='File extensions to include (default: all text files)')
    parser.add_argument('--priority-files', nargs='+',
                        help='Files to prioritize regardless of size limits')
    parser.add_argument('--max-size', type=int, default=1024*1024,
                        help='Maximum file size in bytes (default: 1MB)')
    parser.add_argument('--max-lines', type=int, default=1000,
                        help='Maximum lines per file before truncation (default: 1000)')
    parser.add_argument('--no-toc', action='store_true',
                        help='Skip table of contents to save space')
    parser.add_argument('--no-ignore', action='store_true',
                    help='Skip parsing ignore files (.gitignore, .dockerignore, etc.)')
    
    args = parser.parse_args()
    OUTPUT_FILE = "llm_context.txt"
    print("🔄 Gathering files...")
    files = gather_files_enhanced(
        args.folders,
        extensions=args.ext,
        max_file_size=args.max_size,
        priority_files=args.priority_files,
        output_file=OUTPUT_FILE,  # Pass output file to avoid circular reference
        respect_ignore_files=not args.no_ignore  # Add this line
    )
    
    if not files:
        print("⛔ No files found matching criteria")
        return
    
    print(f"📁 Found {len(files)} files, analyzing...")
    
    # Analyze files
    analyzer = FileAnalyzer()
    file_data = []
    
    for filepath in files:
        metadata = analyzer.analyze_file(filepath)
        file_data.append((filepath, metadata))
    
    # Smart ordering
    # file_data = smart_file_ordering(file_data)
    
    print("📝 Writing enhanced context file...")
    
    # Write output - fix the missing arguments
    stats = write_enhanced_output(
        file_data,
        OUTPUT_FILE,
        "enhanced",  # header_fmt - fixed missing argument
        args.max_lines,
        not args.no_toc,  # include_toc - fixed missing argument (invert no_toc)
    )
    
    # Summary
    print("\n" + "="*50)
    print("✅ ENHANCED MERGE COMPLETE")
    print("="*50)
    print(f"📊 Files processed    : {stats['files_processed']}")
    print(f"📝 Lines written      : {stats['lines_written']:,}")
    print(f"✂️  Files truncated    : {stats['files_truncated']}")
    print(f"💾 Output size       : {stats['output_size']:,} bytes")
    print(f"🎯 Output file       : {OUTPUT_FILE}")
    print("\n🤖 Ready for LLM analysis with enhanced context!")

if __name__ == "__main__":
    main()