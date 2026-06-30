@echo off
chcp 65001 >nul
echo 正在整理文件...

:: 创建 txt 和 ques_images 文件夹（不存在则自动创建）
if not exist "txt" mkdir "txt"
if not exist "ques_images" mkdir "ques_images"

:: 移动所有 .txt 文件到 txt 文件夹
move /y "*.txt" "txt\" >nul 2>&1

:: 移动所有 .png 文件到 ques_images 文件夹
move /y "*.png" "ques_images\" >nul 2>&1

echo 整理完成！
pause >nul