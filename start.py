import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from keep_alive import keep_alive

# Load env variables
load_dotenv()
token: str = os.getenv('DISCORD_TOKEN')
logs_channel_id: int = os.getenv('LOGS_CHANNEL_ID')
events_channel_id: int = os.getenv('EVENTS_CHANNEL_ID')

class MyBot(commands.Bot):

    # Get all cogs
    async def setup_hook(self):
        for extension in ['events']:
            await self.load_extension(f'cogs.{extension}')

    # Check Discord version & that bot is ready
    async def on_ready(self) -> None:
        print(f"Discord version : {discord.__version__}")
        print("La Secrétaire est prête pour son service !")

    # Get channel ID from ENV to logs events
    async def get_log_channel_id() -> int:
        return logs_channel_id

# To use only few intents
intents = discord.Intents.default()
# intents.presences = True
intents.members = True
intents.message_content = True
# intents.guilds = True
intents.guild_scheduled_events = True

bot = MyBot(command_prefix='!', intents=intents)
bot.logs_channel_id = int(logs_channel_id)
bot.events_channel_id = int(events_channel_id)

def main():
    #Launch the bot
    keep_alive()
    bot.run(token=token)

if __name__ == '__main__':
    main()