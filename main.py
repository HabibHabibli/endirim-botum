import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web
import database 

logging.basicConfig(level=logging.INFO)

# 👇 BURAYA ÖZ TOKENİNİ VƏ ADMİN ID-LƏRİNİ YAZ
TOKEN = "8740821772:AAFoNLga7GqOTcqb5s7lBfIrBpUqcU2A2LI"
ADMIN_IDS = [8645642283, 2111781743, 1365999883]  

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- FSM STATES (Vəziyyətlər) ---
class AdminState(StatesGroup):
    link_kateqoriya = State()
    link_ad = State()
    link_url = State()
    reply_target_uid = State()
    reply_msg = State()

class DeleteState(StatesGroup):
    kat_sec = State()

class BroadcastState(StatesGroup):
    mesaj_metni = State()

class SuggestionState(StatesGroup):
    mesaj = State()

class BodySizeState(StatesGroup):
    boy = State()
    ceki = State()

# --- MENYULAR ---
def ana_menyu():
    duymeler = [
        [KeyboardButton(text="🔥 Günün Endirimləri"), KeyboardButton(text="🎟 Aktiv Kodlar")],
        [KeyboardButton(text="🕵️ Gizli Kampaniyalar"), KeyboardButton(text="⚡ Flash Endirimlər")],
        [KeyboardButton(text="🛍 Məhsul Kateqoriyası"), KeyboardButton(text="📏 Bədən Ölçüsü")],
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
        [InlineKeyboardButton(text="👶 Uşaq Geyimləri", callback_data="nav_usaq"), InlineKeyboardButton(text="🕶 Aksesuar", callback_data="nav_aks")],
        [InlineKeyboardButton(text="💄 Baxım Məhsulları", callback_data="nav_baxim")]
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

def admin_top_cat_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Günün Endirimləri", callback_data="ucat_gunun"), InlineKeyboardButton(text="🎟 Aktiv Kodlar", callback_data="ucat_kod")],
        [InlineKeyboardButton(text="🕵️ Gizli Kampaniyalar", callback_data="ucat_gizli"), InlineKeyboardButton(text="⚡ Flash Endirimlər", callback_data="ucat_flash")],
        [InlineKeyboardButton(text="🛍 Məhsul Kateqoriyası (Alt menyu)", callback_data="nav_main")]
    ])

# --- NAVİQASİYA ---
@dp.callback_query(F.data.startswith("nav_"))
async def handle_nav(c: types.CallbackQuery, state: FSMContext):
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
    elif nav == "nav_baxim": kb = nav_gender_kb("baxim")
    else: return
    
    await c.message.edit_reply_markup(reply_markup=kb)
    await c.answer()

# --- LİNKLƏRİ GÖSTƏRMƏ ---
async def linkleri_goster(message: types.Message, kateqoriya, bashliq):
    linkler = database.kateqoriya_linklerini_getir(kateqoriya)
    if not linkler:
        return await message.answer(f"Hazırda bu bölmədə yeni link/kod yoxdur. Tezliklə əlavə olunacaq! ⏳")
    
    if kateqoriya == "gizli" and not database.vip_yoxla(message.from_user.id):
        return await message.answer("🔒 Bu bölmə yalnız 'Sadiq İzləyici'lər (VIP) üçündür!\nVIP olmaq üçün botdakı linklərə mütəmadi daxil olun.")

    mesaj = f"*{bashliq}*\nAşağıdakı düymələrə basaraq məhsula baxa bilərsiniz:\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for link_id, name, _ in linkler:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=name, callback_data=f"getlink_{link_id}")])
    
    await message.answer(mesaj, reply_markup=keyboard, parse_mode="Markdown")

# --- KATEQORİYA KLİKLƏRİ (Əlavə, Silmə və Baxış üçün) ---
@dp.callback_query(F.data.startswith("ucat_"))
async def handle_ucat(c: types.CallbackQuery, state: FSMContext):
    cat = c.data.replace("ucat_", "")
    cat_adi = cat.replace("_", " ").title()
    current_state = await state.get_state()

    # 1. ADMIN LİNK ƏLAVƏ EDİRSƏ
    if current_state == AdminState.link_kateqoriya.state:
        await state.update_data(kat=cat)
        await c.message.answer(f"✅ Kateqoriya seçildi: {cat_adi}\n\nMəhsulun (və ya kodun) adını yazın:")
        await state.set_state(AdminState.link_ad)
    
    # 2. ADMIN LİNKƏ BAXIRSA VƏ YA SİLİRSƏ
    elif current_state == DeleteState.kat_sec.state:
        linkler = database.kateqoriya_linklerini_getir(cat)
        if not linkler:
            await c.message.answer(f"'{cat_adi}' kateqoriyasında heç bir link yoxdur.")
        else:
            mesaj = f"📋 **{cat_adi}** bölməsindəki aktiv linklər:\n\n"
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            for l_id, name, url in linkler:
                mesaj += f"🔸 **{name}**\n🔗 {url}\n\n"
                kb.inline_keyboard.append([InlineKeyboardButton(text=f"❌ {name} (Sil)", callback_data=f"dellink_{l_id}")])
            await c.message.answer(mesaj + "Silmək istədiyiniz məhsulun düyməsinə basın:", reply_markup=kb, disable_web_page_preview=True, parse_mode="Markdown")
        await state.clear()

    # 3. İSTİFADƏÇİ BAXIRSA
    else:
        await linkleri_goster(c.message, cat, f"🛍 Seçilmiş Bölmə: {cat_adi}")
    await c.answer()

# İstifadeci linke basanda:
@dp.callback_query(F.data.startswith("getlink_"))
async def linki_ver_ve_say(callback: types.CallbackQuery):
    link_id = int(callback.data.split("_")[1])
    url = database.linki_getir(link_id)
    if url:
        database.klik_artir(callback.from_user.id)
        await callback.message.answer(f"🔗 Sizin linkiniz:\n\n{url}")
        await callback.answer("Göndərildi!", show_alert=False)
    else:
        await callback.answer("Məlumat tapılmadı.", show_alert=True)

# Admin linki silməyə basanda:
@dp.callback_query(F.data.startswith("dellink_"))
async def link_sil_action(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    link_id = int(callback.data.split("_")[1])
    database.link_sil(link_id)
    await callback.message.edit_text("✅ Link bazadan uğurla silindi!")
    await callback.answer()

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
# 📏 BƏDƏN ÖLÇÜSÜ (KALKULYATOR)
# ==========================================
@dp.message(F.text == "📏 Bədən Ölçüsü")
async def size_start(message: types.Message, state: FSMContext):
    await message.answer("Boyunuzu sm ilə yazın (məsələn: 170):")
    await state.set_state(BodySizeState.boy)

@dp.message(BodySizeState.boy)
async def size_boy(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Xahiş edirəm rəqəm yazın.")
    await state.update_data(boy=int(message.text))
    await message.answer("İndi isə çəkinizi kq ilə yazın (məsələn: 65):")
    await state.set_state(BodySizeState.ceki)

@dp.message(BodySizeState.ceki)
async def size_ceki(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Xahiş edirəm rəqəm yazın.")
    data = await state.get_data()
    boy = data['boy'] / 100
    bmi = int(message.text) / (boy ** 2)
    
    if bmi < 18.5: beden = "XS və ya S"
    elif 18.5 <= bmi < 24.9: beden = "S və ya M"
    elif 25 <= bmi < 29.9: beden = "L və ya XL"
    else: beden = "XXL və üstü"
        
    await message.answer(f"Təxmini Trendyol ölçünüz: **{beden}** 👕\n\n*(Qeyd: Bu standart kütlə indeksinə əsaslanır. Məhsulun qəlibinə görə dəyişə bilər)*", parse_mode="Markdown")
    await state.clear()


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
    
    try:
        await bot.send_message(target, f"🎁 **Admin sizin istəyinizə uyğun məhsul tapdı!**\n\n{m.text}")
        await m.answer("✅ Link uğurla və yalnız həmin istifadəçiyə göndərildi.")
    except:
        await m.answer("❌ İstifadəçiyə mesaj çatmadı (bəlkə botu bloklayıb).")

    for admin in ADMIN_IDS:
        if admin != m.from_user.id:
            try: await bot.send_message(admin, f"ℹ️ Admin @{m.from_user.username} istifadəçinin istəyinə cavab verdi:\n{m.text}")
            except: pass
    await state.clear()


# ==========================================
# 👑 ADMIN PANELİ
# ==========================================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Kateqoriyaya Link"), KeyboardButton(text="📋 Linklərə Bax / Sil")],
        [KeyboardButton(text="📢 Hamıya Mesaj (Kateqoriyasız)")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👥 İstifadəçi Sayı")],
        [KeyboardButton(text="🔙 Ana Menyuya Qayıt")]
    ], resize_keyboard=True)
    await message.answer("👑 Admin Paneli. Nə etmək istəyirsiniz?", reply_markup=kb)

# ADMIN - Ana Menyuya Qayıtmaq
@dp.message(F.text == "🔙 Ana Menyuya Qayıt")
async def back_to_main_menu(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Ana menyuya qayıtdınız. 🛍", reply_markup=ana_menyu())

# ADMIN - Linklərə Baxmaq və Silmək
@dp.message(F.text == "📋 Linklərə Bax / Sil")
async def adm_del_1(m: types.Message, state: FSMContext):
    if m.from_user.id not in ADMIN_IDS: return
    await m.answer("Hansı kateqoriyadakı linklərə baxmaq (və ya silmək) istəyirsiniz?", reply_markup=admin_top_cat_kb())
    await state.set_state(DeleteState.kat_sec)

# ADMIN - İstifadəçi Sayına Baxmaq
@dp.message(F.text == "👥 İstifadəçi Sayı")
async def show_users_count(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    users = database.butun_istifadecileri_getir()
    await message.answer(f"👥 **Botun Ümumi İstifadəçi Sayı:** {len(users)} nəfər.", parse_mode="Markdown")

# ADMIN - Hamıya Mesaj (Broadcast - Mətn və ŞƏKİL Dəstəkli)
@dp.message(F.text == "📢 Hamıya Mesaj (Kateqoriyasız)")
async def broadcast_start(m: types.Message, state: FSMContext):
    if m.from_user.id not in ADMIN_IDS: return
    await m.answer("Bütün bot istifadəçilərinə gedəcək məlumatı (şəkil və ya sadəcə mətn) göndərin:")
    await state.set_state(BroadcastState.mesaj_metni)

@dp.message(BroadcastState.mesaj_metni)
async def broadcast_send(m: types.Message, state: FSMContext):
    users = database.butun_istifadecileri_getir()
    count = 0
    await m.answer("🚀 Mesaj göndərilir...")
    
    for uid in users:
        try:
            if m.photo:
                # Əgər göndərilən şəkildirsə (və altındakı yazını da götürürük)
                caption_text = m.caption if m.caption else ""
                await bot.send_photo(uid, photo=m.photo[-1].file_id, caption=f"📢 **YENİ KAMPANİYA!**\n\n{caption_text}")
            else:
                # Əgər sadəcə mətndirsə
                await bot.send_message(uid, f"📢 **YENİ KAMPANİYA!**\n\n{m.text}")
                
            count += 1
            await asyncio.sleep(0.05) # Telegramın spam limitinə düşməmək üçün kiçik fasilə
        except: 
            pass
            
    await m.answer(f"✅ Kateqoriyasız linkiniz/şəkliniz {count} nəfərə uğurla çatdırıldı.")
    await state.clear()

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    clicks = database.gunun_hesabati()
    await message.answer(f"📊 **Gündəlik Hesabat**\nBu gün botdakı linklərə ümumi **{clicks}** klik edilib.")

# ADMIN - Kateqoriyaya Link Əlavə Etmək (VƏ YA YENİLƏMƏK)
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
    
    # Eyni adda köhnə link varsa, üstünə yazır (YENİLƏYİR), yoxdursa YENİSİNİ YARADIR.
    database.link_elave_et(data['kat'], data['ad'], m.text)
    
    await m.answer(f"✅ Link '{data['kat']}' kateqoriyasına əlavə edildi (və ya yeniləndi).\n(İstifadəçilərə bildiriş getmədi).")
    
    for admin in ADMIN_IDS:
        if admin != m.from_user.id:
            try: await bot.send_message(admin, f"ℹ️ Digər admin '{data['kat']}' bölməsinə '{data['ad']}' linkini əlavə etdi/yenilədi.")
            except: pass
    await state.clear()

# --- RENDER ÜÇÜN VEB-SERVER ---
async def ping(request):
    return web.Response(text="Trendyol Bot is alive!")

async def main():
    database.bazani_yarat()
    print("Trendyol Affiliate Bot işə düşdü...")
    
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
