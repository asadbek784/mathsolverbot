MathSolver Pro - Render.com Deploy
====================================

FAYLLAR:
  main.py                    - server + bot
  MathSolver_Complete.html   - ilova
  requirements.txt           - kutubxonalar
  render.yaml                - Render konfiguratsiya

====================================
RENDER.COM GA DEPLOY:
====================================

1. GITHUB REPO YARATING
   - github.com ga kiring (bepul ro'yxat)
   - "New repository" → mathsolver-pro → Create
   - "uploading an existing file" bosing
   - Bu 4 ta faylni drag & drop qiling
   - "Commit changes" bosing

2. main.py NI TAHRIRLANG
   - main.py faylini GitHub da oching
   - Qalam (✏️) tugmasi
   - BOT_TOKEN = "..." → tokeningizni yozing
   - "Commit changes"

3. RENDER GA ULANG
   - dashboard.render.com ga kiring
   - "New +" → "Web Service"
   - "Connect a repository" → mathsolver-pro
   - Sozlamalar:
       Name:         mathsolver-pro
       Runtime:      Python
       Build:        pip install -r requirements.txt
       Start:        gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
   - "Create Web Service" bosing

4. MANZILNI OLING
   - Deploy tugagach (2-3 daqiqa):
   - https://mathsolver-pro.onrender.com
   - Bu manzilni telefondan oching!

====================================
MUHIM:
====================================

- Admin paroli: asadbek
- Admin TG ID: 7861699284 (allaqachon yozilgan)
- BOT_TOKEN ni GitHub da yozing!

- Render bepul rejasi: 750 soat/oy
  (bir xizmat uchun yetarli)
- 15 daqiqa faolsiz bo'lsa "uyquga" ketadi
  (birinchi kirish sekin bo'ladi)

- Doimiy ishlash uchun UptimeRobot.com da
  bepul monitor qo'ying:
  https://mathsolver-pro.onrender.com/ping
====================================
