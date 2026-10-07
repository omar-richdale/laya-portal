"""Package original generated images into an offline gallery and image-only PDF."""
import hashlib
import json
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "docs/presentation/v1"
images = sorted((DECK / "out").glob("[0-9][0-9].png"))
assert len(images) == 12
pdf = DECK / "output/local-system-one.pdf"
c = canvas.Canvas(str(pdf), pagesize=(960, 540))
c.setTitle("Local System One — Sift, Bugsmith and VPN QA")
c.setAuthor("Richdale AI")
manifest = []
for path in images:
    with Image.open(path) as image:
        dimensions = image.size
    c.drawImage(ImageReader(str(path)), 0, 0, width=960, height=540, preserveAspectRatio=True, anchor="c")
    c.showPage()
    manifest.append({"slide": path.stem, "path": "out/" + path.name, "size": dimensions,
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
c.save()
(DECK / "manifest.json").write_text(json.dumps({"slides": manifest, "format": "complete generated slide images; raster text", "style_reference": "sift/docs/presentation/v3"}, indent=2), encoding="utf-8")
gallery = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local System One</title><style>body{margin:0;background:#0b1326;color:#f4f6fb;font:17px system-ui}header{padding:24px 5vw;display:flex;gap:20px;align-items:center;flex-wrap:wrap}a{color:#f5a623}main{max-width:1400px;margin:auto;padding:0 16px 40px}figure{margin:0 0 30px}img{width:100%;height:auto;display:block}figcaption{color:#8a94a6;padding:10px 0}h1{font-size:25px;margin:0}nav{position:sticky;top:0;background:#0b1326ed;padding:12px 5vw;display:flex;gap:12px;flex-wrap:wrap}html{scroll-behavior:smooth}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}</style>
<header><h1>Local System One</h1><a href="output/local-system-one.pptx">PowerPoint</a><a href="output/local-system-one.pdf">PDF</a><a href="PRESENTER-GUIDE.md">Presenter guide</a><a href="../../benchmark/REPORT.md">Benchmark report</a></header><nav>'''
gallery += ''.join(f'<a href="#slide-{p.stem}">{p.stem}</a>' for p in images) + '</nav><main>'
for path in images:
    gallery += f'<figure id="slide-{path.stem}"><img src="out/{path.name}" alt="Slide {path.stem}; full text brief in bodies/{path.stem}.txt"><figcaption>Slide {path.stem} / 12 · <a href="prompts/slide-{path.stem}.txt">Generation prompt</a></figcaption></figure>'
gallery += '</main></html>'
(DECK / "index.html").write_text(gallery, encoding="utf-8")
print(pdf)
