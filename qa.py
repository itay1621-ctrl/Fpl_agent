import re

with open('App.py', encoding='utf-8') as f:
    content = f.read()

print('--- HTML Tag Balance ---')
div_open = len(re.findall(r'<div\b[^>]*>', content))
div_close = len(re.findall(r'</div\s*>', content))
span_open = len(re.findall(r'<span\b[^>]*>', content))
span_close = len(re.findall(r'</span\s*>', content))
print(f'div: {div_open} open, {div_close} close')
print(f'span: {span_open} open, {span_close} close')

print('\n--- CSS Braces Balance ---')
css_blocks = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
for i, css in enumerate(css_blocks):
    open_b = css.count('{')
    close_b = css.count('}')
    print(f'Block {i}: {open_b} open, {close_b} close')

print('\n--- Translation Checks ---')
# Extract keys manually
try:
    en_part = content.split('"en": {')[1].split('}')[0]
    he_part = content.split('"he": {')[1].split('}')[0]
    en_keys = re.findall(r'"([a-zA-Z0-9_]+)":', en_part)
    he_keys = re.findall(r'"([a-zA-Z0-9_]+)":', he_part)
    print(f'Missing in Hebrew: {set(en_keys) - set(he_keys)}')
    print(f'Missing in English: {set(he_keys) - set(en_keys)}')
except Exception as e:
    print('Failed to parse translations:', e)
