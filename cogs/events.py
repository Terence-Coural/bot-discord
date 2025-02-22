import discord
from discord.ext import commands
import urllib.parse

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Build associated channel name
    def associatedChannelName(
            self,
            event: discord.ScheduledEvent
        ) -> str:
        date_event: str = event.start_time.strftime("%m-%d")
        raw_name_channel: str = f'{date_event}_{event.name}'
        name_channel: str = raw_name_channel.lower().replace(' ', '-')
        return name_channel

    # Get associated channel with ID inside description link
    def getAssociatedChannelID(
            self,
            event: discord.ScheduledEvent
        ) -> int:
        event_desc = event.description
        desc, infos, discord_url = event_desc.partition("\nPlus d'infos : ")
        path = urllib.parse.urlparse(discord_url).path

        # Split left URL sections (ex: /channels/XXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXX)
        # Mid part = ID server
        # Last part = ID channel
        id_channel: int = path.split('/')[3]
        return id_channel

    # Get text channel associated to event
    def associatedChannel(
            self,
            event: discord.ScheduledEvent
        ) -> discord.TextChannel:
        id_channel = int(self.getAssociatedChannelID(event))
        associated_channel = discord.utils.get(event.guild.text_channels, id=id_channel)
        return associated_channel

    # Send a msg to associated channel
    async def associatedChannelEmbedMsg(
            self,
            associated_channel: discord.TextChannel,
            title: str,
            description: str,
            color
        ):
        embed_msg = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        await associated_channel.send(embed=embed_msg)

    # Sort a channel inside a category
    async def sortAssociatedTextChannel(self, category: discord.CategoryChannel, channel: discord.TextChannel):
        originList = category.text_channels
        min_pos: int = originList[0].position
        print(f'Min position = {min_pos}')
        if len(originList) < 1:
            print(f'No previous event')
            return
        else:
            sorted_list = sorted(originList, key=lambda x: x.name)
            print(f'Origin list : {originList}\n\n')
            print(f'Sorted list : {sorted_list}\n\n')

            # Get index of new position in sorted list
            for index, sortedChannel in enumerate(sorted_list):
                print(index, sortedChannel)
                if sortedChannel.name == channel.name:
                    new_pos_index = index
                    print(f'New position is set to {new_pos_index}')

            # Move channel to new position
            await channel.move(beginning=True, offset=new_pos_index, category=category)

    #Create automatically a new text channel when a scheduled event is created
    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):

        # Get infos for text channel creation & event edition
        events_cat = event.guild.get_channel(self.bot.events_channel_id)
        name_channel = self.associatedChannelName(event)

        # Create new text channel for events
        new_channel = await event.guild.create_text_channel(
            name_channel,
            category=events_cat,
            topic=event.url,
            nsfw=True
        )

        # Sort new channel in category
        await self.sortAssociatedTextChannel(events_cat, new_channel)

        # Add a channel link into event description
        link_txt: str = f'\nPlus d\'infos : {new_channel.jump_url}'
        max_size: int = 1000 - len(link_txt)
        suffix: str = '…'
        if len(event.description) < max_size:
            event_description: str = event.description + link_txt
        else:
            event_description_trunc: str = ' '.join(event.description[:max_size + 1].split(' ')[0:-1]) + suffix
            event_description: str = event_description_trunc + link_txt
        await event.edit(description=event_description)

        # Add log into logs channel defined
        member = event.guild.get_member(event.creator_id)
        logs_channel = event.guild.get_channel(self.bot.logs_channel_id)
        logs_desc: str = f'{member.display_name} a créé un événement !'
        embed_log = discord.Embed(title="Création d'un événement", description=logs_desc, color=0x9b59b6)
        embed_log.add_field(name="global_name", value=member.global_name, inline=True)
        embed_log.add_field(name="discord_name", value=event.creator, inline=True)
        embed_log.add_field(name="Événement", value=event.name, inline=False)
        embed_log.add_field(name="URL", value=event.url, inline=False)
        embed_log.add_field(name="Lien du canal associé", value=new_channel.jump_url, inline=False)
        await logs_channel.send(embed=embed_log)


    #Logs when event is deleted
    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):

        # Get event associated text channel & send a msg
        event_txt_channel = self.associatedChannel(event)
        await self.associatedChannelEmbedMsg(
            event_txt_channel,
            f"Suppression de l'événement {event.name}",
            f"L'événement {event.name} a été annulé !",
            0x9b59b6 #purple
        )

        # Add log into logs channel defined
        logs_channel = event.guild.get_channel(self.bot.logs_channel_id)
        embed_log = discord.Embed(title="Suppression d'un événement", color=0x9b59b6)
        embed_log.add_field(name="Événement", value=event.name, inline=False)
        embed_log.add_field(name="Lien du canal associé", value=event_txt_channel.jump_url, inline=False)
        await logs_channel.send(embed=embed_log)
    
    
    #Change channels URL & name when event is edited
    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):

        # Event's title or date is modified
        if (before.status == discord.EventStatus.scheduled) & (after.status == discord.EventStatus.scheduled):
            
            # Check if title or start time date change
            if (before.name != after.name) | (before.start_time != after.start_time):

                # Get old txt channel object, edit new text channel name & sort it in category
                event_txt_channel: discord.TextChannel = self.associatedChannel(before)
                new_txt_channel_name: str = self.associatedChannelName(after)
                events_cat = before.guild.get_channel(self.bot.events_channel_id)
                modifiedChannel = await event_txt_channel.edit(name=new_txt_channel_name)
                print(f'{modifiedChannel}\n\n')
                await self.sortAssociatedTextChannel(events_cat, modifiedChannel)

                # Get new txt channel & send it msg
                await self.associatedChannelEmbedMsg(
                    event_txt_channel,
                    f"Modification de l'événement {before.name}",
                    f"L'événement {before.name} a été modifié {'en ' + after.name if before.name != after.name else ''}.\nVérifiez bien la date et l'heure de l'événement !",
                    0x9b59b6 #purple
                )

                # Add log into logs channel defined
                logs_channel = before.guild.get_channel(self.bot.logs_channel_id)
                embed_log = discord.Embed(title="Modification d'un événement", color=0x9b59b6)
                embed_log.add_field(name="Événement", value=before.name, inline=False)
                embed_log.add_field(name="Lien du canal associé", value=event_txt_channel.jump_url, inline=False)
                await logs_channel.send(embed=embed_log)

        # Event is ended
        elif (before.status == discord.EventStatus.active) & (after.status == discord.EventStatus.ended):

            # Get event associated text channel & send a msg
            event_txt_channel = self.associatedChannel(before)
            await self.associatedChannelEmbedMsg(
                event_txt_channel,
                f"Fin de l'événement {before.name}",
                f"L'événement {before.name} est fini !",
                0x9b59b6 #purple
            )

            # Add log into logs channel defined
            logs_channel = before.guild.get_channel(self.bot.logs_channel_id)
            embed_log = discord.Embed(title="Fin d'un événement", color=0x9b59b6)
            embed_log.add_field(name="Événement", value=before.name, inline=False)
            embed_log.add_field(name="Lien du canal associé", value=event_txt_channel.jump_url, inline=False)
            await logs_channel.send(embed=embed_log)

# Add cog to bot
async def setup(bot):
    await bot.add_cog(EventsCog(bot))