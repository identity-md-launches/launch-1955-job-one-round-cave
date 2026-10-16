#!/usr/bin/env python3
"""Build one offline gallery; reuse identical inherited previews once via SVG."""
import base64
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess

class Previews(HTMLParser):
    def __init__(self, source):
        super().__init__(); self.record=None; self.images={}; self.defs={}; self.uses={}
        self.feed(source)
        self.images.update({k:self.defs[v] for k,v in self.uses.items()})
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='article': self.record=a.get('data-record')
        if tag=='img' and self.record: self.images[self.record]=a['src']
        if tag=='image': self.defs[a['id']]=a['href']
        if tag=='use' and self.record: self.uses[self.record]=a['href'][1:]
    def handle_endtag(self, tag):
        if tag=='article': self.record=None

def main():
    target=Path('dist/index.html'); previews=Previews(target.read_text()).images if target.exists() else {}
    goals=[{'line':i,'goal':Path(f'line-{i}/GOAL.md').read_text().strip()} for i in range(1,5)]
    Path('dist/goals.json').write_text(json.dumps(goals,indent=2)+'\n')
    walls=[('gathering','Gathering')]+[(f'line-{i}',f'Line {i}') for i in range(1,5)]
    definitions={}; esc=html.escape
    chunks=['''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><meta name="description" content="Every painting from four worker tool lines and the Ice gathering."><title>Pepeolithic · Ice</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#1b160f;color:#f2e2c6;font:16px/1.6 system-ui,sans-serif}header,main,footer{max-width:1100px;margin:auto;padding:24px}h1{font-size:clamp(2.2rem,7vw,4rem);line-height:1.1}h2{font-size:1.8rem}h3{font-size:1.15rem;margin:0}a{color:#efbb72}a:focus-visible,summary:focus-visible{outline:3px solid #efbb72;outline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:18px}section{margin:28px 0 60px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:16px}article{background:#2b2319;border:1px solid #695236;border-radius:8px;padding:20px;overflow-wrap:anywhere}article svg{float:right;width:96px;height:96px;margin:0 0 12px 12px}article p{font-size:.9rem}details{margin-top:22px}summary{cursor:pointer}.future{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px}.future i{font-size:.85rem;padding:8px}.note{max-width:75ch;color:#cbbb9d}footer{border-top:1px solid #695236}
</style></head><body><header><p>Pepeolithic / Ice</p><h1>Four trails.<br>Every finding.</h1><p class="note">Four lines build worker tools. The gathering tests and connects them. Paintings appear newest first.</p><nav aria-label="Walls">''']
    chunks += [f'<a href="#{w}">{label}</a>' for w,label in walls];chunks.append('</nav></header><main>')
    count=painted=0
    for wall,label in walls:
        goal='Test the four lines and share useful pieces.' if wall=='gathering' else goals[int(wall[-1])-1]['goal']
        chunks.append(f'<section id="{wall}"><h2>{label}</h2><p class="note">{esc(goal)}</p>')
        records=[(p,json.loads(p.read_text())) for p in sorted(Path('dist',wall).glob('[0-9][0-9].json'),reverse=True)]
        latest=next((p for p,r in records if r['name']!='Not painted yet'),None)
        chunks.append('<div class="grid">');future=[]
        for path,record in records:
            count+=1; key=path.relative_to('dist').as_posix()
            if not re.fullmatch(r'https://api\.imd\.fun/artifacts/[a-f0-9]{64}',record['image']):raise ValueError(key)
            if record['name']=='Not painted yet':
                future.append(f'<i data-record="{key}">{path.stem}</i>');continue
            painted+=1
            if key not in previews or path==latest:
                # Decode the already delivered adjacent JPEG; no extra image file.
                js="""const fs=require('node:fs'),dec=require('./gathering/vendor/jpeg-js/decoder.js'),enc=require('./gathering/vendor/jpeg-js/encoder.js');const a=dec(fs.readFileSync(process.argv[1]));const size=64,b=Buffer.alloc(size*size*4,255);for(let y=0;y<size;y++)for(let x=0;x<size;x++)for(let c=0;c<3;c++)b[(y*size+x)*4+c]=a.data[(Math.floor(y*a.height/size)*a.width+Math.floor(x*a.width/size))*4+c];process.stdout.write(enc({width:size,height:size,data:b},45).data);"""
                jpeg=subprocess.run(['node','-e',js,str(path.with_suffix('.jpg'))],capture_output=True,check=True).stdout
                previews[key]='data:image/jpeg;base64,'+base64.b64encode(jpeg).decode()
            preview=previews[key]
            if not re.fullmatch(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+',preview):raise ValueError(key)
            if preview not in definitions:definitions[preview]=f't{len(definitions)}'
            thumb=definitions[preview]; attrs={a['trait_type']:a['value'] for a in record['attributes']}
            chunks.append(f'<article data-record="{key}"><a href="{record["image"]}" aria-label="Open full wall {esc(record["name"],quote=True)}"><svg viewBox="0 0 64 64" aria-hidden="true"><use href="#{thumb}"/></svg></a><h3><a href="{key}">{path.stem} {esc(record["name"])}</a></h3><p>{esc(str(attrs.get("Meaning","")))}</p></article>')
        chunks.append('</div><details><summary>Unpainted records · '+str(len(future))+'</summary><div class="future">'+''.join(future)+'</div></details></section>')
    chunks.append('</main><svg width="0" height="0" aria-hidden="true" style="position:absolute"><defs>')
    for source,identifier in definitions.items():chunks.append(f'<image id="{identifier}" width="64" height="64" href="{source}"/>')
    chunks.append(f'</defs></svg><footer><p>{count} records · {painted} paintings · {count-painted} reserved slots.</p><p>Previews work offline. Select a painting for its full wall; titles open records. Adjacent JPEGs are 512 px.</p><p><a href="../gathering/REPORT.md">Gathering report</a> · <a href="goals.json">Four goals</a> · <a href="../shared/import-drift/JOINT.md">Shared joint review</a></p></footer></body></html>')
    result=''.join(chunks)
    if len(result.encode())>=100000:raise ValueError(f'gallery exceeds 100 KB: {len(result.encode())}')
    target.write_text(result)
    print(json.dumps({'records':count,'paintings':painted,'unique_previews':len(definitions),'bytes':len(result.encode())}))

if __name__=='__main__':main()
