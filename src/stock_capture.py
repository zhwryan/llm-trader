import time
import subprocess
import os
from datetime import datetime
from typing import Optional, Tuple

# Constants
DEFAULT_APP_NAME = "同花顺"
DEFAULT_SAVE_DIR = "screenshots"
WAIT_FOR_APP_ACTIVATION_SEC = 3.0  # 等待应用激活的时间
WAIT_FOR_CHART_LOAD_SEC = 1.5  # 等待股票图表加载完成的时间
KEYSTROKE_DELAY_SEC = 0.2  # 按键延迟时间，防止操作过快
SEARCH_LIST_DELAY_SEC = 1.0  # 等待搜索结果列表浮现的时间
CHECK_INTERVAL_SEC = 0.5  # 检查间隔时间

# Key Codes
KEY_CODE_ESC = 53
KEY_CODE_ENTER = 36
DIGIT_KEY_CODES = {
    '0': 29,
    '1': 18,
    '2': 19,
    '3': 20,
    '4': 21,
    '5': 23,
    '6': 22,
    '7': 26,
    '8': 28,
    '9': 25
}


class AppleScriptRunner:
    """
    AppleScript 执行器
    Encapsulates AppleScript execution logic.
    """

    @staticmethod
    def run(script: str, verbose_error: bool = True) -> Optional[str]:
        """
        执行 AppleScript 并返回结果
        Execute AppleScript and return the result.
        Returns None if execution fails.
        """
        try:
            result = subprocess.run(["osascript", "-e", script],
                                    capture_output=True,
                                    text=True,
                                    check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # AppleScript execution error
            if verbose_error:
                print(f"⚠️ AppleScript execution failed: {e.stderr.strip()}")
            return None
        except Exception as e:
            print(f"❌ System error executing AppleScript: {e}")
            return None


class StockAppController:
    """
    股票应用控制器
    Controls the stock trading application via AppleScript.
    """

    def __init__(self, app_name: str = DEFAULT_APP_NAME):
        self.app_name = app_name

    def activate(self) -> bool:
        """
        激活应用并置顶
        Activates the application and brings it to front.
        """
        print(f"正在激活应用: {self.app_name}")

        # 1. 尝试使用 open 命令 (处理最小化/虚拟桌面)
        try:
            subprocess.run(["open", "-a", self.app_name], check=True)
            time.sleep(CHECK_INTERVAL_SEC)
        except Exception:
            pass

        # 2. 使用 AppleScript 确保窗口获得焦点
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
        return AppleScriptRunner.run(script) == "ok"

    def hide(self):
        """
        隐藏应用
        Hides the application.
        """
        print(f"正在隐藏应用: {self.app_name}")
        script = f'tell application "System Events" to set visible of process "{self.app_name}" to false'
        AppleScriptRunner.run(script)

    def is_frontmost(self) -> bool:
        """
        检查应用是否在前台
        Checks if the application is currently frontmost.
        """
        script = 'tell application "System Events" to get name of first application process whose frontmost is true'
        return AppleScriptRunner.run(script) == self.app_name

    def wait_until_frontmost(self,
                             timeout: float = WAIT_FOR_APP_ACTIVATION_SEC
                             ) -> bool:
        """
        等待应用直到置顶
        Waits until the application is frontmost.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_frontmost():
                return True
            time.sleep(CHECK_INTERVAL_SEC)
        return False

    def send_keystrokes(self, text: str) -> bool:
        """
        模拟键盘输入
        Simulates keyboard input.
        """
        print(f"正在输入: {text}")

        # 构建输入指令序列
        # 优先使用 Key Code (绕过输入法)，否则使用 Keystroke (逐字输入)
        input_cmds = []
        if text.isdigit():
            for char in text:
                if char in DIGIT_KEY_CODES:
                    input_cmds.append(f'key code {DIGIT_KEY_CODES[char]}')
                    input_cmds.append('delay 0.05')
        else:
            for char in text:
                input_cmds.append(f'keystroke "{char}"')
                input_cmds.append('delay 0.05')

        input_script_block = "\n            ".join(input_cmds)

        script = f'''
        tell application "System Events"
            tell process "{self.app_name}"
                set frontmost to true
            end tell
            
            delay 0.5 -- Ensure app is fully active
            key code {KEY_CODE_ESC} -- ESC to clear potential dialogs
            delay 0.2
            
            {input_script_block}
            
            delay {SEARCH_LIST_DELAY_SEC} -- Wait for search results to populate
            key code {KEY_CODE_ENTER} -- Enter
        end tell
        '''
        if AppleScriptRunner.run(script) is None:
            print(f"⚠️ 输入 '{text}' 执行失败，请检查权限或应用状态")
            return False
        return True

    def get_window_id(self) -> Optional[int]:
        """
        获取主窗口 ID
        Gets the main window ID.
        """
        script = f'''
        tell application "System Events"
            tell process "{self.app_name}"
                if exists (window 1) then return id of window 1
            end tell
        end tell
        '''
        # Suppress error because this is a probing strategy; failure is expected for some apps.
        res = AppleScriptRunner.run(script, verbose_error=False)
        return int(res) if res and res.isdigit() else None

    def get_window_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        获取主窗口区域 (x, y, w, h)
        Gets the main window region.
        """
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
        res = AppleScriptRunner.run(script)
        if res:
            try:
                parts = [int(p.strip()) for p in res.split(',') if p.strip()]
                if len(parts) == 4:
                    return tuple(parts)
            except ValueError:
                pass
        return None


class ScreenshotManager:
    """
    截图管理器
    Handles screenshot operations.
    """

    def __init__(self, save_dir: str = DEFAULT_SAVE_DIR):
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

    def take(self, filename: str, app_controller: StockAppController) -> bool:
        """
        执行截图策略：Window ID -> 区域 -> 全屏
        Takes a screenshot using the best available strategy.
        Strategies: Window ID -> Region -> Fullscreen
        """
        filepath = os.path.join(self.save_dir, filename)
        print(f"正在截图: {filepath}")

        # Strategy 1: Window ID
        wid = app_controller.get_window_id()
        if wid:
            try:
                subprocess.run(
                    ["screencapture", "-l",
                     str(wid), "-x", "-o", filepath],
                    check=True)
                print("✅ 截图成功 (Window ID模式)")
                return True
            except subprocess.CalledProcessError:
                print("⚠️ Window ID 截图失败，尝试降级...")

        # Strategy 2: Region
        region = app_controller.get_window_region()
        if region:
            try:
                x, y, w, h = region
                subprocess.run([
                    "screencapture", "-R", f"{x},{y},{w},{h}", "-x", filepath
                ],
                               check=True)
                print("✅ 截图成功 (区域模式)")
                return True
            except subprocess.CalledProcessError:
                print("⚠️ 区域截图失败，尝试降级...")

        # Strategy 3: Fullscreen
        try:
            print("⚠️ 无法定位窗口，使用全屏截图兜底")
            subprocess.run(["screencapture", "-x", filepath], check=True)
            print("✅ 截图成功 (全屏模式)")
            return True
        except Exception as e:
            print(f"❌ 截图完全失败: {e}")
            return False


def capture_stock_workflow(stock_code: str,
                           app_name: str = DEFAULT_APP_NAME) -> Optional[str]:
    """
    主流程：激活应用 -> 输入代码 -> 截图 -> 隐藏应用
    Main workflow: Activate -> Input Code -> Screenshot -> Hide
    Returns: filepath if successful, None otherwise
    """
    app = StockAppController(app_name)
    screenshot_mgr = ScreenshotManager()

    # 1. Activate App
    if not app.activate():
        print(f"❌ 无法激活应用: {app_name}，请确认应用已启动。")
        return None

    if not app.wait_until_frontmost():
        print(f"⚠️ 警告: {app_name} 可能未置顶，后续操作可能失败。")

    # 2. Input Stock Code
    if not app.send_keystrokes(stock_code):
        print("❌ 股票代码输入失败，终止流程")
        return None

    # Wait for chart to load
    time.sleep(WAIT_FOR_CHART_LOAD_SEC)

    # 3. Take Screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{stock_code}_{timestamp}.png"
    if screenshot_mgr.take(filename, app):
        filepath = os.path.join(screenshot_mgr.save_dir, filename)
        # 4. Hide App
        app.hide()
        return filepath

    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        code = sys.argv[1]
    else:
        code = "603259"

    path = capture_stock_workflow(code)
    if path:
        print(f"SCREENSHOT_SAVED: {path}")
    else:
        sys.exit(1)
