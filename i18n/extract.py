"""Extract English bias descriptions and SVG labels into JSON for translation."""
import json, re, subprocess, urllib.parse

s = open('biases_wikipedia.html', encoding='utf-8').read()
entries = re.findall(r"<div class='bias'>\s*<h2>(.*?)</h2>\s*<a href='(.*?)'.*?<div class='content'>(.*?)</div>\s*<div class='attribution'>", s, re.S)
biases, seen = [], {}
for name, url, content in entries:
    content = re.split(r'<h[2-6]', content)[0]  # keep only the lead section
    content = re.sub(r'<math.*?</math>', '', content, flags=re.S).strip()
    if content in seen:
        biases.append({'name': name, 'url': url, 'same_as': seen[content]})
        continue
    seen[content] = name
    biases.append({'name': name, 'url': url, 'html': content})

# Russian Wikipedia titles via langlinks
titles = {urllib.parse.unquote(b['url'].split('/wiki/')[1].split('#')[0]).replace('_', ' ') for b in biases}
ru = {}
tl = sorted(titles)
for i in range(0, len(tl), 50):
    q = urllib.parse.urlencode({'action': 'query', 'titles': '|'.join(tl[i:i+50]), 'prop': 'langlinks',
                                'lllang': 'ru', 'redirects': 1, 'format': 'json', 'formatversion': 2})
    out = subprocess.run(['curl', '-s', '-A', 'bias-codex-ru/0.1', 'https://en.wikipedia.org/w/api.php?' + q],
                         capture_output=True, check=True).stdout
    d = json.loads(out)['query']
    back = {r['to']: r['from'] for r in d.get('redirects', [])}
    norm = {n['to']: n['from'] for n in d.get('normalized', [])}
    for p in d['pages']:
        t = p['title']; orig = back.get(t, t); orig = norm.get(orig, orig)
        if p.get('langlinks'):
            ru[orig] = p['langlinks'][0]['title']
for b in biases:
    t = urllib.parse.unquote(b['url'].split('/wiki/')[1].split('#')[0]).replace('_', ' ')
    if t in ru:
        b['ru_wiki'] = ru[t]

json.dump(biases, open('i18n/biases_en.json', 'w'), ensure_ascii=False, indent=1)

# SVG labels: default (English) <text> of each <switch>, as list of tspans
svg = open('assets/images/cognitive_bias_codex_en.svg', encoding='utf-8').read()
labels = []
for t in re.findall(r'<text(?![^>]*systemLanguage)[^>]*>(.*?)</text>', svg, re.S):
    spans = re.findall(r'<tspan[^>]*>(.*?)</tspan>', t, re.S) or [t]
    labels.append([re.sub(r'<[^>]+>', '', x) for x in spans])
json.dump(labels, open('i18n/labels_en.json', 'w'), ensure_ascii=False, indent=1)
print(len(biases), sum(1 for b in biases if 'html' in b), len(ru), len(labels),
      sum(len(re.sub(r'<[^>]+>', '', b.get('html', ''))) for b in biases))
