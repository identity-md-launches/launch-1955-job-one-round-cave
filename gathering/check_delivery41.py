#!/usr/bin/env python3
"""Offline structural, scope and evidence checks; not visual certification."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess

from build_gallery import Previews
from check_delivery import Gallery, png_dimensions, jpeg_dimensions


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    png=Path('artifacts/gathering/wall-v21.png').read_bytes()
    assert png==Path('artifacts/gathering/wall.png').read_bytes()
    assert png_dimensions(png)==(1254,1254) and png[24:26]==bytes((8,2))
    jpeg=Path('dist/gathering/41.jpg').read_bytes()
    assert jpeg_dimensions(jpeg)==(512,512) and len(jpeg)<100000
    record=json.loads(Path('dist/gathering/41.json').read_text())
    assert set(record)=={'name','image','attributes'}
    assert record['image']=='https://api.imd.fun/artifacts/'+hashlib.sha256(png).hexdigest()
    attrs={a['trait_type']:a['value'] for a in record['attributes']}
    assert len(attrs)==len(record['attributes'])==6
    assert set(attrs)=={'Cave','Wall','Number','Left behind','Meaning','One thing'}
    assert attrs['Cave']=='Ice' and attrs['Wall']=='Gathering'
    assert type(attrs['Number']) is int and attrs['Number']==41
    assert attrs['One thing']=='Gathering' and attrs['Meaning'] and attrs['Left behind']
    assert json.loads(Path('dist/goals.json').read_text())==[
        {'line':i,'goal':Path(f'line-{i}/GOAL.md').read_text().strip()} for i in range(1,5)]
    content=Path('dist/index.html').read_text()
    gallery=Gallery(content); previews=Previews(content)
    records={p.relative_to('dist').as_posix():json.loads(p.read_text())
             for p in Path('dist').glob('*/[0-9][0-9].json')}
    assert len(records)==len(gallery.records)==204
    assert set(records)==set(gallery.records)
    assert len(content.encode())<100000
    assert not set(gallery.tags)&{'script','iframe','link'}
    assert len(previews.images)==104
    assert set(previews.images)=={k for k,v in records.items() if v['name']!='Not painted yet'}
    for source in previews.images.values():
        assert re.fullmatch(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+',source)
        a,b=jpeg_dimensions(base64.b64decode(source.split(',')[1])); assert a==b and a>0
    for href in gallery.links:
        if href.startswith('#'): assert f'id="{href[1:]}"' in content
        elif not href.startswith('https://'): assert (Path('dist')/href).is_file(),href
    for wall in ['gathering']+[f'line-{i}' for i in range(1,5)]:
        painted=[k for k in gallery.records if k.startswith(wall+'/') and records[k]['name']!='Not painted yet']
        assert painted==sorted(painted,reverse=True)
        for number in range(2,22):
            p=Path('dist',wall,f'{number:02}.json')
            assert json.loads(p.read_text())=={'name':'Not painted yet','image':'https://api.imd.fun/artifacts/b5e794cb2c70bd232230e389707698c69c2080786d606a13b39f9315c9a90799','attributes':[{'trait_type':'Cave','value':'Ice'}]}
            assert not p.with_suffix('.jpg').exists()
    review=json.loads(Path('gathering/image-checks41.json').read_text())
    assert review['visual_review_completed'] and review['unmet_visual_requirements']==[]
    assert review['png']['sha256']==hashlib.sha256(png).hexdigest()
    assert review['ancestor_sha256']==digest('artifacts/gathering/wall-v20.png')
    assert json.loads(Path('dist/gathering/40.json').read_text())['image'].endswith(review['ancestor_sha256'])
    js="""const fs=require('node:fs'),{decode}=require('./gathering/thumbnail.js');const a=decode(fs.readFileSync('artifacts/gathering/wall-v20.png')),b=decode(fs.readFileSync('artifacts/gathering/wall-v21.png'));let changed=0,outside=0;for(let y=0;y<a.height;y++)for(let x=0;x<a.width;x++){let p=(y*a.width+x)*3;if(a.pixels[p]!==b.pixels[p]||a.pixels[p+1]!==b.pixels[p+1]||a.pixels[p+2]!==b.pixels[p+2]){changed++;if(x<620||x>680||y<190||y>255)outside++;}}console.log(JSON.stringify({changed,outside}));"""
    pixels=json.loads(subprocess.run(['node','-e',js],capture_output=True,text=True,check=True).stdout)
    assert pixels=={'changed':858,'outside':0}
    tests=json.loads(Path('gathering/test-runs41.json').read_text())
    trials=json.loads(Path('gathering/current-checks41.json').read_text())
    assert tests['ok'] and tests['line_tests']==796 and tests['shared_tests']==139 and tests['gathering_tests']==8
    assert tests['sources_unchanged_after_checks'] and trials['ok'] and len(trials['results'])==61
    expected={str(p.parent) for p in Path('.').glob('line-*/tools/*/README.md')}
    assert expected=={f"line-{r['line']}/tools/{r['tool']}" for r in trials['results']}
    assert Path('gathering/COINS.md').read_text().splitlines()[0]=='none'
    assert not any(Path('gathering',name).exists() for name in ('coin-order.json','deploy-order.json'))
    assert json.loads(Path('gathering/declared-review41.json').read_text())['reproduced']
    evidence=json.loads(Path('gathering/origin-evidence41.json').read_text())
    assert evidence['inventory']['files']==40 and len(evidence['sites'])==43
    for item in evidence['inventory']['manifest']:
        assert digest(Path('shared/import-drift')/item['path'])==item['sha256']
    assert json.loads(Path('gathering/origin-review41.json').read_text())['comparison']['equal']
    baseline=json.loads(Path('test/scratch/line-before.json').read_text())
    actual={str(p):digest(p) for i in range(1,5) for p in Path(f'line-{i}').rglob('*') if p.is_file()}
    assert baseline==actual
    roots=[f'line-{i}' for i in range(1,5)]+[f'dist/line-{i}' for i in range(1,5)]
    assert not subprocess.run(['git','diff','HEAD','--',*roots],capture_output=True,check=True).stdout
    changes=subprocess.run(['git','diff','--name-only','HEAD'],capture_output=True,text=True,check=True).stdout.splitlines()
    added=subprocess.run(['git','ls-files','--others','--exclude-standard'],capture_output=True,text=True,check=True).stdout.splitlines()
    for name in set(changes+added):
        if name.startswith(('test/scratch/','artifacts/gathering/')): continue
        assert name.split('/')[0] in ('gathering','shared','dist'),name
        assert Path(name).is_file() and Path(name).stat().st_size<100000,name
    outputs=['artifacts/gathering/wall-v21.png','artifacts/gathering/wall.png']
    assert not subprocess.run(['git','ls-files','--',*outputs],capture_output=True,check=True).stdout
    report={'ok':True,'line_tests':796,'shared_tests':139,'gathering_tests':8,'cli_trials':61,
            'line_paths_unchanged':True,'records':204,'paintings':104,'placeholders':100,
            'gallery_bytes':len(content.encode()),'pixels':pixels,'png':review['png'],'jpeg':review['jpeg'],
            'unmet_visual_requirements':[],'named_outputs_untracked':True,'independent_certification':False}
    Path('gathering/delivery-checks41.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
