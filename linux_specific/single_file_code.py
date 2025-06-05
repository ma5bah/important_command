#!/usr/bin/env python3

import os
import argparse

EXCLUDE_DIRS = {
    'node_modules', 'venv', '.venv', '__pycache__', '.git', '.idea', '.vscode', 'dist', 'build', ".DS_Store",
}

def is_excluded(path):
    for part in path.split(os.sep):
        if part in EXCLUDE_DIRS:
            return True
    return False

def gather_files(paths, extensions=None):
    files = []
    for path in paths:
        if os.path.isfile(path):
            if not is_excluded(path):
                if (not extensions) or any(path.endswith(ext) for ext in extensions):
                    files.append(os.path.abspath(path))
        elif os.path.isdir(path):
            for root, dirs, fs in os.walk(path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for file in fs:
                    full_path = os.path.join(root, file)
                    if not is_excluded(full_path):
                        if (not extensions) or any(full_path.endswith(ext) for ext in extensions):
                            files.append(os.path.abspath(full_path))
        else:
            print(f"⚠️ Skipping invalid path: {path}")
    return sorted(set(files))  # Remove duplicates and sort for deterministic order

def write_combined_file(file_list, output_file, add_line_numbers=False):
    total_lines = 0
    total_bytes = 0
    files_merged = 0

    with open(output_file, 'w', encoding='utf-8') as out:
        for file in file_list:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    rel_file = os.path.relpath(file, start=os.getcwd())
                    out.write(f"\n# ===== File Name: {rel_file} =====\n\n")
                    line_number = 1
                    for line in f:
                        if add_line_numbers:
                            out.write(f"{line_number}: {line}")
                            line_number += 1
                        else:
                            out.write(line)
                        total_lines += 1
                files_merged += 1
            except Exception as e:
                print(f"⚠️ Could not read '{file}': {e}")

    total_bytes = os.path.getsize(output_file)
    return files_merged, total_lines, total_bytes

def main():
    parser = argparse.ArgumentParser(
        description="Recursively merge files from given paths into a single file. Supports extension filter, line numbers, and prints summary."
    )
    parser.add_argument("-f", "--files", nargs="+", required=True, help="Files or directories to include recursively")
    parser.add_argument("-o", "--output", default="output.txt", help="Output file name (default: output.txt)")
    parser.add_argument("--ext", nargs="*", help="Only include files with these extensions (e.g. --ext .py .js)")
    parser.add_argument("--line-numbers", default=True, action="store_true", help="Add line numbers, restarting at 1 for each file")

    args = parser.parse_args()

    # Prepare extension filter (if any)
    extensions = args.ext if args.ext else None

    files_to_merge = gather_files(args.files, extensions)
    if not files_to_merge:
        print("⛔ No valid files to merge. Exiting.")
        exit(1)

    files_merged, total_lines, total_bytes = write_combined_file(
        files_to_merge, args.output, add_line_numbers=args.line_numbers
    )

    print(f"\n===== SUMMARY =====")
    print(f"Files merged : {files_merged}")
    print(f"Total lines  : {total_lines}")
    print(f"Total bytes  : {total_bytes}")
    print(f"Output file  : {args.output}")

if __name__ == "__main__":
    main()
