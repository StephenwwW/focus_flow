@echo off
chcp 65001 > nul
REM ============================================================================
REM  FocusFlow 應用程式自動打包腳本 (Windows) 
REM ============================================================================
REM
REM  使用方式:
REM  1. 請確認此檔案與 main.py, requirements.txt, icon.ico 位於同一個資料夾。
REM  2. 直接雙擊執行此 build.bat 檔案即可。
REM
REM ============================================================================

ECHO [INFO] 開始執行 FocusFlow 打包程序...
ECHO.

REM --- 步驟 1: 將目前路徑切換到本腳本所在的資料夾 ---
cd /d "%~dp0"
ECHO [INFO] 目前工作目錄已設定為: %cd%
ECHO.

REM --- 步驟 2: 建立虛擬環境 (如果不存在) ---
IF NOT EXIST "venv" (
    ECHO [INFO] 'venv' 虛擬環境不存在，正在建立中...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO [ERROR] 建立虛擬環境失敗!
        ECHO [ERROR] 請確認您的電腦已正確安裝 Python 並且設定了環境變數。
        GOTO:END
    )
    ECHO [INFO] 虛擬環境建立成功。
) ELSE (
    ECHO [INFO] 'venv' 虛擬環境已存在，跳過建立步驟。
)
ECHO.

REM --- 步驟 3: 啟用虛擬環境並安裝套件 ---
ECHO [INFO] 正在啟用虛擬環境並安裝必要的 Python 套件...
CALL "venv\Scripts\activate.bat"

pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] 從 requirements.txt 安裝套件時發生錯誤! 請檢查網路連線或檔案內容。
    GOTO:END
)

pip install pyinstaller
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] 安裝 pyinstaller 時發生錯誤! 請檢查網路連線。
    GOTO:END
)
ECHO [INFO] 所有套件安裝完成。
ECHO.

REM --- 步驟 4: 執行 PyInstaller 打包 ---
ECHO [INFO] ==================================================
ECHO [INFO]               即將開始打包應用程式
ECHO [INFO] ==================================================
ECHO.

pyinstaller --name Focus_Flow --windowed --onefile --icon="icon.ico" main.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] PyInstaller 打包失敗! 請向上捲動視窗查看詳細的錯誤訊息。
) ELSE (
    ECHO.
    ECHO [SUCCESS] ==================================================
    ECHO [SUCCESS]                  打包成功！
    ECHO [SUCCESS] 您的執行檔位於 'dist' 資料夾中:
    ECHO [SUCCESS] %cd%\dist\Focus_Flow.exe
    ECHO [SUCCESS] ==================================================
)

:END
ECHO.
ECHO 按下任意鍵結束...
PAUSE > nul
