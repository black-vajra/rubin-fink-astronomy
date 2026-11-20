"""Restartable Fink collector with a persistent process heartbeat."""
from datetime import datetime, timezone
from pathlib import Path
import os
import signal
import subprocess
import time

ROOT = Path.home() / "rubin-quasar"
HEARTBEAT = ROOT / "last-collector-seen"
stopping = False


def stop(signum, frame):
    global stopping
    stopping = True


def mark_seen():
    temp = HEARTBEAT.with_suffix(".tmp")
    temp.write_text(str(time.time()))
    temp.replace(HEARTBEAT)


def main():
    output = ROOT / "alerts" / "unattended"
    output.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    now = datetime.now(timezone.utc)
    if HEARTBEAT.exists():
        previous = float(HEARTBEAT.read_text())
        print(f"Collector gap: approximately {max(0, now.timestamp() - previous) / 60:.1f} minutes; restart {now.isoformat()}", flush=True)
    else:
        print(f"First collector start at {now.isoformat()}", flush=True)
    client = Path.home() / "rubin-live/venv/bin/finkctl"
    with subprocess.Popen([str(client), "stream", "-survey", "lsst", "--save",
                           "-outdir", str(output)], env=dict(os.environ, HOME=str(ROOT / "fink-home"))) as child:
        while not stopping and child.poll() is None:
            mark_seen()
            for _ in range(30):
                if stopping or child.poll() is not None:
                    break
                time.sleep(1)
        if not stopping:
            print(f"Fink collector exited with status {child.returncode}", flush=True)
            return child.returncode or 1
        if child.poll() is None:
            child.send_signal(signal.SIGINT)
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        mark_seen()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
