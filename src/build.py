"""Assemble the self-contained report page.

usage: python3 src/build.py site/data.json data/logos.json site/index.html
"""
import datetime, json, os, re, sys

DATA, LOGOS, OUT = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
page = open(os.path.join(here, "template.html")).read()
js = open(os.path.join(here, "script.js")).read()
data = open(DATA).read()
json.loads(data)  # fail early on bad data
logos = json.load(open(LOGOS))
symbols = "".join(f'<symbol id="logo-{k}" viewBox="{v["viewBox"]}" fill-rule="evenodd">{v["body"]}</symbol>' for k, v in logos.items())
page = re.sub(r"(<script>\n).*?(</script>)", lambda m: m.group(1) + js + m.group(2), page, count=1, flags=re.S)
built = datetime.datetime.now(datetime.timezone.utc).strftime("%-d %b %Y")
page = page.replace("__LOGOS__", symbols).replace("__DATA__", data.replace("</", "<\\/")).replace("__BUILT__", built)
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w").write(page)
print(f"wrote {OUT} ({len(page):,} bytes)")
