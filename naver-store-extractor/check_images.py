import json, re
data = json.loads(open('output/2849385212/content_raw.json', 'rb').read())
rc = data.get('renderContent', '')

imgs = re.findall(r'src="(https?://[^"<>\s]+)"', rc)
print('img srcs:', len(imgs))
for u in imgs[:10]:
    print(' ', u[:120])

ps = re.findall(r'https://[a-z0-9-]+\.pstatic\.net[^"\'<>\s\\]+', rc)
print('\npstatic:', len(ps))
for u in ps[:5]:
    print(' ', u[:120])
