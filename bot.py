# bot.py
# Simple Telegram bot: collect texts -> export txt | merge txt files | split txt file by lines
# python-telegram-bot==21.6
#
# IMPORTANT:
# - Put your Telegram bot token in TOKEN below.
# - Do NOT publish this repository publicly if you keep the token in code.
# - If your token was shared anywhere, revoke it in @BotFather with /revoke and generate a new one.

import io
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "PUT_YOUR_TOKEN_HERE"  # ضع توكنك هنا

START_TEXT = """\
✅ بوت تحويل النصوص ودمج/تقسيم ملفات TXT (سهل)

📌 تحويل النص إلى ملف:
1) ارسل الأمر /x
2) ارسل النصوص اللي تريدها (رسالة أو عدة رسائل)
3) ارسل الأمر /a لتحويل كل النصوص إلى ملف TXT
4) ارسل الأمر /f لحذف النصوص والبدء من جديد

📌 دمج ملفات TXT:
1) ارسل الأمر /e
2) ارسل الملفات .txt المراد دمجها (عدة ملفات)
3) بعد ما تخلص ارسال ارسل الأمر /d لدمج الملفات وارسالها للمستخدم
4) ارسل الأمر /k لحذف الملفات المضافة للدمج والبدء من جديد

📌 تقسيم ملف TXT حسب عدد الأسطر:
1) ارسل الأمر /y 500   (مثال: 500 سطر لكل جزء)
2) ارسل الملف .txt المراد تقسيمه
3) سيصلك ملفات parts متعددة (بدون ضغط)

ملاحظة:
- أثناء /x إذا كتبت "A" لوحدها (بدون /) راح يعمل تصدير أيضاً.
"""


@dataclass
class State:
    # Text-to-file mode
    collecting_text: bool = False
    text_lines: List[str] = field(default_factory=list)

    # Merge mode
    merging: bool = False
    merge_files: List[List[str]] = field(default_factory=list)

    # Split mode
    splitting: bool = False
    split_size: int = 0  # lines per part


USER: Dict[int, State] = {}


def st(uid: int) -> State:
    if uid not in USER:
        USER[uid] = State()
    return USER[uid]


def normalize_text(text: str) -> List[str]:
    # للجلسة: نحذف الأسطر الفارغة
    lines = [ln.strip() for ln in (text or "").splitlines()]
    return [ln for ln in lines if ln]


def ensure_txt_filename(name: str, fallback: str) -> str:
    name = (name or "").strip()
    if not name:
        return fallback
    if not name.lower().endswith(".txt"):
        return fallback
    return name


def split_lines_keep_blanks(text: str) -> List[str]:
    # للتقسيم: نحافظ على كل الأسطر حتى الفارغة (كما بالملف)
    return (text or "").splitlines()


# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)


async def x_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)
    s.collecting_text = True
    s.merging = False
    s.splitting = False
    await update.message.reply_text("✅ تم تشغيل وضع جمع النصوص.\nأرسل النصوص الآن، ثم /a للتصدير أو /f للحذف.")


async def a_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)

    if not s.text_lines:
        await update.message.reply_text("لا توجد نصوص محفوظة. استخدم /x ثم أرسل النصوص.")
        return

    content = "\n".join(s.text_lines).strip() + "\n"
    buf = io.BytesIO(content.encode("utf-8"))
    buf.name = "output.txt"

    await update.message.reply_document(document=buf, filename="output.txt", caption="✅ تم تحويل النصوص إلى ملف TXT")


async def f_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)
    s.text_lines.clear()
    s.collecting_text = True
    s.merging = False
    s.splitting = False
    await update.message.reply_text("🧹 تم حذف النصوص. أرسل نصوص جديدة الآن، ثم /a للتصدير.")


async def e_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)
    s.merging = True
    s.collecting_text = False
    s.splitting = False
    s.merge_files.clear()
    await update.message.reply_text("🧩 تم تشغيل وضع دمج الملفات.\nأرسل ملفات .txt الآن، ثم /d للدمج أو /k للحذف.")


async def d_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)
    if not s.merging:
        await update.message.reply_text("وضع الدمج غير مفعل. ارسل /e أولاً.")
        return

    if not s.merge_files:
        await update.message.reply_text("لم ترسل ملفات بعد. أرسل ملفات .txt ثم /d.")
        return

    merged_lines: List[str] = []
    for file_lines in s.merge_files:
        merged_lines.extend(file_lines)

    content = "\n".join(merged_lines).strip() + "\n"
    buf = io.BytesIO(content.encode("utf-8"))
    buf.name = "merged.txt"

    await update.message.reply_document(
        document=buf,
        filename="merged.txt",
        caption=f"✅ تم دمج {len(s.merge_files)} ملف(ات)"
    )

    s.merging = False
    s.merge_files.clear()


async def k_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)
    s.merge_files.clear()
    s.merging = True
    s.collecting_text = False
    s.splitting = False
    await update.message.reply_text("🧹 تم حذف ملفات الدمج. أرسل ملفات .txt جديدة الآن، ثم /d للدمج.")


async def y_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/y 500  -> split next uploaded txt file into parts of 500 lines"""
    s = st(update.effective_user.id)
    parts = (update.message.text or "").split()

    if len(parts) < 2:
        await update.message.reply_text("استخدم الأمر هكذا:\n/y 500\n(يعني 500 سطر لكل جزء)")
        return

    try:
        n = int(parts[1])
    except ValueError:
        await update.message.reply_text("الرقم لازم يكون عدد صحيح.\nمثال: /y 500")
        return

    if n <= 0:
        await update.message.reply_text("الرقم لازم يكون أكبر من 0.\nمثال: /y 500")
        return

    if n > 200000:
        await update.message.reply_text("الرقم كبير جداً. استخدم رقم أصغر (مثلاً 500 أو 1000).")
        return

    s.splitting = True
    s.split_size = n
    s.collecting_text = False
    s.merging = False
    await update.message.reply_text(f"✂️ وضع التقسيم ON\nارسل الآن ملف .txt المراد تقسيمه إلى أجزاء كل جزء = {n} سطر.")


# ---------- Handlers ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)
    msg = (update.message.text or "").strip()

    if s.splitting:
        await update.message.reply_text("✂️ أنت في وضع التقسيم.\nأرسل ملف .txt فقط للتقسيم.")
        return

    if s.collecting_text and msg in ("A", "a"):
        return await a_cmd(update, context)

    if s.merging:
        await update.message.reply_text("🧩 أنت في وضع دمج الملفات.\nأرسل ملفات .txt فقط، ثم /d للدمج أو /k للحذف.")
        return

    if not s.collecting_text:
        await update.message.reply_text("ابدأ بـ /x لجمع النصوص أو /e لدمج الملفات أو /y <عدد> لتقسيم ملف.")
        return

    lines = normalize_text(msg)
    if not lines:
        await update.message.reply_text("أرسل نص واضح.")
        return

    s.text_lines.extend(lines)
    await update.message.reply_text(f"➕ تم حفظ {len(lines)} سطر(اً). (الإجمالي: {len(s.text_lines)})")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = st(update.effective_user.id)
    doc: Optional[Document] = update.message.document
    if not doc:
        return

    filename = ensure_txt_filename(doc.file_name, "")
    if not filename:
        await update.message.reply_text("أرسل ملف .txt فقط.")
        return

    f = await doc.get_file()
    b = await f.download_as_bytearray()
    text = b.decode("utf-8", errors="replace")

    # ====== SPLIT MODE ======
    if s.splitting:
        lines_all = split_lines_keep_blanks(text)
        if not lines_all:
            await update.message.reply_text("الملف فارغ.")
            s.splitting = False
            s.split_size = 0
            return

        n = s.split_size
        chunks = [lines_all[i:i+n] for i in range(0, len(lines_all), n)]

        # إرسال كل الأجزاء كملفات TXT (بدون ضغط مهما كان العدد)
        for idx, chunk in enumerate(chunks, start=1):
            content = "\n".join(chunk).rstrip("\n") + "\n"
            buf = io.BytesIO(content.encode("utf-8"))
            buf.name = f"part_{idx:03}.txt"
            await update.message.reply_document(
                document=buf,
                filename=f"part_{idx:03}.txt",
                caption=f"جزء {idx}/{len(chunks)}"
            )

        await update.message.reply_text(f"✅ تم تقسيم الملف إلى {len(chunks)} جزء (كل جزء {n} سطر).")

        s.splitting = False
        s.split_size = 0
        return

    # ====== MERGE MODE ======
    lines_norm = normalize_text(text)

    if s.merging:
        s.merge_files.append(lines_norm)
        await update.message.reply_text(f"📄 تم إضافة ملف للدمج. (عدد الملفات: {len(s.merge_files)})")
        return

    # ====== COLLECT TEXT MODE ======
    if not s.collecting_text:
        await update.message.reply_text("هذا ملف txt.\nللجمع كنص: ارسل /x أولاً.\nللدمج: /e\nللتقسيم: /y 500")
        return

    s.text_lines.extend(lines_norm)
    await update.message.reply_text(f"📄 تم إضافة {len(lines_norm)} سطر(اً) من الملف. (الإجمالي: {len(s.text_lines)})")


def main():
    if not TOKEN or "PUT_YOUR_TOKEN_HERE" in TOKEN:
        raise RuntimeError("ضع التوكن الصحيح داخل TOKEN.")

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("x", x_cmd))
    app.add_handler(CommandHandler("a", a_cmd))
    app.add_handler(CommandHandler("f", f_cmd))

    app.add_handler(CommandHandler("e", e_cmd))
    app.add_handler(CommandHandler("d", d_cmd))
    app.add_handler(CommandHandler("k", k_cmd))

    app.add_handler(CommandHandler("y", y_cmd))

    # Messages
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
