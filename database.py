import sqlite3

def bazani_yarat():
    conn = sqlite3.connect('endirim_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT
        )
    ''')
    conn.commit()
    conn.close()

def istifadeci_elave_et(user_id, username):
    conn = sqlite3.connect('endirim_bot.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
    except sqlite3.IntegrityError:
        pass 
    conn.close()

# YENİ ƏLAVƏ EDİLƏN FUNKSİYA
def butun_istifadecileri_getir():
    conn = sqlite3.connect('endirim_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    return [user[0] for user in users] # ID-ləri siyahı kimi qaytarır

if __name__ == '__main__':
    bazani_yarat()
    print("Baza hazırdır!")