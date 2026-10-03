"""Copy pinned browser assets from npm archives; never extract arbitrary paths.

Download with npm pack three@0.186.1 gsap@3.15.0
@fontsource-variable/fraunces@5.3.0 @fontsource-variable/dm-sans@5.3.0
--pack-destination output --silent, then run this script.
"""
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    "three-0.186.1.tgz": {
        "package/build/three.module.js": "vendor/three.module.js",
        "package/build/three.core.js": "vendor/three.core.js",
        "package/LICENSE": "vendor/THREE-LICENSE.txt",
    },
    "gsap-3.15.0.tgz": {
        "package/dist/gsap.min.js": "vendor/gsap.min.js",
        "package/README.md": "vendor/GSAP-README.md",
    },
    "fontsource-variable-fraunces-5.3.0.tgz": {
        "package/files/fraunces-latin-wght-normal.woff2": "fonts/fraunces.woff2",
        "package/LICENSE": "fonts/FRAUNCES-LICENSE.txt",
    },
    "fontsource-variable-dm-sans-5.3.0.tgz": {
        "package/files/dm-sans-latin-wght-normal.woff2": "fonts/dm-sans.woff2",
        "package/LICENSE": "fonts/DM-SANS-LICENSE.txt",
    },
}


def main():
    for archive, files in ASSETS.items():
        with tarfile.open(ROOT / "output" / archive) as package:
            for member, relative in files.items():
                destination = ROOT / "static" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                try:
                    source = package.extractfile(member)
                except KeyError:
                    if member.endswith("/LICENSE"):
                        source = package.extractfile("package/LICENSE.txt")
                    else:
                        raise
                content = source.read()
                if destination.suffix in (".js", ".md", ".txt"):
                    content = ("\n".join(line.rstrip() for line in content.decode("utf-8").splitlines()).rstrip() + "\n").encode("utf-8")
                destination.write_bytes(content)
                print(f"{relative}: {destination.stat().st_size:,} bytes")
    # Minify only vendored dependencies, not the application or component code.
    # Notices remain in the assets and the adjacent source/license documents.
    subprocess.run([shutil.which("npx"), "--yes", "esbuild@0.28.2",
                    "static/vendor/three.module.js", "static/vendor/three.core.js",
                    "--minify", "--legal-comments=inline", "--supported:template-literal=false", "--outdir=output/minified-vendor"],
                   cwd=ROOT, check=True)
    for filename in ("three.module.js", "three.core.js"):
        shutil.copyfile(ROOT / "output" / "minified-vendor" / filename, ROOT / "static" / "vendor" / filename)


if __name__ == "__main__":
    main()
