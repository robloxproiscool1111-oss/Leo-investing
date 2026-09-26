@echo off
cd /d "%~dp0"
title Leo Investing Parcel Web App
where node >nul 2>nul
if errorlevel 1 (
	echo Node.js is required to run the Parcel web app.
	echo Install the LTS version from https://nodejs.org/ and restart this window.
	pause
	exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
	echo npm was not found. Reinstall Node.js LTS from https://nodejs.org/ and restart this window.
	pause
	exit /b 1
)
if not exist node_modules\parcel (
	echo Installing Parcel dependencies...
	call npm install
	if errorlevel 1 (
		echo Dependency installation failed.
		pause
		exit /b 1
	)
)
echo Starting Leo Investing with Parcel...
echo Parcel will open the browser when ready.
call npm start
pause
