#!/usr/bin/env python3
"""Genera due elenchi letti dal sito (così il browser non deve mai "indovinare" i nomi dei file):
  galleria/foto.json      -> foto di images/galleria/<categoria>/, dalla più recente, con dimensioni
  galleria/immagini.json  -> tutte le immagini direttamente in images/ (nome senza estensione -> file)
In locale, dalla radice del sito:  python3 .github/scripts/galleria.py"""
import json, os, re, subprocess

BASE = "images/galleria"
EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg")
EXT_GALLERIA = (".jpg", ".jpeg", ".png", ".webp")

try:
    from PIL import Image
except Exception:
    Image = None

def etichetta(cartella):
    nome = re.sub(r"^\d+[-_ ]*", "", cartella)
    nome = nome.replace("-", " ").replace("_", " ").strip()
    return nome[:1].upper() + nome[1:]

def data_caricamento(path):
    try:
        out = subprocess.run(["git", "log", "--follow", "--format=%at", "--", path],
                             capture_output=True, text=True, check=True).stdout.split()
        if out:
            return int(out[-1])
    except Exception:
        pass
    return int(os.path.getmtime(path))

def dimensioni(path):
    if Image is None:
        return {}
    try:
        with Image.open(path) as im:
            w, h = im.size
            try:
                if im.getexif().get(274) in (5, 6, 7, 8):  # foto da telefono ruotate
                    w, h = h, w
            except Exception:
                pass
            return {"w": w, "h": h}
    except Exception:
        return {}

categorie, foto = [], []
if os.path.isdir(BASE):
    for cartella in sorted(os.listdir(BASE), key=str.lower):
        percorso = os.path.join(BASE, cartella)
        if not os.path.isdir(percorso):
            continue
        nome, trovate = etichetta(cartella), False
        for f in os.listdir(percorso):
            if f.lower().endswith(EXT_GALLERIA):
                p = f"{BASE}/{cartella}/{f}"
                voce = {"src": p, "cat": nome, "_d": data_caricamento(p)}
                voce.update(dimensioni(p))
                foto.append(voce)
                trovate = True
        if trovate:
            categorie.append(nome)

foto.sort(key=lambda x: (-x["_d"], x["src"].lower()))
for x in foto:
    del x["_d"]

immagini = {}
if os.path.isdir("images"):
    for f in sorted(os.listdir("images"), key=str.lower):
        if os.path.isfile(os.path.join("images", f)) and f.lower().endswith(EXT):
            immagini[os.path.splitext(f)[0]] = f"images/{f}"

os.makedirs("galleria", exist_ok=True)
with open("galleria/foto.json", "w", encoding="utf-8") as fh:
    json.dump({"categorie": categorie, "foto": foto}, fh, ensure_ascii=False, indent=1)
with open("galleria/immagini.json", "w", encoding="utf-8") as fh:
    json.dump(immagini, fh, ensure_ascii=False, indent=1)
print(len(foto), "foto in", len(categorie), "categorie;", len(immagini), "immagini del sito")
