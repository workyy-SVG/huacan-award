"""Single release entry point; validates files, build, tests and JavaScript."""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = ['streamlit_app.py','published-theme.html','qwen_live.py','provider_budget.py',
            'request_limits.py','release_fixes.py','release_quality.py','release_runtime.js',
            'qwen-demos.js','qwen-component/index.html','cases.json','dictionary-cache.json',
            'opencc-full.gz.b64','zili-lookup-results-original.js','mobile-home.css',
            'reading-edition.css','reading-notes.js','cover-lettering.css','folk-stats.html',
            '.streamlit/config.toml','requirements.txt']
REQUIRED.append('qwen-component/asset-manifest.json')
REQUIRED.append('guide.html')
REQUIRED.append('regions-polish.css')
REQUIRED.extend(['stats-3d.js','stats-3d.css'])
REQUIRED.append('featured-spacing.css')
REQUIRED.extend(['voice-assistant.js','voice-assistant.css'])

def check():
    for name in REQUIRED:
        if not (ROOT/name).is_file(): raise FileNotFoundError(name)
    import json
    for entry in json.loads((ROOT/'qwen-component'/'asset-manifest.json').read_text(encoding='utf-8')).values():
        if not (ROOT/'qwen-component'/'atlas'/entry['file']).is_file(): raise FileNotFoundError(entry['file'])
    for path in ROOT.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    commands = [[sys.executable,'check_bundle.py'],[sys.executable,'check_fixes.py'],
                [sys.executable,'-m','unittest','test_quality','-v'],['node','check_bridge.js'],
                ['node','--check','validation-final-0.js'],['node','--check','release_runtime.js'],
                ['node','--check','qwen-demos.js'],['node','--check','stats-3d.js'],
                ['node','--check','voice-assistant.js'],['node','test_voice_assistant.cjs']]
    for command in commands:
        subprocess.run(command,cwd=ROOT,check=True)
    print('PASS: complete release validation')

if __name__ == '__main__': check()
