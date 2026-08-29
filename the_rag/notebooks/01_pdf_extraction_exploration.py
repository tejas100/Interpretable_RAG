"""
01_pdf_extraction_exploration.py

EXPLORATION NOTEBOOK — not pipeline code. This is a lab notebook: it
records the investigation into how unstructured's `fast` vs `hi_res`
PDF strategies behave, and specifically how we discovered and diagnosed
the duplicate-element issue in hi_res output.

Nothing here needs to run again for the pipeline to work — the actual
reusable result of this investigation is `resolve_duplicates()`, which
lives in `pipeline/pdf_cleaning.py`. Re-read THIS file when you want to
remember *why* that function works the way it does, or when you hit a
similar-smelling issue on a different PDF and want the debugging
playbook rather than just the fix.

Document under test: Doc_corpus/research_papers/Toy_Models_of_Superposition.pdf
(Anthropic, "Toy Models of Superposition" — chosen as a medium-difficulty
first PDF: math-heavy but not the most table-dense paper in the corpus.)
"""

import pickle
import os
from collections import Counter, defaultdict
from unstructured.partition.pdf import partition_pdf


# ============================================================
# SECTION 1 — Load or build the hi_res extraction, with caching
# ============================================================
# hi_res runs a real object-detection model (YOLOX) over a rendered
# image of every page, PLUS a Tesseract OCR pass to supplement it —
# this took ~4-5 minutes for a ~60 page paper. Re-running that on every
# script execution while iterating on cleanup logic is a waste of time,
# so: partition once, pickle the element list, and every later run
# loads from disk instead. Unstructured `Element` objects are plain
# Python objects — pickle handles them fine.
#
# NOTE: this cache is specific to ONE file. If you explore a different
# PDF, use a different cache_path (e.g. slugify the filename) or you'll
# silently load the wrong document's cached elements.

filepath = "Doc_corpus/research_papers/Toy_Models_of_Superposition.pdf"
cache_path = "cache_toy_models_hires.pkl"

if os.path.exists(cache_path):
    print("Loading from cache...")
    with open(cache_path, "rb") as f:
        elements_hires = pickle.load(f)
else:
    print("Running hi_res partition (this will take a few minutes)...")
    elements_hires = partition_pdf(filename=filepath, strategy="hi_res")
    with open(cache_path, "wb") as f:
        pickle.dump(elements_hires, f)
    print("Cached.")

print(f"Total elements: {len(elements_hires)}")


# ============================================================
# SECTION 2 — Why we went looking for duplicates in the first place
# ============================================================
# Earlier exploration (see conversation history / README if you write
# one) compared `fast` strategy output against `hi_res` on page 2 of
# this paper. `fast` (pdfminer text-layer only, no layout awareness)
# fragmented a single sentence into ~10 pieces and mis-typed two
# in-sentence words ("neuroscience", "and deep learning") as `Title`
# elements — almost certainly because those words were hyperlinked
# citations, and pdfminer starts a new text run wherever the font/style
# changes, with no concept of "this is still the same paragraph."
#
# hi_res fixed that fragmentation (the sentence came back as one
# NarrativeText element) but introduced a NEW defect: some elements
# were appearing twice, verbatim, with different types. That's what
# this section investigates.


# ============================================================
# SECTION 3 — First pass: naive duplicate detection (TEXT ONLY)
# ============================================================
# WARNING: this check is intentionally naive and we later proved it
# wrong / too broad. Kept here because the mistake is instructive —
# see Section 5.

texts_all = [str(el).strip() for el in elements_hires]
counts_all = Counter(texts_all)
dupes_all_naive = {t: c for t, c in counts_all.items() if c > 1}
total_dupe_elements = sum(dupes_all_naive.values())
print(f"\n[naive] Whole doc: {len(texts_all)} elements, "
      f"{len(dupes_all_naive)} distinct texts appear more than once")
print(f"[naive] ({total_dupe_elements} elements involved, out of {len(texts_all)} total)")

# Finding: ~7.5% of elements involved. Is that concentrated in short
# text (headings) or spread evenly? Check length distributions:
dupe_lengths = [len(t) for t in dupes_all_naive]
non_dupe_lengths = [len(t) for t in texts_all if counts_all[t] == 1]
print(f"[naive] Duplicate text lengths:     min={min(dupe_lengths)}, "
      f"max={max(dupe_lengths)}, avg={sum(dupe_lengths)/len(dupe_lengths):.0f}")
print(f"[naive] Non-duplicate text lengths: min={min(non_dupe_lengths)}, "
      f"max={max(non_dupe_lengths)}, avg={sum(non_dupe_lengths)/len(non_dupe_lengths):.0f}")
# Result: dupes avg ~25 chars, non-dupes avg ~184 chars. Duplication is
# concentrated in short, heading-like text. Good signal — but the
# naive text-only grouping above still isn't safe to act on yet (see
# Section 5: it was catching false positives across DIFFERENT pages).


# ============================================================
# SECTION 4 — What TYPE pairs show up in these naive duplicate groups?
# ============================================================
# Hypothesis: duplicates pair one generic type (Text/UncategorizedText)
# with one specific type (Title/NarrativeText/etc). If true, "keep the
# specific type" is a clean resolution rule.

type_pairs_naive = Counter()
for t in dupes_all_naive:
    types = [type(el).__name__ for el in elements_hires if str(el).strip() == t]
    type_pairs_naive[tuple(sorted(types))] += 1

print("\n[naive] Type-pair breakdown:")
for pair, count in type_pairs_naive.items():
    print(f"  {pair}: {count} occurrences")
# Result: mostly ('Text','Title') and ('NarrativeText','Text') — good,
# matches the hypothesis. But also a few same-type pairs like
# ('NarrativeText','NarrativeText') and ('Image','Image') where the
# "prefer specific type" rule gives no answer. Investigated one of
# these directly (see Section 5) and found something important.


# ============================================================
# SECTION 5 — THE KEY FINDING: same-text != same-detection
# ============================================================
# Inspected the ('NarrativeText','NarrativeText') duplicate pair by
# hand. Text was 'I i' (a tiny OCR fragment, likely leftover from a
# broken subscript/variable name — this paper is math-heavy). Checked
# each copy's full metadata:
#
#   Copy 1: page_number=10, y-coords ≈ 2391-2437
#   Copy 2: page_number=35, y-coords ≈ 2621-2667
#
# DIFFERENT PAGES. 25 pages apart. This was never a duplicate-detection
# bug at all — just two unrelated tiny fragments that happened to
# produce identical text. The naive text-only grouping in Section 3
# was silently treating cross-page coincidences as duplicates.
#
# Lesson: "same text" is not a reliable signal by itself. Need to
# require same PAGE too. Redo the grouping properly:

groups_by_page = defaultdict(list)
for el in elements_hires:
    key = (str(el).strip(), el.metadata.page_number)
    groups_by_page[key].append(el)

real_dupes = {k: v for k, v in groups_by_page.items() if len(v) > 1}
print(f"\n[same-page] Real same-page duplicate groups: {len(real_dupes)}")
# Result: dropped from 37 (naive) to 30 (same-page). Confirms several
# of the naive "duplicates" were cross-page coincidences.

type_pairs_samepage = Counter()
for (text, page), els in real_dupes.items():
    types = tuple(sorted(type(el).__name__ for el in els))
    type_pairs_samepage[types] += 1

print("[same-page] Type-pair breakdown:")
for pair, count in type_pairs_samepage.items():
    print(f"  {pair}: {count} occurrences")


# ============================================================
# SECTION 6 — Is same-page enough? NO. Checked coordinates too.
# ============================================================
# Inspected the ('ListItem','ListItem') same-page duplicate by hand.
# Text was just 'W' (page 32 — again, math-heavy paper, W = weight
# matrix symbol, very plausible as two DIFFERENT list items).
#
#   Box 1: y ≈ 658-702
#   Box 2: y ≈ 816-860
#
# ~150px apart vertically on a 3850px-tall page. NOT a duplicate —
# these are two genuinely different list items that both happen to
# read 'W'. Same-page alone is still too loose a constraint.
#
# This is what motivated adding the coordinate-proximity check in
# `_boxes_close()` (pipeline/pdf_cleaning.py) — required BOTH same
# page AND near-identical bounding box position before calling
# something a real duplicate.

def _boxes_close(coords1, coords2, tolerance=15):
    y1_top, y1_bot = coords1[0][1], coords1[1][1]
    y2_top, y2_bot = coords2[0][1], coords2[1][1]
    return abs(y1_top - y2_top) < tolerance and abs(y1_bot - y2_bot) < tolerance


print("\n[coordinate check] CLOSE vs FAR per same-page duplicate group:")
for (text, page), els in real_dupes.items():
    coords_list = [el.metadata.to_dict().get("coordinates") for el in els]
    if all(c is not None for c in coords_list):
        pts = [c["points"] for c in coords_list]
        is_close = all(_boxes_close(pts[0], p) for p in pts[1:])
        print(f"  {'CLOSE' if is_close else 'FAR  '}  page={page}  text={text[:40]!r}")
    else:
        print(f"  NO-COORD  page={page}  text={text[:40]!r}")
# Result: 27 CLOSE (genuine double-detections — mostly section
# headings), 3 FAR (coincidental same-page matches: 'Demonstrating
# Superposition' p.8, 'W' p.32, 'weights' p.33 — all short, plausible
# words/phrases to legitimately repeat within one page of a technical
# paper). This 27/3 split is exactly what `resolve_duplicates()`
# reproduces automatically.


# ============================================================
# SECTION 7 — Applying the final resolver + sanity checks
# ============================================================
# The actual reusable function now lives in pipeline/pdf_cleaning.py.
# Below is how to use it and how to sanity-check its output on a new
# document.

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from the_rag.pipeline.pdf_cleaning import resolve_duplicates

    cleaned_elements = resolve_duplicates(elements_hires)
    print(f"\n[resolved] Before: {len(elements_hires)} elements")
    print(f"[resolved] After:  {len(cleaned_elements)} elements")
    print(f"[resolved] Removed: {len(elements_hires) - len(cleaned_elements)}")

    # Spot check: a known CLOSE heading should now appear exactly once,
    # with the correctly-classified type (Title, not Text).
    matches = [el for el in cleaned_elements if str(el).strip() == "References"]
    print(f"\n[sanity check] 'References' appears {len(matches)}x after cleaning "
          f"(expect 1)")
    for el in matches:
        print(f"  type={type(el).__name__}, page={el.metadata.page_number}")

    # Spot check: a known FAR case ('weights' on page 33) should be
    # UNTOUCHED — both/all occurrences should still be present.
    weights_before = sum(1 for el in elements_hires if str(el).strip() == "weights"
                          and el.metadata.page_number == 33)
    weights_after = sum(1 for el in cleaned_elements if str(el).strip() == "weights"
                         and el.metadata.page_number == 33)
    print(f"\n[sanity check] 'weights' on page 33: {weights_before} before, "
          f"{weights_after} after (expect equal — should be untouched)")