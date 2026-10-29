"""Optional frame-difference input. Not hand/face recognition; no upload/recording."""
import threading
import time


class MotionCamera:
    def __init__(self):
        self.active = False
        self.status = "CAMERA OFF"
        self.values = [0.] * 4
        self.index = 0
        self.sensitivity = .07
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

    def start(self, index=0):
        if self._thread and self._thread.is_alive():
            self.status = "STOP CAMERA BEFORE RECONNECTING"
            return
        self.index = index
        self._stop.clear()
        self.status = "CONNECTING..."
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()

    def _read(self):
        try:
            import cv2
        except ImportError:
            self.status = "INSTALL CAMERA EXTRA: uv sync --extra camera"
            return
        cap = None
        try:
            cap = cv2.VideoCapture(self.index)
            if not cap.isOpened():
                self.status = "NO CAMERA — TRY DEVICE 1 / 2; KEYBOARD STILL WORKS"
                return
            self.active = True
            self.status = f"CAMERA {self.index} / CALIBRATING"
            previous = None
            warmup = time.monotonic() + 2
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    self.status = "CAMERA DISCONNECTED — KEYBOARD AVAILABLE"
                    break
                gray = cv2.cvtColor(cv2.resize(cv2.flip(frame, 1), (160, 120)), cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (7, 7), 0)
                if previous is not None:
                    diff = cv2.absdiff(gray, previous)
                    changed = diff > 24
                    vals = [float(changed[y:y + 60, x:x + 80].mean()) for y, x in [(0, 0), (0, 80), (60, 0), (60, 80)]]
                    with self._lock:
                        self.values = vals if time.monotonic() > warmup else [0.] * 4
                    if time.monotonic() > warmup:
                        self.status = f"CAMERA {self.index} / LOCAL MOTION"
                previous = gray
                self._stop.wait(.04)
        except Exception:
            self.status = "CAMERA ERROR — KEYBOARD AVAILABLE"
        finally:
            if cap is not None:
                cap.release()
            self.active = False
            with self._lock:
                self.values = [0.] * 4

    def sample(self):
        with self._lock:
            return self.values.copy()

    def stop(self):
        self._stop.set()
        self.status = "CAMERA STOPPING" if self.active else "CAMERA OFF"

