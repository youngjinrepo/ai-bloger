import json

with open('output/2849385212/content_raw.json', 'rb') as f:
    data = json.load(f)

print('editorType:', data.get('editorType'))
tc = data.get('textContent', '')
print('textContent:', tc[:2000] if tc else '(없음)')
