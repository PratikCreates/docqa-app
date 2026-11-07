#!/usr/bin/env python3
"""
Clean up the project by removing test, debug, and temporary files
"""
import os
import glob
from pathlib import Path

def cleanup_project():
    """Remove all test, debug, and temporary files"""
    
    # Files to remove (patterns)
    files_to_remove = [
        # Test files
        'test_*.py',
        'test_*.html',
        'test_*.js',
        'test_*.txt',
        'test_*.ipynb',
        'test-*.py',
        
        # Debug files
        'debug_*.py',
        'debug_*.html',
        
        # Temporary/development files
        'demo_*.py',
        'restart_*.py',
        'start_backend_*.py',
        'start_frontend.py',
        'start_services.py',
        'start_without_openai.py',
        'serve_docs.py',
        'fix_*.py',
        'setup_*.py',
        'verify_*.py',
        
        # Documentation files (keep main ones)
        '*_SUMMARY.md',
        '*_IMPLEMENTATION_*.md',
        '*_FIXES_*.md',
        'copy_test_instructions.md',
        'fix_copy_functionality.md',
        'LOCAL_SETUP.md',
        'github-setup.md',
        'PROJECT_STRUCTURE.md',
        'postgresql_setup_guide.md',
        'GCP_QUICKSTART.md',
        'DEPLOYMENT_SUMMARY.md',
        'SESSION_SUMMARY_*.md',
        'OCR_IMPLEMENTATION_SUMMARY.md',
        
        # Temporary HTML files
        'debug_copy_issue.html',
        'test_docs_link.html',
        'index.html',  # Keep only if it's not the main one
        
        # Temporary scripts
        'simple_copy_fix.js',
        'run_local.py',
        'ml_model.py',
        'research_paper.md',
        'restart_server.py',
        'UserSearch.tsx',
        
        # Setup files that are not needed
        'setup_database_docker.py',
        'setup_ocr.py',
        'setup-gcp.py',
        'ocr_requirements.txt',
        
        # Batch files (Windows specific, not cross-platform)
        '*.bat',
        '*.sh',
        
        # Performance files
        'model_performance.json',
        
        # Test directories content
        'test_ux.txt',
        'test_formatting.txt',
        'test_problems.txt',
    ]
    
    print("🧹 Cleaning up project files...")
    removed_count = 0
    
    for pattern in files_to_remove:
        for file_path in glob.glob(pattern):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"   Removed: {file_path}")
                    removed_count += 1
            except Exception as e:
                print(f"   Error removing {file_path}: {e}")
    
    # Remove specific files that don't match patterns
    specific_files = [
        '.env',  # Remove if it exists in root (should be in backend/)
        'init-db.sql',  # Database setup file
    ]
    
    for file_path in specific_files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"   Removed: {file_path}")
                removed_count += 1
        except Exception as e:
            print(f"   Error removing {file_path}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} files.")
    
    # Show remaining important files
    print("\n📁 Remaining core files:")
    important_files = [
        'README.md',
        'requirements.txt',
        'run_full_stack.py',
        'simple_frontend.html',
        'docker-compose.yml',
        '.gitignore',
        'CHANGELOG.md',
        'CONTRIBUTING.md',
        'setup.py'
    ]
    
    for file_path in important_files:
        if os.path.isfile(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")

if __name__ == "__main__":
    cleanup_project()