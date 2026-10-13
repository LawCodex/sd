# Sudan (SD) — legislation as Markdown

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as plain Markdown in git.

Laws of the Republic of the Sudan in **Arabic** (`ar/`), from the Ministry of Justice compilation
**«قوانين السودان» — Laws of Sudan, 9th edition** (فهرست قوانين السودان ـ الطبعة التاسعة), published by the
Ministry of Justice as an e-book at https://moj.gov.sd/sudanlaws/ (EPUB chapters under
`https://moj.gov.sd/sudanlaws/epub/EPUB/xhtml/`). The compilation is the Ministry's revised statute book
(prepared by its Law Revision Committee): each act is reproduced as amended, with footnotes citing the
amending acts.

**Total: 331 acts** (1903–2010s), retrieved 2026-10-13.

| Directory | Files |
|---|---|
| `ar/laws/<decade>/` | 331 |

## Structure

```
ar/laws/1900s/ … ar/laws/2010s/<year>-<epub-chapter-id>.md
```

File names use the year of the act and the e-book chapter id (stable identifier of the source file); the
Arabic title is in the front matter and H1. Each file contains:

* `## ترتيب المواد` — the table of arrangement of sections as printed in the compilation;
* the act itself: chapter headings (الباب `##`, الفصل `###`, الفرع `####`), each section as
  `###### المادة N` followed by its marginal note (caption) in *italics* and its text.

In the source the marginal notes are typeset on the same lines as the section text; they were separated
programmatically (`scripts/sd_convert.py`). A few acts whose layout did not allow this keep the notes inline.

Front matter: `year` (year of the act as in its short title), `status: unknown` (the compilation does not
mark repealed acts individually), `collection`, `source` (the e-book chapter URL).

## Not covered / known gaps

* **Constitutional framework**: the Ministry of Justice publishes the *Constitutional Document for the
  Transitional Period 2019* (الوثيقة الدستورية للفترة الانتقالية لسنة 2019, Official Gazette No. 1895 of
  3 October 2019) only as a PDF (https://moj.gov.sd/files/download/144) whose text layer is unusable (wrong
  glyph-to-Unicode mapping in the embedded Arabic font; the body pages are images). It was **not** published
  rather than publishing garbled text. The constitutional situation has been contested since the 2021
  military takeover and the war that began in April 2023 (the Document was amended in 2020 and again in
  February 2025 by the Sovereignty Council based in Port Sudan); no consolidated official text was found.
* Acts enacted after the 9th edition of the compilation, and Official Gazette issues (2025–2026 PDFs on the
  MoJ download centre), are not processed.
* Regulations, orders and state (wilaya) legislation are out of scope.
* Volume introductions and the chronological / alphabetical / subject indexes of the e-book are skipped.

## Licence

Sudanese legislation is official text of the State, published by the Ministry of Justice for public
information; official legislative texts are not protected works under Sudanese copyright law. The Markdown conversion is
published under CC0.

## Regenerate

```
python scripts/sd_fetch.py ../_raw/sd       # downloads the EPUB package + chapters (1 request/second)
python scripts/sd_convert.py ../_raw/sd .
```
Requires Python 3 with `requests`, `lxml`.
