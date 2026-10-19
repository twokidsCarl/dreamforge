import sys, pymupdf
cmd, path = sys.argv[1], sys.argv[2]
d = pymupdf.open(path)
if cmd == "text":
    pages = range(len(d)) if len(sys.argv) < 4 else [int(x) for x in sys.argv[3].split(",")]
    for i in pages:
        print(f"===== PAGE {i+1} =====")
        print(d[i].get_text())
elif cmd == "grep":
    import re
    pat = re.compile(sys.argv[3], re.I)
    for i, p in enumerate(d):
        t = p.get_text().replace("\n", " ")
        for m in pat.finditer(t):
            print(f"p{i+1}: ...{t[max(0,m.start()-250):m.end()+250]}...")
elif cmd == "png":
    i = int(sys.argv[3]); out = sys.argv[4]; dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 110
    d[i].get_pixmap(dpi=dpi).save(out)
elif cmd == "info":
    print(len(d), "pages")
if cmd == "crop":
    # crop page i, fractions x0 y0 x1 y1, out, dpi
    i = int(sys.argv[3]); x0,y0,x1,y1 = [float(v) for v in sys.argv[4:8]]; out = sys.argv[8]; dpi = int(sys.argv[9])
    r = d[i].rect
    clip = pymupdf.Rect(r.x0 + x0*r.width, r.y0 + y0*r.height, r.x0 + x1*r.width, r.y0 + y1*r.height)
    d[i].get_pixmap(dpi=dpi, clip=clip).save(out)
