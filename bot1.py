import sqlite3
import hashlib
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters, CallbackQueryHandler

TOKEN = "8098017315:AAHbgLc0AYDu_pUM08EjYHeizOuzHz1Lj_o"
OWNER_ID = 7461772533

DB = '/data/data/com.termux/files/home/ezbug/database.db'

PILIH_TIPE, TUNGGU_HARI, TUNGGU_USERNAME, TUNGGU_PASSWORD = range(4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    return sqlite3.connect(DB)

async def start(update, context):
    await update.message.reply_text(
        "🤖 Bot Owner Aktif!\n\n"
        "/create - Buat user\n"
        "/list - Daftar user\n"
        "/delete - Hapus user\n"
        "/addtime - Tambah waktu akun\n"
        "/approve - Konfirmasi pembayaran\n"
        "/reject - Tolak pembayaran"
    )

async def create_start(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Kamu bukan owner!")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton("♾️ Permanen", callback_data="permanen")],
        [InlineKeyboardButton("⏳ Tidak Permanen", callback_data="tidak_permanen")]
    ]
    await update.message.reply_text(
        "👤 Pilih tipe akun:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PILIH_TIPE

async def pilih_tipe(update, context):
    query = update.callback_query
    await query.answer()
    tipe = query.data
    context.user_data["tipe"] = tipe
    if tipe == "tidak_permanen":
        await query.edit_message_text("⏳ Berapa hari akun aktif?\nContoh: 7")
        return TUNGGU_HARI
    else:
        context.user_data["expired"] = None
        await query.edit_message_text("👤 Masukkan username:")
        return TUNGGU_USERNAME

async def terima_hari(update, context):
    try:
        hari = int(update.message.text.strip())
        expired = (datetime.now() + timedelta(days=hari)).strftime("%Y-%m-%d %H:%M:%S")
        context.user_data["expired"] = expired
        context.user_data["hari"] = hari
        await update.message.reply_text(f"✅ Akun aktif {hari} hari\n\n👤 Masukkan username:")
        return TUNGGU_USERNAME
    except:
        await update.message.reply_text("❌ Masukkan angka yang valid!")
        return TUNGGU_HARI

async def terima_username(update, context):
    username = update.message.text.strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username=?", (username,))
    ada = cursor.fetchone()
    conn.close()
    if ada:
        await update.message.reply_text("❌ Username sudah ada! Coba username lain:")
        return TUNGGU_USERNAME
    context.user_data["username"] = username
    await update.message.reply_text(f"✅ Username: {username}\n\n🔑 Masukkan password:")
    return TUNGGU_PASSWORD

async def terima_password(update, context):
    password = update.message.text.strip()
    username = context.user_data["username"]
    tipe = context.user_data["tipe"]
    expired = context.user_data.get("expired")
    hari = context.user_data.get("hari", "∞")
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role, expired) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), "user", expired)
        )
        conn.commit()
        conn.close()
        tipe_text = "Permanen ♾️" if tipe == "permanen" else f"Tidak Permanen ⏳ ({hari} hari)"
        await update.message.reply_text(
            f"✅ Akun berhasil dibuat!\n\n"
            f"👤 Username: {username}\n"
            f"🔑 Password: {password}\n"
            f"📋 Tipe: {tipe_text}\n"
            f"📅 Expired: {expired if expired else 'Tidak ada'}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {str(e)}")
    return ConversationHandler.END

async def list_users(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Kamu bukan owner!")
        return
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role, expired FROM users")
    users = cursor.fetchall()
    conn.close()
    if not users:
        await update.message.reply_text("Belum ada user!")
        return
    text = "📋 Daftar User:\n\n"
    for i, u in enumerate(users, 1):
        exp = u[2] if u[2] else "Permanen"
        text += f"{i}. {u[0]} ({u[1]}) - {exp}\n"
    await update.message.reply_text(text)

async def delete_start(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Kamu bukan owner!")
        return ConversationHandler.END
    await update.message.reply_text("🗑️ Masukkan username yang mau dihapus:")
    return TUNGGU_USERNAME

async def terima_delete(update, context):
    username = update.message.text.strip()
    if username == "owner":
        await update.message.reply_text("❌ Tidak bisa hapus akun owner!")
        return ConversationHandler.END
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if deleted:
        await update.message.reply_text(f"✅ User {username} berhasil dihapus!")
    else:
        await update.message.reply_text(f"❌ User {username} tidak ditemukan!")
    return ConversationHandler.END

async def addtime(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Kamu bukan owner!")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Format: /addtime username jumlah_hari\nContoh: /addtime john 7")
        return
    username = context.args[0]
    try:
        hari = int(context.args[1])
    except:
        await update.message.reply_text("❌ Jumlah hari harus angka!")
        return
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT expired FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if not user:
        await update.message.reply_text(f"❌ User {username} tidak ditemukan!")
        conn.close()
        return
    if user[0]:
        current = datetime.strptime(user[0], "%Y-%m-%d %H:%M:%S")
        if current < datetime.now():
            current = datetime.now()
    else:
        current = datetime.now()
    new_expired = (current + timedelta(days=hari)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users SET expired=? WHERE username=?", (new_expired, username))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Waktu akun {username} ditambah {hari} hari!\n"
        f"📅 Expired baru: {new_expired}"
    )

async def batal(update, context):
    await update.message.reply_text("❌ Dibatalkan!")
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).read_timeout(7).write_timeout(7).connect_timeout(7).pool_timeout(7).concurrent_updates(True).build()

create_handler = ConversationHandler(
    entry_points=[CommandHandler("create", create_start)],
    states={
        PILIH_TIPE: [CallbackQueryHandler(pilih_tipe)],
        TUNGGU_HARI: [MessageHandler(filters.TEXT & ~filters.COMMAND, terima_hari)],
        TUNGGU_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, terima_username)],
        TUNGGU_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, terima_password)],
    },
    fallbacks=[CommandHandler("batal", batal)]
)

delete_handler = ConversationHandler(
    entry_points=[CommandHandler("delete", delete_start)],
    states={
        TUNGGU_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, terima_delete)],
    },
    fallbacks=[CommandHandler("batal", batal)]
)


BOT2_TOKEN = "8666681681:AAEiRY4vacyOkyEWW2rUcVy9S6tHnSGCC8U"

async def approve(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Kamu bukan owner!")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Format: /approve buyer_id username password [expired]")
        return
    try:
        await update.message.delete()
    except:
        pass
    buyer_id = int(context.args[0])
    username = context.args[1]
    password = context.args[2]
    expired = None
    if len(context.args) >= 4:
        expired = context.args[3].replace("_", " ")
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role, expired) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), "user", expired)
        )
        conn.commit()
        # Ambil msg_id pembeli
        cursor.execute("SELECT msg_id FROM pending_orders WHERE buyer_id=? AND username=?", (buyer_id, username))
        row = cursor.fetchone()
        cursor.execute("DELETE FROM pending_orders WHERE buyer_id=? AND username=?", (buyer_id, username))
        conn.commit()
        conn.close()
        tipe_text = "Permanen ♾️" if not expired else "7 Hari ⏳"
        await update.message.reply_text(f"✅ Akun {username} berhasil dibuat!")
        # Edit pesan menunggu di bot2
        if row:
            from telegram import Bot
            bot2 = Bot(token=BOT2_TOKEN)
            try:
                await bot2.edit_message_text(
                    f"✅ *Pembayaran Dikonfirmasi!*\n\n"
                    f"Akun kamu sudah aktif!\n\n"
                    f"👤 Username: `{username}`\n"
                    f"🔑 Password: `{password}`\n"
                    f"📋 Tipe: {tipe_text}\n\n"
                    f"Terima kasih sudah berbelanja! 🎉",
                    chat_id=buyer_id,
                    message_id=row[0],
                    parse_mode="Markdown"
                )
            except:
                await bot2.send_message(
                    buyer_id,
                    f"✅ *Pembayaran Dikonfirmasi!*\n\n"
                    f"👤 Username: `{username}`\n"
                    f"🔑 Password: `{password}`\n"
                    f"📋 Tipe: {tipe_text}\n\n"
                    f"Terima kasih! 🎉",
                    parse_mode="Markdown"
                )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {str(e)}")

async def reject(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Kamu bukan owner!")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Format: /reject buyer_id [alasan]")
        return
    try:
        await update.message.delete()
    except:
        pass
    buyer_id = int(context.args[0])
    alasan = " ".join(context.args[1:]) if len(context.args) > 1 else "Pembayaran tidak ditemukan"
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT msg_id FROM pending_orders WHERE buyer_id=?", (buyer_id,))
        row = cursor.fetchone()
        cursor.execute("DELETE FROM pending_orders WHERE buyer_id=?", (buyer_id,))
        conn.commit()
        conn.close()
        from telegram import Bot
        bot2 = Bot(token=BOT2_TOKEN)
        if row:
            try:
                await bot2.edit_message_text(
                    f"❌ *Pembayaran Ditolak*\n\nAlasan: {alasan}\n\nKetik /start untuk coba lagi.",
                    chat_id=buyer_id,
                    message_id=row[0],
                    parse_mode="Markdown"
                )
            except:
                await bot2.send_message(buyer_id, f"❌ Pembayaran ditolak.\nAlasan: {alasan}")
        await update.message.reply_text("✅ Pembeli sudah diberi tahu!")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {str(e)}")

app.add_handler(create_handler)
app.add_handler(delete_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_users))
app.add_handler(CommandHandler("addtime", addtime))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("reject", reject))

print("Bot 1 Owner berjalan...")
app.run_polling()
