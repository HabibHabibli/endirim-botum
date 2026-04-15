import psycopg2
import os
from datetime import date

# Baza linkini Render-in gizli ayarlarından (Environment) alırıq
DB_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DB_URL)

def bazani_yarat():
    conn = get_conn()
    c = conn.cursor()
    # Telegram ID-ləri çox böyük rəqəm olduğu üçün BIGINT istifadə edirik
    c.execute('''CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY, username TEXT, first_name TEXT, is_vip INTEGER DEFAULT 0, clicks INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS links (id SERIAL PRIMARY KEY, category TEXT, name TEXT, url TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS clicks (click_date TEXT, total_clicks INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist (user_id BIGINT, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS suggestions (user_id BIGINT, text TEXT)''')
    conn.commit()
    conn.close()

def istifadeci_elave_et(user_id, username, first_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=%s", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (id, username, first_name) VALUES (%s, %s, %s)", (user_id, username, first_name))
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
    c.execute("SELECT clicks FROM users WHERE id=%s", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0] >= 5: 
        return True
    return False

# ==========================================
# 🛠 DİNAMİK LİNKLƏR VƏ SİLMƏ/YENİLƏMƏ
# ==========================================
def link_elave_et(category, name, url):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM links WHERE category=%s AND name=%s", (category, name))
    row = c.fetchone()
    if row:
        c.execute("UPDATE links SET url=%s WHERE id=%s", (url, row[0]))
    else:
        c.execute("INSERT INTO links (category, name, url) VALUES (%s, %s, %s)", (category, name, url))
    conn.commit()
    conn.close()

def link_sil(link_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM links WHERE id=%s", (link_id,))
    conn.commit()
    conn.close()

def kateqoriya_linklerini_getir(category):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, url FROM links WHERE category=%s ORDER BY id DESC LIMIT 10", (category,))
    links = c.fetchall()
    conn.close()
    return links

def linki_getir(link_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT url FROM links WHERE id=%s", (link_id,))
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
    c.execute("SELECT total_clicks FROM clicks WHERE click_date=%s", (today,))
    row = c.fetchone()
    if row: c.execute("UPDATE clicks SET total_clicks = total_clicks + 1 WHERE click_date=%s", (today,))
    else: c.execute("INSERT INTO clicks (click_date, total_clicks) VALUES (%s, 1)", (today,))
    
    c.execute("UPDATE users SET clicks = clicks + 1 WHERE id=%s", (user_id,))
    conn.commit()
    conn.close()

def gunun_hesabati():
    today = str(date.today())
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT total_clicks FROM clicks WHERE click_date=%s", (today,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

# ==========================================
# 💡 TƏKLİF VƏ İSTƏK SİYAHISI
# ==========================================
def isteke_elave_et(user_id, category):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM wishlist WHERE user_id=%s AND category=%s", (user_id, category))
    if not c.fetchone(): c.execute("INSERT INTO wishlist (user_id, category) VALUES (%s, %s)", (user_id, category))
    else: c.execute("DELETE FROM wishlist WHERE user_id=%s AND category=%s", (user_id, category))
    conn.commit()
    conn.close()

def isteyi_olanlari_getir(category):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id FROM wishlist WHERE category=%s", (category,))
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def teklif_yaz(user_id, text):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO suggestions (user_id, text) VALUES (%s, %s)", (user_id, text))
    conn.commit()
    conn.close()
