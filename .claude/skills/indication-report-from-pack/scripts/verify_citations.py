#!/usr/bin/env python3
"""Verify (pack: ...) citations in an indication report against its evidence pack.

Usage:
    python verify_citations.py <report.md> <evidence-pack-dir>

What it does (see indication-report-from-pack Step 2a / Step 5):
  1. Parses every `(pack: ID, ...)` citation out of the report.
  2. Resolves each ID to its file(s) via the pack's MANIFEST.md index table
     (the "Local path" column), preferring the paired Markdown for a PDF.
  3. For any citation carrying a quoted string, checks that the quote actually
     appears in the referenced file, whitespace-insensitive and case-insensitive.

It reports three buckets:
  * verified     - the quote was found in the cited file.
  * unverifiable - nothing mechanical to check (a locator/summary-tier citation
                   with no quoted string).
  * failed       - a quote was given but not found, the ID is unknown, or the
                   cited file could not be read. These are the citation-washing
                   red flags to fix by hand.

Exit code is 1 if there is at least one failure, else 0, so it can gate a build.
Standard library only; PDF bodies are not read (the paired .md is checked
instead), matching the three-tier pack layout.
"""

import os
import re
import sys

# --- text normalisation -----------------------------------------------------

_CURLY = {
    "“": '"', "”": '"',   # curly double quotes
    "‘": "'", "’": "'",   # curly single quotes
    "–": "-", "—": "-",   # en/em dash
    " ": " ",                  # non-breaking space
}


def _straighten(s):
    for a, b in _CURLY.items():
        s = s.replace(a, b)
    return s


def normalize(s):
    """Lowercase, straighten smart punctuation, collapse whitespace."""
    s = _straighten(s).lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# --- citation extraction ----------------------------------------------------

_ID_RE = re.compile(r"[`*]*([A-Za-z]+\d+)")
_QUOTE_RE = re.compile(r'"([^"]+)"')


def extract_citations(text):
    """Return a list of {id, quote, line, raw} for each (pack: ...) citation.

    Parens inside a quoted string are handled: the citation ends at the first
    unquoted closing paren.
    """
    results = []
    for m in re.finditer(r"\(pack:", text):
        i = m.end()
        depth = 1
        in_quote = False
        buf = []
        while i < len(text) and depth > 0:
            c = text[i]
            if c in ('"', "“", "”"):
                in_quote = not in_quote
                buf.append('"')
            elif c == "(" and not in_quote:
                depth += 1
                buf.append(c)
            elif c == ")" and not in_quote:
                depth -= 1
                if depth == 0:
                    break
                buf.append(c)
            else:
                buf.append(c)
            i += 1
        content = "".join(buf).strip()
        line = text.count("\n", 0, m.start()) + 1
        idm = _ID_RE.match(content)
        cid = idm.group(1).upper() if idm else None
        qm = _QUOTE_RE.search(content)
        quote = qm.group(1) if qm else None
        results.append({"id": cid, "quote": quote, "line": line, "raw": content})
    return results


# --- manifest parsing -------------------------------------------------------

_ROW_ID_RE = re.compile(r"^[A-Za-z]+\d+$")
_MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")


def _cell_clean(c):
    return c.strip().strip("`* <>")


def parse_manifest(pack_dir):
    """Map manifest ID -> local path string, read from MANIFEST.md's index table."""
    path = os.path.join(pack_dir, "MANIFEST.md")
    mapping = {}
    if not os.path.isfile(path):
        return mapping, path
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()

    id_col = path_col = None
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        low = [_cell_clean(c).lower() for c in cells]
        if id_col is None and "id" in low:
            id_col = low.index("id")
            if "local path" in low:
                path_col = low.index("local path")
            continue
        if id_col is None or len(cells) <= id_col:
            continue
        idcell = _cell_clean(cells[id_col])
        if _ROW_ID_RE.match(idcell):
            lp = ""
            if path_col is not None and len(cells) > path_col:
                lp = cells[path_col].strip()
            mapping[idcell.upper()] = lp
    return mapping, path


# --- file resolution --------------------------------------------------------

_READABLE = {".md", ".markdown", ".txt", ".json", ".csv", ".tsv"}


def clean_path(lp):
    m = _MD_LINK_RE.search(lp)
    if m:
        lp = m.group(1)
    return lp.strip("`* <>")


def candidate_files(pack_dir, lp):
    """Existing, text-readable files that back a manifest local-path entry."""
    lp = clean_path(lp)
    if not lp:
        return []
    base, ext = os.path.splitext(lp)
    ext = ext.lower()
    if ext == ".pdf":
        raw = [base + ".md", lp]           # prefer the paired Markdown
    elif ext == "":
        raw = [lp + ".md", lp]
    else:
        raw = [lp]

    resolved = []
    for rc in raw:
        for cand in (os.path.join(pack_dir, rc), rc,
                     os.path.join(pack_dir, os.path.basename(rc))):
            if os.path.isfile(cand) and cand not in resolved:
                if os.path.splitext(cand)[1].lower() in _READABLE:
                    resolved.append(cand)
    return resolved


def read_normalized(files):
    chunks = []
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                chunks.append(fh.read())
        except OSError:
            continue
    return normalize("\n".join(chunks))


# --- main -------------------------------------------------------------------

def main(argv):
    if len(argv) != 3:
        sys.stderr.write(
            "usage: verify_citations.py <report.md> <evidence-pack-dir>\n")
        return 2
    report_path, pack_dir = argv[1], argv[2]
    if not os.path.isfile(report_path):
        sys.stderr.write("error: report not found: %s\n" % report_path)
        return 2
    if not os.path.isdir(pack_dir):
        sys.stderr.write("error: pack dir not found: %s\n" % pack_dir)
        return 2

    with open(report_path, encoding="utf-8", errors="replace") as fh:
        report_text = fh.read()

    manifest, manifest_path = parse_manifest(pack_dir)
    if not os.path.isfile(manifest_path):
        sys.stderr.write("warning: no MANIFEST.md in %s; IDs cannot be "
                         "resolved\n" % pack_dir)

    citations = extract_citations(report_text)

    verified, unverifiable, failed = [], [], []
    text_cache = {}

    for c in citations:
        cid, quote, line = c["id"], c["quote"], c["line"]
        if cid is None:
            failed.append((line, "?", "malformed citation: %r" % c["raw"]))
            continue
        if quote is None:
            unverifiable.append((line, cid, "no quote to check (locator/summary tier)"))
            continue
        if cid not in manifest:
            failed.append((line, cid, 'unknown manifest ID; quote "%s"' % quote))
            continue
        if cid not in text_cache:
            files = candidate_files(pack_dir, manifest[cid])
            text_cache[cid] = (files, read_normalized(files))
        files, body = text_cache[cid]
        if not files:
            failed.append((line, cid,
                           'no readable file for ID (path: %r); quote "%s"'
                           % (manifest[cid], quote)))
            continue
        if normalize(quote) in body:
            verified.append((line, cid, '"%s"' % quote))
        else:
            where = ", ".join(os.path.relpath(f, pack_dir) for f in files)
            failed.append((line, cid,
                           'quote not found: "%s"  [searched: %s]'
                           % (quote, where)))

    def dump(title, rows):
        print("\n%s (%d):" % (title, len(rows)))
        for line, cid, msg in rows:
            print("  line %-5d %-6s %s" % (line, cid, msg))

    print("Citation verification for %s against %s"
          % (report_path, pack_dir))
    print("Parsed %d pack citation(s)." % len(citations))
    dump("FAILED", failed)
    dump("UNVERIFIABLE", unverifiable)
    dump("VERIFIED", verified)
    print("\nTally: verified=%d  unverifiable=%d  failed=%d  (total=%d)"
          % (len(verified), len(unverifiable), len(failed), len(citations)))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
