import os
from datetime import date
from pymongo import MongoClient, ReturnDocument

# Render-dən gizli MongoDB linkini alırıq
DB_URL = os.environ.get("DATABASE_URL")

# MongoDB-yə qoşuluruq və "trendyol_bot" adlı baza yaradırıq
client = MongoClient(DB_URL)
db = client["trendyol_bot"]

def bazani_yarat():
    # MongoDB cədvəlləri avtomatik yaradır deyə SQL kimi CREATE TABLE etməyə ehtiyac yoxdur.
    pass

def istifadeci_elave_et(user_id, username, first_name):
    db.users.update_one(
        {'_id': user_id},
        {'$setOnInsert': {'username': username, 'first_name': first_name, 'is_vip': 0, 'clicks': 0}},
        upsert=True
    )

def butun_istifadecileri_getir():
    return [user['_id'] for user in db.users.find({}, {'_id': 1})]

def vip_yoxla(user_id):
    user = db.users.find_one({'_id': user_id})
    if user and user.get('clicks', 0) >= 5:
        return True
    return False

# ==========================================
# 🛠 DİNAMİK LİNKLƏR VƏ SİLMƏ/YENİLƏMƏ
# ==========================================
def link_elave_et(category, name, url):
    # Bu kateqoriyada bu adda məhsul var?
    movcud = db.links.find_one({'category': category, 'name': name})
    if movcud:
        # Varsa, köhnə linki yenilə
        db.links.update_one({'_id': movcud['_id']}, {'$set': {'url': url}})
    else:
        # Yoxdursa, xüsusi rəqəmsal ID yaradıb əlavə et
        counter = db.counters.find_one_and_update(
            {'_id': 'link_id'},
            {'$inc': {'seq': 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        yeni_id = counter['seq']
        db.links.insert_one({'_id': yeni_id, 'category': category, 'name': name, 'url': url})

def link_sil(link_id):
    db.links.delete_one({'_id': link_id})

def kateqoriya_linklerini_getir(category):
    linkler = db.links.find({'category': category}).sort('_id', -1).limit(10)
    # main.py faylını dəyişməmək üçün MongoDB məlumatını Tuple formatına çeviririk
    return [(l['_id'], l['name'], l['url']) for l in linkler]

def linki_getir(link_id):
    link = db.links.find_one({'_id': link_id})
    return link['url'] if link else None

# ==========================================
# 📊 KLİK TRACKER VƏ HESABAT
# ==========================================
def klik_artir(user_id):
    today = str(date.today())
    # Günün ümumi hesabatını artır
    db.clicks.update_one({'_id': today}, {'$inc': {'total_clicks': 1}}, upsert=True)
    # İstifadəçinin şəxsi klikini artır
    db.users.update_one({'_id': user_id}, {'$inc': {'clicks': 1}})

def gunun_hesabati():
    today = str(date.today())
    doc = db.clicks.find_one({'_id': today})
    return doc['total_clicks'] if doc else 0

# ==========================================
# 💡 TƏKLİF VƏ İSTƏK SİYAHISI
# ==========================================
def isteke_elave_et(user_id, category):
    movcud = db.wishlist.find_one({'user_id': user_id, 'category': category})
    if movcud:
        db.wishlist.delete_one({'_id': movcud['_id']})
    else:
        db.wishlist.insert_one({'user_id': user_id, 'category': category})

def isteyi_olanlari_getir(category):
    return [doc['user_id'] for doc in db.wishlist.find({'category': category})]

def teklif_yaz(user_id, text):
    db.suggestions.insert_one({'user_id': user_id, 'text': text})
