import time
import subprocess
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Protocol

# Configuration Constants
DEFAULT_APP_NAME = "同花顺"
DEFAULT_SAVE_DIR = "screenshots"
DEFAULT_TIMEOUT_SEC = 3.0
CHART_LOAD_DELAY_SEC = 2.0
KEYSTROKE_DELAY_SEC = 0.2
CHECK_INTERVAL_SEC = 0.5


class ApplicationError(Exception):
    """Base exception for application related errors."""
    pass


class ActivationError(ApplicationError):
    """Raised when application fails to activate."""
    pass


@dataclass
class WindowRegion:
    x: int
    y: int
    width: int
    height: int

    def to_screencapture_args(self) -> str:
        return f"{self.x},{self.y},{self.width},{self.height}"


class SystemInterface(Protocol):
    """Abstraction for system-level interactions."""

    def run_applescript(self, script: str) -> Optional[str]:
        ...

    def run_command(self, command: list[str]) -> None:
        ...


class MacSystem(SystemInterface):
    """macOS specific system interactions."""

    def run_applescript(self, script: str) -> Optional[str]:
        try:
            result = subprocess.run(["osascript", "-e", script],
                                    capture_output=True,
                                    text=True,
                                    check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
        except Exception as e:
            print(f"System error executing AppleScript: {e}")
            return None

    def run_command(self, command: list[str]) -> None:
        subprocess.run(command, check=True)


class StockAppDriver(ABC):
    """Abstract driver for stock trading applications."""

    @abstractmethod
    def activate(self) -> None:
        ...

    @abstractmethod
    def navigate_to_stock(self, symbol: str) -> None:
        ...

    @abstractmethod
    def hide(self) -> None:
        ...

    @abstractmethod
    def get_window_id(self) -> Optional[int]:
        ...

    @abstractmethod
    def get_window_region(self) -> Optional[WindowRegion]:
        ...


class TongHuaShunMacDriver(StockAppDriver):
    """Driver for TongHuaShun (同花顺) on macOS."""

    def __init__(self,
                 system: SystemInterface,
                 app_name: str = DEFAULT_APP_NAME):
        self.system = system
        self.app_name = app_name

    def activate(self) -> None:
        print(f"Activating {self.app_name}...")
        # Try 'open' command first
        try:
            self.system.run_command(["open", "-a", self.app_name])
            time.sleep(CHECK_INTERVAL_SEC)
        except Exception:
            pass

        # Ensure frontmost via AppleScript
        script = f'''
        tell application "System Events"
            if exists process "{self.app_name}" then
                tell process "{self.app_name}"
                    set frontmost to true
                    try
                        if exists (window 1) then set index of window 1 to 1
                    end try
                end tell
                return "ok"
            end if
        end tell
        '''
        if self.system.run_applescript(script) != "ok":
            raise ActivationError(f"Failed to activate {self.app_name}")

        self._wait_until_frontmost()

    def _wait_until_frontmost(self,
                              timeout: float = DEFAULT_TIMEOUT_SEC) -> None:
        start_time = time.time()
        script = 'tell application "System Events" to get name of first application process whose frontmost is true'

        while time.time() - start_time < timeout:
            res = self.system.run_applescript(script)
            if res == self.app_name:
                return
            time.sleep(CHECK_INTERVAL_SEC)

        print(f"Warning: {self.app_name} might not be frontmost.")

    def navigate_to_stock(self, symbol: str) -> None:
        print(f"Navigating to stock: {symbol}")
        script = f'''
        tell application "System Events"
            keystroke "{symbol}"
            delay {KEYSTROKE_DELAY_SEC}
            key code 36 -- Enter
        end tell
        '''
        self.system.run_applescript(script)
        # Wait for chart to render
        time.sleep(CHART_LOAD_DELAY_SEC)

    def hide(self) -> None:
        print(f"Hiding {self.app_name}...")
        script = f'tell application "System Events" to set visible of process "{self.app_name}" to false'
        self.system.run_applescript(script)

    def get_window_id(self) -> Optional[int]:
        script = f'''
        tell application "System Events"
            tell process "{self.app_name}"
                if exists (window 1) then return id of window 1
            end tell
        end tell
        '''
        res = self.system.run_applescript(script)
        return int(res) if res and res.isdigit() else None

    def get_window_region(self) -> Optional[WindowRegion]:
        script = f'''
        tell application "System Events"
            tell process "{self.app_name}"
                if exists (window 1) then
                    set pos to position of window 1
                    set sz to size of window 1
                    return pos & sz
                end if
            end tell
        end tell
        '''
        res = self.system.run_applescript(script)
        if res:
            try:
                parts = [int(p.strip()) for p in res.split(',') if p.strip()]
                if len(parts) == 4:
                    return WindowRegion(*parts)
            except ValueError:
                pass
        return None


class ScreenCapturer:
    """Handles screenshot logic with fallback strategies."""

    def __init__(self, save_dir: str = DEFAULT_SAVE_DIR):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

    def capture(self, filename: str, app: StockAppDriver) -> Path:
        filepath = self.save_dir / filename
        print(f"Capturing screenshot to: {filepath}")

        # Strategy 1: Window ID (Best for clean capture)
        if wid := app.get_window_id():
            if self._try_capture(["-l", str(wid)], filepath):
                return filepath

        # Strategy 2: Region (Good if ID fails)
        if region := app.get_window_region():
            if self._try_capture(["-R", region.to_screencapture_args()],
                                 filepath):
                return filepath

        # Strategy 3: Fullscreen (Fallback)
        print("Fallback to fullscreen capture.")
        self._try_capture([], filepath)
        return filepath

    def _try_capture(self, args: list[str], filepath: Path) -> bool:
        cmd = ["screencapture"] + args + ["-x", str(filepath)]
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            return False


class ChartAnalyzer(ABC):
    """Abstract base class for chart analysis."""

    @abstractmethod
    def analyze(self, image_path: Path) -> str:
        ...


class ChanTheoryAnalyzer(ChartAnalyzer):
    """
    Analyzes chart using Chan Theory (缠论).
    Note: Real implementation would require a VLM (Vision Language Model) API.
    """

    def analyze(self, image_path: Path) -> str:
        # Simulation of an analysis result since we lack a real VLM in this environment
        # In a production setting, this would call GPT-4o-Vision or similar.
        return f"""
        [Chan Theory Analysis for {image_path.name}]
        ------------------------------------------------
        1. Trend Definition:
           - Current Level: Daily/60min consolidation.
           - Direction: Neutral to Bullish.
        
        2. Structure (Morphology):
           - Detected a 'Center' (ZhongShu) formation.
           - Recent stroke suggests a Type 2 Buy Point (Second Buy).
        
        3. Divergence:
           - MACD divergence observed on the latest bottom.
           
        4. Conclusion:
           - Wait for confirmation of the upward stroke.
           - Stop loss below the recent low.
        ------------------------------------------------
        (Note: This is a simulated analysis based on heuristic templates.)
        """


class StockWorkflow:
    """Orchestrates the stock capture and analysis workflow."""

    def __init__(self, app_driver: StockAppDriver, capturer: ScreenCapturer,
                 analyzer: ChartAnalyzer):
        self.app = app_driver
        self.capturer = capturer
        self.analyzer = analyzer

    def run(self, symbol: str) -> None:
        try:
            # 1. Prepare App
            self.app.activate()

            # 2. Navigate
            self.app.navigate_to_stock(symbol)

            # 3. Capture
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{timestamp}.png"
            image_path = self.capturer.capture(filename, self.app)

            # 4. Analyze
            print(f"\nRunning analysis on {image_path.name}...")
            analysis_result = self.analyzer.analyze(image_path)
            print(analysis_result)

        except ApplicationError as e:
            print(f"Workflow failed: {e}")
        finally:
            self.app.hide()


if __name__ == "__main__":
    # Dependency Injection
    system = MacSystem()
    driver = TongHuaShunMacDriver(system)
    capturer = ScreenCapturer()
    analyzer = ChanTheoryAnalyzer()

    workflow = StockWorkflow(driver, capturer, analyzer)

    # Execution for WuXi AppTec (603259)
    # Or user input if needed
    target_code = "603259"  # 药明康德
    print(f"Starting workflow for {target_code} (药明康德)...")
    workflow.run(target_code)
