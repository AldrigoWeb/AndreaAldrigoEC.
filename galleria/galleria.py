#!/usr/bin/env python3
"""Legge images/galleria/<categoria>/* e scrive galleria/foto.json.
Le foto sono ordinate dalla più recente (data del primo caricamento su Git).
In locale, dalla radice del sito:  python3 .github/scripts/galleria.py"""
import json, os, re, subprocess

BASE = "images/galleria"
EXT = (".jpg", ".jpeg", ".png", ".webp")

def etichetta(cartella):
    nome = re.sub(r"^\d+[-_ ]*", "", cartella)  # "01-vigneto" -> "vigneto"
    nome = nome.replace("-", " ").replace("_", " ").strip()
    return nome[:1].upper() + nome[1:]

def data_caricamento(path):
    # data del primo commit del file (segue anche gli spostamenti di cartella)
    try:
        out = subprocess.run(["git", "log", "--follow", "--format=%at", "--", path],
                             capture_output=True, text=True, check=True).stdout.split()
        if out:
            return int(out[-1])
    except Exception:
        pass
    return int(os.path.getmtime(path))

categorie, foto = [], []
if os.path.isdir(BASE):
    for cartella in sorted(os.listdir(BASE), key=str.lower):
        percorso = os.path.join(BASE, cartella)
        if not os.path.isdir(percorso):
            continue
        nome, trovate = etichetta(cartella), False
        for f in os.listdir(percorso):
            if f.lower().endswith(EXT):
                p = f"{BASE}/{cartella}/{f}"
                foto.append({"src": p, "cat": nome, "_d": data_caricamento(p)})
                trovate = True
        if trovate:
            categorie.append(nome)

foto.sort(key=lambda x: (-x["_d"], x["src"].lower()))
for x in foto:
    del x["_d"]

os.makedirs("galleria", exist_ok=True)
with open("galleria/foto.json", "w", encoding="utf-8") as fh:
    json.dump({"categorie": categorie, "foto": foto}, fh, ensure_ascii=False, indent=1)
print(len(foto), "foto in", len(categorie), "categorie")
