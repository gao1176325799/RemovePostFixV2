#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import argparse
from dataclasses import dataclass
from lxml import etree

COMSIGNAL_DEF = "/MICROSAR/Com/ComConfig/ComSignal"

# 你要求的固定 XML 头
DESIRED_DECL_LF = b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'

def get_autosar_namespace(root):
    if root.tag.startswith("{"):
        return root.tag.split("}")[0][1:]
    raise RuntimeError("Cannot detect AUTOSAR namespace")

def text_of(elem):
    return elem.text.strip() if (elem is not None and elem.text) else ""

def load_arxml(path):
    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    tree = etree.parse(path, parser)
    root = tree.getroot()
    NS = {"a": get_autosar_namespace(root)}
    return tree, root, NS

def save_arxml_strict(tree, out_path):
    """
    写文件时强制：
    1) XML declaration = 你指定的那一行
    2) CRLF
    """
    xml_bytes = etree.tostring(
        tree,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=False
    )

    # 统一成 LF，方便处理“第一行”
    xml_bytes = xml_bytes.replace(b"\r\n", b"\n")

    # 替换/插入第一行 XML 声明
    first, sep, rest = xml_bytes.partition(b"\n")
    if first.startswith(b"<?xml"):
        xml_bytes = DESIRED_DECL_LF + rest
    else:
        xml_bytes = DESIRED_DECL_LF + xml_bytes

    # 再统一成 CRLF
    xml_bytes = xml_bytes.replace(b"\n", b"\r\n")

    with open(out_path, "wb") as f:
        f.write(xml_bytes)

@dataclass
class Config:
    ocan_pat: re.Pattern

def iter_ecuc_container_values(root, NS):
    # 每一步都用这个入口拿容器，避免缓存导致“删除后引用失效”
    return root.findall(".//a:ECUC-CONTAINER-VALUE", namespaces=NS)

def step1_remove_comsignal_without_ocan(root, NS, cfg: Config):
    """
    Step1: 在 ComSignal 容器中，SHORT-NAME 不含 oCANxx -> 删除整个容器
    """
    removed = 0
    scanned = 0

    for cv in iter_ecuc_container_values(root, NS):
        container_def = text_of(cv.find("a:DEFINITION-REF", namespaces=NS))
        if container_def != COMSIGNAL_DEF:
            continue

        scanned += 1
        short_name = text_of(cv.find("a:SHORT-NAME", namespaces=NS))

        if not cfg.ocan_pat.search(short_name):
            parent = cv.getparent()
            if parent is not None:
                parent.remove(cv)
                removed += 1

    return {"step": 1, "scanned": scanned, "removed": removed}

def step2_remove_xcp_rx_tx_comsignals(root, NS):
    """
    Step2 (file2 -> file3):
    在 ComSignal 容器中：
    - SHORT-NAME 以 'XCP_Rx' 或 'XCP_Tx' 开头 → 删除整个容器
    """
    removed = 0
    scanned = 0

    for cv in root.findall(".//a:ECUC-CONTAINER-VALUE", namespaces=NS):
        # 只处理 ComSignal（容器直属 DEFINITION-REF）
        container_def = text_of(cv.find("a:DEFINITION-REF", namespaces=NS))
        if container_def != COMSIGNAL_DEF:
            continue

        scanned += 1
        short_name = text_of(cv.find("a:SHORT-NAME", namespaces=NS))

        short_name_l = short_name.lower()
        if "xcp_rx" in short_name_l or "xcp_tx" in short_name_l:
            parent = cv.getparent()
            if parent is not None:
                parent.remove(cv)
                removed += 1

    return {
        "step": 2,
        "scanned": scanned,
        "removed": removed,
        "rule": "SHORT-NAME startswith XCP_Rx / XCP_Tx",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--ocan_regex", default=r"oCAN00")
    args = ap.parse_args()

    cfg = Config(ocan_pat=re.compile(args.ocan_regex))

    tree, root, NS = load_arxml(args.inp)

    # pipeline：按顺序执行各 step
    s1 = step1_remove_comsignal_without_ocan(root, NS, cfg)
    temp_dir = os.path.dirname(args.out) or "."
    temp_step1 = os.path.join(temp_dir, "2temp.arxml")
    save_arxml_strict(tree, temp_step1)
    s2 = step2_remove_xcp_rx_tx_comsignals(root, NS)
    temp_step2 = os.path.join(temp_dir, "3temp.arxml")
    save_arxml_strict(tree, temp_step2)

    save_arxml_strict(tree, args.out)

    print("[OK]", s1, s2, "out=", args.out, "temp_step1=", temp_step1, "temp_step2=", temp_step2)
if __name__ == "__main__":
    main()
