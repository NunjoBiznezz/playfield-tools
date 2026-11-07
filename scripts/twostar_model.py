"""twostar_model.py - parametric model of a "two overlapping stars" piece of line art
=================================================================================

Helper library (not run on its own). Some Lady Luck art is built from two four-point
stars with concave (inward-curving) sides: a big BACK star and a smaller FRONT star on
top, each with thick black outlines and coloured bands inside. Rather than tracing the
photo's pixels, this rebuilds the art from a handful of measurements, so the outlines
come out as true arcs of one constant width.

All numbers are in pixels of the rectified photo that the measurements came from:
  X0        the art's vertical centre line (the stars are mirror-symmetric about it)
  P0        starting measurements, by name (see NAMES):
              xL, yM          left tip of the back star (the right tip is its mirror)
              yT, yB          top and bottom tips of the back star
              sU, sD          how far the upper / lower sides of the back star curve in
              fxT fyT fxB fyB top-left and bottom-left tips of the front star
              fsT fsB fsS     curve-in of the front star's top / bottom / side edges
              dR dC dG dY     how far in from the outline each inner colour band sits
              WO, WI          width of the outer black outline / of the inner black lines

Use it from a session or a scratch script, e.g.
    import twostar_model as T
    img = T.render(T.P0, shape=(h, w))     # label image, to compare against the photo
and adjust the numbers in P0 until the render lines up with the photo.

render() returns a label image: 0 = nothing, 1-5 = colour bands, 6 = black line.
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import use_venv  # shared Python environment
import numpy as np, cv2
from shapely.geometry import Polygon
X0=1250.28
def arc(p,q,s,c,n=40):
    """points from p to q on a circular arc whose middle is pushed s px toward point c (concave side)"""
    p=np.asarray(p,float); q=np.asarray(q,float); m=(p+q)/2; ch=q-p; L=np.linalg.norm(ch)
    nrm=np.array([-ch[1],ch[0]])/L
    if np.dot(c-m,nrm)<0: nrm=-nrm
    if abs(s)<1e-6: t=np.linspace(0,1,n)[:,None]; return p+(q-p)*t,None
    # (the next three lines are leftovers from working the maths out; R and cen are recomputed below -
    #  only mid, the arc's middle point pushed s px toward c, is used)
    R=(L*L/4+s*s)/(2*s); cen=m+nrm*s-nrm*R
    mid=m+nrm*s; cen=mid+(-nrm)*R*-1
    cen=mid-nrm*R if False else mid+nrm*0
    # centre: equidistant from p,q,mid, on line through m along nrm
    # |m+k nrm - p|^2 = |m+k nrm - mid|^2 -> (L/2)^2 + k^2 = (k-s)^2 -> k = (s^2-(L/2)^2)/(2s)
    k=(s*s-(L/2)**2)/(2*s); cen=m+nrm*k; R=abs(s-k)
    a0=np.arctan2(*(p-cen)[::-1]); a1=np.arctan2(*(q-cen)[::-1]); am=np.arctan2(*(mid-cen)[::-1])
    # choose sweep direction passing through am
    d=(a1-a0)%(2*np.pi); dm=(am-a0)%(2*np.pi)
    if dm>d: d=d-2*np.pi
    t=a0+d*np.linspace(0,1,n); return np.c_[cen[0]+R*np.cos(t),cen[1]+R*np.sin(t)],(cen[0],cen[1],R)
def star(tips,sags):
    """closed polygon through tips (in order) with concave arcs; returns polygon, circles"""
    c=np.mean(tips,0); pts=[]; circ=[]
    for i in range(len(tips)):
        a,cc=arc(tips[i],tips[(i+1)%len(tips)],sags[i],c); pts.append(a[:-1]); circ.append(cc)
    return Polygon(np.vstack(pts)).buffer(0),circ
NAMES=['xL','yM','yT','yB','sU','sD','dR','dC','dG','fxT','fyT','fxB','fyB','fsT','fsB','fsS','dY','WO','WI']
P0=dict(xL=521,yM=696,yT=206,yB=1181,sU=120,sD=120,dR=50,dC=100,dG=137,fxT=871,fyT=276,fxB=855,fyB=1126,fsT=92,fsB=108,fsS=108,dY=55,WO=13,WI=10.5)
def shapes(p):
    """The back star and front star outlines for measurements p. Returns (back, front, back
    circles, front circles)."""
    xR=2*X0-p['xL']
    back,bc=star([(p['xL'],p['yM']),(X0,p['yT']),(xR,p['yM']),(X0,p['yB'])],[p['sU'],p['sU'],p['sD'],p['sD']])
    ftl=(p['fxT'],p['fyT']); ftr=(2*X0-p['fxT'],p['fyT']); fbr=(2*X0-p['fxB'],p['fyB']); fbl=(p['fxB'],p['fyB'])
    front,fc=star([ftl,ftr,fbr,fbl],[p['fsT'],p['fsS'],p['fsB'],p['fsS']])
    return back,front,bc,fc
# Shrink shape g by d pixels with sharp (mitred) corners.
def off(g,d): return g.buffer(-d,join_style=2,mitre_limit=20)
def level(p,n):
    """Centre line of inner band `n` (R, C or G): the back star shrunk by p['d'+n]. If p has
    'u'+n (and optionally 'v'+n) the band is redrawn as a star of its own with that curve-in,
    so its sides bend like the outer star's."""
    back,_,_,_=shapes(p); c=off(back,p['d'+n])
    if 'u'+n not in p: return c
    x,y=np.asarray(c.exterior.coords).T
    xl=x.min(); yt=y.min(); yb=y.max()
    u=max(0.0,p['u'+n])
    if 'v'+n in p: v=max(0.0,p['v'+n])
    else:   # same bend as the outer star: lower sides scaled like the upper ones
        cu=np.hypot(X0-xl,p['yM']-yt); cd=np.hypot(X0-xl,yb-p['yM'])
        cu0=np.hypot(X0-p['xL'],p['yM']-p['yT']); cd0=np.hypot(X0-p['xL'],p['yB']-p['yM'])
        v=u/(cu/cu0)*(p['sD']/p['sU'])*(cd/cd0)
    return star([(xl,p['yM']),(X0,yt),(2*X0-xl,p['yM']),(X0,yb)],[u]*2+[v]*2)[0]
def layers(p):
    """Every filled shape to draw, bottom to top, as (shape, label): black outline then colour
    inside, for the back star, its three inner bands, the front star and its inner band."""
    back,front,_,_=shapes(p); WO,WI=p['WO'],p['WI']
    seq=[(back,6),(off(back,WO),2)]
    for d,lab,n in ((p['dR'],3,'R'),(p['dC'],5,'C'),(p['dG'],4,'G')):
        c=level(p,n)
        seq+=[(c.buffer(WI/2,join_style=2,mitre_limit=20),6),(off(c,WI/2),lab)]
    seq+=[(front,6),(off(front,WO),2)]
    c=off(front,p['dY']); seq+=[(c.buffer(WI/2,join_style=2,mitre_limit=20),6),(off(c,WI/2),1)]
    return seq
def render(p,shape,sc=0.5):
    """Paint layers(p) into a label image of size `shape` (scaled by sc), to compare with the
    photo's label image."""
    img=np.zeros(shape,np.uint8)
    for g,lab in layers(p):
        for q in getattr(g,'geoms',[g]):
            if q.is_empty or q.geom_type!='Polygon': continue
            m=np.zeros(shape,np.uint8); cv2.fillPoly(m,[np.round(np.asarray(q.exterior.coords)*sc*16).astype(np.int32)],1,shift=4)
            for h in q.interiors: cv2.fillPoly(m,[np.round(np.asarray(h.coords)*sc*16).astype(np.int32)],0,shift=4)
            img[m>0]=lab
    return img
