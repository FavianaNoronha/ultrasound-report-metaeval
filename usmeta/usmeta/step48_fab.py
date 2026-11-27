"""Off-schema errors (amendment 1 item 8): a fabricated major finding the extractor has no field for,
and its paired harmless control, a normal statement on the same topic that the reference does not make.

Each pair is (fabricated text, normal text). The writer is asked to state the item like any other fact;
the gold filter then checks it is stated with the intended polarity (regex below), else the report is dropped.
"""
import hashlib, re

from . import step45_freetext as base

PAIRS = {
    "breast": [
        dict(key="axillary_node",
             fab=dict(text="an enlarged axillary lymph node with loss of the fatty hilum",
                      pos=r"axillary", neg=r"\bno\b[^.]{0,40}axillary|axillary[^.]{0,40}\b(normal|not enlarged|unremarkable)"),
             norm=dict(text="no enlarged axillary lymph nodes",
                       pos=r"\bno\b[^.]{0,40}axillary|axillary[^.]{0,40}\b(normal|not enlarged|unremarkable)", neg=r"loss of[^.]{0,20}hilum")),
        dict(key="skin",
             fab=dict(text="thickening of the overlying skin",
                      pos=r"skin[^.]{0,30}thicken|thicken[^.]{0,30}skin", neg=r"normal skin|skin[^.]{0,25}normal|no skin thickening"),
             norm=dict(text="normal thickness of the overlying skin",
                       pos=r"skin[^.]{0,30}normal|normal[^.]{0,25}skin|no skin thickening", neg=r"skin[^.]{0,15}(is |are )?thickened")),
    ],
    "thyroid": [
        dict(key="cervical_node",
             fab=dict(text="an enlarged cervical lymph node",
                      pos=r"lymph node|lymphadenopath", neg=r"\bno\b[^.]{0,40}(lymph|lymphadenopath)|lymph[^.]{0,40}\b(normal|not enlarged|unremarkable)"),
             norm=dict(text="no enlarged cervical lymph nodes",
                       pos=r"\bno\b[^.]{0,40}(lymph|lymphadenopath)|lymph[^.]{0,40}\b(normal|not enlarged|unremarkable)", neg=r"\ban enlarged[^.]{0,20}lymph")),
        dict(key="trachea",
             fab=dict(text="deviation of the trachea",
                      pos=r"trache\w*[^.]{0,30}deviat|deviat\w*[^.]{0,30}trache", neg=r"midline|not deviated|no tracheal deviation"),
             norm=dict(text="the trachea is midline",
                       pos=r"trache\w*[^.]{0,30}midline|midline[^.]{0,20}trache|no tracheal deviation", neg=r"trache\w*[^.]{0,15}(is )?deviated")),
    ],
    "fetal": [
        dict(key="ventricles",
             fab=dict(text="dilated lateral ventricles (ventriculomegaly)",
                      pos=r"ventriculomegal|dilat\w*[^.]{0,30}ventric|ventric\w*[^.]{0,30}dilat", neg=r"no ventriculomegaly|not dilated|ventric\w*[^.]{0,30}normal"),
             norm=dict(text="lateral ventricles of normal width",
                       pos=r"ventric\w*[^.]{0,40}normal|normal[^.]{0,30}ventric|no ventriculomegaly", neg=r"\bdilated lateral|ventriculomegaly(?! is not)")),
        dict(key="cavum",
             fab=dict(text="the cavum septi pellucidi is absent",
                      pos=r"(cavum|septi|septum)[^.]{0,40}(absent|not (seen|visualized|visualised|visible))|(absent|absence of|non-?visuali[sz]ed)[^.]{0,30}(cavum|septum|septi)",
                      neg=r"(cavum|septi|septum)[^.]{0,40}(is |are )?(present|visible|normal)"),
             norm=dict(text="the cavum septi pellucidi is visible",
                       pos=r"(cavum|septi|septum)[^.]{0,40}(visible|present|seen|visuali[sz]ed|normal)", neg=r"absent|not (seen|visualized|visualised|visible)")),
    ],
}


def pick_pair(seed, case_id, organ):
    h = int(hashlib.sha256(f"{seed}|{case_id}|fabpair".encode()).hexdigest(), 16)
    return PAIRS[organ][h % len(PAIRS[organ])]


def extra(pair, kind):
    d = pair[kind]
    return {"key": pair["key"], "kind": kind, "text": d["text"], "pos": d["pos"], "neg": d["neg"]}


# --- patch the Step 45 writer list and gold check so an '_extra' fact is described and verified ---
_describe, _check = base.describe, base.check_field


def describe(organ, f):
    out = _describe(organ, {k: v for k, v in f.items() if k != "_extra"})
    if "_extra" in f:
        out.append(f["_extra"]["text"])
    return out


def check_field(organ, k, v, t):
    if k == "_extra":
        return bool(re.search(v["pos"], t)) and not re.search(v["neg"], t)
    return _check(organ, k, v, t)


base.describe, base.check_field = describe, check_field


def selftest():
    cases = {
        ("breast", "fab", "axillary_node"): ("An enlarged axillary lymph node with loss of the fatty hilum is noted.", "No axillary lymphadenopathy."),
        ("breast", "norm", "axillary_node"): ("No enlarged axillary lymph nodes.", "An enlarged axillary lymph node is seen."),
        ("thyroid", "fab", "trachea"): ("The trachea is deviated to the right.", "The trachea is midline."),
        ("thyroid", "norm", "cervical_node"): ("No enlarged cervical lymph nodes are seen.", "An enlarged cervical lymph node is present."),
        ("fetal", "fab", "ventricles"): ("Ventriculomegaly is present.", "Lateral ventricles are of normal width."),
        ("fetal", "norm", "cavum"): ("The cavum septi pellucidi is visible.", "The cavum septi pellucidi is absent."),
        ("fetal", "fab", "cavum"): ("Absent cavum septi pellucidi.", "The cavum septi pellucidi is visible."),
    }
    bad = 0
    for (organ, kind, key), (good, wrong) in cases.items():
        pair = next(p for p in PAIRS[organ] if p["key"] == key)
        e = extra(pair, kind)
        ok_good = check_field(organ, "_extra", e, good.lower())
        ok_wrong = check_field(organ, "_extra", e, wrong.lower())
        if not ok_good or ok_wrong:
            bad += 1
            print("FAIL", organ, kind, key, ok_good, ok_wrong)
    print("selftest", "ok" if not bad else f"{bad} failures")


if __name__ == "__main__":
    selftest()
