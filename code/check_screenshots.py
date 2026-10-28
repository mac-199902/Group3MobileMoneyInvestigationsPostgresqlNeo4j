"""check_screenshots.py - list expected screenshot codes that have no file yet."""
import os

CODES = """s1-1_01 s1-1_02 s1-1_03 s1-1_04 s1-1_05 s1-2_01 s1-2_02 s1-2_03 s1-2_04 s1-2_05
s2-1_01a s2-1_01b s2-1_02 s2-2_01 s2-2_02 s2-2_03 s2-2_04
s3-1_01 s3-2_01 s3-2_02 s3-2_03 s3-2_04 s3-2_05 s3-3_01 s3-3_02
s4-1_01 s4-2_01 s4-2_02 s4-3_01
s5-1_01 s5-1_02 s5-1_03 s5-1_04 s5-2_01 s5-2_02 s5-2_03
s5-3_01 s5-3_02 s5-3_03 s5-4_01 s5-4_02 s5-4_03
s6-1_01 s6-1_02 s6-1_03 s6-2_01 s6-2_02 s6-2_03 s6-3_01 s6-3_02 s6-3_03
s7-1_01 s7-1_02 s7-2_01 s7-2_02 s8-1_01 s8-1_02 s8-1_03
s9-2_01 s9-2_02 s9-2_03""".split()

files = os.listdir(r"D:\MobileMoneyProject\screenshots")
missing = [c for c in CODES if not any(f.startswith(c + "_") for f in files)]
print(f"{len(CODES) - len(missing)} of {len(CODES)} expected screenshots present")
print("Missing:", " ".join(missing))