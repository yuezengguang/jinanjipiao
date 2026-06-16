@echo off
chcp 65001 >nul
echo ========================================
echo   济南低价机票 - 数据更新
echo ========================================
echo.

cd /d "D:\桌面\ai  test\jinanjipiao"

echo [%date% %time%] 开始抓取数据...
python scraper.py

if %errorlevel% equ 0 (
    echo.
    echo [%date% %time%] ✅ 抓取成功
) else (
    echo.
    echo [%date% %time%] ❌ 抓取失败 (错误码: %errorlevel%)
)

echo.
echo 按任意键退出...
pause >nul
