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

TOKEN = "8740821772:AAHn1gMm_hdn-UDYD41LtcCwYZjW1blMPmc"
ADMIN_ID = 8645642283

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- FSM STATES (Məlumat gözləmə vəziyyətləri) ---
class AdminState(StatesGroup):
    link_kateqoriya = State()
    link_ad = State()
    link_url = State()

class BodySizeState(StatesGroup):
    boy = State()
    ceki = State()

class SuggestionState(StatesGroup):
    mesaj = State()

# --- LÜĞƏT VƏ RƏNGLƏR (Baza) ---
AZ_TR_LUGAT = {
    "şalvar": "Pantolon", "köynək": "Gömlek/Tişört", "gödəkçə": "Mont/Kaban", 
    "ayaqqabı": "Ayakkabı", "papaq": "Şapka", "eşofman": "İdman paltarı (İdman kostyumu)",
    "kapşonlu": "Kapüşonlu (Kapişonlu)", "etek": "Yubka", "elbise": "Don/Paltar", "kaban": "Qalın palto"
}

RENG_UYGUNLUGU = {
    "qara": "Ağ, qırmızı, boz və ya bej ilə əla gedir. Çox asan kombinlənir.",
    "ağ": "Hər rənglə uyğundur! Xüsusilə mavi, qara və ya qəhvəyi ilə.",
    "mavi": "Ağ, bej, sarı və ya narıncı tonlarla cəhd et.",
    "qırmızı": "Qara, ağ, tünd göy (lacivərt) və boz rənglərlə möhtəşəm görünür.",
    "yaşıl": "Qəhvəyi, bej, ağ və ya xardal rəngi ilə uyğunlaşdır."
}

# --- MENYULAR ---
def ana_menyu():
    duymeler = [
        [KeyboardButton(text="🔥 Günün Endirimləri"), KeyboardButton(text="⚡ Flash Endirimlər")],
        [KeyboardButton(text="👑 Ən Çox Satılanlar"), KeyboardButton(text="👗 Günün Kombini")],
        [KeyboardButton(text="🕵️ Gizli Kampaniyalar"), KeyboardButton(text="🎟 Aktiv Kodlar")],
        [KeyboardButton(text="📏 Bədən Ölçüsü"), KeyboardButton(text="📖 AZ-TR Lüğət")],
        [KeyboardButton(text="🎨 Rəng Uyğunluğu"), KeyboardButton(text="❤️ İstək Siyahısı")],
        [KeyboardButton(text="💎 Sadiq İzləyici (VIP)"), KeyboardButton(text="💡 Təklif Qutusu")]
    ]
    return ReplyKeyboardMarkup(keyboard=duymeler, resize_keyboard=True)

def kateqoriya_secim_klaviaturasi():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Günün Endirimləri", callback_data="cat_gunun")],
        [InlineKeyboardButton(text="Flash Endirimlər", callback_data="cat_flash")],
        [InlineKeyboardButton(text="Ən Çox Satılanlar", callback_data="cat_bestseller")],
        [InlineKeyboardButton(text="Gizli Kampaniyalar", callback_data="cat_gizli")],
        [InlineKeyboardButton(text="Günün Kombini", callback_data="cat_kombin")]
    ])

# --- ƏSAS KOMANDALAR ---
@dp.message(CommandStart())
async def start_komandasi(message: types.Message):
    database.istifadeci_elave_et(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(f"Salam, {message.from_user.first_name}! 🛍\n\nTrendyolun ən gizli endirimlərini və kampaniyalarını kəşf etməyə hazırsan? Aşağıdakı menyudan istədiyini seç!", reply_markup=ana_menyu())

# --- DİNAMİK LİNKLƏRİ GÖSTƏRMƏ VƏ KLİK TRACKER ---
async def linkleri_goster(message: types.Message, kateqoriya, bashliq):
    linkler = database.kateqoriya_linklerini_getir(kateqoriya)
    if not linkler:
        await message.answer(f"Hazırda '{bashliq}' bölməsində yeni link yoxdur. Tezliklə əlavə olunacaq! ⏳")
        return
    
    # VIP yoxlanışı (Gizli kampaniyalar üçün)
    if kateqoriya == "cat_gizli" and not database.vip_yoxla(message.from_user.id):
        await message.answer("🔒 Bu bölmə yalnız 'Sadiq İzləyici'lər (VIP) üçündür!\nVIP olmaq üçün botdakı linklərə mütəmadi daxil olun.")
        return

    mesaj = f"*{bashliq}*\nAşağıdakı düymələrə basaraq linkləri götürə bilərsiniz:\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for link_id, name, _ in linkler:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=name, callback_data=f"getlink_{link_id}")])
    
    await message.answer(mesaj, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("getlink_"))
async def linki_ver_ve_say(callback: types.CallbackQuery):
    link_id = int(callback.data.split("_")[1])
    url = database.linki_getir(link_id)
    if url:
        database.klik_artir(callback.from_user.id) # KLİK TRACKER İŞLƏYİR
        await callback.message.answer(f"🔗 Sizin endirim linkiniz:\n{url}")
        await callback.answer("Link göndərildi!", show_alert=False)
    else:
        await callback.answer("Link tapılmadı.", show_alert=True)

# --- MENYU SEÇİMLƏRİ ---
@dp.message(F.text == "🔥 Günün Endirimləri")
async def m_gunun(m: types.Message): await linkleri_goster(m, "cat_gunun", "🔥 Günün Endirimləri")

@dp.message(F.text == "⚡ Flash Endirimlər")
async def m_flash(m: types.Message): await linkleri_goster(m, "cat_flash", "⚡ Flash Endirimlər")

@dp.message(F.text == "👑 Ən Çox Satılanlar")
async def m_bestseller(m: types.Message): await linkleri_goster(m, "cat_bestseller", "👑 Ən Çox Satılanlar")

@dp.message(F.text == "🕵️ Gizli Kampaniyalar")
async def m_gizli(m: types.Message): await linkleri_goster(m, "cat_gizli", "🕵️ Gizli VIP Kampaniyalar")

@dp.message(F.text == "👗 Günün Kombini")
async def m_kombin(m: types.Message): await linkleri_goster(m, "cat_kombin", "👗 Günün Kombini")

@dp.message(F.text == "🎟 Aktiv Kodlar")
async def m_kodlar(m: types.Message):
    await m.answer("🎟 **Aktiv Trendyol Kodları:**\nHazırda sistemdə aktiv əlavə endirim kodu yoxdur. Səhifəmi izləmədə qalın!", parse_mode="Markdown")

@dp.message(F.text == "💎 Sadiq İzləyici (VIP)")
async def check_vip(message: types.Message):
    is_vip = database.vip_yoxla(message.from_user.id)
    if is_vip:
        await message.answer("Təbriklər! Siz VIP (Sadiq İzləyici) statusundasınız! 💎\nGizli kampaniyalara artıq girişiniz var.")
    else:
        await message.answer("Siz hələ VIP deyilsiniz. 😔\nBotun paylaşdığı linklərdən daha çox istifadə edərək VIP ola və gizli kampaniyaları aça bilərsiniz!")

# --- BƏDƏN ÖLÇÜSÜ (BMI) ---
@dp.message(F.text == "📏 Bədən Ölçüsü")
async def size_start(message: types.Message, state: FSMContext):
    await message.answer("Boyunuzu sm ilə yazın (məsələn: 170):")
    await state.set_state(BodySizeState.boy)

@dp.message(BodySizeState.boy)
async def size_boy(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Xahiş edirəm rəqəm yazın.")
    await state.update_data(boy=int(message.text))
    await message.answer("İndi isə çəkinizi kq ilə yazın (məsələn: 65):")
    await state.set_state(BodySizeState.ceki)

@dp.message(BodySizeState.ceki)
async def size_ceki(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Xahiş edirəm rəqəm yazın.")
    data = await state.get_data()
    boy = data['boy'] / 100
    ceki = int(message.text)
    bmi = ceki / (boy ** 2)
    
    if bmi < 18.5: beden = "XS və ya S"
    elif 18.5 <= bmi < 24.9: beden = "S və ya M"
    elif 25 <= bmi < 29.9: beden = "L və ya XL"
    else: beden = "XXL və üstü"
        
    await message.answer(f"Sizin bədən kütlə indeksinizə görə təxmini Trendyol ölçünüz: **{beden}** 👕", parse_mode="Markdown")
    await state.clear()

# --- LÜĞƏT VƏ RƏNGLƏR ---
@dp.message(F.text == "📖 AZ-TR Lüğət")
async def show_dict(message: types.Message):
    metn = "🇹🇷 **Trendyol Türkiyə-Azərbaycan Lüğəti:**\n\n"
    for az, tr in AZ_TR_LUGAT.items(): metn += f"• {az.capitalize()} = {tr}\n"
    await message.answer(metn, parse_mode="Markdown")

@dp.message(F.text == "🎨 Rəng Uyğunluğu")
async def color_advisor(message: types.Message):
    metn = "🎨 **Hansı rənglə nə geyinmək olar?**\n\n"
    for reng, meslehet in RENG_UYGUNLUGU.items(): metn += f"• **{reng.capitalize()}**: {meslehet}\n\n"
    await message.answer(metn, parse_mode="Markdown")

# --- İSTƏK SİYAHISI (WISHLIST) ---
@dp.message(F.text == "❤️ İstək Siyahısı")
async def wishlist_menu(message: types.Message):
    await message.answer("Bildiriş almaq istədiyiniz kateqoriyaları seçin. Mən o bölməyə məhsul qoyanda sizə avtomatik mesaj gələcək! (Təkrar basaraq abunəliyi ləğv edə bilərsiniz)", reply_markup=kateqoriya_secim_klaviaturasi())

@dp.callback_query(F.data.startswith("cat_"))
async def wishlist_toggle(callback: types.CallbackQuery):
    cat = callback.data
    database.isteke_elave_et(callback.from_user.id, cat)
    await callback.answer("İstək siyahınız yeniləndi! ✅", show_alert=True)

# --- TƏKLİF QUTUSU ---
@dp.message(F.text == "💡 Təklif Qutusu")
async def req_start(message: types.Message, state: FSMContext):
    await message.answer("Adminə hansı endirimli məhsulları paylaşmağı təklif edirsiniz? Bura yazın:")
    await state.set_state(SuggestionState.mesaj)

@dp.message(SuggestionState.mesaj)
async def req_save(message: types.Message, state: FSMContext):
    database.teklif_yaz(message.from_user.id, message.text)
    await message.answer("Təklifiniz adminə göndərildi! Çox sağ olun. 🙏")
    await bot.send_message(ADMIN_ID, f"💡 Yeni Təklif gəldi!\nİstifadəçi: @{message.from_user.username}\nMesaj: {message.text}")
    await state.clear()

# --- ADMIN PANELİ ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return await message.answer("Siz admin deyilsiniz!")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Yeni Link Əlavə Et", callback_data="admin_addlink")],
        [InlineKeyboardButton(text="📊 Gündəlik Klik Hesabatı", callback_data="admin_stats")]
    ])
    await message.answer("👑 Admin Panelinə Xoş Gəldin!\nNə etmək istəyirsiniz?", reply_markup=kb)

@dp.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    clicks = database.gunun_hesabati()
    await callback.message.answer(f"📊 **Gündəlik Hesabat**\nBu gün paylaşılan linklərə cəmi **{clicks}** dəfə daxil olunub.")
    await callback.answer()

@dp.callback_query(F.data == "admin_addlink")
async def admin_add_link_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("Hansı kateqoriyaya link əlavə edirsiniz?", reply_markup=kateqoriya_secim_klaviaturasi())
    await state.set_state(AdminState.link_kateqoriya)
    await callback.answer()

@dp.callback_query(AdminState.link_kateqoriya)
async def admin_add_link_cat(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(kat=callback.data)
    await callback.message.answer("Məhsulun (və ya kampaniyanın) adını yazın:")
    await state.set_state(AdminState.link_ad)
    await callback.answer()

@dp.message(AdminState.link_ad)
async def admin_add_link_name(message: types.Message, state: FSMContext):
    await state.update_data(ad=message.text)
    await message.answer("İndi isə Trendyol (Affiliate) linkinizi göndərin:")
    await state.set_state(AdminState.link_url)

@dp.message(AdminState.link_url)
async def admin_add_link_url(message: types.Message, state: FSMContext):
    data = await state.get_data()
    database.link_elave_et(data['kat'], data['ad'], message.text)
    await message.answer(f"✅ Link əlavə edildi!\nKateqoriya: {data['kat']}\nAd: {data['ad']}")
    
    # İstək siyahısında olanlara avtomatik bildiriş göndəririk (ÇOX VACİB FUNKSİYA)
    isteyenler = database.isteyi_olanlari_getir(data['kat'])
    gonderildi = 0
    for uid in isteyenler:
        try:
            await bot.send_message(uid, f"🔔 **Sizin üçün yeni endirim var!**\nİzlədiyiniz bölməyə yeni link əlavə edildi: {data['ad']}\nMenyudan daxil olub baxa bilərsiniz!")
            gonderildi += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"Bu kateqoriyanı izləyən {gonderildi} nəfərə bildiriş göndərildi.")
    await state.clear()

# --- RENDER ÜÇÜN SAXTA VEB-SERVER HİSSƏSİ ---
async def ping(request):
    return web.Response(text="Trendyol Affiliate Bot is alive!")

async def main():
    database.bazani_yarat()
    print("Trendyol Affiliate Bot işə düşdü...")
    
    asyncio.create_task(dp.start_polling(bot))
    
    app = web.Application()
    app.add_routes([web.get('/', ping)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
