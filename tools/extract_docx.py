"""Dump all readable content of a .docx file: paragraphs, tables, text boxes, headers/footers."""
import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn


def iter_block_items(parent):
    """Yield Paragraph and Table objects in document order (body-level)."""
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def main(path: str) -> None:
    doc = Document(path)
    print("=" * 80)
    print("SECTIONS:", len(doc.sections))
    for i, s in enumerate(doc.sections):
        print(f"  section {i}: page {s.page_width}x{s.page_height}, margins {s.left_margin}/{s.right_margin}/{s.top_margin}/{s.bottom_margin}")

    print("=" * 80)
    print("BODY:")
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name if block.style else "?"
            text = block.text
            if text.strip() or style.startswith("Heading"):
                print(f"[P:{style}] {text}")
        else:
            print(f"[TABLE {len(block.rows)}x{len(block.columns)}]")
            for r_i, row in enumerate(block.rows):
                cells = []
                for cell in row.cells:
                    cells.append(" / ".join(p.text for p in cell.paragraphs).strip())
                print(f"  R{r_i}: " + " | ".join(cells))

    # Headers / footers
    for i, s in enumerate(doc.sections):
        for kind, part in (("header", s.header), ("footer", s.footer)):
            txt = "\n".join(p.text for p in part.paragraphs if p.text.strip())
            tbl_txt = []
            for t in part.tables:
                for row in t.rows:
                    tbl_txt.append(" | ".join(c.text for c in row.cells))
            if txt or tbl_txt:
                print(f"=== {kind} section {i} ===")
                if txt:
                    print(txt)
                for line in tbl_txt:
                    print(line)

    # Any stray text in textboxes / shapes (w:txbxContent)
    print("=" * 80)
    print("ALL w:t TEXT NODES (deduped):")
    seen = set()
    for t in doc.element.body.iter(qn("w:t")):
        if t.text and t.text.strip() not in seen:
            seen.add(t.text.strip())
    # too noisy; only print txbx content instead
    print("(skipped raw nodes)")
    txbx = doc.element.body.findall(".//" + qn("w:txbxContent"))
    if txbx:
        print("TEXTBOXES:", len(txbx))
        for i, tb in enumerate(txbx):
            print(f"--- textbox {i} ---")
            print(" ".join(t.text or "" for t in tb.iter(qn("w:t"))))

    # inline images
    rels = doc.part.rels
    images = [r for r in rels.values() if "image" in r.reltype]
    print("=" * 80)
    print("IMAGES:", len(images))
    for r in images:
        print("  ", r.target_ref, len(r.target_part.blob) if hasattr(r.target_part, "blob") else "")

    print("=" * 80)
    print("CORE PROPERTIES:")
    cp = doc.core_properties
    for name in ("title", "subject", "author", "last_modified_by", "created", "modified", "comments"):
        print(f"  {name}: {getattr(cp, name, None)}")


if __name__ == "__main__":
    main(sys.argv[1])
