"""Measure layout of a thesis PDF with pypdf and compare with the measured reference values
(notes/reference_thesis_analysis.md). Usage: .venv/bin/python -I scripts/check_format.py thesis/tex/build/main.pdf [REF.pdf]
Compared: page size (A4 expected here), left text edge, body line pitch, body font size, first-baseline offset from the top
of a full page, page-number position (foot centred on chapter-start pages, top right otherwise), title-page baselines."""
import collections, sys, pypdf

def chunks(p):
    H = float(p.mediabox.height); out = []
    def v(text, cm, tm, fd, fs):
        if not text.strip(): return
        a, b, c, d, e, f = tm; A, B, C, D, E, F = cm
        out.append((round(H - (e * B + f * D + F), 1), round(e * A + f * C + E, 1), round(abs(fs * (d * D + c * B)), 1), text))
    p.extract_text(visitor_text=v); return out

def summarise(path, label):
    r = pypdf.PdfReader(path); print(f"== {label}: {len(r.pages)} pages, size {float(r.pages[0].mediabox.width):.1f} x {float(r.pages[0].mediabox.height):.1f} bp")
    pitch = collections.Counter(); left = collections.Counter(); size = collections.Counter(); first = collections.Counter()
    head = foot = 0
    for p in r.pages[2:]:
        c = chunks(p); H = float(p.mediabox.height)
        body = sorted({y for y, x, s, t in c if 10 < s < 11.5 and 60 < y < H - 60})
        if body: first[body[0]] += 1
        for a, b in zip(body, body[1:]): pitch[round(b - a, 1)] += 1
        for y, x, s, t in c:
            size[s] += 1
            if 60 < y < H - 60 and s < 11.5: left[round(x)] += 1
            if y < 50 and t.strip().isdigit(): head += 1
            if y > H - 55 and t.strip(): foot += 1
    print("  body line pitch (bp), most common:", pitch.most_common(2), "| font sizes:", size.most_common(3))
    print("  left text edge x (bp):", left.most_common(2), "| first baseline (bp from top):", first.most_common(2))
    print("  pages with a number at the top:", head, "| with a footer text:", foot)
    t = chunks(r.pages[0]); print("  title-page baselines:", [y for y, x, s, tx in t])

if __name__ == "__main__":
    summarise(sys.argv[1], "thesis")
    if len(sys.argv) > 2: summarise(sys.argv[2], "reference")
