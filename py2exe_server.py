from distutils.core import setup  
import py2exe  
import sys

if __name__ == "__main__":
    file = input()
    includes = ["encodings", "encodings.*"]
    sys.argv.append("py2exe")
    options = {"py2exe": dict(bundle_files=1)}
    setup(options = options,
        zipfile=None,
        console = [{"script":file}])