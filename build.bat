@echo off
setlocal EnableDelayedExpansion

set SCRIPT_NAME=img2pdf.py
set APP_NAME=IMG2PDF Z
set EXEC_NAME=IMG2PDF_Z.exe
set ICON_FILE=icon_img2pdf_z.ico

:: Always work relative to where this .bat file lives
cd /d "%~dp0"

:: %~dp0 always ends with a backslash. Strip it so paths inside quotes work.
set "PROJ=%~dp0"
set "PROJ=%PROJ:~0,-1%"

echo ===========================================
echo  Building IMG2PDF Z for Windows
echo ===========================================

:: -- CHECK PYTHON --------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

:: -- CHECK SCRIPT --------------------------------------------------------------
if not exist "%SCRIPT_NAME%" (
    echo [ERROR] %SCRIPT_NAME% not found in current directory.
    pause
    exit /b 1
)

:: -- INSTALL DEPENDENCIES ------------------------------------------------------
echo [INFO] Checking dependencies...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    python -m pip install pyinstaller
)
python -m pip show pillow >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Pillow...
    python -m pip install pillow
)

:: -- CLEAN OLD BUILDS ----------------------------------------------------------
echo [INFO] Cleaning old builds...
if exist "%PROJ%\build"        rd /s /q "%PROJ%\build"
if exist "%PROJ%\__pycache__"  rd /s /q "%PROJ%\__pycache__"

:: -- GENERATE ICON -------------------------------------------------------------
echo [INFO] Generating icon...
set "ICON_TMP=%TEMP%\img2pdf_z_make_icon_%RANDOM%.py"
if exist "%ICON_TMP%" del /f /q "%ICON_TMP%"

>> "%ICON_TMP%" echo from PIL import Image, ImageDraw, ImageFont
>> "%ICON_TMP%" echo import sys, math
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo YELLOW = (255, 193, 7, 255)
>> "%ICON_TMP%" echo ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo def bez4(p0, p1, p2, p3, steps=600):
>> "%ICON_TMP%" echo     pts = []
>> "%ICON_TMP%" echo     for i in range(steps + 1):
>> "%ICON_TMP%" echo         t = i / steps
>> "%ICON_TMP%" echo         bx = (1-t)**3*p0[0]+3*(1-t)**2*t*p1[0]+3*(1-t)*t**2*p2[0]+t**3*p3[0]
>> "%ICON_TMP%" echo         by = (1-t)**3*p0[1]+3*(1-t)**2*t*p1[1]+3*(1-t)*t**2*p2[1]+t**3*p3[1]
>> "%ICON_TMP%" echo         pts.append((bx, by))
>> "%ICON_TMP%" echo     return pts
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo def normal_at(pts, i):
>> "%ICON_TMP%" echo     n = len(pts)
>> "%ICON_TMP%" echo     if i == 0:
>> "%ICON_TMP%" echo         dx, dy = pts[1][0]-pts[0][0], pts[1][1]-pts[0][1]
>> "%ICON_TMP%" echo     elif i == n - 1:
>> "%ICON_TMP%" echo         dx, dy = pts[-1][0]-pts[-2][0], pts[-1][1]-pts[-2][1]
>> "%ICON_TMP%" echo     else:
>> "%ICON_TMP%" echo         dx, dy = pts[i+1][0]-pts[i-1][0], pts[i+1][1]-pts[i-1][1]
>> "%ICON_TMP%" echo     L = math.hypot(dx, dy) or 1
>> "%ICON_TMP%" echo     return -dy / L, dx / L
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo def thick_stroke(pts, hw):
>> "%ICON_TMP%" echo     left  = [(pts[i][0] + normal_at(pts,i)[0]*hw, pts[i][1] + normal_at(pts,i)[1]*hw) for i in range(len(pts))]
>> "%ICON_TMP%" echo     right = [(pts[i][0] - normal_at(pts,i)[0]*hw, pts[i][1] - normal_at(pts,i)[1]*hw) for i in range(len(pts))]
>> "%ICON_TMP%" echo     return left + list(reversed(right))
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo def best_font(size):
>> "%ICON_TMP%" echo     for c in ["arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/Arial.ttf"]:
>> "%ICON_TMP%" echo         try:
>> "%ICON_TMP%" echo             return ImageFont.truetype(c, size)
>> "%ICON_TMP%" echo         except Exception:
>> "%ICON_TMP%" echo             pass
>> "%ICON_TMP%" echo     return ImageFont.load_default()
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo def draw_icon(size):
>> "%ICON_TMP%" echo     WORK = size * 8
>> "%ICON_TMP%" echo     img = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
>> "%ICON_TMP%" echo     d = ImageDraw.Draw(img)
>> "%ICON_TMP%" echo     s = WORK / 100.0
>> "%ICON_TMP%" echo     Y = YELLOW
>> "%ICON_TMP%" echo     sw = max(4, round(5.5 * s))
>> "%ICON_TMP%" echo     fold = 18 * s
>> "%ICON_TMP%" echo     rx1, ry1, rx2, ry2 = 12*s, 5*s, 88*s, 95*s
>> "%ICON_TMP%" echo     doc_pts = [(rx1,ry1),(rx2-fold,ry1),(rx2,ry1+fold),(rx2,ry2),(rx1,ry2),(rx1,ry1)]
>> "%ICON_TMP%" echo     d.line(doc_pts, fill=Y, width=sw, joint="curve")
>> "%ICON_TMP%" echo     d.line([(rx2-fold,ry1),(rx2-fold,ry1+fold),(rx2,ry1+fold)], fill=Y, width=sw, joint="curve")
>> "%ICON_TMP%" echo     r2 = sw // 2
>> "%ICON_TMP%" echo     for px, py in [(rx1,ry1),(rx2-fold,ry1),(rx2,ry1+fold),(rx2,ry2),(rx1,ry2)]:
>> "%ICON_TMP%" echo         d.ellipse([px-r2, py-r2, px+r2, py+r2], fill=Y)
>> "%ICON_TMP%" echo     isw = max(3, round(4 * s))
>> "%ICON_TMP%" echo     ix1, iy1, ix2, iy2 = 20*s, 12*s, 65*s, 44*s
>> "%ICON_TMP%" echo     d.line([(ix1,iy1),(ix2,iy1),(ix2,iy2),(ix1,iy2),(ix1,iy1)], fill=Y, width=isw, joint="curve")
>> "%ICON_TMP%" echo     ir2 = isw // 2
>> "%ICON_TMP%" echo     for px, py in [(ix1,iy1),(ix2,iy1),(ix2,iy2),(ix1,iy2)]:
>> "%ICON_TMP%" echo         d.ellipse([px-ir2, py-ir2, px+ir2, py+ir2], fill=Y)
>> "%ICON_TMP%" echo     hw = 3.8 * s
>> "%ICON_TMP%" echo     tail = [(x*s/10.0, 57*s) for x in range(740, 439, -1)]
>> "%ICON_TMP%" echo     curve = bez4((44*s,57*s),(44*s,81*s),(23*s,81*s),(23*s,83*s), steps=600)
>> "%ICON_TMP%" echo     full_path = tail + curve[1:]
>> "%ICON_TMP%" echo     d.polygon(thick_stroke(full_path, hw), fill=Y)
>> "%ICON_TMP%" echo     for cx2, cy2 in [(74*s, 57*s), curve[-1]]:
>> "%ICON_TMP%" echo         d.ellipse([cx2-hw, cy2-hw, cx2+hw, cy2+hw], fill=Y)
>> "%ICON_TMP%" echo     tip_x, tip_y = 23*s, 87*s
>> "%ICON_TMP%" echo     aw2, ah2 = 11*s, 10*s
>> "%ICON_TMP%" echo     d.polygon([(tip_x, tip_y),(tip_x-aw2, tip_y-ah2),(tip_x+aw2, tip_y-ah2)], fill=Y)
>> "%ICON_TMP%" echo     fsz = max(12, int(16 * s))
>> "%ICON_TMP%" echo     font = best_font(fsz)
>> "%ICON_TMP%" echo     cx2 = 70 * s
>> "%ICON_TMP%" echo     bb = d.textbbox((0, 0), "PDF", font=font)
>> "%ICON_TMP%" echo     tw, th = bb[2]-bb[0], bb[3]-bb[1]
>> "%ICON_TMP%" echo     d.text((cx2 - tw/2, ry2 - 11*s - th), "PDF", fill=Y, font=font)
>> "%ICON_TMP%" echo     return img.resize((size, size), Image.LANCZOS)
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo def build_ico(out):
>> "%ICON_TMP%" echo     frames = [draw_icon(sz) for sz in ICO_SIZES]
>> "%ICON_TMP%" echo     frames[-1].save(out, format="ICO", sizes=[(f.width, f.height) for f in frames])
>> "%ICON_TMP%" echo     print("[OK] Icon saved: " + out)
>> "%ICON_TMP%" echo.
>> "%ICON_TMP%" echo build_ico(sys.argv[1])

python "%ICON_TMP%" "%PROJ%\%ICON_FILE%"
del "%ICON_TMP%" >nul 2>&1
if not exist "%PROJ%\%ICON_FILE%" (
    echo [WARN] Icon generation failed, building without icon.
)

:: -- BUILD EXECUTABLE ----------------------------------------------------------
echo [INFO] Building executable...
if exist "%PROJ%\%ICON_FILE%" (
    python -m PyInstaller --onefile --windowed --name "IMG2PDF_Z" --icon "%PROJ%\%ICON_FILE%" --distpath "%PROJ%" --workpath "%PROJ%\build" --specpath "%PROJ%" "%SCRIPT_NAME%"
) else (
    python -m PyInstaller --onefile --windowed --name "IMG2PDF_Z" --distpath "%PROJ%" --workpath "%PROJ%\build" --specpath "%PROJ%" "%SCRIPT_NAME%"
)
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

:: -- CREATE SHORTCUTS ----------------------------------------------------------
echo [INFO] Creating Desktop shortcut...
set "DESKTOP_LNK=%USERPROFILE%\Desktop\%APP_NAME%.lnk"
call :MakeShortcut "%DESKTOP_LNK%" "%PROJ%\%EXEC_NAME%" "%PROJ%"

echo [INFO] Creating Start Menu shortcut...
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%STARTMENU_DIR%" mkdir "%STARTMENU_DIR%"
set "STARTMENU_LNK=%STARTMENU_DIR%\%APP_NAME%.lnk"
call :MakeShortcut "%STARTMENU_LNK%" "%PROJ%\%EXEC_NAME%" "%PROJ%"

:: -- CLEAN UP ------------------------------------------------------------------
echo [INFO] Cleaning up...
del /f /q "%PROJ%\%ICON_FILE%" >nul 2>&1
if exist "%PROJ%\build"          rd /s /q "%PROJ%\build"
if exist "%PROJ%\IMG2PDF_Z.spec" del /f /q "%PROJ%\IMG2PDF_Z.spec"

echo.
echo [OK] Done!
echo    Executable:   %PROJ%\%EXEC_NAME%
echo    Desktop:      %DESKTOP_LNK%
echo    Start Menu:   %STARTMENU_LNK%
pause
exit /b 0

:MakeShortcut
:: %1 = shortcut path   %2 = target exe   %3 = working dir
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell;" ^
    "$sc = $ws.CreateShortcut(\"%~1\");" ^
    "$sc.TargetPath = \"%~2\";" ^
    "$sc.WorkingDirectory = \"%~3\".TrimEnd('\');" ^
    "$sc.IconLocation = \"%~2\";" ^
    "$sc.Description = 'IMG2PDF Z - Image to PDF converter';" ^
    "$sc.Save()" >nul 2>&1
exit /b 0
