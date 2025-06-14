#!/usr/bin/env python3
"""
Simple wrapper script to convert documentation from MD to HTML.
Run this whenever you update the SPR_QS_METHODOLOGY.md file.
"""

import subprocess
import sys
import os

def main():
    """Run the documentation converter."""
    print("Converting documentation from MD to HTML...")
    
    try:
        # Run the conversion script
        result = subprocess.run([
            sys.executable, 
            "scripts/doc_converter.py"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        # Print the output
        print(result.stdout)
        
        if result.returncode == 0:
            print("Documentation conversion completed successfully!")
        else:
            print("Documentation conversion failed:")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running conversion: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 