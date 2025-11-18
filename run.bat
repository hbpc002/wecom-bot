@echo off
chcp 65001 >nul
echo ====================================
echo 企微听录音统计报表系统
echo ====================================
echo.
echo 选择运行模式:
echo 1. 立即执行一次（推荐用于测试）
echo 2. 定时运行模式（每天9点自动执行）
echo 3. 退出
echo.
set /p choice=请输入选择 (1-3): 

if "%choice%"=="1" (
    echo.
    echo 正在立即执行...
    python main.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo 启动定时任务模式...
    echo 按 Ctrl+C 停止程序
    python main.py --schedule
) else if "%choice%"=="3" (
    exit
) else (
    echo 无效选择，请重新运行
    pause
)