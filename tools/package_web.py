"""Package deployable static assets and a clean source handoff, excluding local data."""
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'captures';out.mkdir(exist_ok=True)

def archive(path,files,base):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as package:
        for file in sorted(files):
            if file.is_file():package.write(file,file.relative_to(base).as_posix())
    print(path.name, path.stat().st_size,'bytes')

archive(out/'RECUR-website.zip',(ROOT/'web/dist').rglob('*'),ROOT/'web/dist')
folders=('.github','assets','docs','recur','tests','tools','web')
files=[file for name in folders for file in (ROOT/name).rglob('*')
       if file.is_file() and not any(part in ('__pycache__','node_modules','.openai','.git') for part in file.parts)]
files.extend(ROOT/name for name in ('.gitignore','README.md','START_HERE.md','PROCESS.md','SUBMISSION.md','CREDITS.md','app.py','pyproject.toml','uv.lock'))
archive(out/'RECUR-source.zip',files,ROOT)
with zipfile.ZipFile(out/'RECUR-source.zip') as package:
    names=package.namelist()
    assert '.github/workflows/pages.yml' in names and 'web/dist/index.html' in names
    assert not any(name.startswith(('.venv/','.reference/','captures/','.git/')) for name in names)
