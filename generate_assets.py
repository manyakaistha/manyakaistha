"""Generate the profile's self-contained SVG artwork. Python standard library only."""
from pathlib import Path
from math import sin, cos, pi
from html import escape
from random import Random

OUT = Path(__file__).parent / 'assets'
OUT.mkdir(exist_ok=True)
BG, INK, MUTED, COPPER, MINT = '#102d2b', '#f6f0e5', '#a9bbb1', '#e3ac87', '#b8d7bc'

# Image documents cannot run profile JavaScript. All motion is declarative,
# deterministic, finite (under five seconds), and disabled for reduced motion.
MOTION = '''<style>
@keyframes trace {from {stroke-dashoffset:900} to {stroke-dashoffset:0}}
@keyframes rise {from {transform:scaleY(.15)} to {transform:scaleY(1)}}
@keyframes pulse {0%,100% {opacity:1} 45% {opacity:.3}}
@keyframes sweep {0% {transform:translateX(-17px);opacity:0} 25%,75% {opacity:1} 100% {transform:translateX(17px);opacity:0}}
@keyframes focus {0%,100% {opacity:.2} 50% {opacity:.9}}
@keyframes drift {0%,100% {transform:translateY(0)} 50% {transform:translateY(-8px)}}
.trace {stroke-dasharray:900;animation:trace 3.8s cubic-bezier(.16,1,.3,1) both}
.bar {transform-box:fill-box;transform-origin:center bottom;animation:rise 1.4s cubic-bezier(.16,1,.3,1) both}
.pulse {animation:pulse 2.2s ease-in-out 2}
.signal {animation:sweep 3.8s ease-in-out both}
.heat {animation:focus 3.8s ease-in-out}
.float {animation:drift 4.2s ease-in-out}
@media (prefers-reduced-motion:reduce) {* {animation:none!important}}
</style>'''

def svg(name, width, height, content, title):
    (OUT / name).write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title>
{MOTION}
<rect width="{width}" height="{height}" rx="18" fill="{BG}"/>
{content}</svg>''')

def text(x, y, value, size=14, color=INK, font='Arial, Helvetica, sans-serif', extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{font}" font-size="{size}" {extra}>{escape(value)}</text>'

def line(x1, y1, x2, y2, color=MINT, opacity=.4):
    return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" opacity="{opacity}"/>'

def circle(x,y,r,color=MINT,fill='none',opacity=1):
    return f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{color}" fill="{fill}" opacity="{opacity}"/>'

hero = text(50, 49, 'MANYA KAISTHA', 15, COPPER, extra='letter-spacing="3"')
hero += text(50, 122, 'Curiosity,', 65, font='Georgia, Times New Roman, serif')
hero += text(50, 192, 'made tangible.', 65, COPPER, 'Georgia, Times New Roman, serif', 'font-style="italic"')
hero += text(53, 241, 'AI systems. Thoughtful interfaces. Open experiments.', 18, MUTED)
hero += line(52, 279, 1148, 279, MINT, .2)
hero += text(53, 313, 'BUILD  /  INVESTIGATE  /  EXPLAIN', 12, MUTED, extra='letter-spacing="2"')
hero += text(1148, 313, 'A WORK IN PROGRESS, BY DESIGN.', 11, COPPER, extra='text-anchor="end" letter-spacing="1.5"')
# An orbital construction: ideas connect, converge, and become something useful.
hero += '<g transform="translate(967 151)">'
# Fixed seed preserves the constellation through rebuilds and resizes.
rng = Random(194952412)
for _ in range(24):
    x,y=rng.uniform(-178,178),rng.uniform(-118,108)
    hero += circle(round(x,2),round(y,2),round(rng.uniform(.7,1.5),2),MINT,MINT,.3)
for angle in (-35, 35, 90):
    hero += f'<ellipse class="trace" rx="139" ry="49" transform="rotate({angle})" fill="none" stroke="{MINT}" opacity=".32"/>'
    # Parametric ellipse sampled once; runtime only interpolates its geometry.
    keyframes=''.join(f'{i/64*100:.4f}% {{transform:translate({139*cos(i/64*2*pi):.3f}px,{49*sin(i/64*2*pi):.3f}px)}}' for i in range(65))
    ident='orbit'+str(angle).replace('-','m')
    hero += f'<style>@keyframes {ident} {{{keyframes}}} .{ident} {{transform:translate(139px,0);animation:{ident} 4.8s linear}} @media(prefers-reduced-motion:reduce){{.{ident}{{animation:none}}}}</style>'
    hero += f'<g transform="rotate({angle})"><g class="{ident}">'+circle(0,0,5,COPPER,COPPER)+circle(0,0,10,COPPER,'none',.25)+'</g></g>'
hero += circle(0,0,33,COPPER,BG) + circle(0,0,8,COPPER,COPPER)
for angle in (0, 2.2, 4.25):
    x,y = round(124*cos(angle),2),round(100*sin(angle),2)
    hero += '<g class="pulse">'+circle(x,y,7,COPPER,BG) + circle(x,y,2,COPPER,COPPER)+'</g>'
hero += '</g>'
svg('hero.svg',1200,350,hero,'Manya Kaistha — Curiosity, made tangible. AI systems, thoughtful interfaces, open experiments.')

projects = [
 ('analytics','01','Analytics Query Engine','PLAIN LANGUAGE → INSPECTABLE SQL','Python / FastAPI / DuckDB'),
 ('touchline','02','Touchline','FOLLOW THE EVIDENCE','GraphRAG / FastAPI / Local retrieval'),
 ('flux','03','Flux Reader','ONE WORD. YOUR PACE.','TypeScript / React Native / Expo'),
 ('faceinsight','04','FaceInsight','LOOK INSIDE THE MODEL','PyTorch / LoRA / Next.js'),
 ('matching','05','Sequential Matching','DECISIONS UNDER UNCERTAINTY','Python / Simulation / Evaluation'),
 ('learning','06','DL / GenAI Resources','COMPLEX IDEAS, MADE EXPLORABLE','PyTorch / Notebooks / Interactive guides'),
]

for name,num,title,tag,stack in projects:
    art = text(28,34,num,12,COPPER,extra='letter-spacing="2"')
    art += text(532,34,tag,10,MUTED,extra='text-anchor="end" letter-spacing="1.3"')
    if name=='analytics':
        for i,h in enumerate([18,34,27,53,44,69,84,76,101]):
            x=298+i*22
            art += f'<rect class="bar" style="animation-delay:{i*.09}s" x="{x}" y="{162-h}" width="12" height="{h}" rx="3" fill="{COPPER if i==8 else MINT}" opacity="{.35+i*.065}"/>'
        art += text(29,95,'question',20,INK,'Georgia, serif')+text(29,126,'→ SQL → answer',16,COPPER,'monospace')
        art += line(28,148,244,148,MINT,.2)
    elif name=='touchline':
        pts=[(53,98),(142,72),(147,149),(241,109),(332,66),(350,149),(447,91),(510,142)]
        art+='<g class="trace">'
        for a,b in [(0,1),(0,2),(1,3),(2,3),(3,4),(3,5),(4,6),(5,6),(5,7),(6,7)]: art+=line(*pts[a],*pts[b])
        art+='</g><g class="pulse">'
        for i,(x,y) in enumerate(pts): art+=circle(x,y,7 if i!=3 else 12,COPPER if i==3 else MINT,BG)
        art+='</g>'
    elif name=='flux':
        art+=text(280,127,'curiosity',49,INK,'Georgia, serif','text-anchor="middle"')
        art+='<g class="signal">'+line(280,62,280,82,COPPER,1)+line(280,143,280,163,COPPER,1)+'</g>'
        art+=text(49,119,'←',24,MUTED)+text(488,119,'→',24,MUTED)
    elif name=='faceinsight':
        for row in range(7):
            for col in range(9):
                x,y=58+col*17,64+row*14
                color=COPPER if (col-4)**2+(row-3)**2 < 7 else MINT
                art+=f'<rect class="heat" style="animation-delay:{(col+row)*.05}s" x="{x}" y="{y}" width="11" height="9" rx="2" fill="{color}" opacity="{.2+.65*(1-abs(col-4)/6)}"/>'
        art+=line(231,110,302,110,COPPER,.8)
        art+=text(325,100,'prediction',20,INK,'Georgia, serif')+text(325,130,'+ explanation',16,COPPER,'Georgia, serif')
    elif name=='matching':
        for x in (78,474):
            for y in (75,113,151): art+=circle(x,y,7,MINT,BG)
        for a,b in [(75,113),(113,151),(151,75)]:
            art+=f'<path class="trace" d="M85,{a} C220,{a} 330,{b} 467,{b}" stroke="{COPPER}" fill="none" opacity=".6"/>'
        art+=text(278,119,'?',23,INK,'Georgia, serif','text-anchor="middle"')
    else:
        for i in range(4):
            x=46+i*126
            art+=f'<g class="float" style="animation-delay:{i*.15}s">'
            art+=f'<rect x="{x}" y="66" width="94" height="90" rx="7" fill="none" stroke="{MINT}" opacity=".45"/>'
            art+=text(x+15,95,['01','02','03','04'][i],12,COPPER,'monospace')
            for j,w in enumerate([59,44,51]): art+=line(x+15,110+j*10,x+15+w,110+j*10,MINT,.3)
            art+='</g>'
    art+=line(28,184,532,184,MINT,.2)
    art+=text(28,219,title,26,INK,'Georgia, Times New Roman, serif')
    art+=text(28,248,stack,12,MUTED)
    art+=text(529,221,'↗',24,COPPER,extra='text-anchor="end"')
    svg(name+'.svg',560,274,art,title+' — '+tag)

svg('footer.svg',1200,100,text(40,59,'ALWAYS CURIOUS. ALWAYS BUILDING.',17,COPPER,extra='letter-spacing="3"')+text(1160,59,'Let’s make something worth exploring. ↗',18,INK,'Georgia, serif','text-anchor="end"'),'Always curious. Always building. Let’s make something worth exploring.')

# New image URLs bypass cached copies of the profile's original static artwork.
for name in ('hero','analytics','touchline','flux','faceinsight','matching','learning'):
    (OUT / (name+'-motion.svg')).write_bytes((OUT / (name+'.svg')).read_bytes())

# A still alternative is always useful when sharing an asset outside GitHub.
import re
for asset in OUT.glob('*.svg'):
    if asset.stem.endswith(('-still','-motion')):
        continue
    static = re.sub(r'<style>.*?</style>', '', asset.read_text(), flags=re.S)
    # Orbit dots keep their resting placement even when their stylesheet is removed.
    static = re.sub(r'class="orbit[^"]*"', 'transform="translate(139 0)"', static)
    (OUT / (asset.stem+'-still.svg')).write_text(static)

readme = OUT.parent / 'README.md'
if readme.exists():
    still = readme.read_text().replace('Read the still edition', 'Return to the animated profile')
    still = still.replace('href="STILL.md"', 'href="https://github.com/manyakaistha"')
    still = re.sub(
        r'<picture><source [^>]+/><img src="assets/([^".]+)\.svg" ([^>]+?)/></picture>',
        lambda m: '<img src="assets/'+m.group(1).removesuffix('-motion')+'-still.svg" '+m.group(2)+'/>',
        still,
    )
    (OUT.parent / 'STILL.md').write_text(still)
