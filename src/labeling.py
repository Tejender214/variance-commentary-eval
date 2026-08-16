"""
Blinded labeling queue. Week 2.

Blinding is non-negotiable. Shuffle outputs from ALL conditions into one
randomized queue and strip condition labels. If you know which system produced
an output you will be kinder to your favourite. Everyone is.

Keep the mapping from queue_id -> condition in a SEPARATE file that neither
labeler opens until grading is finished.
"""

import json
import random
import uuid
from pathlib import Path

LABELS_DIR = Path(__file__).resolve().parent.parent / "data" / "labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)


def build_queue(outputs: list, seed: int = 42) -> tuple:
    """
    outputs: list of {condition, company, period, text}
    Returns (queue, keymap). Write queue to a file labelers open; write keymap
    to a file they do NOT.
    """
    queue, keymap = [], {}
    for o in outputs:
        qid = uuid.uuid4().hex[:8]
        queue.append({"queue_id": qid, "text": o["text"]})
        keymap[qid] = {
            "condition": o["condition"],
            "company": o["company"],
            "period": o["period"],
        }
    random.Random(seed).shuffle(queue)

    (LABELS_DIR / "queue.json").write_text(json.dumps(queue, indent=2))
    (LABELS_DIR / "KEYMAP_DO_NOT_OPEN.json").write_text(json.dumps(keymap, indent=2))
    print(f"queue: {len(queue)} items -> {LABELS_DIR/'queue.json'}")
    return queue, keymap
