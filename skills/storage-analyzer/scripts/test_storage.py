"""Synthetic regressions; never scan or modify the user's filesystem."""
import contextlib
import importlib.util
import io
import json
import ntpath
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from report_html import render_report, script_json
import scan

# Avoid an unrelated installed module named server.
SPEC = importlib.util.spec_from_file_location('storage_server', Path(__file__).with_name('server.py'))
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class ReportTests(unittest.TestCase):
    payload = {'path': '</sCrIpT><script>alert(1)</script>&<>\u2028\u2029',
               'name': '__DELETE_CONFIG__ 中文'}

    def test_json_roundtrips_without_script_breakout(self):
        encoded = script_json(self.payload)
        for dangerous in ('<', '>', '&', '\u2028', '\u2029'):
            self.assertNotIn(dangerous, encoded)
        self.assertEqual(json.loads(encoded), self.payload)

    def test_replacement_does_not_rewrite_marker_like_user_data(self):
        template = '<script>const DATA=__REPORT_DATA__;const DELETE=__DELETE_CONFIG__;</script>'
        rendered = render_report(template, self.payload, {'token': 'test-token'})
        self.assertEqual(rendered.count('</script>'), 1)
        self.assertIn('__DELETE_CONFIG__ 中文', rendered)
        self.assertEqual(rendered.count('test-token'), 1)

    def test_server_uses_safe_renderer(self):
        handler = server.Handler.__new__(server.Handler)
        handler.path = '/'
        handler._send = Mock()
        with patch.object(server, 'DATA', self.payload), patch.object(server, 'TPL', '<script>__REPORT_DATA__</script>'):
            handler.do_GET()
        self.assertEqual(handler._send.call_args.args[1].count('</script>'), 1)
        self.assertIn('\\u003c/sCrIpT', handler._send.call_args.args[1])

    def test_static_report_uses_safe_renderer(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'analysis.json'
            output = Path(temporary) / 'report.html'
            source.write_text(json.dumps(self.payload), encoding='utf-8')
            subprocess.run([sys.executable, str(Path(__file__).with_name('build_report.py')), str(source), str(output)], check=True, capture_output=True)
            html = output.read_text(encoding='utf-8')
            self.assertNotIn('</sCrIpT><script>', html)
            self.assertIn('const DELETE = null;', html)


class ActionRootTests(unittest.TestCase):
    def test_windows_application_roots_are_open_only(self):
        with patch.object(server.sys, 'platform', 'win32'), patch.object(server.os, 'path', ntpath), patch.object(server, 'expand', ntpath.normpath), patch.object(server, 'HOME', r'C:\Users\Alice'), patch.dict(os.environ, {'ProgramFiles': r'C:\Program Files', 'ProgramFiles(x86)': r'C:\Program Files (x86)', 'ProgramW6432': r'D:\Apps'}, clear=True):
            for target in (r'C:\Program Files\App', r'c:\program files (x86)\App', r'D:\Apps\App'):
                self.assertTrue(server.within_action_roots(target, 'open'))
                for mode in ('rm', 'trash'):
                    self.assertFalse(server.within_action_roots(target, mode))
            for target in (r'C:\Program Files fake\App', r'C:\Windows\App', r'E:\Apps\App'):
                self.assertFalse(server.within_action_roots(target, 'open'))
            self.assertTrue(server.within_action_roots(r'c:\users\alice\Cache', 'rm'))
            self.assertFalse(server.within_action_roots(r'C:\Users\Alice-other\Cache', 'rm'))

    def test_macos_application_root_is_open_only(self):
        with patch.object(server.sys, 'platform', 'darwin'), patch.object(server, 'HOME', '/Users/alice'):
            self.assertTrue(server.within_action_roots('/Applications/Example.app', 'open'))
            self.assertFalse(server.within_action_roots('/Applications/Example.app', 'rm'))
            self.assertFalse(server.within_action_roots('/Applications/Example.app', 'trash'))
            self.assertFalse(server.within_action_roots('/Applications-evil/Example.app', 'open'))

    def request(self, target, mode):
        handler = server.Handler.__new__(server.Handler)
        body = json.dumps({'token': server.TOKEN, 'mode': mode, 'paths': [str(target)]}).encode()
        handler.path = '/action'
        handler.headers = {'Host': '127.0.0.1', 'Content-Length': str(len(body))}
        handler.rfile = io.BytesIO(body)
        handler._send = Mock()
        handler.do_POST()
        return handler._send.call_args.args[0]

    def test_operation_allowlist_and_deletion_boundary_are_both_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / 'home'
            application = Path(temporary) / 'applications' / 'Example'
            home.mkdir()
            application.mkdir(parents=True)
            allowed = {str(application)}
            with patch.object(server, 'HOME', str(home)), patch.object(server, 'application_roots', return_value=(str(application.parent),)), patch.object(server, 'OPEN_ALLOW', allowed), patch.object(server, 'RM_ALLOW', allowed), patch.object(server, 'TRASH_ALLOW', allowed), patch.object(server, 'open_in_file_manager') as open_app, patch.object(server, 'hard_delete') as remove, patch.object(server, 'move_to_trash') as trash:
                self.assertEqual(self.request(application, 'open'), 200)
                open_app.assert_called_once_with(str(application))
                self.assertEqual(self.request(application, 'rm'), 403)
                self.assertEqual(self.request(application, 'trash'), 403)
                self.assertEqual(self.request(application.parent / 'unlisted', 'open'), 403)
                remove.assert_not_called()
                trash.assert_not_called()

    def test_symlink_cannot_escape_home_deletion_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / 'home'
            target = Path(temporary) / 'outside'
            home.mkdir()
            target.mkdir()
            link = home / 'link'
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError:
                self.skipTest('symlinks unavailable')
            with patch.object(server, 'HOME', str(home)), patch.object(server, 'RM_ALLOW', {str(target)}), patch.object(server, 'hard_delete') as remove:
                self.assertEqual(self.request(link, 'rm'), 403)
                remove.assert_not_called()


class PartialScanTests(unittest.TestCase):
    def make_tree(self, root):
        child = root / 'partial'
        denied = child / 'locked'
        denied.mkdir(parents=True)
        (child / 'readable.bin').write_bytes(b'x' * 2048)
        return child, denied

    def deny_scandir(self, denied):
        actual = os.scandir
        def scan_dir(path):
            if str(path) == str(denied):
                raise PermissionError(str(path))
            return actual(path)
        return patch.object(scan.os, 'scandir', side_effect=scan_dir)

    def test_nested_denial_is_propagated_without_discarding_readable_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child, denied = self.make_tree(root)
            with self.deny_scandir(denied):
                omitted = []
                self.assertEqual(scan.dir_size_bytes(child, omitted), 2048)
                self.assertEqual(omitted, [str(denied)])
                rows = scan.scandir_children(root, min_kb=100000)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['size_kb'], 2)
            self.assertTrue(rows[0]['partial'])
            self.assertTrue(rows[0]['denied'])
            self.assertEqual(rows[0]['denied_paths'], [str(denied)])

    def test_denied_rows_survive_top_n_and_zero_size_filters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child, denied = self.make_tree(root)
            (root / 'large.bin').write_bytes(b'x' * 4096)
            with self.deny_scandir(child):
                rows = scan.scandir_children(root, min_kb=0, limit=1)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]['size_kb'], 0)
            self.assertEqual(rows[1]['denied_paths'], [str(child)])

    def test_unreadable_parent_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(scan.os, 'listdir', side_effect=PermissionError):
            rows = scan.scandir_children(temporary)
            self.assertEqual(rows[0]['denied_paths'], [temporary])
            self.assertTrue(rows[0]['partial'])

    def test_dev_cache_denials_are_reported_below_size_threshold(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / '.cache'
            cache.mkdir()
            denied = cache / 'locked'
            denied.mkdir()
            with patch.dict(os.environ, {'USERPROFILE': str(root), 'LOCALAPPDATA': str(root / 'Local'), 'APPDATA': str(root / 'Roaming')}, clear=True), patch.object(scan, 'scandir_children', return_value=[]), patch.object(scan, 'system_info_windows', return_value={}), self.deny_scandir(denied):
                _, groups = scan.scan_windows()
            self.assertEqual(groups['dev_caches'][0]['denied_paths'], [str(denied)])
            self.assertEqual(groups['dev_caches'][0]['size_kb'], 0)

    def test_readable_sizes_and_symlink_skipping_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child, _ = self.make_tree(root)
            try:
                (child / 'link').symlink_to(child, target_is_directory=True)
            except OSError:
                pass
            rows = scan.scandir_children(root, min_kb=0)
            self.assertEqual(rows[0]['size_kb'], 2)
            self.assertNotIn('partial', rows[0])


if __name__ == '__main__':
    unittest.main()
