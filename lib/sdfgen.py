import numpy as np, math
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
S=8
def glyph_sdf(fontpath, ch, em=40, pad=5, A=None, B=None):
    """returns (floorx, floory, w, h, sdf_float_array[h+2pad, w+2pad] rows top->bottom), d in px (inside +)"""
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    t=TTFont(fontpath); gs=t.getGlyphSet(); g=t.getBestCmap()[ord(ch)]
    bp=BoundsPen(gs); gs[g].draw(bp); upem=t["head"].unitsPerEm
    xmin,ymin,xmax,ymax=[v*em/upem for v in bp.bounds]
    fx,fy=math.floor(xmin),math.floor(ymin); cx,cy=math.ceil(xmax),math.ceil(ymax)
    w,h=cx-fx,cy-fy
    W=w+2*pad; H=h+2*pad
    # canvas covers glyph-space x in [fx-pad, cx+pad], y in [fy-pad, cy+pad]
    img=Image.new("L",(W*S,H*S),0)
    font=ImageFont.truetype(fontpath, em*S)
    d=ImageDraw.Draw(img)
    ox=-(fx-pad)*S; baseline=(cy+pad)*S   # y=0 baseline at row baseline
    d.text((ox,baseline),ch,font=font,fill=255,anchor="ls")
    a=np.array(img)>127
    din=ndimage.distance_transform_edt(a)
    dout=ndimage.distance_transform_edt(~a)
    sd=(din-dout)/S       # + inside
    # downsample by sampling at pixel centres
    sd=sd.reshape(H,S,W,S).mean(axis=(1,3))  # box-average approx of centre sampling
    return fx,fy,w,h,sd
