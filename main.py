import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web
import database 

logging.basicConfig(level=logging.INFO)

# 👇 BURAYA ÖZ TOKENİNİ VƏ ADMİN ID-LƏRİNİ YAZ
TOKEN = "8740821772:AAHn1gMm_hdn-UDYD41LtcCwYZjW1blMPmc"
ADMIN_IDS = [8645642283, 2111781743]  

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- FSM STATES (Vəziyyətlər) ---
class AdminState(StatesGroup):
    link_kateqoriya = State()
    link_ad = State()
    link_url = State()
    reply_target_uid = State() # Şəxsi cavab üçün
    reply_msg = State()

class BroadcastState(StatesGroup):
    mesaj_metni = State()

class SuggestionState(StatesGroup):
    mesaj = State()

# --- MENYULAR ---
def ana_menyu():
    duymeler = [
        [KeyboardButton(text="🔥 Günün Endirimləri"), KeyboardButton(text="🎟 Aktiv Kodlar")],
        [KeyboardButton(text="🕵️ Gizli Kampaniyalar"), KeyboardButton(text="⚡ Flash Endirimlər")],
        [KeyboardButton(text="🛍 Məhsul Kateqoriyası")],
        [KeyboardButton(text="💡 İstək və Təklif Qutusu")]
    ]
    return ReplyKeyboardMarkup(keyboard=duymeler, resize_keyboard=True)

# ==========================================
# 🌳 ALT KATEQORİYA (NAVİQASİYA) SİSTEMİ
# ==========================================
def nav_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👗 Paltar", callback_data="nav_paltar"), InlineKeyboardButton(text="👕 Köynək", callback_data="nav_koynek")],
        [InlineKeyboardButton(text="👖 Şalvar", callback_data="nav_salvar"), InlineKeyboardButton(text="👟 Ayaqqabı", callback_data="nav_ay")],
        [InlineKeyboardButton(text="👶 Uşaq Geyimləri", callback_data="nav_usaq"), InlineKeyboardButton(text="🕶 Aksesuar", callback_data="nav_aks")]
    ])

def nav_gender_kb(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Qadın", callback_data=f"ucat_{prefix}_qadin"), InlineKeyboardButton(text="👨 Kişi", callback_data=f"ucat_{prefix}_kisi")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="nav_main")]
    ])

def nav_ay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Qadın Ayaqqabı", callback_data="nav_ay_qadin"), InlineKeyboardButton(text="👨 Kişi Ayaqqabı", callback_data="nav_ay_kisi")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="nav_main")]
    ])

def nav_ay_type_kb(gender):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👞 Klassik", callback_data=f"ucat_ay_{gender}_klassik"), InlineKeyboardButton(text="👟 Gündəlik", callback_data=f"ucat_ay_{gender}_gundelik")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="nav_ay")]
    ])

def nav_usaq_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👕 Geyim", callback_data="ucat_usaq_geyim"), InlineKeyboardButton(text="👟 Ayaqqabı", callback_data="ucat_usaq_ayaqqabi")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="nav_main")]
    ])

# Adminin ilkin seçimi (Ana kateqoriyalar + Məhsul menyusu)
def admin_top_cat_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Günün Endirimləri", callback_data="ucat_gunun"), InlineKeyboardButton(text="🎟 Aktiv Kodlar", callback_data="ucat_kod")],
        [InlineKeyboardButton(text="🕵️ Gizli Kampaniyalar", callback_data="ucat_gizli"), InlineKeyboardButton(text="⚡ Flash Endirimlər", callback_data="ucat_flash")],
        [InlineKeyboardButton(text="🛍 Məhsul Kateqoriyası (Alt menyu)", callback_data="nav_main")]
    ])

# --- NAVİQASİYA (KATEQORİYA) İDARƏEDİCİSİ ---
@dp.callback_query(F.data.startswith("nav_"))
async def handle_nav(c: types.CallbackQuery):
    nav = c.data
    if nav == "nav_main": kb = nav_main_kb()
    elif nav == "nav_paltar": kb = nav_gender_kb("paltar")
    elif nav == "nav_koynek": kb = nav_gender_kb("koynek")
    elif nav == "nav_salvar": kb = nav_gender_kb("salvar")
    elif nav == "nav_aks": kb = nav_gender_kb("aksesuar")
    elif nav == "nav_ay": kb = nav_ay_kb()
    elif nav == "nav_ay_qadin": kb = nav_ay_type_kb("qadin")
    elif nav == "nav_ay_kisi": kb = nav_ay_type_kb("kisi")
    elif nav == "nav_usaq": kb = nav_usaq_kb()
    else: return
    
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer()

# --- LİNKLƏRİ GÖSTƏRMƏ FUNKSİYASI ---
async def linkleri_goster(message: types.Message, kateqoriya, bashliq):
    linkler = database.kateqoriya_linklerini_getir(kateqoriya)
    if not linkler:
        return await message.answer(f"Hazırda bu bölmədə yeni link/kod yoxdur. Tezliklə əlavə olunacaq! ⏳")
    
    # VIP yoxlaması
    if kateqoriya == "gizli" and not database.vip_yoxla(message.from_user.id):
        return await message.answer("🔒 Bu bölmə yalnız 'Sadiq İzləyici'lər (VIP) üçündür!\nVIP olmaq üçün botdakı linklərə mütəmadi daxil olun.")

    mesaj = f"*{bashliq}*\nAşağıdakı düymələrə basaraq məhsula baxa bilərsiniz:\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for link_id, name, _ in linkler:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=name, callback_data=f"getlink_{link_id}")])
    
    await message.answer(mesaj, reply_markup=keyboard, parse_mode="Markdown")

# --- SON KATEQORİYA SEÇİMİ (İstifadəçi və Admin eyni yerdən keçir) ---
@dp.callback_query(F.data.startswith("ucat_"))
async def handle_ucat(c: types.CallbackQuery, state: FSMContext):
    cat = c.data.replace("ucat_", "")
    current_state = await state.get_state()

    # Əgər klikləyən admin-dirsə və link əlavə edirsə:
    if current_state == AdminState.link_kateqoriya.state:
        await state.update_data(kat=cat)
        await c.message.answer(f"✅ Kateqoriya seçildi: **{cat}**\n\nMəhsulun (və ya kodun) adını yazın:", parse_mode="Markdown")
        await state.set_state(AdminState.link_ad)
    
    # Əgər sadə istifadəçidirsə, həmin kateqoriyanın məhsullarını göstər:
    else:
        await linkleri_goster(c.message, cat, f"🛍 Seçilmiş Bölmə: {cat}")
    await c.answer()

@dp.callback_query(F.data.startswith("getlink_"))
async def linki_ver_ve_say(callback: types.CallbackQuery):
    link_id = int(callback.data.split("_")[1])
    url = database.linki_getir(link_id)
    if url:
        database.klik_artir(callback.from_user.id)
        await callback.message.answer(f"🔗 Sizin linkiniz (və ya kodunuz):\n\n{url}")
        await callback.answer("Göndərildi!", show_alert=False)
    else:
        await callback.answer("Məlumat tapılmadı.", show_alert=True)

# --- ƏSAS KOMANDALAR ---
@dp.message(CommandStart())
async def start_komandasi(message: types.Message):
    database.istifadeci_elave_et(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(f"Salam, {message.from_user.first_name}! 🛍\n\nTrendyolun ən yaxşı endirimləri burada. Aşağıdakı menyudan istədiyini seç!", reply_markup=ana_menyu())

@dp.message(F.text == "🔥 Günün Endirimləri")
async def m_gun(m: types.Message): await linkleri_goster(m, "gunun", "🔥 Günün Endirimləri")

@dp.message(F.text == "🎟 Aktiv Kodlar")
async def m_kod(m: types.Message): await linkleri_goster(m, "kod", "🎟 Aktiv Kodlar")

@dp.message(F.text == "🕵️ Gizli Kampaniyalar")
async def m_gizli(m: types.Message): await linkleri_goster(m, "gizli", "🕵️ Gizli Kampaniyalar")

@dp.message(F.text == "⚡ Flash Endirimlər")
async def m_flash(m: types.Message): await linkleri_goster(m, "flash", "⚡ Flash Endirimlər")

@dp.message(F.text == "🛍 Məhsul Kateqoriyası")
async def m_cat(m: types.Message): await m.answer("Bölməni seçin:", reply_markup=nav_main_kb())

# ==========================================
# 💡 İSTƏK / TƏKLİF VƏ ŞƏXSİ CAVAB SİSTEMİ
# ==========================================
@dp.message(F.text == "💡 İstək və Təklif Qutusu")
async def req_start(message: types.Message, state: FSMContext):
    await message.answer("Hansı məhsulları axtarırsınız? Adminlərə istəyinizi yazın:")
    await state.set_state(SuggestionState.mesaj)

@dp.message(SuggestionState.mesaj)
async def req_save(message: types.Message, state: FSMContext):
    database.teklif_yaz(message.from_user.id, message.text)
    await message.answer("İstəyiniz qəbul edildi! Adminlər sizə xüsusi link tapıb göndərəcək. 🎁")
    
    # Bütün Adminlərə bildiriş və "Cavab Ver" düyməsi gedir
    for admin_id in ADMIN_IDS:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Cavab Ver (Link At)", callback_data=f"reply_{message.from_user.id}")]
        ])
        try:
            await bot.send_message(admin_id, f"💡 **Yeni İstək!**\nKim: @{message.from_user.username}\nMesaj: {message.text}", reply_markup=kb)
        except: pass
    await state.clear()

@dp.callback_query(F.data.startswith("reply_"))
async def admin_reply_start(c: types.CallbackQuery, state: FSMContext):
    if c.from_user.id not in ADMIN_IDS: return
    target_uid = int(c.data.split("_")[1])
    await state.update_data(target_uid=target_uid)
    await c.message.answer("Bu istifadəçiyə göndəriləcək xüsusi linki və məlumatı yazın:")
    await state.set_state(AdminState.reply_msg)
    await c.answer()

@dp.message(AdminState.reply_msg)
async def admin_reply_send(m: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data['target_uid']
    
    # 1. İstifadəçiyə şəxsi olaraq göndəririk
    try:
        await bot.send_message(target, f"🎁 **Admin sizin istəyinizə uyğun məhsul tapdı!**\n\n{m.text}")
        await m.answer("✅ Link uğurla və yalnız həmin istifadəçiyə göndərildi.")
    except:
        await m.answer("❌ İstifadəçiyə mesaj çatmadı (bəlkə botu bloklayıb).")

    # 2. Digər adminləri məlumatlandırırıq
    for admin in ADMIN_IDS:
        if admin != m.from_user.id:
            try: await bot.send_message(admin, f"ℹ️ Admin @{m.from_user.username} istifadəçinin istəyinə cavab verdi:\n{m.text}")
            except: pass
    await state.clear()

# ==========================================
# 👑 ADMIN PANELİ VƏ TOPLU MESAJ (BROADCAST)
# ==========================================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Kateqoriyaya Link")],
        [KeyboardButton(text="📢 Hamıya Mesaj (Kateqoriyasız)")],
        [KeyboardButton(text="📊 Statistika")]
    ], resize_keyboard=True)
    await message.answer("👑 Admin Paneli. Nə etmək istəyirsiniz?", reply_markup=kb)

# Hamıya Mesaj (Broadcast)
@dp.message(F.text == "📢 Hamıya Mesaj (Kateqoriyasız)")
async def broadcast_start(m: types.Message, state: FSMContext):
    if m.from_user.id not in ADMIN_IDS: return
    await m.answer("Bütün bot istifadəçilərinə gedəcək məlumatı və linki bir yerdə yazın:")
    await state.set_state(BroadcastState.mesaj_metni)

@dp.message(BroadcastState.mesaj_metni)
async def broadcast_send(m: types.Message, state: FSMContext):
    users = database.butun_istifadecileri_getir()
    count = 0
    await m.answer("🚀 Mesaj göndərilir...")
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **YENİ KAMPANİYA!**\n\n{m.text}")
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await m.answer(f"✅ Kateqoriyasız linkiniz {count} nəfərə uğurla çatdırıldı.")
    await state.clear()

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    clicks = database.gunun_hesabati()
    await message.answer(f"📊 **Gündəlik Hesabat**\nBu gün botdakı linklərə ümumi **{clicks}** klik edilib.")

# Kateqoriyaya Səssiz Link Əlavə Etmək
@dp.message(F.text == "➕ Kateqoriyaya Link")
async def adm_l_1(m: types.Message, state: FSMContext):
    if m.from_user.id not in ADMIN_IDS: return
    await m.answer("Hansı kateqoriyaya link əlavə edirsiniz?", reply_markup=admin_top_cat_kb())
    await state.set_state(AdminState.link_kateqoriya)

@dp.message(AdminState.link_ad)
async def adm_l_3(m: types.Message, state: FSMContext):
    await state.update_data(ad=m.text)
    await m.answer("Trendyol Linkini (və ya kodu) göndərin:")
    await state.set_state(AdminState.link_url)

@dp.message(AdminState.link_url)
async def adm_l_final(m: types.Message, state: FSMContext):
    data = await state.get_data()
    database.link_elave_et(data['kat'], data['ad'], m.text)
    
    # SƏSSİZ ƏLAVƏ (Heç kimə bildiriş getmir)
    await m.answer(f"✅ Link verilmiş kateqoriyaya uğurla əlavə edildi.\n(İstifadəçilərə heç bir bildiriş getmədi).")
    
    # Yalnız adminlərə hesabat gedir
    for admin in ADMIN_IDS:
        if admin != m.from_user.id:
            try: await bot.send_message(admin, f"ℹ️ Digər admin '{data['kat']}' bölməsinə yeni link əlavə etdi: {data['ad']}")
            except: pass
    await state.clear()

# --- RENDER ÜÇÜN VEB-SERVER ---
async def ping(request):
    return web.Response(text="Trendyol Bot is alive!")

async def main():
    database.bazani_yarat()
    print("Trendyol Affiliate Bot işə düşdü...")
    
    # XƏTANI (CONFLICT) KÖKÜNDƏN HƏLL EDƏN SƏTİR
    await bot.delete_webhook(drop_pending_updates=True) 
    await asyncio.sleep(1)
    
    asyncio.create_task(dp.start_polling(bot))
    
    app = web.Application()
    app.add_routes([web.get('/', ping)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
