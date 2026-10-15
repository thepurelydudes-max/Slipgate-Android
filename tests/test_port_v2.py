import importlib.util
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v2",ROOT/"scripts/apply_port_v2.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class V2Tests(unittest.TestCase):
    def test_domains(self):
        x=mod.targets(ROOT/"profiles")
        self.assertIn("youtube.com",x)
        self.assertIn("discord.com",x)
        self.assertNotIn("twitch.tv",x)
    def test_reader(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"list"
            f.write_text("Example.com\ninvalid/path\nEXAMPLE.COM\n")
            self.assertEqual(mod.domains(f),{"example.com"})
