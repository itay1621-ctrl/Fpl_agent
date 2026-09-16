import re

with open('App.py', encoding='utf-8') as f:
    content = f.read()

css = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)[0]
lines = css.split('\n')
open_count = 0
for i, line in enumerate(lines):
    open_count += line.count('{')
    open_count -= line.count('}')
    if open_count < 0:
        print(f"Negative count at line {i+1}: {line}")
    # print(f"Line {i+1}, count: {open_count}")

print(f"Final count: {open_count}")

# Let's find where the count becomes 2 and stays 2 (or 1 instead of 0)
count = 0
for i, line in enumerate(lines):
    count += line.count('{')
    count -= line.count('}')
    if count > 1 and '@media' not in line and not line.strip().startswith('}'):
        # Usually count is 1 inside a block, 0 outside.
        # Inside media queries, it's 2 inside a block, 1 outside.
        pass

# Let's just print lines where count doesn't match expected block structure
in_media = False
current = 0
for i, line in enumerate(lines):
    if '@media' in line:
        in_media = True
    
    current += line.count('{')
    current -= line.count('}')
    
    if in_media and current == 0:
        in_media = False
        
    # print state
    if current > 2:
        print(f"Suspicious depth {current} at line {i+1}: {line.strip()}")
    if current == 2 and not in_media:
        print(f"Suspicious depth {current} outside media at line {i+1}: {line.strip()}")
