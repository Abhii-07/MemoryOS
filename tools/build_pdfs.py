#!/usr/bin/env python
# Builds deliverable PDFs: markdown -> styled HTML -> print via headless Chrome.
# Usage: python tools/build_pdfs.py [smoke]
#   (no args)  build the full D1 PDF set from reconstruction/
#   smoke      build a single smoke PDF to verify the pipeline works
import sys, os, subprocess, pathlib, html as htmlmod

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
REPO = pathlib.Path(__file__).resolve().parent.parent
OUT_HTML = pathlib.Path(os.environ.get("TEMP", r"C:\Users\CR7\AppData\Local\Temp")) / "memoryos_html"

CSS = """
  @page { size: A4; margin: 20mm 17mm; }
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 10.5pt;
         line-height: 1.5; color: #1a1a1a; }
  h1 { font-size: 20pt; color: #14325c; border-bottom: 2px solid #14325c;
       padding-bottom: 6px; margin-top: 0; }
  h2 { font-size: 14pt; color: #14325c; border-bottom: 1px solid #d0d7e2;
       padding-bottom: 3px; margin-top: 24px; page-break-after: avoid; }
  h3 { font-size: 11.5pt; color: #1f4e8c; margin-top: 18px; page-break-after: avoid; }
  blockquote { border-left: 4px solid #b7c4d6; margin: 10px 0; padding: 6px 14px;
       background: #f4f7fb; color: #444; }
  blockquote p { margin: 4px 0; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; }
  th, td { border: 1px solid #c8d0dc; padding: 5px 8px; text-align: left; vertical-align: top; }
  th { background: #14325c; color: #fff; }
  tr:nth-child(even) td { background: #f4f7fb; }
  code { background: #eef1f6; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; font-size: 9pt; }
  pre { background: #f4f7fb; border: 1px solid #d8dde6; border-radius: 4px; padding: 10px; overflow-x: auto; }
  pre code { background: none; padding: 0; }
  strong { color: #14325c; }
  hr { border: none; border-top: 1px solid #d8dde6; margin: 18px 0; }
  /* ---- diagrams ---- */
  .diagram { border: 1px solid #c8d0dc; border-radius: 6px; padding: 12px;
             background: #fafbfd; margin: 14px 0; }
  .stage { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .box { border: 2px solid #14325c; border-radius: 6px; padding: 8px 12px;
         background: #eaf0f9; font-weight: 600; color: #14325c; flex: 1; min-width: 220px; }
  .box .tag { display: block; font-weight: 400; font-size: 8.5pt; color: #5a6b80; margin-top: 3px; }
  .box-0 { border-color: #4a90d9; background: #e8f1fb; }
  .box-1 { border-color: #d9822b; background: #fdf3e7; }
  .box-2 { border-color: #c05621; background: #fdeee4; }
  .box-3 { border-color: #2e7d5b; background: #e9f6f0; }
  .bottleneck { font-size: 8.5pt; color: #8a2f2f; background: #fbeaea; border: 1px solid #e4b7b7;
                border-radius: 4px; padding: 4px 8px; flex: 1; min-width: 180px; }
  .arrow { text-align: center; font-size: 16pt; color: #555; line-height: 1; margin: 2px 0; }
  .map-title { font-weight: 700; color: #14325c; margin-bottom: 8px; text-align: center; }
  .map-grid { display: flex; align-items: stretch; gap: 10px; }
  .map-col { flex: 1; }
  .map-head { background: #14325c; color: #fff; font-weight: 600;
             border-radius: 4px 4px 0 0; padding: 4px 8px; font-size: 9pt; }
  .map-arrow { display: flex; align-items: center; font-size: 20pt; color: #14325c; }
  .map-item { border: 1px solid #c8d0dc; border-top: none; padding: 4px 8px;
             font-size: 8.5pt; background: #fff; }
  .map-note { margin-top: 8px; font-size: 8.5pt; color: #5a6b80; }
  .cover { text-align: center; margin: 40px 0 30px; }
  .cover h1 { border: none; }
  .cover .sub { color: #5a6b80; font-size: 11pt; }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{title}</title>
<style>{css}</style></head>
<body>{body}</body></html>"""


def md_to_html(md_path):
    from markdown_it import MarkdownIt
    md = MarkdownIt("gfm-like", {"html": True})
    md.disable("linkify")
    return md.render(md_path.read_text(encoding="utf-8"))


def build(md_name, pdf_name, build_dir, title):
    md_path = build_dir / md_name
    if not md_path.exists():
        raise SystemExit(f"missing source markdown: {md_path}")
    OUT_HTML.mkdir(parents=True, exist_ok=True)
    body = md_to_html(md_path)
    html = TEMPLATE.format(title=htmlmod.escape(title), css=CSS, body=body)
    html_path = OUT_HTML / (md_name.replace(".md", ".html"))
    html_path.write_text(html, encoding="utf-8")
    pdf_path = build_dir / pdf_name
    uri = html_path.as_uri()
    subprocess.run([CHROME, "--headless=new", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", uri],
                   check=True, capture_output=True)
    print(f"OK  {pdf_name}  ({pdf_path.stat().st_size} bytes)")


def main():
    recon = REPO / "reconstruction"
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        OUT_HTML.mkdir(parents=True, exist_ok=True)
        smoke = OUT_HTML / "smoke.md"
        smoke.write_text(
            "# Pipeline smoke test\n\nThis PDF verifies the markdown → HTML → Chrome toolchain.\n\n- markdown-it: OK\n- headless Chrome: reached\n",
            encoding="utf-8",
        )
        build("smoke.md", "smoke.pdf", OUT_HTML, "Pipeline Smoke Test")
        print("done (smoke)")
        return
    build("01_problem.md", "problem_reconstruction.pdf", recon, "Problem Reconstruction")
    build("02_timeline.md", "historical_timeline.pdf", recon, "Historical Timeline")
    build("productive_failure_report.md", "productive_failure_report.pdf",
          REPO / "experiments" / "naive_baseline", "Naive Baseline — Productive Failure Report")
    print("done")


if __name__ == "__main__":
    main()