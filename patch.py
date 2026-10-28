#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blacksmith of the Sand Kingdom - Tradução PT-BR (patcher)

Aplica a tradução nos arquivos do SEU jogo. Nenhum arquivo do jogo é distribuído
neste repositório: o script lê os bundles originais, injeta os textos e gera
os arquivos modificados no lugar, guardando um backup em `_backup_original`.

Uso:
    python patch.py "C:\\caminho\\Blacksmith of the Sand Kingdom"
    python patch.py "C:\\caminho\\Blacksmith of the Sand Kingdom" --restore
"""
import argparse, glob, io, json, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))

try:
    import numpy as np
    import UnityPy
    from PIL import Image
    from fontpatch import patch_font
except ImportError as e:  # pragma: no cover
    sys.exit(f"Dependência ausente ({e}). Rode: pip install -r requirements.txt")

BUNDLES = ("exceldb", "ui_prefab", "commonsystem")
BACKUP_DIR = "_backup_original"
TR_DIR = os.path.join(HERE, "translations")
FONTS = {"ui_prefab": "RodinNTLGPro-B SDF", "commonsystem": "RodinNTLGPro-B_fastset SDF"}
FIT_FIELDS = ("ManualText", "EquipInfo", "PartsInfo", "RuneInfo", "SkillText",
              "EnemyMemo", "RecipeInfo", "ItemInfo", "EventInfo", "TrophyText", "EndText")
EXTRA_CHARS = "áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇªº«»¿¡"
MARKER_IDX = 1043          # SystemString: nome do idioma "English" -> "Português"
TAGRE = re.compile(r'<[^>]*>|#\w+#|\[\w+\]|\$\w+\$')


def find_assets(path):
    path = os.path.abspath(path)
    if os.path.isfile(os.path.join(path, "exceldb")):
        return path
    for root, dirs, files in os.walk(path):
        if os.path.basename(root) == "100" and "exceldb" in files and "ui_prefab" in files:
            return root
        if root.count(os.sep) - path.count(os.sep) > 4:
            dirs[:] = []
    sys.exit("Não encontrei StreamingAssets/100 dentro dessa pasta. Aponte para a pasta do jogo.")


def load_translations():
    tr = {}
    for f in glob.glob(os.path.join(TR_DIR, "*_DB.json")):
        tr[os.path.basename(f)[:-5]] = json.load(open(f, encoding="utf-8"))
    namemap = json.load(open(os.path.join(TR_DIR, "_namemap.json"), encoding="utf-8"))
    return tr, namemap


def collect_chars(tr, namemap):
    chars = set(EXTRA_CHARS)
    for t in tr.values():
        for v in t.values():
            chars |= {c for c in v if ord(c) > 127}
    for v in namemap.values():
        chars |= {c for c in v if ord(c) > 127}
    return "".join(sorted(chars))


def _find_font(env, name):
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            tt = o.read_typetree()
        except Exception:
            continue
        if tt.get("m_Name") == name and "m_CharacterTable" in tt and "m_AtlasTextures" in tt:
            return o, tt
    return None, None


def extract_ttf(assets, tmpdir):
    """A fonte TTF do jogo vem embutida no ui_prefab; é usada só para gerar os glifos acentuados."""
    env = UnityPy.load(os.path.join(assets, BACKUP_DIR, "ui_prefab"))
    for o in env.objects:
        if o.type.name == "Font":
            p = os.path.join(tmpdir, "game_font.ttf")
            open(p, "wb").write(bytes(o.read().m_FontData))
            return p
    sys.exit("Fonte TTF do jogo não encontrada no ui_prefab.")


def patch_font_bundle(src, dst, bundle, ttf, chars):
    env = UnityPy.load(src)
    o, tt = _find_font(env, FONTS[bundle])
    if tt is None:
        sys.exit(f"Fonte {FONTS[bundle]} não encontrada em {bundle}.")
    ptr = tt["m_AtlasTextures"][0]
    tobj = [x for x in env.objects if x.path_id == ptr["m_PathID"]][0]
    tex = tobj.read()
    arr = np.array(tex.image)
    a = arr[:, :, 3].copy()
    added = patch_font(tt, a, ttf, chars, log=lambda *x: print("   ", *x))
    arr[:, :, 3] = a
    tex.image = Image.fromarray(arr)
    tex.save()
    o.save_typetree(tt)
    with open(dst, "wb") as f:
        f.write(env.file.save(packer="original"))
    gl = {g["m_Index"]: g["m_Metrics"]["m_HorizontalAdvance"] for g in tt["m_GlyphTable"]}
    adv = {c["m_Unicode"]: gl[c["m_GlyphIndex"]] for c in tt["m_CharacterTable"]}
    return len(added), adv


# ---------- simulação de quebra de linha (para caber nas caixas) ----------
def _clean(t):
    t = t.replace("#NAME#", "Wwwwwwww")
    t = re.sub(r'<sprite index=\d+>', "W", t)
    t = re.sub(r'<[^>]*>', "", t)
    return re.sub(r'\[\w+\]|\$\w+\$', "000", t)


def make_nlines(adv):
    def nlines(t, fs=26, w=580):
        n = 0
        for para in _clean(t).split("\n"):
            cur, c = "", 1
            for wd in para.split(" "):
                tv = (cur + " " + wd) if cur else wd
                if sum(adv.get(ord(ch), 20) for ch in tv) * fs / 40 <= w:
                    cur = tv
                else:
                    if cur:
                        c += 1
                    cur = wd
            n += c
        return n
    return nlines


def patch_exceldb(src, dst, tr, namemap, nlines):
    env = UnityPy.load(src)
    applied = scaled = 0
    problems = []
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            tt = o.read_typetree()
        except Exception:
            continue
        name = tt.get("m_Name")
        la = tt.get("Data", {}).get("ListArray") if isinstance(tt.get("Data"), dict) else None
        if la is None:
            continue
        table = tr.get(name, {})
        dirty = False
        for i, e in enumerate(la):
            for fld, v in e.items():
                if not (isinstance(v, dict) and set(v.keys()) >= {"ja", "en"} and len(v) <= 3):
                    continue
                k = f"{i}:{fld}"
                if k in table:
                    pt, en = table[k], v["en"]
                    if sorted(TAGRE.findall(en)) != sorted(TAGRE.findall(pt)):
                        problems.append((name, k))
                    if fld in FIT_FIELDS:
                        le = nlines(en)
                        if nlines(pt) > le:
                            for pct in (95, 90, 85, 80, 75):
                                if nlines(pt, 26 * pct / 100) <= le:
                                    pt = f"<size={pct}%>{pt}</size>"
                                    scaled += 1
                                    break
                    v["en"] = pt
                    if name == "SystemString_DB" and i == MARKER_IDX:
                        v["ja"] = pt
                    dirty = True
                    applied += 1
                elif fld == "NameText" and v["en"] in namemap:
                    v["en"] = namemap[v["en"]]
                    dirty = True
        if dirty:
            o.save_typetree(tt)
    with open(dst, "wb") as f:
        f.write(env.file.save(packer="original"))
    return applied, scaled, problems


def already_patched(path):
    env = UnityPy.load(path)
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            tt = o.read_typetree()
        except Exception:
            continue
        if tt.get("m_Name") == "SystemString_DB":
            return tt["Data"]["ListArray"][MARKER_IDX]["en"] == "Português"
    return False


def restore(assets):
    bk = os.path.join(assets, BACKUP_DIR)
    if not os.path.isdir(bk):
        sys.exit("Backup não encontrado. Nada a restaurar.")
    for b in BUNDLES:
        shutil.copy2(os.path.join(bk, b), os.path.join(assets, b))
        print(f"Restaurado: {b}")
    print("Jogo restaurado ao original.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("game", help="pasta do jogo (ou StreamingAssets/100)")
    ap.add_argument("--restore", action="store_true", help="restaura os arquivos originais")
    args = ap.parse_args()
    assets = find_assets(args.game)
    print("Arquivos do jogo:", assets)
    if args.restore:
        return restore(assets)

    bk = os.path.join(assets, BACKUP_DIR)
    if not os.path.isdir(bk):
        os.makedirs(bk)
        for b in BUNDLES:
            shutil.copy2(os.path.join(assets, b), os.path.join(bk, b))
        print("Backup criado em", bk)
    elif already_patched(os.path.join(assets, "exceldb")):
        print("Jogo já traduzido; reaplicando a partir do backup original.")

    tr, namemap = load_translations()
    chars = collect_chars(tr, namemap)
    with tempfile.TemporaryDirectory() as tmp:
        ttf = extract_ttf(assets, tmp)
        adv = None
        for b in ("ui_prefab", "commonsystem"):
            print(f"Fonte em {b}...")
            n, a = patch_font_bundle(os.path.join(bk, b), os.path.join(tmp, b), b, ttf, chars)
            print(f"    glifos adicionados: {n}")
            if b == "ui_prefab":
                adv = a
        print("Textos...")
        applied, scaled, problems = patch_exceldb(os.path.join(bk, "exceldb"), os.path.join(tmp, "exceldb"),
                                                  tr, namemap, make_nlines(adv))
        print(f"    textos aplicados: {applied} (ajustados ao tamanho: {scaled})")
        if problems:
            print(f"    aviso: {len(problems)} textos com tags diferentes do original (esperado: 1 no Manual)")
        for b in BUNDLES:
            shutil.copy2(os.path.join(tmp, b), os.path.join(assets, b))
    print("\nPronto! Abra o jogo e escolha Opções > Idioma > Português.")


if __name__ == "__main__":
    main()
