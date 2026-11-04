"""Tests for scripts/thermal_watch.sh with fake readers and a dummy job: when it pauses and when it resumes."""
import os
import stat
import subprocess
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "thermal_watch.sh"


def _exe(path: Path, body: str) -> Path:
    path.write_text("#!/bin/bash\n" + body + "\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


class Rig:
    """Dummy job plus a watcher (1 s samples) whose readers take their values from files that a test can change."""

    def __init__(self, tmp: Path, **start):
        self.state, self.limit, self.gpu, self.log = tmp / "state", tmp / "limit", tmp / "gpu", tmp / "w.log"
        self.set(**{"state": 0, "limit": 100, "gpu": 0, **start})
        ts = _exe(tmp / "ts", f"cat {self.state}")
        therm = _exe(tmp / "therm", f'echo "CPU_Speed_Limit = $(cat {self.limit})"')
        gpu = _exe(tmp / "gpucmd", f"""echo '"Device Utilization %"='$(cat {self.gpu})""")
        self.job = subprocess.Popen(["sleep", "120"])
        env = dict(os.environ, SAMPLE="1", THERM_CMD=str(therm), GPU_CMD=str(gpu))
        self.watch = subprocess.Popen(["/bin/bash", str(SCRIPT), str(self.job.pid), str(self.log), str(ts)], env=env)

    def set(self, **kw):
        for k, v in kw.items():
            getattr(self, k).write_text(str(v))

    def stopped(self) -> bool:
        out = subprocess.run(["ps", "-o", "stat=", "-p", str(self.job.pid)], capture_output=True, text=True).stdout
        return out.startswith("T")

    def close(self):
        self.watch.kill()
        self.job.kill()
        self.job.wait()
        self.watch.wait()


def _wait(pred, secs: float) -> bool:
    end = time.time() + secs
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.1)
    return False


def test_serious_state_pauses_at_once_and_resumes_only_after_five_healthy_samples(tmp_path):
    rig = Rig(tmp_path, state=2)
    try:
        assert _wait(rig.stopped, 3)
        time.sleep(2)
        assert rig.stopped()                         # still serious: stays paused
        rig.set(state=0)
        time.sleep(3)
        assert rig.stopped()                         # healthy, but not yet for 5 samples
        assert _wait(lambda: not rig.stopped(), 6)
    finally:
        rig.close()


def test_throttling_below_90_needs_two_samples(tmp_path):
    rig = Rig(tmp_path, limit=85)
    try:
        assert _wait(rig.stopped, 4)
    finally:
        rig.close()


def test_mild_throttling_for_a_short_time_does_not_pause(tmp_path):
    rig = Rig(tmp_path, limit=95)
    try:
        assert not _wait(rig.stopped, 3)
    finally:
        rig.close()


def test_gpu_alone_and_fair_state_never_pause(tmp_path):
    rig = Rig(tmp_path, gpu=100)
    try:
        assert not _wait(rig.stopped, 12)
    finally:
        rig.close()
    rig = Rig(tmp_path, state=1)
    try:
        assert not _wait(rig.stopped, 3)
    finally:
        rig.close()


def test_gpu_with_heat_pauses_after_ten_samples(tmp_path):
    rig = Rig(tmp_path, gpu=95, state=1)
    try:
        assert _wait(rig.stopped, 14)
    finally:
        rig.close()
