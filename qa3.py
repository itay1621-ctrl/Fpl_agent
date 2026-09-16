import re

with open('App.py', encoding='utf-8') as f:
    content = f.read()

css = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)[0]
lines = css.split('\n')

stack = []
for i, line in enumerate(lines):
    for char in line:
        if char == '{':
            stack.append(i + 1)
        elif char == '}':
            if stack:
                stack.pop()
            else:
                print(f"Extra closing brace at line {i+1}")

if stack:
    print(f"Unclosed braces opened at lines: {stack}")
