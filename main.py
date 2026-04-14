import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web
import database 

logging.basicConfig(level=logging.INFO)

TOKEN = "8740821772:AAHn1gMm_hdn-UDYD41LtcCwYZjW1blMPmc"
ADMIN_ID = 8645642283

bot = Bot(token=TOKEN)
dp = Dispatcher()

class BroadcastState(StatesGroup):
    mesaji_gozleyir = State()

def ana_menyu_yarat():
    duymeler = [
        [KeyboardButton(text="🔥 Günün Endirimləri"), KeyboardButton(text="🎟 Aktiv Kuponlar")],
        [KeyboardButton(text="🛍 Trendyol Seçilmişlər"), KeyboardButton(text="✨ Ətirlər (Lattafa və s.)")],
        [KeyboardButton(text="📞 Adminlə Əlaqə")]
    ]
    return ReplyKeyboardMarkup(keyboard=duymeler, resize_keyboard=True)

@dp.message(CommandStart())
async def start_komandasi(message: types.Message):
    database.istifadeci_elave_et(message.from_user.id, message.from_user.username)
    xos_geldin_mesaji = (
        f"Salam, {message.from_user.first_name}! 🚀\n\n"
        "Günün ən yaxşı endirimləri və kampaniyalar botuna xoş gəldin.\n"
        "Aşağıdakı menyudan sənə maraqlı olan bölməni seçə bilərsən:"
    )
    await message.answer(xos_geldin_mesaji, reply_markup=ana_menyu_yarat())

@dp.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Admin Panelinə Xoş Gəldin!\n\nHamısına mesaj göndərmək üçün mənə mesajı yazın (mətn, şəkil, link ola bilər). Ləğv etmək üçün /cancel yazın.")
        await state.set_state(BroadcastState.mesaji_gozleyir)
    else:
        await message.answer("Siz admin deyilsiniz! 🚫")

@dp.message(BroadcastState.mesaji_gozleyir)
async def mesaji_yayinla(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("Toplu mesaj göndərilməsi ləğv edildi.", reply_markup=ana_menyu_yarat())
        await state.clear()
        return
    users = database.butun_istifadecileri_getir()
    ugurlu = 0
    await message.answer("⏳ Mesajlar göndərilir, zəhmət olmasa gözləyin...")
    for user_id in users:
        try:
            await message.send_copy(chat_id=user_id)
            ugurlu += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Toplu mesaj uğurla {ugurlu} nəfərə göndərildi!", reply_markup=ana_menyu_yarat())
    await state.clear()

@dp.message(F.text == "🔥 Günün Endirimləri")
async def gunun_endirimi(message: types.Message):
    await message.answer("🔥 **Bu gün üçün aktiv olan endirimlər:**\n1. Xiaomi Redmi Note seriyası ehtiyat hissələrinə 20% endirim!\n2. Zara mağazalarında 1 alana 1 pulsuz.", parse_mode="Markdown")

@dp.message(F.text == "🎟 Aktiv Kuponlar")
async def aktiv_kuponlar(message: types.Message):
    await message.answer("🎟 **Aktiv kuponlar:**\n• AliExpress: `ALISUMMER24`\n• Trendyol: `TRENDYOL15`", parse_mode="Markdown")

@dp.message(F.text == "🛍 Trendyol Seçilmişlər")
async def trendyol_linkler(message: types.Message):
    await message.answer("Burada Trendyol məhsullarının və çarx kampaniyalarının linkləri olacaq.")

@dp.message(F.text == "✨ Ətirlər (Lattafa və s.)")
async def etir_bolmesi(message: types.Message):
    await message.answer("Orijinal Lattafa, Ahmed Al Maghribi və 'dupe' versiyalar burada olacaq!")

@dp.message(F.text == "📞 Adminlə Əlaqə")
async def admin_elaqe(message: types.Message):
    await message.answer("Təkliflər üçün adminə yazın: @senin_username_in")

# --- RENDER ÜÇÜN SAXTA VEB-SERVER HİSSƏSİ ---
async def ping(request):
    return web.Response(text="Bot is alive!")

async def main():
    database.bazani_yarat()
    print("Bot işə düşdü...")
    
    # 1. Botu arxa planda işə salırıq
    asyncio.create_task(dp.start_polling(bot))
    
    # 2. Renderin pulsuz xidməti üçün saxta veb-server başladırıq
    app = web.Application()
    app.add_routes([web.get('/', ping)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # 3. Sonsuz dövr ki, proqram dayanmasın
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
