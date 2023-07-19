from typing import List

import discord
import ao3
import textwrap
from setting_manager import *

__rating_emoji = {
    "General Audiences": "🟩",
    "Teen And Up Audiences": "🟨",
    "Mature": "🟧",
    "Explicit": "🟥",
    "Not Rated": "⬜",
}
__category_emoji = {}
delete_emoji = '❌✖❎'
settings = {}


def filter_works(ctx: discord.ApplicationContext, works) -> List:
    if ctx.channel.nsfw:
        return works.to_list()

    filtered_works = []
    for work in works:
        if len(filtered_works) == 20:
            break

        if (work.rating == 'Explicit' and setting(ctx.guild.id, 'restrict_explicit')) \
                or work.rating == 'Mature' and setting(ctx.guild.id, 'restrict_mature'):
            continue
        filtered_works.append(work)
    return filtered_works


def get_work_embed(work: ao3.Work, chapter: ao3.Chapter = None, user_id=None):
    try:
        # author, title, url
        work_authors = "by " + ', '.join([f'[{author.name}]({author.url})' for author in work.authors])
        description = f"*{work_authors}*\n" \
                      + f"{__rating_emoji[work.rating]} {work.rating}\n" \
                      + f"*{', '.join(work.archive_warnings)}*"
        work_embed = discord.Embed(title=work.title, description=description, url=work.url)

        # chapter
        if chapter is not None:
            chapter_text = f'[{chapter.name}]({chapter.url})'
            if chapter.summary:
                chapter_text += f' | Summary: ||{textwrap.shorten(chapter.summary, width=1000, placeholder="...",)}||'

            work_embed.add_field(
                name=f"Chapter {chapter.number}",
                value=chapter_text,
                inline=False
            )

        # fandoms
        fandoms = " | ".join([f'[{tag.name}]({tag.url}/works)' for tag in work.fandoms])
        if len(fandoms):
            work_embed.add_field(
                name="Fandoms",
                value=textwrap.shorten(
                    fandoms,
                    width=1000,
                    placeholder="...",
                ),
                inline=False)

        # relationships
        relationships = " | ".join([f'[{tag.name}]({tag.url}/works)' for tag in work.relationships])
        if len(relationships):
            work_embed.add_field(
                name="Relationships",
                value=textwrap.shorten(
                    relationships,
                    width=1000,
                    placeholder="...",
                ),
                inline=False)

        # other characters (don't list characters already included in relationship tags)
        other_characters = ""
        for character in [f'[{tag.name}]({tag.url}/works)' for tag in work.characters]:
            if character not in relationships:
                other_characters += character + " | "
        if len(other_characters):
            work_embed.add_field(
                name=f"{'Other ' if len(relationships) else ''}Characters",
                value=other_characters[0:len(other_characters) - 2],
                inline=False
            )

        # tags
        tags = " | ".join([f'[{tag.name}]({tag.url}/works)' for tag in work.tags])
        if len(tags):
            work_embed.add_field(
                name="Tags",
                value=textwrap.shorten(
                    tags,
                    width=1000,
                    placeholder="...",
                ),
                inline=False)

        # summary
        work_embed.add_field(
            name="Summary",
            value=textwrap.shorten(
                work.summary if work.summary else "(no summary)",
                width=1000,
                placeholder="...",
            ),
            inline=False)

        # footer
        footer_content = \
            f"Words: {work.words} | " + \
            f"Chapters: {work.chapter_count}/{'?' if work.chapter_max is None else work.chapter_max} | " + \
            f"Kudos: {work.kudos} | Bookmarks: {work.bookmarks} | Hits: {work.hits}"

        dates = "\n"
        if work.published is not None:
            dates += f" | Published on: {str(work.published)[:10]}"
        if work.updated is not None:
            dates += f" | Updated on: {str(work.updated)[:10]}"
        footer_content += dates

        if user_id is not None:
            footer_content += "\n\nReact with ❌ to delete this embed | " + str(user_id)

        work_embed.set_footer(text=footer_content)
        work_embed.set_thumbnail(url=work.authors[0].pfp)
        return work_embed
    except Exception as e:
        print(e)
        return e


def get_results_embed(ctx, query: str, works: List, count=None):
    # create embed
    if count is None:
        count = len(works)
    embed = discord.Embed(
        title="Search Results",
        description=f"{count} results for {query}"
    )

    # create options
    work_options = []

    for i, work in enumerate(works):
        work_authors = "by " + ', '.join([author.name for author in work.authors])
        work_options.append(
            discord.SelectOption(
                label=textwrap.shorten(
                    f"{i + 1}. {work.title} {work_authors}",
                    width=95,
                    placeholder="...",
                ),
                emoji=__rating_emoji[work.rating],
                value=str(work.work_id),
                description=textwrap.shorten(
                    "" if work.summary is None else work.summary,
                    width=95,
                    placeholder="...",
                )
            )
        )

    class Select(discord.ui.Select):
        def __init__(self):
            options = work_options
            super().__init__(
                placeholder="Select an option",
                min_values=1,
                max_values=1,
                options=options
            )

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            work_id = int(self.values[0])
            await ctx.respond(
                embed=get_work_embed(ao3.Work(work_id), ctx.user.id)
            )
            return

    class SelectView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.add_item(Select())

    return {
        'embed': embed,
        'view': SelectView()
    }
