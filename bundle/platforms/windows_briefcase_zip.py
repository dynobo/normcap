"""Run adjustments while packaging with briefcase during CI/CD."""

from platforms.windows_briefcase  import WindowsBriefcase


class WindowsBriefcaseZip(WindowsBriefcase):
    """Create portable package for Windows using Briefcase."""

    binary_suffix = ""
    binary_extension = "zip"
    binary_platform = "x86_64-Windows"

    def run_framework(self) -> None:
        self.run(cmd="briefcase create windows VisualStudio", cwd=self.PROJECT_PATH)
        self._patch_main_cpp()
        self.run(cmd="briefcase build windows VisualStudio", cwd=self.PROJECT_PATH)
        self._patch_windows_installer()
        self.run(cmd="briefcase package windows VisualStudio -p zip", cwd=self.PROJECT_PATH)
