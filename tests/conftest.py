import pytest
from _pytest.terminal import TerminalReporter


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter, exitstatus: int, config
):
    yield
    if hasattr(config, "all_confs"):
        terminalreporter.section("OCR Avg Confidences")
        terminalreporter.write(f"Conf.\tSimil.\tTest Explanation\n")
        terminalreporter.write("-" * 65 + "\n")
        for c in config.all_confs:
            terminalreporter.write(f"{c[0]:.1f}\t{c[1]:.2f}\t({c[2]})\n")
        terminalreporter.write("-" * 65 + "\n")
        conf_sum = sum([c[0] for c in config.all_confs])
        sim_sum = sum([c[1] for c in config.all_confs])
        count = len(config.all_confs)
        terminalreporter.write(f"{conf_sum/count:.2f}\t{sim_sum/count:.2f}\tMean\n")
        terminalreporter.write(f"{conf_sum:.2f}\t{sim_sum:.2f}\tSum\n")
