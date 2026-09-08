#!/usr/bin/env python3
import argparse
import copy
import json
import os
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "workflows", "manifold.json")
FLAT = os.path.join(REPO, "workflows", "manifold-flat.json")

NS = uuid.UUID("11111111-2222-3333-4444-555555555555")


def uid(*parts):
    return str(uuid.uuid5(NS, "|".join(str(p) for p in parts)))


REMOVE_BG_ID = 500

TOP_LEVEL_KEEP = {122, 316, REMOVE_BG_ID, 246, 330, 332, 405}

SOURCE = [193, 192, 248, 303, 312, 302, 55, 56, 242, 15, 298, 299, 420, 421, 422]
GENERATE = [319, 40, 318, 314, 315, 199, 279, 125, 126, 108, 87, 3, 119, 117,
            4, 247, 91, 18, 92, 202, 400]
RETOPO = [324, 402, 403, 401, 325, 326, 327, 328, 333, 329, 331, 334, 404,
          423, 424, 425, 426, 427, 428]

GROUPS = [("Source", SOURCE), ("Generate", GENERATE), ("Retopo", RETOPO)]

PROMOTED = {
    "Source": [],
    "Generate": [(3, "seed"), (3, "steps"), (3, "cfg"),
                 (18, "seed"), (18, "steps"), (18, "cfg")],
    "Retopo": [(325, "target_quads"), (334, "name")],
}

TUNE = [
    (18, "steps", 12),
    (423, "value", 3.0),
    (403, "voxel_scale", 3.0),
]

INPUT_NAMES = {
    ("Source", 122, 0): "image",
    ("Source", 122, 1): "mask",
    ("Source", 316, 0): "use_trellis",
    ("Source", 500, 0): "remove_background",
    ("Generate", 316, 0): "use_trellis",
    ("Generate", 298, 0): "pixal3d_positive",
    ("Generate", 299, 0): "trellis_positive",
    ("Generate", 298, 1): "pixal3d_negative",
    ("Generate", 299, 1): "trellis_negative",
    ("Retopo", 316, 0): "use_trellis",
    ("Retopo", 122, 0): "source_image",
}
OUTPUT_NAMES = {
    ("Source", 298, 0): "pixal3d_positive",
    ("Source", 298, 1): "pixal3d_negative",
    ("Source", 299, 0): "trellis_positive",
    ("Source", 299, 1): "trellis_negative",
    ("Generate", 247, 0): "voxel_preview",
    ("Generate", 400, 0): "mesh",
    ("Retopo", 404, 0): "clean_preview",
    ("Retopo", 329, 0): "quad_preview",
    ("Retopo", 331, 0): "planar_preview",
}

INSTANCE_POS = {"Source": [820, 100], "Generate": [1300, 100], "Retopo": [1780, 100]}
PREVIEW_POS = {246: [2320, 100], 405: [2320, 560], 330: [2320, 1020], 332: [2320, 1480]}
PREVIEW_TITLES = {246: "Voxel preview", 405: "Clean preview",
                  330: "Quad preview", 332: "Planar preview"}


WIDGET_ORDER = {
    "ManifoldBlenderClean": ["voxel_scale", "min_component", "smooth", "solidify"],
    "ManifoldBlenderDecimate": ["mode", "angle", "ratio", "target_faces"],
    "ManifoldBlenderFinish": ["target_height", "triangulate", "smart_uv",
                              "uv_angle", "uv_margin"],
    "ManifoldQuadRemesh": ["target_quads", "adaptivity", "anisotropy",
                           "sharp_edge", "smooth_normal", "edge_scaling"],
    "ManifoldSaveAsset": ["name", "note"],
    "ManifoldFromMesh": [],
    "ManifoldFreeModels": [],
}


def widget_names(node):
    named = node.get("widgets_values_named")
    if named:
        return list(named.keys())
    if node["type"] in WIDGET_ORDER:
        return WIDGET_ORDER[node["type"]]
    return []


def widget_items(node):
    named = node.get("widgets_values_named")
    if named:
        return dict(named)
    names = widget_names(node)
    vals = node.get("widgets_values") or []
    return {n: vals[i] for i, n in enumerate(names) if i < len(vals)}


def set_widget(node, name, value):
    names = widget_names(node)
    if name not in names:
        raise SystemExit(f"node {node['id']} has no widget {name}")
    node["widgets_values"][names.index(name)] = value
    if node.get("widgets_values_named"):
        node["widgets_values_named"][name] = value


def add_remove_background(wf):
    nodes = {n["id"]: n for n in wf["nodes"]}
    sw = nodes[248]
    if any(i.get("name") == "switch" for i in sw.get("inputs", [])):
        raise SystemExit("248 already has a switch input")
    value = sw["widgets_values"][0]
    lid = max(l[0] for l in wf["links"]) + 1
    wf["nodes"].append(dict(
        id=REMOVE_BG_ID, type="PrimitiveBoolean", pos=[0, 1180], size=[330, 70],
        flags={}, mode=0, inputs=[],
        outputs=[dict(name="BOOLEAN", type="BOOLEAN", links=[lid])],
        title="Remove background",
        properties={"cnr_id": "comfy-core", "ver": "0.33.0",
                    "Node name for S&R": "PrimitiveBoolean"},
        widgets_values=[value], widgets_values_named={"value": value},
        color="#322", bgcolor="#533"))
    sw["inputs"].append(dict(name="switch", type="BOOLEAN",
                             widget={"name": "switch"}, link=lid))
    wf["links"].append([lid, REMOVE_BG_ID, 0, 248, len(sw["inputs"]) - 1,
                        "BOOLEAN"])
    wf["last_node_id"] = max(wf["last_node_id"], REMOVE_BG_ID)
    wf["last_link_id"] = lid
    return wf


def build(src):
    wf = add_remove_background(copy.deepcopy(src))
    nodes = {n["id"]: n for n in wf["nodes"]}
    links = {l[0]: l for l in wf["links"]}

    assigned = {}
    for name, ids in GROUPS:
        for i in ids:
            if i in assigned:
                raise SystemExit(f"node {i} in two groups")
            assigned[i] = name
    unassigned = set(nodes) - set(assigned) - TOP_LEVEL_KEEP
    if unassigned:
        raise SystemExit(f"unpartitioned nodes: {sorted(unassigned)}")
    missing = sorted(i for i in TOP_LEVEL_KEEP if i not in nodes)
    if missing:
        raise SystemExit(f"top level nodes not in "
                         f"{os.path.relpath(FLAT, REPO)}: {missing}")

    defs = []
    instances = {}
    new_top_links = []
    next_link = max(links) + 1
    next_node = max(nodes) + 1

    plan = {}
    for name, ids in GROUPS:
        inside = set(ids)
        inner, bnd_in, bnd_out = [], [], []
        for l in wf["links"]:
            _, o, os_, t, ts, ty = l
            oi, ti = o in inside, t in inside
            if oi and ti:
                inner.append(l)
            elif ti:
                bnd_in.append(l)
            elif oi:
                bnd_out.append(l)
        plan[name] = dict(inside=inside, inner=inner, bnd_in=bnd_in, bnd_out=bnd_out)

    for name, ids in GROUPS:
        p = plan[name]
        in_keys, out_keys = [], []
        for l in p["bnd_in"]:
            k = (l[1], l[2])
            if k not in in_keys:
                in_keys.append(k)
        for l in p["bnd_out"]:
            k = (l[1], l[2])
            if k not in out_keys:
                out_keys.append(k)
        p["in_keys"], p["out_keys"] = in_keys, out_keys

    for name, ids in GROUPS:
        p = plan[name]
        sg_id = uid(name)
        inner_nodes = []
        for i in ids:
            n = copy.deepcopy(nodes[i])
            n.setdefault("flags", {})
            inner_nodes.append(n)
        inner_by_id = {n["id"]: n for n in inner_nodes}

        sg_links = []
        for l in p["inner"]:
            sg_links.append(dict(id=l[0], origin_id=l[1], origin_slot=l[2],
                                 target_id=l[3], target_slot=l[4], type=l[5]))

        sg_inputs = []
        for idx, (oid, oslot) in enumerate(p["in_keys"]):
            ls = [l for l in p["bnd_in"] if (l[1], l[2]) == (oid, oslot)]
            ty = ls[0][5]
            sname = INPUT_NAMES.get((name, oid, oslot))
            if sname is None:
                tgt = inner_by_id[ls[0][3]]
                sname = tgt["inputs"][ls[0][4]]["name"]
            link_ids = []
            for l in ls:
                link_ids.append(l[0])
                sg_links.append(dict(id=l[0], origin_id=-10, origin_slot=idx,
                                     target_id=l[3], target_slot=l[4], type=l[5]))
            sg_inputs.append(dict(id=uid(name, "in", idx), name=sname, type=ty,
                                  linkIds=link_ids, localized_name=sname,
                                  pos=[-100, 40 + idx * 20]))

        sg_outputs = []
        for idx, (oid, oslot) in enumerate(p["out_keys"]):
            ls = [l for l in p["bnd_out"] if (l[1], l[2]) == (oid, oslot)]
            ty = ls[0][5]
            sname = OUTPUT_NAMES.get((name, oid, oslot))
            if sname is None:
                sname = inner_by_id[oid]["outputs"][oslot].get("name") or ty
            lid = next_link
            next_link += 1
            sg_links.append(dict(id=lid, origin_id=oid, origin_slot=oslot,
                                 target_id=-20, target_slot=idx, type=ty))
            sg_outputs.append(dict(id=uid(name, "out", idx), name=sname, type=ty,
                                   linkIds=[lid], localized_name=sname,
                                   pos=[900, 40 + idx * 20]))

        keep_link_ids = {l["id"] for l in sg_links}
        for n in inner_nodes:
            for inp in n.get("inputs", []):
                if inp.get("link") is not None and inp["link"] not in keep_link_ids:
                    inp["link"] = None
            for out in n.get("outputs", []):
                if out.get("links"):
                    kept = [x for x in out["links"] if x in keep_link_ids]
                    out["links"] = kept or None
            n.pop("order", None)
        for idx, (oid, oslot) in enumerate(p["out_keys"]):
            lid = sg_outputs[idx]["linkIds"][0]
            out = inner_by_id[oid]["outputs"][oslot]
            out["links"] = (out.get("links") or []) + [lid]

        defs.append(dict(
            id=sg_id, version=1,
            state=dict(lastGroupId=0,
                       lastNodeId=max(n["id"] for n in inner_nodes),
                       lastLinkId=max([l["id"] for l in sg_links] or [0]),
                       lastRerouteId=0),
            revision=0, config={}, name=name,
            inputNode=dict(id=-10, bounding=[-200, 20, 120, 60 + 20 * len(sg_inputs)]),
            outputNode=dict(id=-20, bounding=[900, 20, 120, 60 + 20 * len(sg_outputs)]),
            inputs=sg_inputs, outputs=sg_outputs, widgets=[],
            nodes=inner_nodes, groups=[], links=sg_links, extra={}))

        proxy = []
        for nid, wname in PROMOTED[name]:
            n = inner_by_id[nid]
            if wname not in widget_names(n):
                raise SystemExit(f"{name}: node {nid} has no widget {wname}")
            proxy.append([str(nid), wname])

        inst = dict(
            id=next_node, type=sg_id, pos=INSTANCE_POS[name], size=[340, 400],
            flags={}, mode=0,
            inputs=[dict(name=s["name"], type=s["type"], link=None) for s in sg_inputs],
            outputs=[dict(name=s["name"], type=s["type"], links=[]) for s in sg_outputs],
            properties=dict(proxyWidgets=proxy, cnr_id="comfy-core", ver="0.34.5"),
            widgets_values=[])
        next_node += 1
        instances[name] = inst
        p["instance"] = inst

    def owner(nid):
        return assigned.get(nid)

    def resolve_out(nid, slot):
        g = owner(nid)
        if g is None:
            return nid, slot
        idx = plan[g]["out_keys"].index((nid, slot))
        return plan[g]["instance"]["id"], idx

    def resolve_in(l):
        g = owner(l[3])
        if g is None:
            return l[3], l[4]
        idx = plan[g]["in_keys"].index((l[1], l[2]))
        return plan[g]["instance"]["id"], idx

    top_nodes = [nodes[i] for i in TOP_LEVEL_KEEP]
    for n in top_nodes:
        for inp in n.get("inputs", []):
            inp["link"] = None
        for out in n.get("outputs", []):
            out["links"] = []
        n.pop("order", None)
    for name, _ in GROUPS:
        top_nodes.append(instances[name])
    top_by_id = {n["id"]: n for n in top_nodes}

    seen = set()
    for l in wf["links"]:
        _, o, os_, t, ts, ty = l
        go, gt = owner(o), owner(t)
        if go is not None and go == gt:
            continue
        so_id, so_slot = resolve_out(o, os_)
        ti_id, ti_slot = resolve_in(l)
        key = (so_id, so_slot, ti_id, ti_slot)
        if key in seen:
            continue
        seen.add(key)
        lid = next_link
        next_link += 1
        new_top_links.append([lid, so_id, so_slot, ti_id, ti_slot, ty])
        src_out = top_by_id[so_id]["outputs"][so_slot]
        src_out["links"] = (src_out.get("links") or []) + [lid]
        tgt = top_by_id[ti_id]
        tgt_in = tgt["inputs"][ti_slot]
        tgt_in["link"] = lid

    for n in top_nodes:
        for out in n.get("outputs", []):
            if not out.get("links"):
                out["links"] = None

    for nid, pos in PREVIEW_POS.items():
        if nid in top_by_id:
            top_by_id[nid]["pos"] = pos
            top_by_id[nid]["title"] = PREVIEW_TITLES[nid]
    top_by_id[122]["pos"] = [0, 100]
    top_by_id[316]["pos"] = [0, 1040]
    top_by_id[REMOVE_BG_ID]["pos"] = [0, 1180]

    wf["nodes"] = top_nodes
    wf["links"] = new_top_links
    wf["groups"] = []
    wf["definitions"] = dict(subgraphs=defs)
    wf["last_node_id"] = next_node - 1
    wf["last_link_id"] = next_link - 1

    for d in defs:
        for n in d["nodes"]:
            for nid, wname, val in TUNE:
                if n["id"] == nid:
                    set_widget(n, wname, val)
    return wf


def validate(wf):
    errs = []
    top = {n["id"]: n for n in wf["nodes"]}
    defs = {d["id"]: d for d in wf["definitions"]["subgraphs"]}
    tl = {l[0]: l for l in wf["links"]}

    def compatible(a, b):
        if a == b or "*" in (a, b):
            return True
        return a in str(b).split(",") or b in str(a).split(",")

    def sockets(node):
        if node["type"] in defs:
            d = defs[node["type"]]
            return ([(s["name"], s["type"]) for s in d["inputs"]],
                    [(s["name"], s["type"]) for s in d["outputs"]])
        return ([(i.get("name"), i.get("type")) for i in node.get("inputs", [])],
                [(o.get("name"), o.get("type")) for o in node.get("outputs", [])])

    for l in wf["links"]:
        lid, o, os_, t, ts, ty = l
        if o not in top or t not in top:
            errs.append(f"top link {lid} endpoint missing")
            continue
        _, oo = sockets(top[o])
        ii, _ = sockets(top[t])
        if os_ >= len(oo):
            errs.append(f"top link {lid} origin slot {os_} out of range on {o}")
        elif not compatible(ty, oo[os_][1]):
            errs.append(f"top link {lid} type {ty} != origin {oo[os_][1]}")
        if ts >= len(ii):
            errs.append(f"top link {lid} target slot {ts} out of range on {t}")
        elif not compatible(ty, ii[ts][1]):
            errs.append(f"top link {lid} type {ty} != target {ii[ts][1]}")

    for n in wf["nodes"]:
        for inp in n.get("inputs", []):
            if inp.get("link") is not None and inp["link"] not in tl:
                errs.append(f"node {n['id']} input {inp.get('name')} dangling link")
        for out in n.get("outputs", []):
            for x in (out.get("links") or []):
                if x not in tl:
                    errs.append(f"node {n['id']} output dangling link {x}")

    for d in defs.values():
        by = {n["id"]: n for n in d["nodes"]}
        ids = {l["id"] for l in d["links"]}
        for l in d["links"]:
            for end, slot, isout in ((l["origin_id"], l["origin_slot"], True),
                                     (l["target_id"], l["target_slot"], False)):
                if end in (-10, -20):
                    arr = d["inputs"] if end == -10 else d["outputs"]
                    if slot >= len(arr):
                        errs.append(f"{d['name']} link {l['id']} boundary slot {slot} oob")
                    elif not compatible(l["type"], arr[slot]["type"]):
                        errs.append(f"{d['name']} link {l['id']} boundary type mismatch")
                elif end not in by:
                    errs.append(f"{d['name']} link {l['id']} node {end} missing")
                else:
                    arr = by[end]["outputs" if isout else "inputs"]
                    if slot >= len(arr):
                        errs.append(f"{d['name']} link {l['id']} slot {slot} oob on {end}")
                    elif not compatible(l["type"], arr[slot].get("type")):
                        errs.append(f"{d['name']} link {l['id']} type mismatch on {end}")
        for n in d["nodes"]:
            for inp in n.get("inputs", []):
                if inp.get("link") is not None and inp["link"] not in ids:
                    errs.append(f"{d['name']} node {n['id']} dangling input link")
            for out in n.get("outputs", []):
                for x in (out.get("links") or []):
                    if x not in ids:
                        errs.append(f"{d['name']} node {n['id']} dangling output link {x}")
        for s in d["inputs"] + d["outputs"]:
            for x in s["linkIds"]:
                if x not in ids:
                    errs.append(f"{d['name']} socket {s['name']} dangling linkId {x}")

    for n in wf["nodes"]:
        if n["type"] in defs:
            by = {x["id"]: x for x in defs[n["type"]]["nodes"]}
            for nid, wname in n["properties"].get("proxyWidgets", []):
                if int(nid) not in by:
                    errs.append(f"proxyWidget node {nid} missing")
    return errs


def flatten(wf):
    defs = {d["id"]: d for d in wf["definitions"]["subgraphs"]} if "definitions" in wf else {}

    def walk(nodes, links, prefix, boundary_in, out_collect):
        by = {n["id"]: n for n in nodes}
        lby = {}
        for l in links:
            if isinstance(l, dict):
                lby[l["id"]] = (l["origin_id"], l["origin_slot"], l["target_id"],
                                l["target_slot"], l["type"])
            else:
                lby[l[0]] = (l[1], l[2], l[3], l[4], l[5])

        memo = {}

        def res_out(nid, slot):
            if nid == -10:
                return boundary_in[slot]
            n = by[nid]
            if n["type"] in defs:
                key = (prefix, nid)
                if key not in memo:
                    memo[key] = expand(n, prefix)
                return memo[key][slot]
            return (f"{prefix}{nid}", slot)

        def expand(inst, pfx):
            d = defs[inst["type"]]
            bin_ = {}
            for i, inp in enumerate(inst.get("inputs", [])):
                if inp.get("link") is None:
                    continue
                o, os_, _, _, _ = lby[inp["link"]]
                bin_[i] = res_out(o, os_)
            sub_prefix = f"{pfx}{inst['id']}:"
            return walk(d["nodes"], d["links"], sub_prefix, bin_, out_collect)

        for n in nodes:
            if n["type"] in defs:
                key = (prefix, n["id"])
                if key not in memo:
                    memo[key] = expand(n, prefix)
                continue
            if n["type"] in ("MarkdownNote", "Note"):
                continue
            gid = f"{prefix}{n['id']}"
            ins = {}
            for k, v in widget_items(n).items():
                ins[k] = v
            for inp in n.get("inputs", []):
                if inp.get("link") is None:
                    continue
                o, os_, _, _, _ = lby[inp["link"]]
                ins[inp["name"]] = list(res_out(o, os_))
            out_collect[gid] = dict(class_type=n["type"], inputs=ins)

        res = {}
        for l in lby.values():
            if l[2] == -20:
                res[l[3]] = res_out(l[0], l[1])
        return res

    out = {}
    walk(wf["nodes"], wf["links"], "", {}, out)
    return out


def canon(flat):
    sig = {}

    def node_sig(key, depth=0, seen=()):
        if key in sig:
            return sig[key]
        if key in seen or depth > 60:
            return f"<cycle {flat[key]['class_type']}>"
        n = flat[key]
        parts = [n["class_type"]]
        for k in sorted(n["inputs"]):
            v = n["inputs"][k]
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and v[0] in flat:
                parts.append(f"{k}=<{node_sig(v[0], depth + 1, seen + (key,))}#{v[1]}>")
            else:
                parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
        s = "(" + ";".join(parts) + ")"
        return s

    return sorted(node_sig(k) for k in flat)


def dumps(obj):
    return json.dumps(obj, indent=2) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(FLAT):
        raise SystemExit(f"missing {FLAT}")
    with open(FLAT) as f:
        src = json.load(f)
    if "definitions" in src:
        raise SystemExit(f"{FLAT} unexpectedly contains subgraphs")

    for n in src["nodes"]:
        for nid, wname, val in TUNE:
            if n["id"] == nid:
                set_widget(n, wname, val)

    flat_text = dumps(src)
    wf = build(src)
    wf_text = dumps(wf)
    errs = validate(wf)
    print(f"[a] structural validation: {len(errs)} error(s)")
    for e in errs:
        print("    " + e)
    failed = bool(errs)

    fa = flatten(src)
    fb = flatten(wf)

    bkey = next((k for k, v in fb.items()
                 if v["class_type"] == "PrimitiveBoolean"
                 and k.endswith(str(REMOVE_BG_ID))), None)
    if bkey:
        bval = fb[bkey]["inputs"]["value"]
        del fb[bkey]
        for v in fb.values():
            for name, val in list(v["inputs"].items()):
                if isinstance(val, list) and len(val) == 2 and val[0] == bkey:
                    v["inputs"][name] = bval
        print(f"    (inlined new '{'Remove background'}' boolean = {bval} "
              f"for comparison)")
    print(f"[b] flatten: flat={len(fa)} nodes, subgraphed={len(fb)} nodes")
    ca, cb = canon(fa), canon(fb)
    only_a = [x for x in ca if x not in cb]
    only_b = [x for x in cb if x not in ca]
    if not only_a and not only_b:
        print("    canonical graphs identical (tuning applied to both sides)")
    else:
        failed = True
        print(f"    MISMATCH: {len(only_a)} only in flat, {len(only_b)} only in subgraphed")
        for x in only_a[:6]:
            print("    -", x[:220])
        for x in only_b[:6]:
            print("    +", x[:220])

    if args.check:
        for path, text in ((FLAT, flat_text), (SRC, wf_text)):
            with open(path) as f:
                if f.read() != text:
                    failed = True
                    print(f"[c] {os.path.relpath(path, REPO)} is stale")
        print("flatten reproduced in python only; confirm in the ComfyUI "
              "frontend after node changes")
        raise SystemExit(1 if failed else 0)

    for path, text in ((FLAT, flat_text), (SRC, wf_text)):
        with open(path, "w") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(path, REPO)}")

    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
