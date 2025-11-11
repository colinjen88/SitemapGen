@echo off
echo ============================================
echo 清理 SitemapGen 專案臨時檔案
echo ============================================
echo.

REM 清理 build 和 dist 資料夾
if exist build (
    echo 刪除 build 資料夾...
    rmdir /s /q build
)

if exist dist (
    echo 刪除 dist 資料夾...
    rmdir /s /q dist
)

REM 清理 Python cache
if exist __pycache__ (
    echo 刪除 __pycache__ 資料夾...
    rmdir /s /q __pycache__
)

if exist src\__pycache__ (
    echo 刪除 src\__pycache__ 資料夾...
    rmdir /s /q src\__pycache__
)

REM 清理自動產生的 spec 檔案（保留 sitemap_gui.spec）
if exist SitemapGen.spec (
    echo 刪除 SitemapGen.spec...
    del /q SitemapGen.spec
)

if exist SitemapGen*.spec (
    echo 刪除其他自動產生的 spec 檔案...
    del /q SitemapGen*.spec 2>nul
)

REM 清理進度檔和輸出檔（可選）
echo.
echo 是否要清理進度檔（.pkl）和輸出檔（.xml）？
choice /C YN /M "按 Y 清理，按 N 保留"
if errorlevel 2 goto skip_output
if errorlevel 1 goto clean_output

:clean_output
echo 清理進度檔和輸出檔...
del /q *.pkl 2>nul
del /q *.xml 2>nul
del /q autosave\*.bak 2>nul
goto end

:skip_output
echo 保留進度檔和輸出檔

:end
echo.
echo ============================================
echo 清理完成！
echo ============================================
pause
