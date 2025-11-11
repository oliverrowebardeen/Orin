@echo off
setlocal enabledelayedexpansion

:: Configuration
set MODEL_PATH=models\DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf
set LLAMA_BIN=bin\llama\llama-cli.exe

:: Check for model
if not exist "%MODEL_PATH%" (
    echo Error: Model not found at %MODEL_PATH%
    echo Please ensure the model is in the correct location.
    pause
    exit /b 1
)

:: Check for llama-cli
if not exist "%LLAMA_BIN%" (
    echo Error: llama-cli not found at %LLAMA_BIN%
    echo Please ensure llama.cpp is properly set up.
    pause
    exit /b 1
)

:: Default to interactive mode if no arguments
if "%~1"=="" (
    echo Starting Orin in interactive mode...
    echo (Type your question or /help for commands)
    echo.
    python -m src.main --repl
) else (
    :: Pass all arguments to the Python script
    python -m src.main %*
)

pause