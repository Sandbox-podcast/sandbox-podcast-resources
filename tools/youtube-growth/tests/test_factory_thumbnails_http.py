"""Verify the thumbnail preview surface against persistent files over real HTTP."""
import hashlib
from http.client import HTTPConnection
import io
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image
from youtube_growth.factory.contracts import load_config
from youtube_growth.factory.store import Store
from youtube_growth.factory.web import make_server


class ThumbnailTypographyTests(unittest.TestCase):
    def test_punctuation_is_not_left_alone_on_a_new_line(self):
        from youtube_growth.factory.thumbnails import _wrap
        from youtube_growth.thumbnails import _font
        font = _font(60)
        width = max(font.getlength("LISIBLE"), font.getlength("PETIT ?"))+2
        lines = _wrap("LISIBLE EN PETIT ?", font, width)
        self.assertIsNotNone(lines)
        self.assertNotIn("?", lines)
        self.assertEqual(" ".join(lines), "LISIBLE EN PETIT ?")


class ThumbnailHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.preview = self.state / "episodes" / "fixture" / "thumbnails" / "preview.png"
        self.preview.parent.mkdir(parents=True)
        Image.new("RGB", (320, 180), "#071322").save(self.preview)
        self.sha = hashlib.sha256(self.preview.read_bytes()).hexdigest()
        self.bundle = {"bundle_id": "bundle-fixture", "episode_id": "fixture", "variants": [
            {"concept_id": "concept", "previews": [{"kind": "preview_320", "path": str(self.preview), "sha256": self.sha}]}]}
        with Store(self.state) as store:
            store.put("thumbnail_bundle", self.bundle["bundle_id"], self.bundle, episode_id="fixture")
        self.server = make_server(self.state, load_config(), port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            return response.status, response.getheader("Content-Type"), response.read()
        finally:
            connection.close()

    def test_real_png_preview_is_served_with_the_registered_hash(self):
        status, mime, data = self.request("/thumbnail/bundle-fixture/concept/320")
        self.assertEqual(status, 200)
        self.assertEqual(mime, "image/png")
        self.assertEqual(hashlib.sha256(data).hexdigest(), self.sha)
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual(image.size, (320, 180))

    def test_unknown_or_encoded_paths_cannot_browse_local_files(self):
        for path in ("/thumbnail/bundle-fixture/../320", "/thumbnail/%2e%2e/concept/320", "/thumbnail/bundle-fixture/concept/999", "/thumbnail/bundle-fixture/unknown/320"):
            self.assertEqual(self.request(path)[0], 404)

    def test_registered_image_outside_state_is_refused(self):
        outside = self.root / "outside.png"
        outside.write_bytes(self.preview.read_bytes())
        self.bundle["variants"][0]["previews"][0]["path"] = str(outside)
        with Store(self.state) as store:
            store.put("thumbnail_bundle", self.bundle["bundle_id"], self.bundle, episode_id="fixture")
        self.assertEqual(self.request("/thumbnail/bundle-fixture/concept/320")[0], 403)

    def test_replaced_preview_is_not_shown_as_a_reviewed_image(self):
        Image.new("RGB", (320, 180), "red").save(self.preview)
        self.assertEqual(self.request("/thumbnail/bundle-fixture/concept/320")[0], 409)


if __name__ == "__main__":
    unittest.main()
