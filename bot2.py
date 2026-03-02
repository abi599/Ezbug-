import sqlite3
import hashlib
import random
import string
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler

TOKEN = "8666681681:AAEiRY4vacyOkyEWW2rUcVy9S6tHnSGCC8U"
OWNER_ID = 7461772533
DB = '/data/data/com.termux/files/home/ezbug/database.db'
QRIS_4000 = '/data/data/com.termux/files/home/ezbug/qris_4000.jpg'
QRIS_8000 = '/data/data/com.termux/files/home/ezbug/qris_8000.jpg'

PILIH_PRODUK, TUNGGU_USERNAME, TUNGGU_PASSWORD, TUNGGU_BUKTI = range(4)

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def get_db():
    return sqlite3.connect(DB)

def generate_invoice():
    return "INV-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def batal_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batalkan Pembelian", callback_data="batal")]])

async def hapus_nanti(bot, chat_id, message_id, delay=300):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def start(update, context):
    context.user_data.clear()
    try:
        await update.message.delete()
    except:
        pass
    keyboard = [
        [InlineKeyboardButton("♾️ Akun Permanen - Rp 8.000", callback_data="permanen")],
        [InlineKeyboardButton("⏳ Akun 7 Hari - Rp 4.000", callback_data="tidak_permanen")]
    ]
    msg = await context.bot.send_message(
        update.effective_chat.id,
        "🎉 *Selamat Datang di Ezbug Store!*\n\nSilakan pilih produk:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data["mid"] = msg.message_id
    return PILIH_PRODUK

async def pilih_produk(update, context):
    query = update.callback_query
    await query.answer()
    tipe = query.data
    context.user_data["tipe"] = tipe
    context.user_data["invoice"] = generate_invoice()
    if tipe == "permanen":
        context.user_data["harga"] = 8000
        context.user_data["expired"] = None
        context.user_data["tipe_text"] = "Akun Permanen ♾️"
    else:
        context.user_data["harga"] = 4000
        expired = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        context.user_data["expired"] = expired
        context.user_data["tipe_text"] = "Akun 7 Hari ⏳"
    await query.edit_message_text(
        f"📧 *STEP 1: USERNAME*\n\n"
        f"Produk: *{context.user_data['tipe_text']}*\n"
        f"Harga: *Rp {context.user_data['harga']:,}*\n\n"
        f"Kirim username yang diinginkan:\n"
        f"⚠️ Minimal 3 karakter",
        parse_mode="Markdown",
        reply_markup=batal_keyboard()
    )
    return TUNGGU_USERNAME

async def terima_username(update, context):
    username = update.message.text.strip()
    chat_id = update.effective_chat.id
    mid = context.user_data.get("mid")
    user_mid = update.message.message_id
    if len(username) < 3:
        await context.bot.edit_message_text(
            "❌ Username minimal 3 karakter!\nCoba lagi:",
            chat_id=chat_id, message_id=mid,
            reply_markup=batal_keyboard()
        )
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_mid)
        except:
            pass
        return TUNGGU_USERNAME
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username=?", (username,))
    ada = cursor.fetchone()
    conn.close()
    if ada:
        await context.bot.edit_message_text(
            "❌ Username sudah dipakai! Coba lain:",
            chat_id=chat_id, message_id=mid,
            reply_markup=batal_keyboard()
        )
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_mid)
        except:
            pass
        return TUNGGU_USERNAME
    context.user_data["username"] = username
    await context.bot.edit_message_text(
        f"🔑 *STEP 2: PASSWORD*\n\n"
        f"Produk: *{context.user_data['tipe_text']}*\n"
        f"Harga: *Rp {context.user_data['harga']:,}*\n"
        f"Username: *{username}*\n\n"
        f"Kirim password yang diinginkan:\n"
        f"⚠️ Minimal 6 karakter",
        chat_id=chat_id, message_id=mid,
        parse_mode="Markdown",
        reply_markup=batal_keyboard()
    )
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=user_mid)
    except:
        pass
    return TUNGGU_PASSWORD

async def terima_password(update, context):
    password = update.message.text.strip()
    chat_id = update.effective_chat.id
    mid = context.user_data.get("mid")
    user_mid = update.message.message_id
    if len(password) < 6:
        await context.bot.edit_message_text(
            f"❌ Password minimal 6 karakter!\n"
            f"Username: *{context.user_data['username']}*\n\n"
            f"Coba lagi:",
            chat_id=chat_id, message_id=mid,
            parse_mode="Markdown",
            reply_markup=batal_keyboard()
        )
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_mid)
        except:
            pass
        return TUNGGU_PASSWORD
    context.user_data["password"] = password
    tipe = context.user_data["tipe"]
    harga = context.user_data["harga"]
    tipe_text = context.user_data["tipe_text"]
    username = context.user_data["username"]
    invoice = context.user_data["invoice"]
    berlaku = (datetime.now() + timedelta(minutes=5)).strftime("%d/%m/%Y, %H.%M.%S")
    qris = QRIS_8000 if tipe == "permanen" else QRIS_4000
    caption = (
        f"🧾 *INVOICE PEMBAYARAN*\n\n"
        f"🗒️ Invoice: `{invoice}`\n"
        f"📦 Produk: *{tipe_text}*\n"
        f"💰 Total: *Rp {harga:,}*\n\n"
        f"👤 Username: `{username}`\n"
        f"🔑 Password: `{password}`\n\n"
        f"📱 *CARA BAYAR:*\n"
        f"1. Scan QR Code di atas\n"
        f"2. Bayar sesuai nominal\n"
        f"3. Kirim screenshot bukti bayar\n\n"
        f"⏰ Berlaku sampai: {berlaku}\n"
        f"⚠️ Invoice otomatis dihapus 5 menit!"
    )
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=mid)
    except:
        pass
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=user_mid)
    except:
        pass
    with open(qris, 'rb') as f:
        msg = await context.bot.send_photo(
            chat_id, f,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=batal_keyboard()
        )
    context.user_data["mid"] = msg.message_id
    asyncio.create_task(hapus_nanti(context.bot, chat_id, msg.message_id, 300))
    return TUNGGU_BUKTI

async def terima_bukti(update, context):
    if not update.message.photo:
        return TUNGGU_BUKTI
    chat_id = update.effective_chat.id
    mid = context.user_data.get("mid")
    user_mid = update.message.message_id
    user = update.effective_user
    username = context.user_data["username"]
    password = context.user_data["password"]
    tipe_text = context.user_data["tipe_text"]
    harga = context.user_data["harga"]
    expired = context.user_data.get("expired")
    invoice = context.user_data["invoice"]
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=mid)
    except:
        pass
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=user_mid)
    except:
        pass
    tunggu_msg = await context.bot.send_message(
        chat_id,
        "⏳ *Menunggu Konfirmasi Owner...*\n\nPembayaran kamu sedang dicek.\nSabar ya! 😊",
        parse_mode="Markdown"
    )
    conn2 = sqlite3.connect(DB)
    c2 = conn2.cursor()
    c2.execute("INSERT INTO pending_orders VALUES (?,?,?,?,?,?)",
        (user.id, tunggu_msg.message_id, username, password, expired, invoice))
    conn2.commit()
    conn2.close()
    approve_cmd = f"/approve {user.id} {username} {password}"
    if expired:
        approve_cmd += f" {expired.replace(' ', '_')}"
    from telegram import Bot
    bot1 = Bot(token="8098017315:AAHbgLc0AYDu_pUM08EjYHeizOuzHz1Lj_o")
    await bot1.send_message(
        OWNER_ID,
        f"🔔 *PESANAN BARU!*\n\n"
        f"🗒️ Invoice: `{invoice}`\n"
        f"👤 Pembeli: {user.first_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📦 Produk: {tipe_text}\n"
        f"💰 Harga: Rp {harga:,}\n"
        f"👤 Username: `{username}`\n"
        f"🔑 Password: `{password}`\n\n"
        f"Ketik:\n`{approve_cmd}`",
        parse_mode="Markdown"
    )
    await bot1.forward_message(OWNER_ID, chat_id, update.message.message_id)
    context.user_data.clear()
    return ConversationHandler.END

async def batal_callback(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("❌ Pesanan dibatalkan!\n\nKetik /start untuk mulai lagi.")
    return ConversationHandler.END

async def batal(update, context):
    context.user_data.clear()
    try:
        await update.message.delete()
    except:
        pass
    await context.bot.send_message(
        update.effective_chat.id,
        "❌ Pesanan dibatalkan!\n\nKetik /start untuk mulai lagi."
    )
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).read_timeout(30).write_timeout(30).connect_timeout(30).pool_timeout(30).concurrent_updates(True).build()

beli_handler = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("start", start)],
    states={
        PILIH_PRODUK: [CallbackQueryHandler(pilih_produk, pattern="^(permanen|tidak_permanen)$")],
        TUNGGU_USERNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, terima_username),
            CallbackQueryHandler(batal_callback, pattern="^batal$")
        ],
        TUNGGU_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, terima_password),
            CallbackQueryHandler(batal_callback, pattern="^batal$")
        ],
        TUNGGU_BUKTI: [
            MessageHandler(filters.PHOTO, terima_bukti),
            CallbackQueryHandler(batal_callback, pattern="^batal$")
        ],
    },
    fallbacks=[
        CommandHandler("batal", batal),
        CommandHandler("start", start)
    ]
)

app.add_handler(beli_handler)

print("Bot 2 Pembeli berjalan...")
app.run_polling()
