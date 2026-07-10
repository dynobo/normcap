"""Run adjustments while packaging with briefcase during CI/CD."""

import urllib.request
import zipfile

from retry import retry

from platforms.utils import BuilderBase, bundle_tesseract_windows_ub_mannheim


class WindowsBriefcase(BuilderBase):
    """Create prebuilt package for Windows using Briefcase."""

    binary_suffix = ""
    binary_extension = "msi"
    binary_platform = "x86_64-Windows"

    @retry(tries=5, delay=1, backoff=2)
    def _download_openssl(self) -> None:
        """Download openssl needed for QNetwork https connections."""
        # For mirrors see: https://wiki.openssl.org/index.php/Binaries
        # openssl_url = "http://mirror.firedaemon.com/OpenSSL/openssl-1.1.1q.zip"
        # openssl_url = "https://indy.fulgan.com/SSL/openssl-1.0.2u-x64_86-win64.zip"
        openssl_url = "https://wiki.overbyte.eu/arch/openssl-4.0.1-win64.zip"
        target_path = self.PROJECT_PATH / "normcap" / "resources" / "openssl"
        target_path.mkdir(exist_ok=True)
        zip_path = self.BUILD_PATH / "openssl.zip"
        urllib.request.urlretrieve(openssl_url, zip_path)  # noqa: S310
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target_path)

        zip_path.unlink()

    def bundle_tesseract(self) -> None:
        """Download tesseract binaries including dependencies into resource path."""
        bundle_tesseract_windows_ub_mannheim(self)

    def run_framework(self) -> None:
        self.run(cmd="briefcase create windows VisualStudio", cwd=self.PROJECT_PATH)
        self.run(cmd="briefcase build windows VisualStudio", cwd=self.PROJECT_PATH)
        self.run(cmd="briefcase package windows VisualStudio", cwd=self.PROJECT_PATH)

    def install_system_deps(self) -> None: ...

    def pre_framework(self) -> None:
        self.bundle_tesseract()
        self._download_openssl()
