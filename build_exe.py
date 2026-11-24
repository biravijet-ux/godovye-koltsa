"""Сборка самостоятельного Windows EXE без перезаписи старых выпусков."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from les import VERSION

HERE = Path(__file__).resolve().parent


def build(destination=None):
    dst = Path(destination).resolve() if destination else HERE.parent / "releases" / f"Годовые-кольца-{VERSION}-Windows"
    archive = Path(str(dst) + ".zip")
    if dst.exists() or archive.exists():
        raise FileExistsError(f"Папка или архив уже существуют: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rings-exe-build-") as temp:
        root = Path(temp)
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                        "--onefile", "--console", "--name", "GodovyeKoltsa",
                        "--distpath", str(root / "dist"), "--workpath", str(root / "work"),
                        "--specpath", str(root), str(HERE / "launch.py")], cwd=HERE, check=True)
        dst.mkdir()
        shutil.copy2(root / "dist/GodovyeKoltsa.exe", dst / "GodovyeKoltsa.exe")
    shutil.copy2(HERE / "README.md", dst / "README.md")
    shutil.make_archive(str(dst), "zip", root_dir=dst.parent, base_dir=dst.name)
    return dst, archive


if __name__ == "__main__":
    folder, archive = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"EXE: {folder}")
    print(f"Архив: {archive}")
