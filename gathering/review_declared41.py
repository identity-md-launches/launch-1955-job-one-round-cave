#!/usr/bin/env python3
"""Reproduce a static script-target precedence defect using workspace-only sources."""
import importlib.util
import json
from pathlib import Path
import tempfile

spec=importlib.util.spec_from_file_location('declared_review','line-3/tools/declared-scripts/scripts.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
with tempfile.TemporaryDirectory(dir='test/scratch') as folder:
    root=Path(folder)
    (root/'trail/cli').mkdir(parents=True)
    (root/'trail/__init__.py').write_text('')
    (root/'trail/cli.py').write_text('raise RuntimeError("source must never execute")\ndef main(): pass\n')
    (root/'trail/cli/__init__.py').write_text('raise RuntimeError("source must never execute")\nother=1\n')
    report=tool.inspect('line-3/tools/declared-scripts/examples/pyproject.toml',root)
    row=next(r for r in report['scripts'] if r['name']=='trail')
    assert row['source']=='trail/cli.py' and row['status']=='module_and_object_found'
    evidence={'finding':'declared-scripts-package-precedence','reproduced':True,
              'input':{'trail/cli.py':'defines main','trail/cli/__init__.py':'does not define main'},
              'expected':{'source':'trail/cli/__init__.py','status':'module_found_object_not_declared'},
              'actual':row,'source_execution':'none',
              'repair':'Prefer a regular package __init__.py over the same-named .py module, consistently with Import Map. Add a collision regression.'}
    Path('gathering/declared-review41.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
