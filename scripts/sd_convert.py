#!/usr/bin/env python3
"""Convert the MoJ "Laws of Sudan" e-book chapters (see sd_fetch.py) and the Constitutional
Document into LawCodex Markdown.

In the e-book each law's marginal notes (article captions) are typeset on the same lines as the
article text, separated by runs of spaces; captions are separated out and printed in italics under
the article heading.

Usage: python sd_convert.py RAW_DIR OUT_REPO_DIR
"""
import collections
import datetime
import json
import os
import re
import sys
import unicodedata

from lxml import html as LH

RAW, OUT = sys.argv[1], sys.argv[2]
TODAY = datetime.date.today().isoformat()
EPUB = os.path.join(RAW, "epub")
BASE_URL = "https://moj.gov.sd/sudanlaws/epub/"
LOG = open(os.path.join(RAW, "convert.log"), "w", encoding="utf-8")
DIG = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

TITLE_RX = re.compile(r"^((?:ال)?(?:قانون|مرسوم|أمر|لائحة|الوثيقة|دستور|نظام|اتفاقية)[^\n]{0,200}?لسنة\s*(\d{4})(?:\s*م)?)\s*$")
ART_RX = re.compile(r"^(\d+)\s*[ـ\-–]\s*(.*)$")
HEAD = [(r"^الباب\s", 2), (r"^الفصل\s", 3), (r"^الفرع\s", 4)]


def yq(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def norm(s):
    s = unicodedata.normalize("NFKC", s.replace("\xa0", " "))
    return s


def para_items(path):
    doc = LH.fromstring(re.sub(r"^<\?xml[^>]*>", "", open(path, "rb").read().decode("utf-8", "replace").lstrip("\ufeff").lstrip()))
    body = doc.find("body") if doc.find("body") is not None else doc
    items = []
    for el in body.iter("p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td"):
        if el.tag in ("td", "li") and el.find(".//p") is not None:
            continue
        t = norm(el.text_content())
        style = el.get("style") or ""
        m = re.search(r"margin-right:\s*(\d+)", style)
        indented = bool(m and int(m.group(1)) >= 80)
        centered = "center" in style
        items.append((t, indented, centered, el.tag))
    return items


def split_line(t, indented, gap_format=True):
    """-> (note, body)"""
    raw = t.rstrip().replace("↑", "")
    if not raw.strip():
        return "", ""
    if indented or re.match(r"^\s{4,}", raw):
        return "", raw.strip()
    parts = re.split(r"\s{4,}", raw.strip())
    if len(parts) >= 2:
        return parts[0].strip(), " ".join(p.strip() for p in parts[1:])
    s = raw.strip()
    m = re.match(r"^([^\d\(\"«]{2,70}?)\s+(\d+\s*ـ\s*.*)$", s)
    if m and not ART_RX.match(s):
        return m.group(1).strip(), m.group(2).strip()
    if ART_RX.match(s) or len(s) > 60 or not gap_format or re.match(r"^[\(\"«\-–]", s):
        return "", s
    return s, ""   # short line without body: caption fragment


def convert_chapter(path):
    items = para_items(path)
    texts = [re.sub(r"\s+", " ", re.sub(r"[\u200e\u200f]", "", t)).strip() for t, *_ in items]
    # title: first line (or two consecutive lines) matching TITLE_RX
    title, year, ti, span = None, None, None, 1
    for i, t in enumerate(texts[:12]):
        for k in (1, 2):
            cand = " ".join(texts[i:i + k])
            m = TITLE_RX.match(cand.translate(DIG))
            if m and texts[i].startswith(("قانون", "مرسوم", "أمر", "لائحة", "الوثيقة", "دستور", "نظام", "اتفاقية", "ال")):
                title, year, ti, span = cand, m.group(2), i, k
                break
        if title:
            break
    if not title:
        return None
    # body starts at the second occurrence of the title (after the "ترتيب المواد" table of contents)
    starts = [i + span - 1 for i in range(len(texts)) if " ".join(texts[i:i + span]) == title]
    toc_start = next((i for i, t in enumerate(texts) if t.startswith("ترتيب المواد")), None)
    body_start = starts[1] if len(starts) > 1 else ti + span - 1
    md = []
    if toc_start is not None and toc_start < body_start:
        md += ["## ترتيب المواد", ""]
        for t in texts[toc_start + 1:body_start]:
            if t and t != "بسم الله الرحمن الرحيم" and t not in title:
                md.append("- " + t)
        md.append("")
    md += ["## " + title, ""]
    cur_note, para = [], []
    gap_format = sum(1 for t, *_ in items[body_start + 1:] if re.search(r"\S\s{4,}\S", t.strip())) >= 3
    note_slot = None  # index in md where the caption of the current article goes

    def flush():
        if para:
            md.append(" ".join(para))
            md.append("")
            para.clear()

    def flush_note():
        nonlocal note_slot
        if note_slot is not None and cur_note:
            md[note_slot] = "*" + " ".join(cur_note).strip() + "*"
        cur_note.clear()
        note_slot = None

    for (t, indented, centered, tag), flat in zip(items[body_start + 1:], texts[body_start + 1:]):
        if not flat or re.fullmatch(r"\d{1,4}", flat) or re.fullmatch(r"\[\d+\]", flat) or flat == "↑":
            continue
        if centered:
            flush()
            lvl = next((l for rx, l in HEAD if re.match(rx, flat)), None)
            md += [("#" * lvl + " " + flat) if lvl else flat, ""]
            continue
        note, body = split_line(t, indented, gap_format)
        if not body:
            lvl = next((l for rx, l in HEAD if re.match(rx, note)), None)
            if lvl and len(note) < 80:
                flush()
                flush_note()
                md += ["#" * lvl + " " + note, ""]
            else:
                cur_note.append(note)
            continue
        m = ART_RX.match(body)
        if m:
            flush()
            flush_note()
            md += ["###### المادة " + m.group(1), ""]
            note_slot = len(md)
            md += ["", ""]
            if note:
                cur_note.append(note)
            para.append(m.group(2))
            continue
        if note:
            cur_note.append(note)
        if para and (re.search(r"[\.:؛]$", para[-1]) or re.match(r"^\(\s*[ء-ي\d]{1,3}\s*\)", body)):
            flush()
        para.append(body)
    flush()
    flush_note()
    text = "\n".join(md)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return title, year, text


def main():
    opf = open(os.path.join(EPUB, "EPUB", "package.xml"), encoding="utf-8").read()
    items = dict(re.findall(r'<item id="([^"]+)" href="([^"]+)"', opf))
    spine = re.findall(r'<itemref idref="([^"]+)"', opf)
    counts = collections.Counter()
    seen = collections.Counter()
    for idref in spine:
        href = items[idref]
        path = os.path.join(EPUB, "EPUB", href)
        if not os.path.exists(path):
            print("MISSING", href, file=LOG)
            continue
        res = convert_chapter(path)
        if not res:
            print("SKIP (no law title)", href, file=LOG)
            counts["skipped"] += 1
            continue
        title, year, body = res
        if body.count("\n") < 6:
            print("SKIP (empty)", href, title, file=LOG)
            counts["skipped"] += 1
            continue
        typ = "law"
        sub = "laws"
        if re.match(r"^(ال)?مرسوم", title):
            typ, sub = "decree", "decrees"
        elif re.match(r"^(ال)?(أمر|لائحة|نظام)", title):
            typ, sub = "regulation", "regulations"
        elif re.match(r"^(ال)?(الوثيقة|دستور)", title):
            typ, sub = "constitution", "constitution"
        slug_base = "%s-%s" % (year, os.path.splitext(os.path.basename(href))[0])
        fn = os.path.join(OUT, "ar", sub, year[:3] + "0s", slug_base + ".md")
        fm = ["---", "title: " + yq(title), "identifier: " + yq(title), "type: " + typ, "jurisdiction: sd",
              "language: ar", "year: %s" % year, "status: unknown",
              "collection: \"قوانين السودان — الطبعة التاسعة (Laws of Sudan, 9th edition), Ministry of Justice\"",
              "source: " + yq(BASE_URL + "EPUB/" + href), "retrieved: " + TODAY, "---"]
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, "w", encoding="utf-8") as f:
            f.write("\n".join(fm) + "\n\n# " + title + "\n\n" + body)
        counts[typ] += 1
    for k, v in sorted(counts.items()):
        print(k, v)


if __name__ == "__main__":
    main()
