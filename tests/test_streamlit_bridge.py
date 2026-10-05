"""Offline transport integration checks; no real websites are scanned."""
import base64
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from dataclasses import asdict
from unittest.mock import patch
from PIL import Image
import server
from sitecheck.models import Scan, Options
from streamlit_bridge import dispatch, initialize_store

class StreamlitBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"QUALITY_DATA_DIR": self.tmp.name, "QUALITY_APP_PASSWORD": ""})
        self.env.start()
        initialize_store(Path(self.tmp.name))
        server.JOBS.clear()
        server.SESSIONS.clear()
        self.cookie = ""
        self.counter = 0

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def call(self, path, data=None, cookie=None):
        self.counter += 1
        response, updated = dispatch({"id": str(self.counter), "path": path,
                                    "method": "POST" if data is not None else "GET",
                                    "body": json.dumps(data) if data is not None else ""},
                                   self.cookie if cookie is None else cookie)
        body = base64.b64decode(response["body"])
        decoded = json.loads(body) if response["content_type"] == "application/json" else body
        return response, decoded, updated

    def fixture(self):
        scan = Scan("https://fixture.invalid/", asdict(Options()))
        scan.add(page=scan.url, category="Metadata", severity="Review", title="Fixture finding",
                 evidence="Offline test fixture", fix="Review the page metadata.")
        scan.notes = ["SAMPLE DATA: offline transport test only."]
        return server.STORE.save_scan(scan)

    def test_boot_and_settings_round_trip(self):
        self.assertEqual(self.call('/api/boot')[1]['scans'], [])
        self.assertEqual(self.call('/api/settings', {'report_brand':'Updated heading'})[0]['status'], 200)
        self.assertEqual(self.call('/api/boot')[1]['settings']['report_brand'], 'Updated heading')

    def test_password_is_scoped_to_session(self):
        with patch.dict(os.environ, {"QUALITY_APP_PASSWORD":"test-password"}):
            self.assertEqual(self.call('/api/boot')[0]['status'], 401)
            self.assertEqual(self.call('/api/login', {'password':'wrong'})[0]['status'], 401)
            response, body, cookie = self.call('/api/login', {'password':'test-password'})
            self.assertEqual(response['status'], 200)
            self.assertNotIn('wqc_session', json.dumps(response))
            self.assertEqual(self.call('/api/boot', cookie=cookie)[0]['status'], 200)
            self.assertEqual(self.call('/api/boot', cookie='')[0]['status'], 401)

    def test_request_boundary_and_permission(self):
        for path in ['https://example.com/api/boot', '//example.com/api/boot', '/etc/passwd', '/api/boot#bad']:
            self.assertEqual(self.call(path)[0]['status'], 400)
        self.assertEqual(self.call('/api/scan', {'url':'https://example.com','consent':False})[0]['status'],400)
        self.assertEqual(self.call('/api/scan', {'url':'file:///etc/passwd','consent':True})[0]['status'],400)

    def test_scan_job_transport_with_offline_scan_fixture(self):
        scan = self.fixture()
        with patch.object(server, 'run_scan', return_value=scan):
            response, body, _ = self.call('/api/scan', {'url':scan['url'],'consent':True,'options':{}})
            self.assertEqual(response['status'],202)
            for _ in range(100):
                job = self.call('/api/job/'+body['job_id'])[1]
                if job['state'] in ('completed','failed'): break
                time.sleep(.01)
            self.assertEqual(job['state'],'completed')
            self.assertEqual(self.call('/api/scan/'+job['scan_id'])[1]['scan']['url'], scan['url'])

    def test_reviews_and_binary_downloads(self):
        scan = self.fixture()
        rid = scan['issues'][0]['id']
        self.assertEqual(self.call('/api/review', {'id':rid,'review':{'status':'In progress','notes':'Fixture'}})[0]['status'],200)
        for kind, signature in [('pdf',b'%PDF'),('zip',b'PK'),('csv',None),('card',None)]:
            response, body, _ = self.call('/api/export?id='+scan['id']+'&kind='+kind+'&issue='+rid)
            self.assertEqual(response['status'],200,(kind,body))
            self.assertGreater(len(body),20)
            self.assertTrue(response['filename'])
            if signature: self.assertTrue(body.startswith(signature))

    def test_image_bytes_and_artifact_boundary(self):
        path = server.STORE.artifacts/'fixture.png'
        Image.new('RGB',(3,3),'white').save(path)
        response, body, _ = self.call('/api/artifact?path='+str(path))
        self.assertEqual(response['status'],200)
        self.assertEqual(body,path.read_bytes())
        self.assertEqual(self.call('/api/artifact?path=/etc/passwd')[0]['status'],400)

if __name__ == '__main__':
    unittest.main()
