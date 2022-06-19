"""Adjustments executed while packaging with briefcase during CI/CD."""

import shutil
import urllib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .utils import BRIEFCASE_EXCLUDES, BuilderBase, rm_recursive


class WindowsBriefcase(BuilderBase):
    """Create prebuild package for Windows using Nuitka."""

    binary_suffix = "_legacy"

    def bundle_tesseract(self):  # noqa: D102
        # Link to download artifact might change

        # https://ci.appveyor.com/project/zdenop/tesseract/build/artifacts

        if (self.TESSERACT_PATH / "tesseract.exe").exists():
            print("Tesseract.exe already present. Skipping download.")
            return

        url = "https://ci.appveyor.com/api/projects/zdenop/tesseract/artifacts/tesseract.zip"
        urllib.request.urlretrieve(f"{url}", self.BUILD_PATH / "tesseract.zip")
        with zipfile.ZipFile(self.BUILD_PATH / "tesseract.zip") as artifact_zip:
            members = [
                m
                for m in artifact_zip.namelist()
                if ".test." not in m and ".training." not in m
            ]
            subdir = members[0].split("/")[0]
            artifact_zip.extractall(path=self.RESOURCE_PATH, members=members)  #
        (self.BUILD_PATH / "tesseract.zip").unlink()
        print("Tesseract binaries downloaded.")

        for each_file in Path(self.RESOURCE_PATH / subdir).glob("*.*"):
            each_file.rename(self.TESSERACT_PATH / each_file.name)
        (self.TESSERACT_PATH / "google.tesseract.tesseract-master.exe").rename(
            self.TESSERACT_PATH / "tesseract.exe"
        )
        shutil.rmtree(self.RESOURCE_PATH / subdir)
        print("Binaries moved. Tesseract.exe renamed.")

    def download_openssl(self):
        """Download openssl needed for QNetwork https connections."""
        target_path = self.PROJECT_PATH / "src" / "normcap" / "resources" / "openssl"
        target_path.mkdir(exist_ok=True)
        zip_path = self.BUILD_PATH / "openssl.zip"
        urllib.request.urlretrieve(
            "http://wiki.overbyte.eu/arch/openssl-1.1.1m-win64.zip", zip_path
        )
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_path)

        zip_path.unlink()
        print("Openssl extracted")

    def patch_windows_installer(self):
        """Customize wix-installer.

        Currently only branding is added.
        """
        # pylint: disable=too-many-locals
        print("Preparing installer...")

        wxs_file = self.PROJECT_PATH / "windows" / "msi" / "NormCap" / "normcap.wxs"

        # Cache header for inserting later
        with open(wxs_file, encoding="utf-8") as f:
            header_lines = f.readlines()[:3]

        ns = "{http://schemas.microsoft.com/wix/2006/wi}"
        ET.register_namespace("", ns[1:-1])

        tree = ET.parse(wxs_file)
        root = tree.getroot()
        product = root.find(f"{ns}Product")

        # Copy installer images
        left = "normcap_install_bg.bmp"
        top = "normcap_install_top.bmp"
        for image in [left, top]:
            original = self.IMG_PATH / image
            target = self.PROJECT_PATH / "windows" / "msi" / "NormCap" / image
            shutil.copy(original, target)

        # Set installer images
        ET.SubElement(
            product, "WixVariable", {"Id": "WixUIDialogBmp", "Value": f"{left}"}
        )
        ET.SubElement(
            product, "WixVariable", {"Id": "WixUIBannerBmp", "Value": f"{top}"}
        )

        # Allow upgrades
        major_upgrade = ET.SubElement(product, "MajorUpgrade")
        major_upgrade.set("DowngradeErrorMessage", "Can't downgrade. Uninstall first.")

        sequence = product.find(f"{ns}InstallExecuteSequence")
        product.remove(sequence)

        upgrade = product.find(f"{ns}Upgrade")
        product.remove(upgrade)

        # Write & fix header
        tree.write(wxs_file, encoding="utf-8", xml_declaration=False)
        with open(wxs_file, "r+", encoding="utf-8") as f:
            lines = f.readlines()
            f.seek(0)
            f.writelines(header_lines + lines)

        print("Installer prepared.")

    def rename_package_file(self):  # noqa: D102
        source = list(Path(self.PROJECT_PATH / "windows").glob("*.msi"))[0]
        target = (
            self.BUILD_PATH
            / f"NormCap-{self.get_version()}-Windows{self.binary_suffix}.dmg"
        )
        target.unlink(missing_ok=True)
        shutil.move(source, target)

    def run_framework(self):  # noqa: D102
        app_dir = (
            self.PROJECT_PATH / "windows" / "msi" / "NormCap" / "src" / "app_packages"
        )
        self.run(cmd="briefcase create", cwd=self.PROJECT_PATH)
        rm_recursive(directory=app_dir, exclude=BRIEFCASE_EXCLUDES["app_packages"])
        rm_recursive(
            directory=app_dir / "PySide6", exclude=BRIEFCASE_EXCLUDES["pyside6"]
        )
        self.run(cmd="briefcase build", cwd=self.PROJECT_PATH)
        self.patch_windows_installer()
        self.run(cmd="briefcase package", cwd=self.PROJECT_PATH)

    def install_system_deps(self):  # noqa: D102
        pass

    def create(self):  # noqa: D102
        self.download_tessdata()
        self.download_openssl()
        self.bundle_tesseract()
        self.run_framework()
        self.rename_package_file()
