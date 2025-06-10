#!/usr/bin/env python3
"""
Enhanced file merger for LLM consumption with improved context effectiveness.

Key improvements for LLM effectiveness:
• Hierarchical file organization with clear structure
• File type detection and syntax highlighting hints
• Dependency analysis and logical ordering
• Content quality metrics and filtering
• Enhanced metadata for better LLM understanding
• Token estimation and optimization
• Smart truncation for large files

Usage:
    python merge_for_llm.py -f src tests --priority-files main.py app.py -o context.txt
"""
import os
import argparse
import pathlib
import itertools
import re
import mimetypes
from datetime import datetime, timezone
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set

# Configuration
EXCLUDE_DIRS = {
    "node_modules", "venv", ".venv", "__pycache__", ".git", ".idea",
    ".vscode", "dist", "build", ".DS_Store", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", "htmlcov", "logs", "tmp", "temp"
}

EXCLUDE_FILES = {
    ".gitignore", ".env.local", "*.log", "*.tmp", "*.pyc",
    "package-lock.json", "yarn.lock", "poetry.lock", "*.svg", "*.png",
    "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.ico", "*.css",
    "LICENSE", "COPYING", "CHANGELOG.md", "CONTRIBUTING.md",

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

class FileAnalyzer:
    """Analyzes files for better LLM context organization."""
    
    def __init__(self):
        self.import_graph = defaultdict(set)
        self.file_metrics = {}
    
    def analyze_file(self, filepath: str) -> Dict:
        """Analyze a single file for metadata and dependencies."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {'error': str(e), 'lines': 0, 'bytes': 0, 'imports': []}
        
        lines = content.count('\n') + 1
        bytes_size = len(content.encode('utf-8'))
        
        # Detect file type and language
        ext = os.path.splitext(filepath)[1].lower()
        file_type = FILE_TYPES.get(ext, 'text')
        
        # Extract imports/dependencies
        imports = self._extract_imports(content, file_type)
        
        # Calculate complexity metrics
        complexity = self._calculate_complexity(content, file_type)
        
        # Estimate tokens (rough approximation)
        estimated_tokens = len(content.split()) * 1.3  # Rough estimate
        
        return {
            'lines': lines,
            'bytes': bytes_size,
            'file_type': file_type,
            'imports': imports,
            'complexity': complexity,
            'estimated_tokens': int(estimated_tokens),
            'is_config': self._is_config_file(filepath),
            'is_test': self._is_test_file(filepath),
            'priority_score': self._calculate_priority(filepath)
        }
    
    def _extract_imports(self, content: str, file_type: str) -> List[str]:
        """Extract import statements based on file type."""
        imports = []
        
        if file_type == 'python':
            # Python imports
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
        elif file_type in ['javascript', 'typescript', 'jsx', 'tsx']:
            # JS/TS imports
            import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
            imports.extend(re.findall(import_pattern, content))
        elif file_type == 'java':
            # Java imports
            import_pattern = r'import\s+([^;]+);'
            imports.extend(re.findall(import_pattern, content))
        
        return imports[:10]  # Limit to first 10 imports
    
    def _calculate_complexity(self, content: str, file_type: str) -> int:
        """Calculate rough complexity score."""
        if file_type == 'python':
            # Count functions, classes, and control structures
            complexity = (
                content.count('def ') +
                content.count('class ') * 2 +
                content.count('if ') +
                content.count('for ') +
                content.count('while ') +
                content.count('try:')
            )
        else:
            # Generic complexity based on brackets and keywords
            complexity = (
                content.count('{') +
                content.count('function') +
                content.count('class') +
                content.count('if(') +
                content.count('for(') +
                content.count('while(')
            )
        
        return min(complexity, 100)  # Cap at 100
    
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
    other_files = []
    
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
    core_files.sort(key=lambda x: (x[1]['complexity'], x[0]), reverse=True)
    test_files.sort(key=lambda x: x[0])
    
    # Combine in logical order
    return entry_points + config_files + core_files + test_files

def generate_enhanced_header(file_data: List[Tuple[str, Dict]], header_fmt: str) -> str:
    """Generate enhanced header with project analysis and clear LLM instructions."""
    
    total_files = len(file_data)
    total_lines = sum(data['lines'] for _, data in file_data)
    total_tokens = sum(data.get('estimated_tokens', 0) for _, data in file_data)
    
    # Language distribution
    languages = Counter(data['file_type'] for _, data in file_data)
    main_language = languages.most_common(1)[0][0] if languages else 'unknown'
    
    # Project type detection
    has_setup_py = any('setup.py' in fp for fp, _ in file_data)
    has_package_json = any('package.json' in fp for fp, _ in file_data)
    has_requirements = any('requirements' in fp for fp, _ in file_data)
    
    project_type = 'unknown'
    if has_setup_py or has_requirements:
        project_type = 'python'
    elif has_package_json:
        project_type = 'nodejs'
    
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace('+00:00', 'Z')
    
    llm_instructions = f"""
############################  LLM_CONTEXT_DIRECTIVE  ############################
## COMPREHENSIVE CODEBASE  – MERGED, AUTHORITATIVE SOURCE OF TRUTH
##
##  Project      : {project_type}
##  Language     : {main_language}
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
  3. Core implementation (simple ➜ complex)  
  4. Tests & fixtures  

───────────────────────── HARD RULES (NON-NEGOTIABLE) ─────────────────────────
1. **Wrapper integrity** – Never delete, reorder, or nest the `<<< FILE … >>>` /
   `<<< END FILE >>>` markers. Everything between a pair = that file, full stop.

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

6. **Scope of edits**  
   • Work exclusively on the most recent version of each file.  
   • Limit explanations, summaries, or patches to that scope.

7. **Patch discipline**  
   • Wrap **every** delivered patch in the same `<<< FILE … >>>` wrappers.  
   • If providing explanations only, avoid altering code blocks.

──────────────────────────────── END OF RULES ────────────────────────────────
"""

    return llm_instructions

def is_excluded(path: str) -> bool:
    """Check if path should be excluded."""
    parts = path.split(os.sep)
    return any(part in EXCLUDE_DIRS for part in parts)

def should_exclude_file(filepath: str) -> bool:
    """Check if specific file should be excluded."""
    filename = os.path.basename(filepath)
    return any(
        filename == pattern or 
        (pattern.startswith('*.') and filename.endswith(pattern[1:]))
        for pattern in EXCLUDE_FILES
    )

def gather_files_enhanced(paths: List[str], extensions: Optional[List[str]] = None,
                         max_file_size: int = 1024*1024,  # 1MB default
                         priority_files: Optional[List[str]] = None) -> List[str]:
    """Enhanced file gathering with size limits and priority handling."""
    
    collected = []
    priority_set = set(priority_files or [])
    
    for p in paths:
        if os.path.isfile(p):
            if not is_excluded(p) and not should_exclude_file(p):
                if not extensions or any(p.endswith(ext) for ext in extensions):
                    # Check file size unless it's a priority file
                    if p in priority_set or os.path.getsize(p) <= max_file_size:
                        collected.append(os.path.abspath(p))
                    else:
                        print(f"⚠️  Skipping large file: {p} ({os.path.getsize(p)} bytes)")
        
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for fname in files:
                    fp = os.path.join(root, fname)
                    if not is_excluded(fp) and not should_exclude_file(fp):
                        if not extensions or any(fp.endswith(ext) for ext in extensions):
                            if fp in priority_set or os.path.getsize(fp) <= max_file_size:
                                collected.append(os.path.abspath(fp))
                            else:
                                print(f"⚠️  Skipping large file: {fp} ({os.path.getsize(fp)} bytes)")
    
    # Deduplicate keeping last occurrence
    seen, deduped = set(), []
    for fp in reversed(collected):
        if fp not in seen:
            seen.add(fp)
            deduped.append(fp)
    
    return list(reversed(deduped))

def truncate_large_content(content: str, max_lines: int = 500) -> Tuple[str, bool]:
    """Smart truncation of large files with context preservation."""
    lines = content.split('\n')
    if len(lines) <= max_lines:
        return content, False
    
    # Keep beginning and end, skip middle
    keep_start = max_lines // 2
    keep_end = max_lines // 2
    
    truncated_lines = (
        lines[:keep_start] +
        [f"\n... [TRUNCATED: {len(lines) - max_lines} lines omitted for brevity] ...\n"] +
        lines[-keep_end:]
    )
    
    return '\n'.join(truncated_lines), True

def write_enhanced_output(file_data: List[Tuple[str, Dict]], output_path: str,
                         header_fmt: str, line_numbers: bool = False,
                         max_lines_per_file: int = 1000, include_toc: bool = True) -> Dict:
    """Write enhanced output with metadata and smart formatting."""
    
    header = generate_enhanced_header(file_data, header_fmt)
    total_files = len(file_data)
    total_lines_written = 0
    total_truncated = 0
    
    with open(output_path, 'w', encoding='utf-8') as out:
        # Write header
        out.write(header + "\n\n")
        
        # Write enhanced table of contents (optional)
        if include_toc:
            out.write("### PROJECT STRUCTURE & ANALYSIS\n")
            out.write("IDX │ FILE PATH                                                │ TYPE       │ LINES │ TOKENS │ COMPLEXITY │ PRIORITY\n")
            out.write("────┼──────────────────────────────────────────────────────────┼────────────┼───────┼────────┼────────────┼─────────\n")
            
            for i, (filepath, metadata) in enumerate(file_data, 1):
                rel_path = os.path.relpath(filepath, start=os.getcwd())
                file_type = metadata.get('file_type', 'unknown')
                lines = metadata.get('lines', 0)
                tokens = metadata.get('estimated_tokens', 0)
                complexity = metadata.get('complexity', 0)
                priority = metadata.get('priority_score', 0)
                
                out.write(f"{i:3d} │ {rel_path[:56].ljust(56)} │ {file_type[:10].ljust(10)} │ {lines:5d} │ {tokens:6d} │ {complexity:10d} │ {priority:7d}\n")
            
            out.write("\n")
        else:
            out.write("# Table of Contents omitted to save context space\n\n")
        
        # Write file contents
        for filepath, metadata in file_data:
            rel_path = os.path.relpath(filepath, start=os.getcwd())
            file_type = metadata.get('file_type', 'text')
            
            # Enhanced file header with metadata
            out.write(f"<<< FILE: {rel_path} >>>\n")
            out.write(f"# Metadata: type={file_type}, lines={metadata.get('lines', 0)}, "
                     f"complexity={metadata.get('complexity', 0)}, "
                     f"tokens≈{metadata.get('estimated_tokens', 0)}\n")
            
            if metadata.get('imports'):
                out.write(f"# Key imports: {', '.join(metadata['imports'][:3])}\n")
            
            out.write(f"# {'─' * 60}\n")
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Smart truncation for very large files
                content, was_truncated = truncate_large_content(content, max_lines_per_file)
                if was_truncated:
                    total_truncated += 1
                
                if line_numbers:
                    for line_num, line in enumerate(content.split('\n'), 1):
                        out.write(f"{line_num:4d}: {line}\n")
                        total_lines_written += 1
                else:
                    out.write(content)
                    total_lines_written += content.count('\n')
                
                if not content.endswith('\n'):
                    out.write('\n')
                    
            except Exception as e:
                out.write(f"# ERROR: Could not read file - {e}\n")
            
            out.write("<<< END FILE >>>\n\n")
        
        # Enhanced end marker
        out.write("<<< END OF MERGED CONTEXT >>>\n")
        out.write(f"# Summary: {total_files} files processed, {total_truncated} truncated\n")
    
    return {
        'files_processed': total_files,
        'lines_written': total_lines_written,
        'files_truncated': total_truncated,
        'output_size': os.path.getsize(output_path)
    }

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced file merger for optimal LLM consumption",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python merge_for_llm.py -f src/ --priority-files main.py app.py
  python merge_for_llm.py -f . --ext .py .js --max-size 500000 -o context.txt
  python merge_for_llm.py -f backend frontend --header yaml --max-lines 800
        """
    )
    
    parser.add_argument("-f", "--files", nargs="+", required=True,
                       help="Files or directories to include")
    parser.add_argument("-o", "--output", default="llm_context.txt",
                       help="Output file (default: llm_context.txt)")
    parser.add_argument("--ext", nargs="*",
                       help="File extensions to include (e.g., .py .js)")
    parser.add_argument("--priority-files", nargs="*",
                       help="Files to include regardless of size limits")
    parser.add_argument("--max-size", type=int, default=1024*1024,
                       help="Max file size in bytes (default: 1MB)")
    parser.add_argument("--max-lines", type=int, default=1000,
                       help="Max lines per file before truncation (default: 1000)")
    parser.add_argument("--line-numbers", action="store_true",
                       help="Add line numbers to files")
    parser.add_argument("--include-toc", action="store_true", default=True,
                       help="Include table of contents (default: True)")
    parser.add_argument("--no-toc", dest="include_toc", action="store_false",
                       help="Skip table of contents to save context space")
    parser.add_argument("--header", choices=["plain", "yaml", "json"], default="plain",
                       help="Header format (default: plain)")
    
    args = parser.parse_args()
    
    print("🔍 Analyzing project structure...")
    
    # Gather files with enhanced filtering
    files = gather_files_enhanced(
        args.files, 
        args.ext,
        args.max_size,
        args.priority_files
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
    file_data = smart_file_ordering(file_data)
    
    print("📝 Writing enhanced context file...")
    
    # Write output
    stats = write_enhanced_output(
        file_data,
        args.output,
        args.header,
        args.line_numbers,
        args.max_lines,
        args.include_toc
    )
    
    # Summary
    print("\n" + "="*50)
    print("✅ ENHANCED MERGE COMPLETE")
    print("="*50)
    print(f"📊 Files processed    : {stats['files_processed']}")
    print(f"📝 Lines written      : {stats['lines_written']:,}")
    print(f"✂️  Files truncated    : {stats['files_truncated']}")
    print(f"💾 Output size       : {stats['output_size']:,} bytes")
    print(f"🎯 Output file       : {args.output}")
    print("\n🤖 Ready for LLM analysis with enhanced context!")

if __name__ == "__main__":
    main()