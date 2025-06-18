#!/usr/bin/env python3

# Fix the quotes to be properly escaped for Python syntax
with open('scripts/report_generator.py', 'rb') as f:
    content = f.read()

print("Before fix:")
line = content.splitlines()[431]
print(repr(line))

# Replace unescaped quotes with properly escaped quotes
content = content.replace(b"'Segoe UI'", b"\\'Segoe UI\\'")

print("After fix:")
line = content.splitlines()[431] 
print(repr(line))

with open('scripts/report_generator.py', 'wb') as f:
    f.write(content)

print("Fixed quotes to be properly escaped") 