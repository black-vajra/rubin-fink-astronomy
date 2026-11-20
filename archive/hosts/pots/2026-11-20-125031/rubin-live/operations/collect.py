import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

root = Path.home() / "rubin-live"
heartbeat = root / "operations" / "last-collector-seen"


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(timespec="seconds")


now = time.time()
if heartbeat.exists():
    previous = float(heartbeat.read_text())
    gap = max(0, now - previous)
    print(f"Collector gap: approximately {gap / 60:.1f} minutes "
          f"({utc(previous)} to {utc(now)})", flush=True)
else:
    print(f"First unattended collector start at {utc(now)}", flush=True)


def mark_seen():
    temporary = heartbeat.with_suffix(".tmp")
    temporary.write_text(str(time.time()))
    temporary.replace(heartbeat)


stopping = False


def request_stop(signum, frame):
    global stopping
    stopping = True


signal.signal(signal.SIGTERM, request_stop)
signal.signal(signal.SIGINT, request_stop)

with subprocess.Popen([
    str(root / "venv" / "bin" / "finkctl"), "stream", "-survey", "lsst",
    "--save", "-outdir", str(root / "alerts" / "unattended"),
]) as child:
    while not stopping:
        status = child.poll()
        if status is not None:
            print(f"Fink collector exited with status {status}", flush=True)
            raise SystemExit(status or 1)
        mark_seen()
        for _ in range(30):
            if stopping or child.poll() is not None:
                break
            time.sleep(1)

    if child.poll() is None:
        child.send_signal(signal.SIGINT)
        try:
            child.wait(timeout=20)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
    mark_seen()
    print("Collector stopped.", flush=True)
