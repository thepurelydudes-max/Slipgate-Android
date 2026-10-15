import importlib.util
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("port",ROOT/"scripts/apply_port.py")
port=importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)
class PortTest(unittest.TestCase):
    def test_target_lists(self):
        general,youtube,discord=port.load_profiles(ROOT/"profiles")
        self.assertIn("youtube.com",youtube)
        self.assertIn("discord.com",discord)
        self.assertIn("youtube.com",general)
        self.assertNotIn("twitch.tv",general)
    def test_parser(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"l.txt"
            f.write_text("#comment\nEXAMPLE.COM\ninvalid/path\nexample.com\n")
            self.assertEqual(port.read_domains(f),{"example.com"})
if __name__=="__main__":
    unittest.main()
