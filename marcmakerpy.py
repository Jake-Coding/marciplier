import subprocess
import os
paff = os.path.abspath(os.path.expanduser(os.path.expandvars("MARKMakerStuffs")))

for filename in os.listdir(paff):
    f = os.path.join(paff, filename)
    print(f)
    if not f.endswith("marc21.txt") and f.endswith(".txt"):
        os.system(f"cmarcedit -s \"{f}\" -d \"{f.replace(".txt", ".mrc")}\" -make")