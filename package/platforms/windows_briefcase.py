"""Adjustments executed while packaging with briefcase during CI/CD."""

import shutil
import urllib
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from platforms.utils import (
    BRIEFCASE_EXCLUDES,
    BuilderBase,
    bundle_tesseract_windows,
    rm_recursive,
)


class WindowsBriefcase(BuilderBase):
    """Create prebuild package for Windows using Nuitka."""

    binary_suffix = ""

    def bundle_tesseract(self):
        """Download tesseract binaries including dependencies into resource path."""
        bundle_tesseract_windows(self)

    def download_openssl(self):
        """Download openssl needed for QNetwork https connections."""
        # For mirrors see: https://wiki.openssl.org/index.php/Binaries
        # OPENSSL_URL = "http://mirror.firedaemon.com/OpenSSL/openssl-1.1.1q.zip"
        openssl_url = "http://wiki.overbyte.eu/arch/openssl-1.1.1q-win64.zip"
        target_path = self.PROJECT_PATH / "src" / "normcap" / "resources" / "openssl"
        target_path.mkdir(exist_ok=True)
        zip_path = self.BUILD_PATH / "openssl.zip"
        urllib.request.urlretrieve(openssl_url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_path)

        zip_path.unlink()

    def patch_windows_installer(self):
        """Customize wix-installer."""
        wxs_file = self.PROJECT_PATH / "windows" / "app" / "NormCap" / "normcap.wxs"

        # Cache header for inserting later
        with open(wxs_file, encoding="utf-8") as f:
            header_lines = f.readlines()[:3]

        ns = "{http://schemas.microsoft.com/wix/2006/wi}"
        ElementTree.register_namespace("", ns[1:-1])

        tree = ElementTree.parse(wxs_file)
        root = tree.getroot()
        product = root.find(f"{ns}Product")

        # Copy installer images
        left = "normcap_install_bg.bmp"
        top = "normcap_install_top.bmp"
        for image in [left, top]:
            original = self.IMG_PATH / image
            target = self.PROJECT_PATH / "windows" / "app" / "NormCap" / image
            shutil.copy(original, target)

        # Set installer images
        ElementTree.SubElement(
            product, "WixVariable", {"Id": "WixUIDialogBmp", "Value": f"{left}"}
        )
        ElementTree.SubElement(
            product, "WixVariable", {"Id": "WixUIBannerBmp", "Value": f"{top}"}
        )

        # Allow upgrades
        major_upgrade = ElementTree.SubElement(product, "MajorUpgrade")
        major_upgrade.set("DowngradeErrorMessage", "Can't downgrade. Uninstall first.")

        # Cleanup tessdata folder on uninstall
        ElementTree.SubElement(
            product,
            "CustomAction",
            {
                "Id": "Cleanup_tessdata",
                "Directory": "TARGETDIR",
                "ExeCommand": 'cmd /C "rmdir /s /q %localappdata%\\normcap '
                + '& rmdir /s /q %localappdata%\\dynobo";',
                "Execute": "deferred",
                "Return": "ignore",
                "HideTarget": "no",
                "Impersonate": "no",
            },
        )
        sequence = product.find(f"{ns}InstallExecuteSequence")
        ElementTree.SubElement(
            sequence,
            "Custom",
            {"Action": "Cleanup_tessdata", "Before": "RemoveFiles"},
        ).text = 'REMOVE="ALL"'

        # Remove node which throws error during compilation
        remove_existing_product = sequence.find(f"{ns}RemoveExistingProducts")
        sequence.remove(remove_existing_product)

        upgrade = product.find(f"{ns}Upgrade")
        product.remove(upgrade)

        # Write & fix header
        tree.write(wxs_file, encoding="utf-8", xml_declaration=False)
        with open(wxs_file, "r+", encoding="utf-8") as f:
            lines = f.readlines()
            f.seek(0)
            f.writelines(header_lines + lines)

    def rename_package_file(self):
        source = list(Path(self.PROJECT_PATH / "windows").glob("*.msi"))[0]
        target = (
            self.BUILD_PATH
            / f"NormCap-{self.get_version()}-x86_64-Windows{self.binary_suffix}.msi"
        )
        target.unlink(missing_ok=True)
        shutil.move(source, target)

    def run_framework(self):
        app_dir = (
            self.PROJECT_PATH / "windows" / "app" / "NormCap" / "src" / "app_packages"
        )
        self.run(cmd="briefcase create", cwd=self.PROJECT_PATH)
        rm_recursive(directory=app_dir, exclude=BRIEFCASE_EXCLUDES["app_packages"])
        rm_recursive(
            directory=app_dir / "PySide6", exclude=BRIEFCASE_EXCLUDES["pyside6"]
        )
        self.run(cmd="briefcase build", cwd=self.PROJECT_PATH)
        self.patch_windows_installer()
        self.run(cmd="briefcase package", cwd=self.PROJECT_PATH)

    def install_system_deps(self):
        pass

    def create(self):
        self.download_tessdata()
        self.download_openssl()
        self.bundle_tesseract()
        self.run_framework()
        self.rename_package_file()
