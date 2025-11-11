@echo off
echo 開始建立 SitemapGen 執行檔...
echo.

REM 清理舊檔案
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist SitemapGen.spec del /q SitemapGen.spec

echo 正在使用 PyInstaller 建立執行檔...
pyinstaller --onefile --noconsole --name SitemapGen sitemap_gui.py

echo.
if exist dist\SitemapGen.exe (
    echo ============================================
    echo 執行檔建立成功！
    echo 位置: dist\SitemapGen.exe
    echo ============================================
    dir dist\SitemapGen.exe
) else (
    echo ============================================
    echo 執行檔建立失敗，請檢查錯誤訊息
    echo ============================================
)

pause
