"""Create versioned, smaller image assets served by the existing component."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent

def build():
    target = ROOT/'qwen-component'/'atlas'
    target.mkdir(exist_ok=True)
    manifest = {}
    source_size = output_size = 0
    for source in sorted((ROOT/'static'/'atlas').iterdir()):
        if source.suffix.lower() not in ('.jpg','.jpeg','.png','.webp'): continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        name = source.stem + '-' + digest + '.webp'
        output = target/name
        with Image.open(source) as image:
            image.thumbnail((1600,1600),Image.Resampling.LANCZOS)
            image.convert('RGBA' if 'A' in image.getbands() else 'RGB').save(output,'WEBP',quality=85,method=6)
        manifest[source.name] = {'file':name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
        source_size += source.stat().st_size
        output_size += output.stat().st_size
    (ROOT/'qwen-component'/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Atlas files:',len(manifest),'source bytes:',source_size,'served bytes:',output_size)

if __name__=='__main__': build()
