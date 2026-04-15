import sqlite3
from datetime import date

def get_conn():
    return sqlite3.connect("bot_baza.db")

def bazani_yarat():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, is_vip INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, name TEXT, url TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS clicks (click_date TEXT, total_clicks INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist (user_id INTEGER, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS suggestions (user_id INTEGER, text TEXT)''')
    conn.commit()
    conn.close()

def istifadeci_elave_et(user_id, username, first_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)", (user_id, username, first_name))
        conn.commit()
    conn.close()

def butun_istifadecileri_getir():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def vip_yoxla(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT clicks FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0] >= 5: 
        return True
    return False

# ==========================================
# 🛠 YENİ: DİNAMİK LİNKLƏR VƏ SİLMƏ/YENİLƏMƏ
# ==========================================
def link_elave_et(category, name, url):
    conn = get_conn()
    c = conn.cursor()
    # Əvvəlcə yoxlayırıq: bu kateqoriyada bu adda məhsul varmı?
    c.execute("SELECT id FROM links WHERE category=? AND name=?", (category, name))
    row = c.fetchone()
    if row:
        # Varsa, köhnə linki yenisi ilə əvəz edir (Dublikat yaratmır)
        c.execute("UPDATE links SET url=? WHERE id=?", (url, row[0]))
    else:
        # Yoxdursa, yeni link kimi əlavə edir
        c.execute("INSERT INTO links (category, name, url) VALUES (?, ?, ?)", (category, name, url))
    conn.commit()
    conn.close()

# YENİ FUNKSİYA: Seçilmiş linki bazadan tamamilə silmək üçün
def link_sil(link_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM links WHERE id=?", (link_id,))
    conn.commit()
    conn.close()

def kateqoriya_linklerini_getir(category):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, url FROM links WHERE category=? ORDER BY id DESC LIMIT 10", (category,))
    links = c.fetchall()
    conn.close()
    return links

def linki_getir(link_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT url FROM links WHERE id=?", (link_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ==========================================
# 📊 KLİK TRACKER VƏ HESABAT
# ==========================================
def klik_artir(user_id):
    today = str(date.today())
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT total_clicks FROM clicks WHERE click_date=?", (today,))
    row = c.fetchone()
    if row: c.execute("UPDATE clicks SET total_clicks = total_clicks + 1 WHERE click_date=?", (today,))
    else: c.execute("INSERT INTO clicks (click_date, total_clicks) VALUES (?, 1)", (today,))
    c.execute("UPDATE users SET clicks = clicks + 1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def gunun_hesabati():
    today = str(date.today())
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT total_clicks FROM clicks WHERE click_date=?", (today,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

# ==========================================
# 💡 TƏKLİF VƏ İSTƏK SİYAHISI
# ==========================================
def isteke_elave_et(user_id, category):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM wishlist WHERE user_id=? AND category=?", (user_id, category))
    if not c.fetchone(): c.execute("INSERT INTO wishlist (user_id, category) VALUES (?, ?)", (user_id, category))
    else: c.execute("DELETE FROM wishlist WHERE user_id=? AND category=?", (user_id, category))
    conn.commit()
    conn.close()

def isteyi_olanlari_getir(category):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id FROM wishlist WHERE category=?", (category,))
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def teklif_yaz(user_id, text):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO suggestions (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    conn.close()
