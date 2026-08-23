# from unstructured.partition.auto import partition # looks at the file extension/content and routes to the right file-type-specific partitioner (partition_html, partition_pdf, etc.) automatically

# filepath = "Doc_corpus/html/Transfusion-Arxiv.html"
# elements = partition(filename=filepath)

# print(f"Total elements: {len(elements)}")
# print()

# for i, el in enumerate(elements[:15]):
#     print(f"[{i}] {type(el).__name__!r:20} text={str(el)[:40]!r}")
#     print(f"     metadata: {el.metadata.to_dict()}")
#     print()

from unstructured.partition.auto import partition

for filepath in ["Doc_corpus/html/Our_First_Generalist_Policy.html", "Doc_corpus/html/Transfusion-Arxiv.html"]:
    print(f"\n=== {filepath} ===")
    elements = partition(filename=filepath)
    for el in elements:
        if type(el).__name__ == "Title":
            depth = el.metadata.to_dict().get("category_depth", "—")
            print(f"  depth={depth}\t{str(el)[:60]!r}")
            
import glob
from unstructured.partition.auto import partition

for filepath in glob.glob("Doc_corpus/html/*.html"):
    elements = partition(filename=filepath)
    total = len(elements)
    with_depth = sum(1 for el in elements if "category_depth" in el.metadata.to_dict())
    pct = (with_depth / total * 100) if total else 0
    print(f"{with_depth}/{total} ({pct:.0f}%)\t{filepath}")