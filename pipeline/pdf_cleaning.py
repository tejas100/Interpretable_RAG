"""
pdf_cleaning.py

Post-processing utilities for `unstructured`'s hi_res PDF partitioning
output. Import from here — don't copy-paste these functions elsewhere,
so there's exactly one version to fix if a bug shows up later.

    from pipeline.pdf_cleaning import resolve_duplicates

Background (see notebooks/01_pdf_extraction_exploration.py for the full
investigation that led here):

`hi_res` strategy runs a YOLOX layout-detection model AND a Tesseract OCR
pass over each page, then merges their outputs. On short, heading-like
elements (titles, section headers, short lead-in lines), the merge step
sometimes emits the SAME physical text twice — once from each detection
path, usually with different `Element` types (e.g. one comes back as
generic `Text`, the other as the correctly-classified `Title`).

We verified empirically (on "Toy Models of Superposition.pdf"):
  - Duplication is NOT random. It's concentrated in short text
    (avg ~25 chars) vs. non-duplicate text (avg ~184 chars) — consistent
    with small heading-sized regions being the ones that get double-boxed.
  - Naively deduping by "same text" alone is WRONG. Short strings like a
    single 'W' or the word 'weights' can legitimately appear more than
    once, in genuinely different places in a 60-page document — that's
    coincidence, not a detection bug.
  - The only reliable signal for "these two elements are actually the
    same physical detection" is: same text + same page + bounding boxes
    that sit at (near) the same position. Same-page alone is NOT enough
    (verified: two 'W' elements on the same page, ~150px apart, were
    genuinely different list items — not a duplicate).
"""

from collections import defaultdict


# Rough priority order for picking which duplicate to KEEP when a group
# resolves to "these are really the same detection." Prefer whichever
# element unstructured classified with a specific, meaningful type over
# the generic fallback types (`Text` / `UncategorizedText`), since the
# generic type usually means unstructured wasn't confident about what
# the region actually was.
TYPE_PRIORITY = {
    "Title": 3,
    "NarrativeText": 3,
    "ListItem": 3,
    "Table": 3,
    "Image": 3,
    "FigureCaption": 3,
    "Formula": 3,
    "Text": 1,
    "UncategorizedText": 1,
}


def _boxes_close(coords1, coords2, tolerance=15):
    """
    True if two element bounding boxes sit within `tolerance` pixels of
    each other vertically. `coords` here is the `.points` tuple from
    unstructured's metadata: (top-left, bottom-left, bottom-right, top-right),
    each an (x, y) pair in PixelSpace.

    We only compare the y-coordinates (top edge + bottom edge) — that was
    sufficient to distinguish real duplicates from coincidental same-page
    text matches in testing, and is more robust than also requiring x to
    match (columns/indentation can shift x slightly between detection
    passes even for a genuine duplicate).
    """
    y1_top, y1_bot = coords1[0][1], coords1[1][1]
    y2_top, y2_bot = coords2[0][1], coords2[1][1]
    return abs(y1_top - y2_top) < tolerance and abs(y1_bot - y2_bot) < tolerance


def resolve_duplicates(elements, tolerance=15):
    """
    Collapses duplicate-detection artifacts from hi_res PDF extraction.

    Two elements are treated as the SAME physical detection (and merged
    down to one) only if ALL of the following hold:
      1. Identical text (after stripping whitespace)
      2. Same page number
      3. Bounding boxes within `tolerance` px of each other vertically

    When a group is a genuine duplicate, keeps whichever element has the
    most specific (highest-priority) type — see TYPE_PRIORITY above —
    and drops the rest.

    Elements that share text but sit on different pages, or on the same
    page but far apart, are left completely untouched: that's treated as
    coincidence, not a detection bug, and merging them would silently
    delete real content.

    Elements missing coordinate metadata are also left untouched (can't
    verify position => don't guess).

    Parameters
    ----------
    elements : list[unstructured.documents.elements.Element]
        Output of partition_pdf(..., strategy="hi_res") (or any element
        list carrying page_number + coordinates metadata).
    tolerance : int
        Max pixel difference (vertical) to still count as "same position".
        15px was sufficient on a 3850px-tall page render; revisit if a
        different DPI/page size is in play.

    Returns
    -------
    list[Element]
        A new list with duplicate detections collapsed. Original list is
        not mutated.
    """
    groups = defaultdict(list)
    for el in elements:
        key = (str(el).strip(), el.metadata.page_number)
        groups[key].append(el)

    to_drop_ids = set()

    for (text, page), els in groups.items():
        if len(els) < 2:
            continue  # not a duplicate group at all

        coords_list = [el.metadata.to_dict().get("coordinates") for el in els]
        if not all(c is not None for c in coords_list):
            continue  # can't verify position — leave untouched, don't guess

        pts = [c["points"] for c in coords_list]
        if not all(_boxes_close(pts[0], p, tolerance) for p in pts[1:]):
            continue  # positions differ — genuinely separate occurrences, keep all

        # Confirmed same physical detection — keep the best-typed copy.
        best = max(els, key=lambda e: TYPE_PRIORITY.get(type(e).__name__, 0))
        for el in els:
            if el is not best:
                to_drop_ids.add(id(el))

    return [el for el in elements if id(el) not in to_drop_ids]