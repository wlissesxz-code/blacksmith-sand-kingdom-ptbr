import numpy as np, math, io
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfgen import glyph_sdf

A0, B0 = 127.7, 21.86

def find_slot(mask_cum, W, H, bw, bh, start=(0,0), step=1):
    """find top-left (r,c) of an all-zero block bw x bh in nonzero-mask using integral image"""
    cum = mask_cum
    rows = cum.shape[0]-1; cols = cum.shape[1]-1
    for r in range(start[0], rows-bh+1):
        # vectorised over columns
        s = cum[r+bh, bw:] - cum[r, bw:] - cum[r+bh, :cols-bw+1] + cum[r, :cols-bw+1]
        idx = np.nonzero(s==0)[0]
        if idx.size: return r, int(idx[0])
    return None

def patch_font(tt, atlas_img_L, ttf_path, chars, em=None, log=print):
    """tt: TMP font typetree dict (modified in place). atlas_img_L: numpy uint8 (rows top->bottom) modified in place.
       Returns list of added chars."""
    pad = tt["m_AtlasPadding"]
    em = em or tt["m_FaceInfo"]["m_PointSize"]
    Hh, Ww = atlas_img_L.shape
    have = {c["m_Unicode"] for c in tt["m_CharacterTable"]}
    todo = [ch for ch in chars if ord(ch) not in have]
    ttf = TTFont(ttf_path); cmap = ttf.getBestCmap(); upem = ttf["head"].unitsPerEm; gs = ttf.getGlyphSet()
    miss_ttf = [ch for ch in todo if ord(ch) not in cmap]
    todo = [ch for ch in todo if ord(ch) in cmap]
    maxidx = max(g["m_Index"] for g in tt["m_GlyphTable"])
    mask = (atlas_img_L > 0).astype(np.int32)
    cum = np.zeros((Hh+1, Ww+1), dtype=np.int64)
    cum[1:,1:] = mask.cumsum(0).cumsum(1)
    added = []
    cursor = (0,0)
    for ch in todo:
        gname = cmap[ord(ch)]
        bp = BoundsPen(gs); gs[gname].draw(bp)
        adv = ttf["hmtx"][gname][0]*em/upem
        if bp.bounds is None:   # blank glyph (space-like)
            maxidx += 1
            tt["m_GlyphTable"].append({"m_Index":maxidx,"m_Metrics":{"m_Width":0.0,"m_Height":0.0,"m_HorizontalBearingX":0.0,"m_HorizontalBearingY":0.0,"m_HorizontalAdvance":float(adv)},"m_GlyphRect":{"m_X":0,"m_Y":0,"m_Width":0,"m_Height":0},"m_Scale":1.0,"m_AtlasIndex":0})
            tt["m_CharacterTable"].append({"m_ElementType":1,"m_Unicode":ord(ch),"m_GlyphIndex":maxidx,"m_Scale":1.0})
            added.append(ch); continue
        fx, fy, w, h, sd = glyph_sdf(ttf_path, ch, em=em, pad=pad)
        val = np.clip(A0 + B0*sd, 0, 255).round().astype(np.uint8)
        bh, bw = val.shape
        pos = find_slot(cum, Ww, Hh, bw+2, bh+2, start=cursor)
        if pos is None:
            log("NO SPACE for", repr(ch)); continue
        r, c = pos
        cursor = (r, 0)
        # place with 1px guard
        top = r+1; left = c+1
        atlas_img_L[top:top+bh, left:left+bw] = np.maximum(atlas_img_L[top:top+bh, left:left+bw], val)
        cum_update = (atlas_img_L[r:r+bh+2, c:c+bw+2] > 0)
        # rebuild cum lazily for the affected rows (cheap approach: recompute fully per glyph is expensive; do local patch)
        mask[r:r+bh+2, c:c+bw+2] = 1
        cum[1:,1:] = mask.cumsum(0).cumsum(1)
        # glyph rect (pixel box without padding), bottom-origin y
        rx = left + pad
        ry_top = top + pad
        ry = Hh - (ry_top + h)
        maxidx += 1
        xmin, ymin, xmax, ymax = [v*em/upem for v in bp.bounds]
        tt["m_GlyphTable"].append({"m_Index":maxidx,"m_Metrics":{"m_Width":float(xmax-xmin),"m_Height":float(ymax-ymin),"m_HorizontalBearingX":float(xmin),"m_HorizontalBearingY":float(ymax),"m_HorizontalAdvance":float(adv)},"m_GlyphRect":{"m_X":int(rx),"m_Y":int(ry),"m_Width":int(w),"m_Height":int(h)},"m_Scale":1.0,"m_AtlasIndex":0})
        tt["m_CharacterTable"].append({"m_ElementType":1,"m_Unicode":ord(ch),"m_GlyphIndex":maxidx,"m_Scale":1.0})
        if "m_UsedGlyphRects" in tt:
            tt["m_UsedGlyphRects"].append({"m_X":int(rx),"m_Y":int(ry),"m_Width":int(w),"m_Height":int(h)})
        added.append(ch)
    if miss_ttf: log("not in TTF:", miss_ttf)
    return added
