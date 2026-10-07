#!/usr/bin/env python3
"""Genera gli elenchi letti dal sito (così il browser non deve mai "indovinare" i nomi dei file):
  galleria/foto.json      -> foto di images/galleria/<categoria>/, dalla più recente, con dimensioni e miniatura
  galleria/immagini.json  -> tutte le immagini direttamente in images/ (nome senza estensione -> file)
  galleria/thumb/...      -> miniature leggere (800 px di larghezza) delle foto della galleria
In locale, dalla radice del sito:  python3 .github/scripts/galleria.py   (serve:  pip install pillow)"""
import json, os, re, shutil, subprocess

BASE = "images/galleria"
THUMB = "galleria/thumb"
THUMB_W = 800
EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg")
EXT_GALLERIA = (".jpg", ".jpeg", ".png", ".webp")

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    print("ATTENZIONE: Pillow non disponibile, niente dimensioni né miniature")

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

def prepara(path, cartella, nome_file):
    """Legge la foto (già ruotata come da EXIF), ne salva la miniatura e restituisce w, h, thumb."""
    if Image is None:
        return {}
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)      # foto da telefono: orientamento corretto
            w, h = im.size
            info = {"w": w, "h": h}
            dest_dir = os.path.join(THUMB, cartella)
            os.makedirs(dest_dir, exist_ok=True)
            dest = f"{THUMB}/{cartella}/{os.path.splitext(nome_file)[0]}.jpg"
            t = im.convert("RGB")
            if t.width > THUMB_W:
                t = t.resize((THUMB_W, round(t.height * THUMB_W / t.width)), Image.LANCZOS)
            t.save(dest, "JPEG", quality=78, optimize=True, progressive=True)
            info["thumb"] = dest
            return info
    except Exception as e:
        print("Errore su", path, "->", e)
        return {}

# le miniature vengono rigenerate da zero: così non restano quelle di foto cancellate
shutil.rmtree(THUMB, ignore_errors=True)
os.makedirs(THUMB, exist_ok=True)

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
                voce.update(prepara(p, cartella, f))
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
