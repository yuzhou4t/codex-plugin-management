"""Execute documented local setup and JSON examples without making API calls."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
IMA = REPO / 'skills' / 'ima-skill'


@unittest.skipUnless(shutil.which('node') and shutil.which('bash'), 'Node and Bash required for documented examples')
class ImaExamplesTests(unittest.TestCase):
    def bash(self, snippet, cwd, env):
        result = subprocess.run(['bash', '-eu', '-c', snippet], cwd=cwd, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def setup_snippet(self, document):
        match = re.search(r'```bash\n(IMA_SKILL_DIR=.*?)\n```', document, re.S)
        self.assertIsNotNone(match)
        return match[1]

    def test_all_module_wrappers_resolve_custom_and_default_codex_home(self):
        for doc in ('SKILL.md', 'knowledge-base/SKILL.md', 'notes/SKILL.md'):
            snippet = self.setup_snippet((IMA / doc).read_text(encoding='utf-8'))
            for custom in (False, True):
                with self.subTest(doc=doc, custom=custom), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    home = root / 'user home'
                    codex_home = root / 'custom codex' if custom else home / '.codex'
                    installed = codex_home / 'skills' / 'ima-skill'
                    installed.mkdir(parents=True)
                    # A fake executable records arguments only. No credentials/network.
                    (installed / 'ima_api.cjs').write_text('process.stdout.write(JSON.stringify(process.argv.slice(2)));', encoding='utf-8')
                    env = {**os.environ, 'HOME': str(home)}
                    env.pop('CODEX_HOME', None)
                    if custom:
                        env['CODEX_HOME'] = str(codex_home)
                    output = self.bash(snippet + '\nima_api "openapi/test" \'{"name":"a\\"b"}\'', root, env)
                    self.assertEqual(json.loads(output), ['openapi/test', '{"name":"a\\"b"}'])

    def test_custom_home_preflight_runs_outside_the_skill_directory(self):
        document = (IMA / 'knowledge-base/SKILL.md').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / 'custom codex'
            installed = codex_home / 'skills' / 'ima-skill'
            shutil.copytree(IMA, installed)
            sample = root / '报价 "sample".pdf'
            sample.write_bytes(b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n')
            env = {**os.environ, 'CODEX_HOME': str(codex_home), 'SAMPLE_FILE': str(sample)}
            output = self.bash(self.setup_snippet(document) + '\nnode "$IMA_SKILL_DIR/knowledge-base/scripts/preflight-check.cjs" --file "$SAMPLE_FILE"', root, env)
            result = json.loads(output)
            self.assertTrue(result['pass'], result)
            self.assertEqual(result['file_name'], sample.name)

    def test_upload_json_builders_preserve_filename_and_dynamic_fields(self):
        document = (IMA / 'knowledge-base/SKILL.md').read_text(encoding='utf-8')
        builders = {}
        for name in ('REPEATED_BODY', 'CREATE_MEDIA_BODY', 'ADD_KNOWLEDGE_BODY'):
            match = re.search(r'^' + name + r'=\$\(node -e .*?^\' -- .*?\)$', document, re.M | re.S)
            self.assertIsNotNone(match, name)
            builders[name] = match[0]
        for filename in ('simple.pdf', 'a"b\\c\n中文.pdf', '--check.pdf', "$(touch SHOULD_NOT_EXIST)'quoted.pdf"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temporary:
                env = {**os.environ, 'FILE_NAME': filename, 'MEDIA_TYPE': '1', 'FILE_SIZE': '1234',
                       'CONTENT_TYPE': 'application/pdf', 'FILE_EXT': 'pdf', 'KB_ID': 'kb"\\key',
                       'MEDIA_ID': 'media"\\id', 'COS_KEY': 'cos"\\object'}
                values = {name: json.loads(self.bash(code + '\nprintf \'%s\' "$' + name + '"', temporary, env)) for name, code in builders.items()}
                self.assertEqual(values['REPEATED_BODY']['params'], [{'name': filename, 'media_type': 1}])
                self.assertEqual(values['CREATE_MEDIA_BODY']['file_name'], filename)
                self.assertEqual(values['CREATE_MEDIA_BODY']['file_size'], 1234)
                self.assertEqual(values['ADD_KNOWLEDGE_BODY']['title'], filename)
                self.assertEqual(values['ADD_KNOWLEDGE_BODY']['file_info']['file_name'], filename)
                self.assertEqual(values['ADD_KNOWLEDGE_BODY']['file_info']['cos_key'], env['COS_KEY'])
                self.assertEqual(values['ADD_KNOWLEDGE_BODY']['media_id'], env['MEDIA_ID'])
                for body in values.values():
                    self.assertEqual(body['knowledge_base_id'], env['KB_ID'])
                self.assertFalse((Path(temporary) / 'SHOULD_NOT_EXIST').exists())

    def test_no_stale_claude_install_paths_remain(self):
        for doc in IMA.rglob('*.md'):
            self.assertNotIn('.claude/skills/ima-skill', doc.read_text(encoding='utf-8'), str(doc))


class GuidanceTests(unittest.TestCase):
    def test_discovered_processes_require_verified_ownership_or_confirmation(self):
        document = (REPO / 'skills/stabilize-local-agent-project/SKILL.md').read_text(encoding='utf-8')
        self.assertNotIn('立即停止它', document)
        for boundary in ('当前 Agent 在本轮任务中启动', '身份已核实且可安全中止', '获得用户明确确认后再停止', '等待确认期间不得终止、暂停或重启'):
            self.assertIn(boundary, document)

    def test_light_accent_meets_small_text_contrast_on_declared_surfaces(self):
        document = (REPO / 'skills/apply-personal-app-design-system/references/design-system.md').read_text(encoding='utf-8')
        def hex_token(name):
            return re.search(r'\| `' + name + r'` \| `(#\w+)`', document)[1]
        def rgb(color):
            return [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        def luminance(color):
            channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in color]
            return sum(v * weight for v, weight in zip(channels, (.2126, .7152, .0722)))
        def contrast(left, right):
            a, b = sorted((luminance(left), luminance(right)))
            return (b + .05) / (a + .05)
        backgrounds = [rgb(hex_token(name)) for name in ('background-start', 'background-end', 'surface-control')]
        backgrounds.append(rgb('#FFFFFF'))
        for surface in ('surface', 'surface-raised'):
            alpha = float(re.search(r'\| `' + surface + r'` \| `rgba\(255,255,255,(.*?)\)`', document)[1])
            backgrounds.extend([[alpha + (1-alpha)*v for v in background] for background in backgrounds[:2]])
        for foreground in ('accent', 'accent-strong'):
            for background in backgrounds:
                with self.subTest(foreground=foreground, background=background):
                    self.assertGreaterEqual(contrast(rgb(hex_token(foreground)), background), 4.5)


if __name__ == '__main__':
    unittest.main()
