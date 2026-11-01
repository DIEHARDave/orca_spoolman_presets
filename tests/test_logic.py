import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import orca_spoolman_presets as osp  # noqa: E402


def cand(name, rank, bundle_id=""):
    return {"name": name, "base": osp.base_name(name, bundle_id), "rank": rank}


def system(name, vendor, ftype, is_global=True):
    return {"name": name, "base": osp.base_name(name), "vendor": vendor, "type": ftype, "global": is_global}


CANDIDATES = [
    cand("Sunlu HS PLA+", osp.RANK_USER),
    cand("Sunlu HS PLA+ 2.0", osp.RANK_USER),
    cand("Sunlu PLA+ 2.0", osp.RANK_USER),
    cand("Sunlu Silk PLA+", osp.RANK_USER),
    cand("Sunlu HS PLA+ @Creality", osp.RANK_USER),
    cand("CCTREE PLA Matte", osp.RANK_USER),
    cand("Epelay PLA+", osp.RANK_USER),
    cand("VERTEXFIL PLA", osp.RANK_USER),
    cand("_local/spoolman/Sunlu PLA", osp.RANK_BUNDLE, "spoolman"),
    cand("SUNLU PLA+ 2.0 @System", osp.RANK_SYSTEM),
    cand("SUNLU PLA+ @System", osp.RANK_SYSTEM),
    cand("Generic PLA @System", osp.RANK_SYSTEM),
]

SYSTEMS = [
    system("SUNLU PLA+ 2.0 @System", "SUNLU", "PLA"),
    system("SUNLU PLA+ @System", "SUNLU", "PLA"),
    system("SUNLU PETG @FF AD5M", "SUNLU", "PETG", is_global=False),
    system("Generic PLA @System", "Generic", "PLA"),
    system("Generic PLA High Speed @System", "Generic", "PLA"),
    system("Generic PETG @System", "Generic", "PETG"),
    system("Generic PLA+ @System", "Generic", "PLA+"),
]


def best(vendor, material, name):
    found = osp.match_preset(osp.spool_keys(vendor, material, name), CANDIDATES)
    return found["name"] if found else None


class MatchTest(unittest.TestCase):
    def test_longest_line_wins_over_shorter(self):
        self.assertEqual(best("Sunlu", "PLA+", "HS PLA+ 2.0 Olive Green"), "Sunlu HS PLA+ 2.0")
        self.assertEqual(best("Sunlu", "PLA", "HS PLA+ White"), "Sunlu HS PLA+")

    def test_case_and_printer_suffix_are_ignored(self):
        self.assertEqual(best("SUNLU", "PLA", "Silk PLA+ Dual-Color Black Purple"), "Sunlu Silk PLA+")
        self.assertEqual(osp.base_name("Sunlu HS PLA+ @Creality"), "Sunlu HS PLA+")

    def test_user_preset_beats_system_on_a_tie(self):
        self.assertEqual(best("Sunlu", "PLA", "PLA+ 2.0 Black"), "Sunlu PLA+ 2.0")

    def test_color_only_names_match_through_the_material(self):
        self.assertEqual(best("Epelay", "PLA+", "Green"), "Epelay PLA+")
        self.assertEqual(best("Vertexfil", "PLA", "Cyan"), "VERTEXFIL PLA")
        self.assertEqual(best("CCTREE", "PLA", "Matte Navy Blue"), "CCTREE PLA Matte")
        self.assertEqual(best("Sunlu", "PLA", "Black"), "_local/spoolman/Sunlu PLA")

    def test_own_preset_without_vendor_matches_the_bare_name(self):
        candidates = CANDIDATES + [cand("Soleyin Ultra PLA", osp.RANK_USER),
                                   cand("Snapmaker PLA @System", osp.RANK_SYSTEM)]
        keys = osp.spool_keys("Creality", "PLA", "Soleyin Ultra PLA Ocean Blue")
        self.assertEqual(osp.match_preset(keys, candidates, "Soleyin Ultra PLA Ocean Blue")["name"],
                         "Soleyin Ultra PLA")
        # A built-in preset never matches the bare name: "PLA Silk" is not Snapmaker's.
        self.assertIsNone(osp.match_preset(["Miailuy PLA Silk"], [cand("PLA @System", osp.RANK_SYSTEM)], "PLA Silk"))

    def test_partial_words_do_not_match(self):
        self.assertIsNone(osp.match_preset(["Sunlu PLAX Red"], [cand("Sunlu PLA", 0)]))
        self.assertIsNone(best("Jayo", "PLA", "Olive Green"))

    def test_named_preset_by_base_name(self):
        found = osp.find_named_preset("sunlu hs pla+", CANDIDATES)
        self.assertEqual(found["name"], "Sunlu HS PLA+")
        self.assertIsNone(osp.find_named_preset("Deleted PLA", CANDIDATES))


class LineTest(unittest.TestCase):
    def test_proposed_lines(self):
        cases = [
            ("HS PLA+ 2.0 Olive Green", "PLA+", "HS PLA+ 2.0"),
            ("PLA-Meta Cherry Red", "PLA", "PLA-Meta"),
            ("Silk PLA+ Light Gold", "PLA+", "Silk PLA+"),
            ("Soleyin Ultra PLA Strawberry Milk", "PLA", "Soleyin Ultra PLA"),
            ("SnapSpeed PLA Blue Gray", "PLA", "SnapSpeed PLA"),
            ("Matte Beige", "PLA", "PLA Matte"),
            ("Black", "PLA+", "PLA+"),
            ("Fluorescent PLA Green", "PLA", "Fluorescent PLA"),
            ("Silk Gold-Copper-Blue", "PLA", "PLA Silk"),
        ]
        for name, material, expected in cases:
            self.assertEqual(osp.propose_line(name, material), expected, name)


class ParentTest(unittest.TestCase):
    def test_vendor_preset_sharing_most_words(self):
        self.assertEqual(osp.choose_parent("Sunlu", "PLA", "Sunlu HS PLA+ 2.0", SYSTEMS)["name"],
                         "SUNLU PLA+ 2.0 @System")

    def test_generic_for_unknown_vendor(self):
        self.assertEqual(osp.choose_parent("Jayo", "PLA", "Jayo PLA", SYSTEMS)["name"], "Generic PLA @System")
        self.assertEqual(osp.choose_parent("Jayo", "PLA+", "Jayo PLA+", SYSTEMS)["name"], "Generic PLA+ @System")

    def test_global_vendor_preset_preferred(self):
        systems = SYSTEMS + [system("SUNLU PETG @System", "SUNLU", "PETG")]
        self.assertEqual(osp.choose_parent("Sunlu", "PETG", "Sunlu PETG", systems)["name"], "SUNLU PETG @System")

    def test_printer_specific_vendor_preset_loses_to_generic(self):
        systems = SYSTEMS + [system("Snapmaker PLA SnapSpeed @U1", "Snapmaker", "PLA", is_global=False)]
        self.assertEqual(osp.choose_parent("Snapmaker", "PLA", "Snapmaker SnapSpeed PLA", systems)["name"],
                         "Generic PLA @System")
        only = [system("Snapmaker PLA SnapSpeed @U1", "Snapmaker", "PLA", is_global=False)]
        self.assertEqual(osp.choose_parent("Snapmaker", "PLA", "Snapmaker SnapSpeed PLA", only)["name"],
                         "Snapmaker PLA SnapSpeed @U1")

    def test_extra_parent_words_count_against_it(self):
        systems = SYSTEMS + [system("SUNLU Wood PLA @System", "SUNLU", "PLA"),
                             system("SUNLU PLA Matte @System", "SUNLU", "PLA")]
        self.assertEqual(osp.choose_parent("Sunlu", "PLA", "Sunlu Fluorescent PLA", systems)["name"],
                         "SUNLU PLA+ @System")
        self.assertEqual(osp.choose_parent("Sunlu", "PLA", "Sunlu PLA Matte", systems)["name"],
                         "SUNLU PLA Matte @System")

    def test_none_without_a_material_match(self):
        self.assertIsNone(osp.choose_parent("X", "PEEK", "X PEEK", SYSTEMS))


class MissingTest(unittest.TestCase):
    def test_groups_unmatched_filaments(self):
        fils = [
            {"name": "Olive Green", "material": "PLA", "vendor": {"name": "JAYO"},
             "settings_extruder_temp": 210, "settings_bed_temp": 60, "density": 1.24, "diameter": 1.75},
            {"name": "Lime", "material": "PLA", "vendor": {"name": "Jayo"}, "settings_extruder_temp": 215},
            {"name": "HS PLA+ 2.0 Blue", "material": "PLA+", "vendor": {"name": "Sunlu"}},
            {"name": "Odd", "material": "PLA", "vendor": {"name": "Jayo"}, "extra": {"orca_preset": "\"Sunlu HS PLA+\""}},
        ]
        items = osp.missing_presets(fils, CANDIDATES, SYSTEMS)
        self.assertEqual([i["name"] for i in items], ["JAYO PLA"])
        self.assertEqual(items[0]["count"], 2)
        self.assertEqual(items[0]["parent"], "Generic PLA @System")
        data = osp.preset_json(items[0])
        self.assertEqual(data["inherits"], "Generic PLA @System")
        self.assertEqual(data["filament_vendor"], ["JAYO"])
        self.assertEqual(data["filament_density"], ["1.24"])
        self.assertIn(data["nozzle_temperature"], (["210"], ["215"]))
        self.assertEqual(data["hot_plate_temp"], ["60"])


class MiscTest(unittest.TestCase):
    def test_decode_extra(self):
        self.assertEqual(osp.decode_extra('"Sunlu HS PLA+"'), "Sunlu HS PLA+")
        self.assertEqual(osp.decode_extra('""'), "")
        self.assertEqual(osp.decode_extra(None), "")

    def test_lanes(self):
        lanes = osp.lanes_from_lane_data({
            "T1": {"lane": "1", "material": ""},
            "T0": {"lane": "0", "material": "PLA", "spool_id": 77},
            "bad": "x",
        })
        self.assertEqual(lanes, [(1, 77, "PLA"), (2, None, "")])

    def test_preset_names(self):
        self.assertTrue(osp.valid_preset_name("Sunlu HS PLA+ 2.0"))
        for bad in ("", " x", "a/b", "x @C5", ".hidden"):
            self.assertFalse(osp.valid_preset_name(bad), bad)

    def test_first_config_value(self):
        self.assertEqual(osp._first('"SUNLU";"X"'), "SUNLU")
        self.assertEqual(osp._first('""'), "")
        self.assertEqual(osp._first("PLA"), "PLA")


if __name__ == "__main__":
    unittest.main()
