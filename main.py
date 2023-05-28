# TODO: add return type hints to ao3 api
from helper import *

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print('Logged in')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="You Read"))


@bot.event
async def on_guild_join(guild):
    reset_server(guild.id)  # ensure no old config exists


@bot.event
async def on_guild_leave(guild):
    reset_server(guild.id)  # clean out old config


@bot.command(description="Display information about a work from ao3, accepts an id, url, or any search query")
async def work(ctx: discord.ApplicationContext, query: discord.Option(str)):
    # TODO: support parsing chapter
    # TODO: add filter for single embed
    work = None
    try:
        if query.isnumeric():
            work = ao3.Work(query)
        elif ao3.Work.get_work_id_from_url(query) is not None:
            work = ao3.Work(ao3.Work.get_work_id_from_url(query))
    except ao3.AO3Exception:
        pass

    if work:

        if not ctx.channel.nsfw and (work.rating == 'Explicit' and setting(ctx.guild.id, 'restrict_explicit')) \
                or work.rating == 'Mature' and setting(ctx.guild.id, 'restrict_mature'):
            embed = discord.Embed(
                title="Prohibited Work",
                description=
                f"The work *{work.title}* is rated **{work.rating}**, which is not allowed to be posted outside "
                f"R18 channels.",
                color=discord.Colour.from_rgb(255, 255, 0),
            )
            embed.set_footer(text="(Server moderators can use the /config filters command to change this rule)")
            await ctx.respond(
                embed=embed,
                ephemeral=True
            )
            return

        embed = get_work_embed(work, ctx.user.id)

        # handle error generating embed
        if embed is Exception:
            await ctx.respond(
                embed=discord.Embed(
                    title="Error Generating Work Embed",
                    description=
                    "If you were expecting this to work, screenshot this message and send it to the developer:"
                    + f"\n*QUERY: {query}*\n*{embed}*",
                    color=discord.Colour.from_rgb(255, 0, 0),
                ),
                ephemeral=True
            )
            return
        elif embed is None:
            await ctx.respond(
                embed=discord.Embed(
                    title="Error Generating Work Embed",
                    description=
                    "Something broke really bad and we have no idea what or why. Sorry about that.",
                    color=discord.Colour.from_rgb(255, 255, 255)
                ),
                ephemeral=True
            )
            return

        await ctx.respond(
            embed=embed,
            ephemeral=False
        )
    else:  # perform search
        fandom = setting(ctx.guild.id, 'default_fandom')
        if fandom is None:
            fandom = ''
        works = ao3.Work.search(query=query, fandom_names=fandom)
        original_works_count = len(works)
        works = filter_works(ctx, works)
        if len(works) == 0:
            await ctx.respond(
                content=f'No results found for search: "{query}"',
                ephemeral=True,
                delete_after=15
            )
            return
        else:
            results = get_results_embed(ctx, query, works)
            """if filtered_count > 0:
                footer_content = f"{filtered_count} result{'' if filtered_count == 1 else 's'} hidden"
                results['embed'].set_footer(text=footer_content)"""
            await ctx.respond(
                embed=results['embed'],
                view=results['view'],
                ephemeral=True,
                delete_after=120
            )
            return


# create Slash Command group with bot.create_group
config = bot.create_group(name="config", description="Edit Server Settings")


@config.command(description="Name of fandom to automatically filter all searched works to")
async def default_fandom(
        ctx, fandom: discord.Option(str, "fandom name, exclude this field to remove", required=False, default='')):
    if fandom.strip() == '':
        await ctx.respond(f"Removed default fandom")
    else:
        tag = ao3.Tag(fandom)
        if tag is not None and tag.type.lower() == "fandom":
            setting(ctx.guild.id, 'default_fandom', tag.name)
            await ctx.respond(f"Updated default fandom to **{tag.name}** (<{tag.url}>)")
        else:
            await ctx.respond(f"Unable to find fandom **{fandom}**")


@config.command(description="allow/block certain content outside r18 channels")
async def filters(ctx,
                  rating: discord.Option(str, choices=['Mature', 'Explicit']),
                  block_type: discord.Option(str, choices=['Allow', 'R18 Only'])
                  ):
    setting(ctx.guild.id,
            {'Mature': 'restrict_mature', 'Explicit': 'restrict_explicit'}[rating],
            {'Allow': False, 'R18 Only': True}[block_type]
            )
    await ctx.respond(f'Updated rating **{rating}** to filter type **{block_type}**')


@config.command(description="promo channels automatically delete all messages that don't contain an ao3 link")
async def promo_channel(ctx: discord.ApplicationContext,
                         option: discord.Option(str, choices=['add', 'remove']),
                         channel: discord.Option(discord.TextChannel)
                         ):
    promo_channels = setting(ctx.guild.id, 'promo_channels')
    if option == 'add':
        if channel.id not in promo_channels:
            promo_channels.append(channel.id)
            response = f"Added <#{channel.id}> to promo channel list.\n"
            response += f"Promo Channels: {', '.join([f'<#{pcid}>' for pcid in promo_channels])}"
            await ctx.respond(response)
        else:
            response = f"Channel already in list.\n"
            response += f"Promo Channels: {', '.join([f'<#{pcid}>' for pcid in promo_channels])}"
            await ctx.respond(response)
    else:
        if channel.id in promo_channels:
            promo_channels.remove(channel.id)
            response = f"Removed <#{channel.id}> from promo channel list.\n"
            response += f"Promo Channels: {', '.join([f'<#{pcid}>' for pcid in promo_channels])}"
            await ctx.respond(response)
        else:
            response = f"Channel not in list.\n"
            response += f"Promo Channels: {', '.join([f'<#{pcid}>' for pcid in promo_channels])}"
            await ctx.respond(response)
    setting(ctx.guild.id, 'promo_channels', promo_channels)


@config.command(description='Reset all bot settings for this server, this cannot be undone')
async def reset_config(ctx: discord.ApplicationContext,
                       query: discord.Option(str, 'Use param "CONFIRM" if you are sure.', required=False, default='')):
    if query != 'CONFIRM':
        await ctx.respond(
            'YOU MUST RUN THIS COMMAND WITH THE PARAMETER "__CONFIRM__".\n'
            + 'REMEMBER, THIS CANNOT BE UNDONE. I DO NOT KEEP BACKUPS OF YOUR SETTINGS.'
        )
    else:
        reset_server(ctx.guild.id)
        await ctx.respond('SUCCESSFULLY RESET YOUR SERVER SETTINGS TO DEFAULT.')


@config.command(description="Dumps the raw configuration for this server")
async def debug_dump(ctx: discord.ApplicationContext):
    await ctx.respond(str(setting(ctx.guild.id)))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    is_promo_channel = message.channel.id in setting(message.guild.id, 'promo_channels')
    msg_words = message.content.split(" ")
    url = ""
    for word in msg_words:
        if "archiveofourown.org" in word:
            url = word
            break
    if url == "":
        if is_promo_channel:
            embed = discord.Embed(
                title="Work Link Required",
                description=
                f"Include an [AO3 Work Link]({ao3.baseURL}) in your message inside this promotional channel.",
                color=discord.Colour.from_rgb(255, 255, 0),
            )
            embed.set_footer(text=f"Triggered by <@{message.author.id}>")
            await message.reply(
                embed=embed,
                delete_after=10
            )
            await message.delete()
        return

    work = ao3.Work(ao3.Work.get_work_id_from_url(url))
    if (not message.channel.nsfw) \
            and ((work.rating == 'Explicit' and setting(message.guild.id, 'restrict_explicit'))
                 or (work.rating == 'Mature' and setting(message.guild.id, 'restrict_mature'))):
        embed = discord.Embed(
            title="Prohibited Work",
            description=
            f"The work *{work.title}* is rated **{work.rating}**, which is not allowed to be posted outside "
            f"R18 channels.",
            color=discord.Colour.from_rgb(255, 255, 0),
        )
        embed.set_footer(text="(Server moderators can use the /config filters command to change this rule)")
        await message.reply(
            embed=embed,
            delete_after=10
        )
        await message.delete()
        return

    work_embed = get_work_embed(work, message.author.id)
    await message.edit(suppress=True)
    await message.reply(embed=work_embed)


@bot.event
async def on_raw_reaction_add(reaction):
    channel = await bot.get_guild(reaction.guild_id).fetch_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)

    if message.author.id != bot.user.id:
        return

    if reaction.emoji.name in delete_emoji or 'doubt' in reaction.emoji.name.lower():
        try:
            user_id = int(message.embeds[0].footer.text.split('|')[-1].strip())
            if user_id == reaction.user_id:
                await message.delete()
            """else:
                await reaction."""
        except ValueError:
            return


bot.run(open('bot.config').read())
