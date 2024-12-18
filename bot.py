import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from keep_alive import keep_alive

keep_alive()
# Enable logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# List of supported games
GAMES = [
    "Aether Gazer", "Genshin Impact", "Honkai Impact 3rd", "Honkai: Star Rail", "LifeAfter", 
    "Point Blank", "Punishing: Gray Raven", "Sausage Man", "Super Sus", "Valorant", "Zenless Zone Zero", 
    "Arena of Valor", "Call Of Duty", "Free Fire", "Mobile Legends: Bang Bang"
]

API_URLS = {
    "Aether Gazer": "/ag?id=", 
    "Genshin Impact": "/gi?id=", 
    "Honkai Impact 3rd": "/hi?id=", 
    "Honkai: Star Rail": "/hsr?id=", 
    "LifeAfter": "/la?id={id}&server={server}", 
    "Point Blank": "/pb?id=", 
    "Punishing: Gray Raven": "/pgr?id={id}&server={server}", 
    "Sausage Man": "/sm?id=", 
    "Super Sus": "/sus?id=", 
    "Valorant": "/valo?id=", 
    "Zenless Zone Zero": "/zzz?id=", 
    "Arena of Valor": "/aov?id=", 
    "Call Of Duty": "/cod?id=", 
    "Free Fire": "/ff?id=", 
    "Mobile Legends: Bang Bang": "/ml?id={id}&server={server}"
}

API_BASE_URL = "https://api.isan.eu.org/nickname"
FORCE_JOIN_GROUP = '@aybeechannel'  # Replace with your group username (e.g., @mygroup123)

async def is_user_in_group(user_id: int) -> bool:
    """Check if a user is in the required group."""
    try:
        member = await bot.get_chat_member(chat_id=FORCE_JOIN_GROUP, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking user in group: {e}")
        return False

async def force_to_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Force user to join the required group."""
    user_id = update.effective_user.id
    if not await is_user_in_group(user_id):
        keyboard = [
            [InlineKeyboardButton("Join Group", url=f"https://t.me/{FORCE_JOIN_GROUP[1:]}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the join message and store the message ID
        join_message = await update.message.reply_text(
            f"🚫 **Kindly join our group to access the bot's features.**\n👉 [Join Here](https://t.me/{FORCE_JOIN_GROUP[1:]})", 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Store the message ID so we can delete it later
        context.user_data['join_message_id'] = join_message.message_id
        return False
    else:
        # If the user is now a member, delete the join message (if it exists)
        join_message_id = context.user_data.get('join_message_id')
        if join_message_id:
            try:
                await update.message.bot.delete_message(chat_id=update.effective_chat.id, message_id=join_message_id)
            except Exception as e:
                logger.error(f"Error deleting join message: {e}")
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if not await force_to_join(update, context):
        return  # User must join the group first
    
    keyboard = [[InlineKeyboardButton(game, callback_data=game)] for game in GAMES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please select a game to check the user ID:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses for selecting a game."""
    query = update.callback_query
    await query.answer()
    game = query.data
    context.user_data['game'] = game
    await query.edit_message_text(text=f'You selected: {game}\nPlease enter the player ID (and server if required). Example: 123456789 (server if needed)')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user input for player ID and server."""
    if not await force_to_join(update, context):
        return  # User must join the group first
    
    user_input = update.message.text.split()
    game = context.user_data.get('game')
    if not game:
        await update.message.reply_text('Please select a game first using /start.')
        return
    
    player_id = user_input[0] if len(user_input) > 0 else None
    server = user_input[1] if len(user_input) > 1 else None
    
    if not player_id:
        await update.message.reply_text('Please provide a valid player ID.')
        return
    
    try:
        if "{id}" in API_URLS[game] and "{server}" in API_URLS[game]:
            endpoint = API_URLS[game].format(id=player_id, server=server if server else "")
        elif "{id}" in API_URLS[game]:
            endpoint = API_URLS[game].format(id=player_id)
        else:
            endpoint = API_URLS[game] + player_id
        
        response = requests.get(API_BASE_URL + endpoint)
        result = response.json()
        
        if result.get('success'):
            message = f"✅ Success!\n\nGame: {result.get('game')}\nID: {result.get('id')}\nServer: {result.get('server')}\nName: {result.get('name')}"
        else:
            message = f"❌ Error: {result.get('message')}"
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await update.message.reply_text("❌ Failed to check the ID. Please try again later.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Use /start to check a player ID for supported games.')

def main() -> None:
    """Start the bot."""
    global bot
    application = ApplicationBuilder().token("7541354470:AAE0-R-NzuRBhlN97owEixaeBj_VfKoCkm4").build()  # Replace 'YOUR_BOT_TOKEN' with your bot token
    bot = application.bot  # Initialize the bot instance
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("help", help_command))
    
    application.run_polling()

if __name__ == '__main__':
    main()
