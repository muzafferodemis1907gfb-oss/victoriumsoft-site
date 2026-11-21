@echo off
chcp 65001 >NUL
cd /d "%~dp0"
echo VictoriumSoft SEO v17 + Yeni Yayindaki Uygulamalar
where py >NUL 2>NUL
if %errorlevel%==0 (
  py -3 build_seo_v17.py
) else (
  python build_seo_v17.py
)
echo.
if %errorlevel% neq 0 echo Islem basarisiz oldu. Python 3 veya internet baglantinizi kontrol edin.
echo Olusan ZIP: victoriumsoft-v17-output\victoriumsoft-v17-SEO-PATCH.zip
pause
