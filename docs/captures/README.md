# Captures d'écran du rapport

Placer ici les 12 captures listées à la section 6.4 du rapport, en respectant
les noms de fichiers indiqués.

Après ajout, régénérer le PDF :

```bash
cd docs
python3 -c "
import markdown, pathlib
md = pathlib.Path('RAPPORT.md').read_text(encoding='utf-8')
body = markdown.Markdown(extensions=['tables','fenced_code','sane_lists']).convert(md)
html = pathlib.Path('RAPPORT.html').read_text(encoding='utf-8')
head = html.split('</style></head><body>')[0] + '</style></head><body>'
pathlib.Path('RAPPORT.html').write_text(head + body + '</body></html>', encoding='utf-8')
"
google-chrome --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=RAPPORT.pdf RAPPORT.html
```
