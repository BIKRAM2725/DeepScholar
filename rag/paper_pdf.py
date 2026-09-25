
import io
import os
import unicodedata
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Frame, FrameBreak, Image, KeepTogether,
    NextPageTemplate, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

# --------------------------------------------------------------------------
# Page geometry (IEEE conference format: US Letter, 2 columns of 3.5 in)
# --------------------------------------------------------------------------
W, H = letter
MARGIN_X = 0.625 * inch
MARGIN_TOP = 0.75 * inch
MARGIN_BOTTOM = 1.0 * inch
GAP = 0.25 * inch
COL_W = (W - 2 * MARGIN_X - GAP) / 2
FULL_W = W - 2 * MARGIN_X

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

# --------------------------------------------------------------------------
# Fonts: use real Times New Roman (or Liberation Serif) when installed, so
# symbols like >=, alpha, en-dash render correctly. Otherwise fall back to the
# built-in Times, which only supports Windows-1252 (text is sanitised then).
# --------------------------------------------------------------------------
_WIN = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
_FONT_CANDIDATES = [
    tuple(os.path.join(_WIN, f) for f in
          ("times.ttf", "timesbd.ttf", "timesi.ttf", "timesbi.ttf")),
    ("/Library/Fonts/Times New Roman.ttf",
     "/Library/Fonts/Times New Roman Bold.ttf",
     "/Library/Fonts/Times New Roman Italic.ttf",
     "/Library/Fonts/Times New Roman Bold Italic.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
]


def _setup_fonts():
    if os.environ.get("PAPER_BUILTIN_FONT") != "1":
        for paths in _FONT_CANDIDATES:
            if not all(os.path.exists(p) for p in paths):
                continue
            try:
                names = ["PaperSerif", "PaperSerif-Bold",
                         "PaperSerif-Italic", "PaperSerif-BoldItalic"]
                for name, path in zip(names, paths):
                    pdfmetrics.registerFont(TTFont(name, path))
                pdfmetrics.registerFontFamily(
                    "PaperSerif", normal=names[0], bold=names[1],
                    italic=names[2], boldItalic=names[3])
                return names, True
            except Exception as e:  # corrupt font file etc.
                print(f"[PDF] could not load {paths[0]}: {e}")
    return ["Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"], False


(F_REG, F_BOLD, F_ITAL, F_BOLDITAL), UNICODE_OK = _setup_fonts()

# Optional: `pip install pyphen` gives proper hyphenation in narrow columns.
try:
    import pyphen  # noqa: F401
    _HYPH = "en_US"
except ImportError:
    _HYPH = ""

# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------
_BUILTIN_REPLACE = {
    "\u2265": ">=", "\u2264": "<=", "\u2192": "->", "\u2190": "<-",
    "\u2212": "-", "\u2010": "-", "\u2011": "-", "\u2022": "-",
    "\u00d7": "x",
}
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)


def _clean(text):
    text = unicodedata.normalize("NFKC", text or "")   # exotic spaces -> " "
    text = text.translate(_INVISIBLE)
    if not UNICODE_OK:
        for k, v in _BUILTIN_REPLACE.items():
            text = text.replace(k, v)
        text = text.encode("cp1252", errors="ignore").decode("cp1252")
    return text


def _p(text):
    """Sanitise + escape text for use inside a Paragraph."""
    return escape(_clean(text))


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------
def _style(name, **kw):
    kw.setdefault("hyphenationLang", _HYPH)
    return ParagraphStyle(name, **kw)


TITLE = _style("title", fontName=F_REG, fontSize=24, leading=28,
               alignment=TA_CENTER, spaceAfter=8)
AUTHOR = _style("author", fontName=F_REG, fontSize=11, leading=13.5,
                alignment=TA_CENTER)
AFFIL = _style("affil", fontName=F_ITAL, fontSize=9, leading=11,
               alignment=TA_CENTER)
BODY = _style("body", fontName=F_REG, fontSize=10, leading=12,
              alignment=TA_JUSTIFY, firstLineIndent=12, spaceAfter=1)
ABSTRACT = _style("abstract", fontName=F_BOLD, fontSize=9, leading=11,
                  alignment=TA_JUSTIFY, spaceAfter=4)
HEADING = _style("h1", fontName=F_REG, fontSize=10, leading=12,
                 alignment=TA_CENTER, spaceBefore=9, spaceAfter=4)
SUBHEAD = _style("h2", fontName=F_ITAL, fontSize=10, leading=12,
                 alignment=TA_LEFT, spaceBefore=5, spaceAfter=2)
CAPTION = _style("caption", fontName=F_REG, fontSize=8, leading=9.5,
                 alignment=TA_CENTER, spaceBefore=3, spaceAfter=8)
TABLE_LABEL = _style("tlabel", fontName=F_REG, fontSize=8, leading=9.5,
                     alignment=TA_CENTER, spaceBefore=4)
TABLE_TITLE = _style("ttitle", fontName=F_REG, fontSize=8, leading=9.5,
                     alignment=TA_CENTER, spaceAfter=3)
REF = _style("ref", fontName=F_REG, fontSize=8, leading=9.5,
             alignment=TA_LEFT, leftIndent=22, firstLineIndent=-22,
             spaceAfter=2)


# --------------------------------------------------------------------------
# Diagram helpers
# --------------------------------------------------------------------------
def _wrap(text, font, size, max_w):
    """Word-wrap text to max_w points; honours explicit '\\n' breaks."""
    lines = []
    for chunk in text.split("\n"):
        cur = ""
        for word in chunk.split():
            trial = f"{cur} {word}".strip()
            if stringWidth(trial, font, size) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines or [""]


def flowchart(steps, width=COL_W, font_size=8):
    """Vertical process flowchart. Boxes grow to fit wrapped text."""
    box_w = width * 0.86
    x0 = (width - box_w) / 2
    pad, gap = 5, 14
    lh = font_size * 1.22

    wrapped = [_wrap(_clean(s), F_REG, font_size, box_w - 12) for s in steps]
    heights = [max(24, 2 * pad + len(ls) * lh) for ls in wrapped]
    total = sum(heights) + gap * (len(steps) - 1)

    d = Drawing(width, total)
    y_top = total
    for i, (lines, h) in enumerate(zip(wrapped, heights)):
        y = y_top - h
        d.add(Rect(x0, y, box_w, h, strokeColor=colors.black, strokeWidth=0.8,
                   fillColor=colors.HexColor("#EEF2F7")))
        block_top = y + h / 2 + len(lines) * lh / 2
        for j, line in enumerate(lines):
            d.add(String(width / 2, block_top - font_size * 0.85 - j * lh,
                         line, textAnchor="middle", fontName=F_REG,
                         fontSize=font_size))
        if i < len(steps) - 1:                     # arrow to the next box
            cx = width / 2
            d.add(Line(cx, y, cx, y - gap + 4, strokeWidth=0.8))
            d.add(Polygon([cx - 3, y - gap + 5, cx + 3, y - gap + 5,
                           cx, y - gap], fillColor=colors.black,
                          strokeColor=colors.black))
        y_top = y - gap
    return d


def bar_chart(metrics, vmax=1.0, width=COL_W, height=150):
    """Vector bar chart of {name: value}; values must lie in [0, vmax]."""
    d = Drawing(width, height)
    bc = VerticalBarChart()
    bc.x, bc.y = 30, 26
    bc.width, bc.height = width - 40, height - 42
    bc.data = [list(metrics.values())]
    bc.categoryAxis.categoryNames = [_clean(k) for k in metrics]
    bc.categoryAxis.labels.fontName = F_REG
    bc.categoryAxis.labels.fontSize = 7
    bc.valueAxis.labels.fontName = F_REG
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = vmax
    bc.valueAxis.valueStep = vmax / 5
    bc.valueAxis.visibleGrid = 1
    bc.valueAxis.gridStrokeColor = colors.HexColor("#CCCCCC")
    bc.valueAxis.gridStrokeWidth = 0.4
    bc.bars[0].fillColor = colors.HexColor("#4A6FA5")
    bc.bars[0].strokeColor = colors.black
    bc.bars[0].strokeWidth = 0.4
    bc.barLabelFormat = "%.3f" if vmax <= 1 else "%.1f"
    bc.barLabels.nudge = 7
    bc.barLabels.fontName = F_REG
    bc.barLabels.fontSize = 7
    d.add(bc)
    return d


def metrics_table(rows, width=COL_W * 0.8):
    """IEEE-style table: horizontal rules only. rows[0] is the header."""
    rows = [[_clean(str(c)) for c in r] for r in rows]
    t = Table(rows, colWidths=[width * 0.62, width * 0.38], hAlign="CENTER")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), F_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), F_REG),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
    ]))
    return t


def image_flowable(data, width=COL_W, max_h=3.2 * inch):
    """Scale a PNG/JPG (bytes) to the column width."""
    try:
        iw, ih = ImageReader(io.BytesIO(data)).getSize()
    except Exception:
        raise ValueError("Unsupported or corrupt image (use PNG or JPG).")
    w, h = width, width * ih / iw
    if h > max_h:
        w, h = max_h * iw / ih, max_h
    img = Image(io.BytesIO(data), width=w, height=h)
    img.hAlign = "CENTER"
    return img


# --------------------------------------------------------------------------
# Document builder
# --------------------------------------------------------------------------
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(F_REG, 9)
    canvas.drawCentredString(W / 2, 0.5 * inch, str(doc.page))
    canvas.restoreState()


def _column(x, y, h, fid):
    return Frame(x, y, COL_W, h, id=fid, leftPadding=0, rightPadding=0,
                 topPadding=0, bottomPadding=0)


def _measure(flowables, width):
    total = 0
    for f in flowables:
        _, h = f.wrap(width, 10000)
        total += h + f.getSpaceBefore() + f.getSpaceAfter()
    return total


def build_ieee_pdf(title, authors, abstract, keywords, sections, references):
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=letter, leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title=_clean(title), author=_clean(authors).replace("\n", ", "),
    )

    # --- title block (height measured, so long titles never overflow) ---
    head = [Paragraph(_p(title), TITLE)]
    lines = [ln.strip() for ln in (authors or "").splitlines() if ln.strip()]
    lines = lines or ["Author Name"]
    head.append(Paragraph(_p(lines[0]), AUTHOR))
    head += [Paragraph(_p(ln), AFFIL) for ln in lines[1:]]
    title_h = _measure(head, FULL_W) + 14

    col_h = H - MARGIN_TOP - MARGIN_BOTTOM
    x1, x2 = MARGIN_X, MARGIN_X + COL_W + GAP
    title_frame = Frame(MARGIN_X, H - MARGIN_TOP - title_h, FULL_W, title_h,
                        id="title", leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="first", onPage=_footer, frames=[
            title_frame,
            _column(x1, MARGIN_BOTTOM, col_h - title_h, "c1"),
            _column(x2, MARGIN_BOTTOM, col_h - title_h, "c2"),
        ]),
        PageTemplate(id="later", onPage=_footer, frames=[
            _column(x1, MARGIN_BOTTOM, col_h, "c1b"),
            _column(x2, MARGIN_BOTTOM, col_h, "c2b"),
        ]),
    ])

    story = [NextPageTemplate("later")] + head + [
        FrameBreak(),
        Paragraph(f"<i>Abstract\u2014</i>{_p(abstract)}", ABSTRACT),
        Paragraph(f"<i>Index Terms\u2014</i>{_p(keywords)}", ABSTRACT),
        Spacer(1, 4),
    ]

    # --- body ---
    for i, sec in enumerate(sections):
        story.append(CondPageBreak(0.7 * inch))
        story.append(Paragraph(f"{ROMAN[i]}. {_p(sec['heading'].upper())}",
                               HEADING))
        sub_no = 0
        for blk in sec["blocks"]:
            kind = blk[0]
            if kind == "p":
                story.append(Paragraph(_p(blk[1]), BODY))
            elif kind == "sub":
                sub_no += 1
                story.append(CondPageBreak(0.6 * inch))
                story.append(Paragraph(f"{chr(64 + sub_no)}. {_p(blk[1])}",
                                       SUBHEAD))
            elif kind == "fig":
                _, flowable, caption = blk
                story.append(KeepTogether([Spacer(1, 4), flowable,
                                           Paragraph(_p(caption), CAPTION)]))
            elif kind == "table":
                _, rows, label, ttl = blk
                story.append(KeepTogether([
                    Paragraph(_p(label), TABLE_LABEL),
                    Paragraph(_p(ttl.upper()), TABLE_TITLE),
                    metrics_table(rows), Spacer(1, 8)]))

    story.append(CondPageBreak(0.7 * inch))
    story.append(Paragraph("REFERENCES", HEADING))
    for n, ref in enumerate(references, 1):
        story.append(Paragraph(f"[{n}]&nbsp;&nbsp;{_p(ref)}", REF))

    doc.build(story)
    return buf.getvalue()