"""
TG Saver Bot - download videos from Telegram
"""

import os
import re
import logging
from pathlib import Path
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from parser import parse_filename, ParseResult
from downloader import download_by_message
from dotenv import load_dotenv
load_dotenv()
import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

NL = chr(10)
WAIT_CATEGORY, WAIT_CONFIRM, WAIT_EDIT_TITLE, WAIT_EDIT_SEASON, WAIT_EDIT_EPISODE, WAIT_CUSTOM_FOLDER = range(6)
user_sessions = {}


def _check_user(update):
    if not config.ALLOWED_USERS:
        return True
    return update.effective_user.id in config.ALLOWED_USERS


def _get_category_keyboard():
    buttons = []
    for cat in config.CATEGORIES:
        emoji = config.CATEGORY_EMOJI.get(cat, "")
        buttons.append([InlineKeyboardButton(f"{emoji} {cat}", callback_data=f"cat:{cat}")])
    return InlineKeyboardMarkup(buttons)


def _get_confirm_keyboard():
    buttons = [
        [InlineKeyboardButton("确认下载", callback_data="confirm:yes"),
         InlineKeyboardButton("修改名称", callback_data="confirm:edit")],
        [InlineKeyboardButton("改类型", callback_data="confirm:category"),
         InlineKeyboardButton("取消", callback_data="confirm:cancel")],
    ]
    return InlineKeyboardMarkup(buttons)


def _get_edit_keyboard():
    buttons = [
        [InlineKeyboardButton("改标题", callback_data="edit:title"),
         InlineKeyboardButton("改季数", callback_data="edit:season")],
        [InlineKeyboardButton("改集数", callback_data="edit:episode"),
         InlineKeyboardButton("完成修改", callback_data="edit:done")],
    ]
    return InlineKeyboardMarkup(buttons)

async def _do_save(update, context, session):
    query = update.callback_query
    parsed = session["parsed"]
    file_id = session["file_id"]
    file_name = session.get("file_name", "video.mp4")

    # Determine folder
    cat = parsed.category
    if cat == "其他":
        folder_name = session.get("custom_folder", "未分类")
        save_dir = config.DOWNLOAD_DIR / folder_name
    elif cat in ("电视剧", "动漫"):
        save_dir = config.DOWNLOAD_DIR / cat / parsed.folder_name
        if parsed.season:
            save_dir = save_dir / f"Season {parsed.season:02d}"
    else:
        save_dir = config.DOWNLOAD_DIR / cat / parsed.folder_name

    save_dir.mkdir(parents=True, exist_ok=True)

    # Use original filename or parsed stem
    ext = Path(file_name).suffix or ".mp4"
    save_path = save_dir / (parsed.file_stem + ext)

    # Avoid overwrite
    if save_path.exists():
        for i in range(1, 100):
            alt = save_dir / f"{parsed.file_stem} ({i}){ext}"
            if not alt.exists():
                save_path = alt
                break

    await query.edit_message_text(f"正在下载 {file_name}...")

    try:
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_drive(str(save_path))
        size_mb = save_path.stat().st_size / 1024 / 1024
        result = [
            "下载完成！",
            f"类型: {cat}",
            f"路径: {save_path.relative_to(config.DOWNLOAD_DIR)}",
            f"大小: {size_mb:.1f} MB",
        ]
        await query.edit_message_text(NL.join(result))
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await query.edit_message_text(f"下载失败: {e}")

    user_sessions.pop(update.effective_user.id, None)

async def start(update, context):
    if not _check_user(update):
        return
    await update.message.reply_text(
        "TG Saver Bot" + NL + NL +
        "转发视频给我，自动识别并下载到指定文件夹。" + NL +
        "直接转发视频消息即可开始"
    )


async def handle_video(update, context):
    if not _check_user(update):
        await update.message.reply_text("无权限")
        return

    user_id = update.effective_user.id
    message = update.message
    video = message.video or message.document
    if not video:
        await update.message.reply_text("请发送视频文件")
        return

    file_id = video.file_id
    file_name = getattr(video, "file_name", None) or f"video_{message.message_id}.mp4"
    caption = message.caption or ""
    file_size = getattr(video, "file_size", 0)
    size_mb = file_size / 1024 / 1024 if file_size else 0

    parsed = parse_filename(file_name, caption)

    # Track forward info for Pyrogram download
    forward_chat_id = None
    forward_msg_id = None
    if hasattr(message, 'forward_origin') and message.forward_origin:
        origin = message.forward_origin
        if hasattr(origin, 'chat'):
            chat = origin.chat
            # Channels need -100 prefix for Pyrogram
            forward_chat_id = chat.id
            if forward_chat_id > 0:
                forward_chat_id = int(f"-100{forward_chat_id}")
            forward_msg_id = origin.message_id

    user_sessions[user_id] = {
        "file_id": file_id,
        "file_name": file_name,
        "caption": caption,
        "parsed": parsed,
        "forward_chat_id": forward_chat_id,
        "forward_msg_id": forward_msg_id,
    }

    info = [
        f"收到视频: {file_name}",
        f"大小: {size_mb:.1f} MB",
        f"识别: {parsed}",
        "",
        "请选择视频类型:",
    ]
    await update.message.reply_text(NL.join(info), reply_markup=_get_category_keyboard())
    return WAIT_CATEGORY

async def category_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await query.edit_message_text("会话已过期，请重新发送视频")
        return ConversationHandler.END

    cat = query.data.split(":")[1]
    session["parsed"].category = cat

    # If 其他, ask for custom folder name
    if cat == "其他":
        await query.edit_message_text("请输入文件夹名称:")
        return WAIT_CUSTOM_FOLDER

    parsed = session["parsed"]
    info = [f"类型: {cat}", f"标题: {parsed.title}"]
    if parsed.year: info.append(f"年份: {parsed.year}")
    if parsed.season: info.append(f"季: S{parsed.season:02d}")
    if parsed.episode: info.append(f"集: E{parsed.episode:02d}")
    info.append("")
    info.append("确认下载吗？")
    await query.edit_message_text(NL.join(info), reply_markup=_get_confirm_keyboard())
    return WAIT_CONFIRM


async def custom_folder(update, context):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await update.message.reply_text("会话已过期")
        return ConversationHandler.END

    folder_name = update.message.text.strip()
    if not folder_name:
        await update.message.reply_text("文件夹名不能为空，请重新输入:")
        return WAIT_CUSTOM_FOLDER

    session["custom_folder"] = folder_name
    parsed = session["parsed"]

    info = [
        f"类型: 其他",
        f"文件夹: {folder_name}",
        f"标题: {parsed.title}",
    ]
    if parsed.year: info.append(f"年份: {parsed.year}")
    info.append("")
    info.append("确认下载吗？")

    await update.message.reply_text(NL.join(info), reply_markup=_get_confirm_keyboard())
    return WAIT_CONFIRM

async def confirm_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await query.edit_message_text("会话已过期")
        return ConversationHandler.END

    action = query.data.split(":")[1]
    if action == "cancel":
        user_sessions.pop(user_id, None)
        await query.edit_message_text("已取消")
        return ConversationHandler.END
    elif action == "category":
        await query.edit_message_text("重新选择类型:", reply_markup=_get_category_keyboard())
        return WAIT_CATEGORY
    elif action == "edit":
        parsed = session["parsed"]
        info = [f"当前标题: {parsed.title}"]
        info.append("选择要修改的内容:")
        await query.edit_message_text(NL.join(info), reply_markup=_get_edit_keyboard())
        return WAIT_CONFIRM
    elif action == "yes":
        await _do_save(update, context, session)
        return ConversationHandler.END
    return WAIT_CONFIRM

async def edit_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await query.edit_message_text("会话已过期")
        return ConversationHandler.END
    action = query.data.split(":")[1]
    if action == "done":
        parsed = session["parsed"]
        info = [f"类型: {parsed.category}", f"标题: {parsed.title}"]
        info.append("确认下载吗？")
        await query.edit_message_text(NL.join(info), reply_markup=_get_confirm_keyboard())
        return WAIT_CONFIRM
    elif action == "title":
        await query.edit_message_text("请输入新标题:")
        context.user_data["editing"] = "title"
        return WAIT_EDIT_TITLE
    elif action == "season":
        await query.edit_message_text("请输入季数:")
        context.user_data["editing"] = "season"
        return WAIT_EDIT_SEASON
    elif action == "episode":
        await query.edit_message_text("请输入集数:")
        context.user_data["editing"] = "episode"
        return WAIT_EDIT_EPISODE
    return WAIT_CONFIRM


async def edit_title(update, context):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await update.message.reply_text("会话已过期")
        return ConversationHandler.END
    new_title = update.message.text.strip()
    session["parsed"].title = new_title
    await update.message.reply_text(f"标题已改为: {new_title}", reply_markup=_get_edit_keyboard())
    return WAIT_CONFIRM


async def edit_season(update, context):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await update.message.reply_text("会话已过期")
        return ConversationHandler.END
    text = update.message.text.strip()
    try:
        season = int(text)
        session["parsed"].season = season
        await update.message.reply_text(f"季数已改为: S{season:02d}", reply_markup=_get_edit_keyboard())
    except ValueError:
        await update.message.reply_text("请输入数字")
        return WAIT_EDIT_SEASON
    return WAIT_CONFIRM


async def edit_episode(update, context):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        await update.message.reply_text("会话已过期")
        return ConversationHandler.END
    text = update.message.text.strip()
    try:
        episode = int(text)
        session["parsed"].episode = episode
        session["parsed"].is_episode = True
        await update.message.reply_text(f"集数已改为: E{episode:02d}", reply_markup=_get_edit_keyboard())
    except ValueError:
        await update.message.reply_text("请输入数字")
        return WAIT_EDIT_EPISODE
    return WAIT_CONFIRM

async def cancel(update, context):
    user_id = update.effective_user.id
    user_sessions.pop(user_id, None)
    await update.message.reply_text("已取消")
    return ConversationHandler.END


def main():
    if not config.BOT_TOKEN:
        print("请设置 BOT_TOKEN 环境变量")
        return

    # Create download dirs
    for cat in config.CATEGORIES:
        if cat != "其他":
            (config.DOWNLOAD_DIR / cat).mkdir(parents=True, exist_ok=True)

    # Configure proxy and local API
    builder = Application.builder().token(config.BOT_TOKEN)
    if config.LOCAL_API_URL:
        builder = builder.base_url(config.LOCAL_API_URL).local_mode(True)
    elif config.PROXY_URL:
        builder = builder.proxy(config.PROXY_URL).get_updates_proxy(config.PROXY_URL)
    app = builder.build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video)
        ],
        states={
            WAIT_CATEGORY: [CallbackQueryHandler(category_callback, pattern="^cat:")],
            WAIT_CONFIRM: [
                CallbackQueryHandler(confirm_callback, pattern="^confirm:"),
                CallbackQueryHandler(edit_callback, pattern="^edit:"),
            ],
            WAIT_EDIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_title)],
            WAIT_EDIT_SEASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_season)],
            WAIT_EDIT_EPISODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_episode)],
            WAIT_CUSTOM_FOLDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_folder)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    # Set bot commands menu
    from telegram import BotCommand
    async def post_init(app):
        await app.bot.set_my_commands([
            BotCommand("start", "开始使用"),
        ])
    app.post_init = post_init
    
    print("TG Saver Bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
