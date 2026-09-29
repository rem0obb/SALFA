import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from flare_generator import DEFAULT_UPDATE_SEED, generate_code, generate_many, read_update_seed
from ctf_generator_gui import parse_vins, self_test


class FlareGeneratorTests(unittest.TestCase):
    def test_matches_independent_sha1_fold(self):
        vin = "SALFA2AEXEH401960"
        seed = bytes(range(160))
        digest = hashlib.sha1(b"FiE_Gen21_NAVI_00_EU" + vin.encode("ascii") + seed).digest()
        expected = 0
        for word in struct.unpack(">5I", digest):
            expected ^= word
        self.assertEqual(generate_code(vin, seed), f"{expected:08X}")

    def test_firmware_forces_first_character_to_s(self):
        seed = bytes(160)
        self.assertEqual(
            generate_code("XALFA2AEXEH401960", seed),
            generate_code("SALFA2AEXEH401960", seed),
        )

    def test_multiple_vins(self):
        vins = ["SALFA2AEXEH401960", "SALFA2AE8DH343605"]
        results = generate_many(vins, bytes(160), "EU")
        self.assertEqual([vin for vin, _ in results], vins)
        self.assertTrue(all(len(code) == 8 for _, code in results))

    def test_supplied_ctf_examples(self):
        self.assertEqual(generate_code("SALFA2AEXEH401960", DEFAULT_UPDATE_SEED, "EU"), "2A8AD051")
        self.assertEqual(generate_code("SALFA2AE8DH343605", DEFAULT_UPDATE_SEED, "EU"), "2921B711")
        self.assertEqual(read_update_seed(), DEFAULT_UPDATE_SEED)

    def test_gui_accepts_multiple_vins(self):
        self.assertEqual(
            parse_vins("salfa2aexeh401960\nSALFA2AE8DH343605, SALFA2AEXEH401960"),
            ["SALFA2AEXEH401960", "SALFA2AE8DH343605"],
        )
        self.assertTrue(self_test())

    def test_external_update_inf(self):
        seed = bytes(reversed(range(160)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "UPDATE.INF")
            path.write_bytes(seed)
            self.assertEqual(read_update_seed(path), seed)
            self.assertEqual(
                generate_code("SALFA2AEXEH401960", read_update_seed(path), "EU"),
                generate_code("SALFA2AEXEH401960", seed, "EU"),
            )

    def test_rejects_invalid_input(self):
        with self.assertRaises(ValueError):
            generate_code("SHORT", bytes(160))
        with self.assertRaises(ValueError):
            generate_code("SALFA2AEXEH401960", bytes(159))
        with self.assertRaises(ValueError):
            generate_code("SALFA2AEXEH401960", bytes(160), "XX")


if __name__ == "__main__":
    unittest.main()
