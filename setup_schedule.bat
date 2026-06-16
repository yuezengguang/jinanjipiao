@echo off
chcp 65001 >nul
echo ========================================
echo   济南低价机票 - 设定每日定时爬虫
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ 请以管理员身份运行此脚本！
    echo   右键点击 setup_schedule.bat，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo 正在创建定时任务...
echo.

schtasks /create ^
    /tn "JinanFlightScraper" ^
    /tr "\"D:\python\python.exe\" \"D:\桌面\ai  test\jinanjipiao\scraper.py\"" ^
    /sc daily ^
    /st 08:00 ^
    /f ^
    /ru "%USERNAME%"

if %errorlevel% equ 0 (
    echo.
    echo ✅ 定时任务创建成功！
    echo.
    echo   任务名称: JinanFlightScraper
    echo   执行时间: 每天 08:00
    echo   执行内容: python scraper.py
    echo.
    echo 你可以通过以下方式管理：
    echo   - 任务计划程序 (taskschd.msc)
    echo   - 命令行: schtasks /query /tn JinanFlightScraper
    echo   - 删除:   schtasks /delete /tn JinanFlightScraper /f
) else (
    echo.
    echo ❌ 创建失败
)

pause
