elements = [
    # 1. Title — page-level heading
    {
        "type": "Title",
        "text": "RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control",
        "metadata": {
            "page_number": 2,
            "coordinates": {"points": [[70, 40], [1780, 40], [1780, 90], [70, 90]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 2. NarrativeText — a normal paragraph
    {
        "type": "NarrativeText",
        "text": "We propose Vision-Language-Action models, a novel class of models that leverage web-scale vision-language pretraining to directly output robotic control actions.",
        "metadata": {
            "page_number": 3,
            "coordinates": {"points": [[70, 200], [1780, 200], [1780, 260], [70, 260]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 3. ListItem — bullet/numbered content
    {
        "type": "ListItem",
        "text": "1. Co-fine-tune on web-scale VQA data and robot trajectory data jointly.",
        "metadata": {
            "page_number": 4,
            "coordinates": {"points": [[90, 300], [1000, 300], [1000, 330], [90, 330]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 4. Header — repeated running header
    {
        "type": "Header",
        "text": "RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control",
        "metadata": {
            "page_number": 8,
            "coordinates": {"points": [[70, 20], [1780, 20], [1780, 45], [70, 45]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 5. Footer — page number / running footer
    {
        "type": "Footer",
        "text": "8",
        "metadata": {
            "page_number": 8,
            "coordinates": {"points": [[900, 1750], [920, 1750], [920, 1770], [900, 1770]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 6. Table — real table, with structured HTML preserved
    {
        "type": "Table",
        "text": "Method Success Rate Seen Unseen RT-1 92% 45% RT-2-PaLI-X 97% 76%",
        "metadata": {
            "page_number": 11,
            "coordinates": {"points": [[100, 400], [1600, 400], [1600, 700], [100, 700]], "system": "PixelSpace"},
            "text_as_html": "<table><tr><th>Method</th><th>Success Rate Seen</th><th>Unseen</th></tr><tr><td>RT-1</td><td>92%</td><td>45%</td></tr><tr><td>RT-2-PaLI-X</td><td>97%</td><td>76%</td></tr></table>",
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 7. Formula — relabeled from UncategorizedText via your regex pass
    {
        "type": "Formula",  # originally "UncategorizedText" before relabeling
        "text": "\u201cterminate \u0394pos_x \u0394pos_y \u0394pos_z \u0394rot_x \u0394rot_y \u0394rot_z gripper_extension\u201d",
        "metadata": {
            "page_number": 6,
            "coordinates": {"points": [[300, 500], [1400, 500], [1400, 550], [300, 550]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 8. Image — a REAL fragmented diagram piece (page 2, Figure 1), empty text
    {
        "type": "Image",
        "text": "",  # hi_res does not OCR inside Image regions — confirmed this session
        "metadata": {
            "page_number": 2,
            "coordinates": {"points": [[850, 480], [1100, 480], [1100, 650], [850, 650]], "system": "PixelSpace"},
            "image_path": "Doc_corpus/extracted_images/rt2/figure-2-6.jpg",
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 9. UncategorizedText — diagram-label fragment leaked from the SAME Figure 1
    {
        "type": "UncategorizedText",
        "text": "ViT",
        "metadata": {
            "page_number": 2,
            "coordinates": {"points": [[1140, 610], [1200, 610], [1200, 640], [1140, 640]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 10. UncategorizedText — genuine OCR garbage, NOT yet filtered (open TODO)
    {
        "type": "UncategorizedText",
        "text": "DOO OOca + 444th dd",
        "metadata": {
            "page_number": 2,
            "coordinates": {"points": [[900, 520], [1050, 520], [1050, 545], [900, 545]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 11. FigureCaption — a real, correctly extracted caption
    {
        "type": "FigureCaption",
        "text": "Figure 1 | RT-2 overview: we represent robot actions as another language, which can be cast into text tokens and trained jointly with web-scale vision-language datasets.",
        "metadata": {
            "page_number": 2,
            "coordinates": {"points": [[70, 1250], [1780, 1250], [1780, 1290], [70, 1290]], "system": "PixelSpace"},
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 12. Image — the missing-text case, page 25 chat-bubble panel
    {
        "type": "Image",
        "text": "",  # actual bubble text ("Pick up the object that is different...") is
                       # NOT extracted here — this is the exact silent-loss case found this session
        "metadata": {
            "page_number": 25,
            "coordinates": {"points": [[300, 150], [700, 150], [700, 390], [300, 390]], "system": "PixelSpace"},
            "image_path": "Doc_corpus/extracted_images/rt2/figure-25-51.jpg",
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 13. Image — a tiny decorative icon, flagged for the size-based filter (not yet applied)
    {
        "type": "Image",
        "text": "",
        "metadata": {
            "page_number": 25,
            "coordinates": {"points": [[100, 150], [163, 150], [163, 213], [100, 213]], "system": "PixelSpace"},
            "image_path": "Doc_corpus/extracted_images/rt2/figure-25-50.jpg",
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 14. [PROPOSED, not yet real] — a caption element, showing the target shape
    #     for the multimodal-captioning fix once it's implemented
    {
        "type": "ImageCaption",  # not a native unstructured category — a custom type
                                    # you'd add yourself once captioning is wired up
        "text": "A robot arm on a desk reaches toward a row of snack items (a water bottle, soda cans, a chocolate bar). Overlaid UI shows the prompt 'Pick up the object that is different from all other objects' and the model's plan: 'Pick rxbar chocolate.'",
        "metadata": {
            "page_number": 25,
            "coordinates": {"points": [[300, 150], [700, 150], [700, 390], [300, 390]], "system": "PixelSpace"},
            "source_image_path": "Doc_corpus/extracted_images/rt2/figure-25-51.jpg",  # links caption back to its image
            "generated_by": "gpt-5-mini",
            "filename": "RT2Vision_Language.pdf",
        },
    },

    # 15. Table — a Table element that LOOKS real but might be an equation-wrapper
    #     (the open, never-resolved question from your original context pack)
    {
        "type": "Table",  # unverified — could be a real table or an equation rendered
                            # as a single-cell HTML table; never individually checked
        "text": "\u0394T = [0.1, -0.2, 0]  \u0394R = [10\u00b0, 25\u00b0, -7\u00b0]",
        "metadata": {
            "page_number": 2,
            "coordinates": {"points": [[1250, 900], [1600, 900], [1600, 970], [1250, 970]], "system": "PixelSpace"},
            "text_as_html": "<table><tr><td>\u0394T = [0.1, -0.2, 0]  \u0394R = [10\u00b0, 25\u00b0, -7\u00b0]</td></tr></table>",
            "filename": "RT2Vision_Language.pdf",
        },
    },
]