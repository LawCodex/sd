#!/usr/bin/env python3
"""Download the Ministry of Justice "Laws of Sudan" (قوانين السودان) e-book (Kotobee web reader at
https://moj.gov.sd/sudanlaws/) — EPUB package + every XHTML chapter in spine order — and the
Constitutional Document PDF from the MoJ download centre.

Usage: python sd_fetch.py RAW_DIR
"""
import os
import re
import sys
import time

import requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "https://moj.gov.sd/sudanlaws/epub/"
RAW = sys.argv[1]
OUT = os.path.join(RAW, "epub")
os.makedirs(os.path.join(OUT, "xhtml"), exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = UA


def get(url):
    for i in range(5):
        try:
            r = S.get(url, timeout=120)
            time.sleep(1.0)
            if r.status_code == 200:
                return r.content
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(10 * (i + 1))
    return None


def save(rel, url):
    fn = os.path.join(OUT, rel)
    if os.path.exists(fn):
        return open(fn, "rb").read()
    data = get(url)
    if data is None:
        print("MISSING", url, flush=True)
        return None
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    open(fn, "wb").write(data)
    return data


def main():
    cont = save("META-INF/container.xml", BASE + "META-INF/container.xml").decode()
    opf_path = re.search(r'full-path="([^"]+)"', cont).group(1)
    opf = save(opf_path, BASE + opf_path).decode("utf-8")
    base_dir = os.path.dirname(opf_path)
    items = dict(re.findall(r'<item id="([^"]+)" href="([^"]+)"', opf))
    spine = re.findall(r'<itemref idref="([^"]+)"', opf)
    for i, idref in enumerate(spine):
        href = items[idref]
        save(os.path.join(base_dir, href), BASE + base_dir + "/" + href)
        if i % 25 == 0:
            print(i, len(spine), flush=True)
    for idref, href in items.items():
        if href.endswith((".xhtml", ".html")) and idref not in spine:
            save(os.path.join(base_dir, href), BASE + base_dir + "/" + href)
    data = get("https://moj.gov.sd/files/download/144")
    if data:
        open(os.path.join(RAW, "constitutional_document_2019.pdf"), "wb").write(data)
    print("done", flush=True)


if __name__ == "__main__":
    main()
