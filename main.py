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

TOKEN = "8740821772:AAHn1gMm_hdn-UDYD41LtcCwYZjW1blMPmc"
ADMIN_IDS = [8645642283, 2111781743] # Admin ID-ləri bura yazın

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- FSM STATES ---
class AdminState(StatesGroup):
    link_kateqoriya = State()
    link_ad = State()
    link_url = State()

class BroadcastState(StatesGroup):
    mesaj_metni = State()

class SuggestionState(StatesGroup):
    mesaj = State()

# --- MENYULAR ---
def ana_menyu():
    duymeler = [
        [KeyboardButton(text="🔥 Günün Endirimləri"), KeyboardButton(text="⚡ Flash Endirimlər")],
        [KeyboardButton(text="🕵️ Gizli Kampaniyalar"), KeyboardButton(text="🎟 Aktiv Kodlar")],
        [KeyboardButton(text="🛍 Məhsul Kateqoriyası")],
        [KeyboardButton(text="❤️ İstək Siyahısı"), KeyboardButton(text="💡 Təklif Qutusu")]
    ]
    return ReplyKeyboardMarkup(keyboard=duymeler, resize_keyboard=True)

# --- ALT KATEQORİYA KLAVİATURALARI (Dinamik Naviqasiya) ---
def cat_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👗 Paltar", callback_data="sub_paltar"), InlineKeyboardButton(text="👕 Köynək", callback_data="sub_koynek")],
        [InlineKeyboardButton(text="👖 Şalvar", callback_data="sub_salvar"), InlineKeyboardButton(text="👟 Ayaqqabı", callback_data="sub_ayaqqabi")],
        [InlineKeyboardButton(text="👶 Uşaq", callback_data="sub_usaq"), InlineKeyboardButton(text="🕶 Aksesuar", callback_data="sub_aksesuar")]
    ])

def cat_gender(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Qadın", callback_data=f"final_{prefix}_qadin"),
         InlineKeyboardButton(text="👨 Kişi", callback_data=f"final_{prefix}_kisi")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="back_to_main")]
    ])

def cat_ayaqqabi_gender():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Qadın Ayaqqabı", callback_data="sub_ay_qadin")],
        [InlineKeyboardButton(text="👨 Kişi Ayaqqabı", callback_data="sub_ay_kisi")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="back_to_main")]
    ])

def cat_ayaqqabi_tip(gender_prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👞 Klassik", callback_data=f"final_{gender_prefix}_klassik")],
        [InlineKeyboardButton(text="👟 Gündəlik", callback_data=f"final_{gender_prefix}_gundelik")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="sub_ayaqqabi")]
    ])

def cat_usaq():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👕 Geyim", callback_data="final_usaq_geyim")],
        [InlineKeyboardButton(text="👟 Ayaqqabı", callback_data="final_usaq_ayaqqabi")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="back_to_main")]
    ])

# --- ADMIN ÜÇÜN SEÇİM (Hər şey daxil) ---
def admin_cat_secim():
    # Admin link əlavə edərkən bütün son nöqtələri burdan seçir
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Günün Endirimi", callback_data="admcat_gunun")],
        [InlineKeyboardButton(text="Flash Endirim", callback_data="admcat_flash")],
        [InlineKeyboardButton(text="Gizli Kampaniya", callback_data="admcat_gizli")],
        [InlineKeyboardButton(text="Aktiv Kod", callback_data="admcat_kod")],
        [InlineKeyboardButton(text="Paltar Qadın", callback_data="admcat_paltar_qadin")],
        [InlineKeyboardButton(text="Ayaqqabı Kişi Klassik", callback_data="admcat_ay_kisi_klassik")]
        # Digər alt kateqoriyalar da eyni məntiqlə bura əlavə edilə bilər
    ])

# --- CALLBACK HANDLERS (Naviqasiya) ---
@dp.callback_query(F.data == "sub_paltar")
async def s_paltar(c: types.CallbackQuery): await c.message.edit_text("Cins seçin:", reply_markup=cat_gender("paltar"))

@dp.callback_query(F.data == "sub_ayaqqabi")
async def s_ay(c: types.CallbackQuery): await c.message.edit_text("Cins seçin:", reply_markup=cat_ayaqqabi_gender())

@dp.callback_query(F.data == "sub_ay_qadin")
async def s_ay_q(c: types.CallbackQuery): await c.message.edit_text("Stil seçin:", reply_markup=cat_ayaqqabi_tip("ay_qadin"))

@dp.callback_query(F.data == "sub_usaq")
async def s_usaq(c: types.CallbackQuery): await c.message.edit_text("Uşaq bölməsi:", reply_markup=cat_usaq())

@dp.callback_query(F.data == "back_to_main")
async def back(c: types.CallbackQuery): await c.message.edit_text("Kateqoriyalar:", reply_markup=cat_main())

# --- LİNKLƏRİ GÖSTƏRMƏ FUNKSİYASI ---
@dp.callback_query(F.data.startswith("final_"))
async def show_links(callback: types.CallbackQuery):
    cat_code = callback.data.replace("final_", "")
    linkler = database.kateqoriya_linklerini_getir(cat_code)
    
    if not linkler:
        await callback.answer("Bu kateqoriyada hələlik link yoxdur.", show_alert=True)
        return

    mesaj = "🔍 **Tapılan Məhsullar:**\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for l_id, name, _ in linkler:
        kb.inline_keyboard.append([InlineKeyboardButton(text=name, callback_data=f"getlink_{l_id}")])
    
    await callback.message.answer(mesaj, reply_markup=kb, parse_mode="Markdown")

# --- ADMIN TOPLU MESAJ (KATEQORİYASIZ LİNK) ---
@dp.message(Command("duyuru"))
async def broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Bütün istifadəçilərə göndəriləcək mesajı yazın (Məlumat və Link daxil):")
    await state.set_state(BroadcastState.mesaj_metni)

@dp.message(BroadcastState.mesaj_metni)
async def broadcast_send(message: types.Message, state: FSMContext):
    users = database.butun_istifadecileri_getir()
    count = 0
    await message.answer("🚀 Mesaj göndərilir...")
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **YENİ TƏKLİF!**\n\n{message.text}", parse_mode="Markdown")
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"✅ Mesaj {count} nəfərə uğurla çatdırıldı.")
    await state.clear()

# --- TƏKLİF QUTUSU VƏ FƏRDİ CAVAB ---
@dp.message(SuggestionState.mesaj)
async def suggestion_handle(message: types.Message, state: FSMContext):
    database.teklif_yaz(message.from_user.id, message.text)
    await message.answer("Təklifiniz qəbul edildi! Adminlər sizə xüsusi olaraq cavab verə bilər.")
    
    # Adminlərə "Xüsusi Cavab Ver" düyməsi ilə göndər
    for aid in ADMIN_IDS:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Cavab Ver (Link At)", callback_data=f"reply_{message.from_user.id}")]])
        try: await bot.send_message(aid, f"💡 **Yeni Təklif!**\nKim: @{message.from_user.username}\nMesaj: {message.text}", reply_markup=kb)
        except: pass
    await state.clear()

@dp.callback_query(F.data.startswith("reply_"))
async def admin_reply_start(callback: types.CallbackQuery, state: FSMContext):
    target_id = callback.data.split("_")[1]
    await state.update_data(target=target_id)
    await callback.message.answer(f"İstifadəçiyə göndəriləcək xüsusi linki və mesajı yazın:")
    await state.set_state(AdminState.link_url) # Mövcud state-i istifadə edirik
    await callback.answer()

# --- ADMIN PANELİ (LİNK ƏLAVƏ) ---
@dp.message(Command("admin"))
async def admin_main(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Kateqoriyaya Link")],
        [KeyboardButton(text="📢 Hamıya Mesaj (/duyuru)")],
        [KeyboardButton(text="📊 Statistika")]
    ], resize_keyboard=True)
    await message.answer("👑 Admin Paneli", reply_markup=kb)

@dp.message(F.text == "➕ Kateqoriyaya Link")
async def adm_l_1(m: types.Message, state: FSMContext):
    await m.answer("Kateqoriya seçin:", reply_markup=admin_cat_secim())
    await state.set_state(AdminState.link_kateqoriya)

@dp.callback_query(AdminState.link_kateqoriya)
async def adm_l_2(c: types.CallbackQuery, state: FSMContext):
    await state.update_data(kat=c.data.replace("admcat_", ""))
    await c.message.answer("Məhsulun adı:")
    await state.set_state(AdminState.link_ad)

@dp.message(AdminState.link_ad)
async def adm_l_3(m: types.Message, state: FSMContext):
    await state.update_data(ad=m.text)
    await m.answer("Trendyol Linki:")
    await state.set_state(AdminState.link_url)

@dp.message(AdminState.link_url)
async def adm_l_final(m: types.Message, state: FSMContext):
    data = await state.get_data()
    # Əgər bu bir "Xüsusi Cavab"dırsa
    if 'target' in data:
        try:
            await bot.send_message(data['target'], f"🎁 **İstəyinizə uyğun tapıldı!**\n\n{m.text}")
            await m.answer("✅ Link yalnız həmin istifadəçiyə göndərildi.")
        except: await m.answer("❌ Mesaj göndərilə bilmədi.")
    else:
        database.link_elave_et(data['kat'], data['ad'], m.text)
        await m.answer(f"✅ Link '{data['kat']}' kateqoriyasına əlavə edildi. (Heç kimə bildiriş getmədi)")
    await state.clear()

# --- DİGƏR FUNKSİYALAR (START, PİNG VƏ S.) ---
@dp.message(F.text == "🛍 Məhsul Kateqoriyası")
async def cat_m(m: types.Message): await m.answer("Bölmə seçin:", reply_markup=cat_main())

@dp.message(F.text == "🔥 Günün Endirimləri")
async def f_gunun(m: types.Message): await linkleri_goster(m, "gunun", "🔥 Günün Endirimləri")

@dp.message(F.text == "🎟 Aktiv Kodlar")
async def f_kod(m: types.Message): await linkleri_goster(m, "kod", "🎟 Aktiv Kodlar")

@dp.callback_query(F.data.startswith("getlink_"))
async def g_link(c: types.CallbackQuery):
    l_id = c.data.split("_")[1]
    url = database.linki_getir(l_id)
    if url: 
        database.klik_artir(c.from_user.id)
        await c.message.answer(f"🔗 Linkiniz:\n{url}")
    await c.answer()

async def ping(request): return web.Response(text="Bot Active")

async def main():
    database.bazani_yarat()
    asyncio.create_task(dp.start_polling(bot))
    app = web.Application()
    app.add_routes([web.get('/', ping)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    while True: await asyncio.sleep(3600)

if __name__ == "__main__": asyncio.run(main())
