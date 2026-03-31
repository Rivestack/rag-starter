import html
import logging
import time
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select, text as sql_text

from app.database import async_session
from app.models import Story, Chunk

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ssr"])

BASE_URL = "https://ask.rivestack.io"


def _esc(text: str) -> str:
    """Escape for safe HTML output."""
    return html.escape(text)


def _format_date(dt: datetime) -> str:
    return dt.strftime("%B %d, %Y")


async def _fetch_related(story_id: str, limit: int = 5) -> dict:
    """Returns {"stories": [...], "query_time_ms": float, "chunks_searched": int}."""
    try:
        async with async_session() as session:
            count_result = await session.execute(
                sql_text("SELECT COUNT(*) FROM chunks WHERE chunk_type = 'title'")
            )
            chunks_searched = count_result.scalar() or 0

            start = time.time()
            result = await session.execute(
                sql_text("""
                    SELECT
                        s.slug, s.title, s.author, s.score, s.created_at,
                        1 - (c.embedding <=> ref.embedding) AS similarity_score
                    FROM chunks c
                    JOIN stories s ON c.story_id = s.id
                    CROSS JOIN (
                        SELECT embedding FROM chunks
                        WHERE story_id = :story_id AND chunk_type = 'title' LIMIT 1
                    ) ref
                    WHERE c.chunk_type = 'title' AND s.id != :story_id
                      AND 1 - (c.embedding <=> ref.embedding) > 0.3
                    ORDER BY c.embedding <=> ref.embedding
                    LIMIT :limit
                """),
                {"story_id": story_id, "limit": limit},
            )
            query_time_ms = (time.time() - start) * 1000

            stories = [
                {
                    "slug": r.slug,
                    "title": r.title,
                    "author": r.author,
                    "score": r.score,
                    "date": r.created_at.strftime("%B %d, %Y"),
                    "similarity": round(float(r.similarity_score) * 100),
                }
                for r in result.fetchall()
            ]
            return {"stories": stories, "query_time_ms": round(query_time_ms, 1), "chunks_searched": chunks_searched}
    except Exception as e:
        logger.error(f"SSR related stories failed: {e}")
        return {"stories": [], "query_time_ms": 0, "chunks_searched": 0}


@router.get("/story/{slug}", response_class=HTMLResponse)
async def ssr_story_page(slug: str, request: Request):
    """Serve a pre-rendered HTML page for story URLs.

    This gives Googlebot real content to index without waiting for JS rendering.
    The SPA JavaScript will hydrate and take over for interactive users.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Story).where(Story.slug == slug)
        )
        story = result.scalar_one_or_none()

        if not story:
            return HTMLResponse(
                content=_not_found_html(),
                status_code=404,
            )

        chunks_result = await session.execute(
            select(Chunk.content, Chunk.chunk_type, Chunk.author)
            .where(Chunk.story_id == story.id)
            .order_by(Chunk.created_at)
        )
        chunks = chunks_result.fetchall()

    related_data = await _fetch_related(str(story.id))
    related = related_data["stories"]
    related_time_ms = related_data["query_time_ms"]
    chunks_searched = related_data["chunks_searched"]

    # Get total stories count for the footer
    async with async_session() as session:
        total_stories = (await session.execute(sql_text("SELECT COUNT(*) FROM stories"))).scalar() or 0
        total_chunks = (await session.execute(sql_text("SELECT COUNT(*) FROM chunks"))).scalar() or 0

    comments = [c for c in chunks if c.chunk_type == "comment"]
    story_text = next((c for c in chunks if c.chunk_type == "story_text"), None)

    hn_url = f"https://news.ycombinator.com/item?id={story.hn_id}"
    page_url = f"{BASE_URL}/story/{story.slug}"
    title = _esc(story.title)
    comment_word = "comment" if story.num_comments == 1 else "comments"
    description = _esc(
        f"{story.title} — {story.score} points by {story.author}, "
        f"{story.num_comments} {comment_word}. Discussion from Hacker News."
    )

    # Build comment HTML
    comments_html = ""
    if comments:
        items = []
        for c in comments:
            author_html = f'<p class="comment-author">{_esc(c.author)}</p>' if c.author else ""
            items.append(
                f'<div class="comment">{author_html}'
                f'<p class="comment-body">{_esc(html.unescape(c.content))}</p></div>'
            )
        comments_html = (
            '<section class="comments">'
            f'<h2>Discussion Highlights ({len(comments)} comments)</h2>'
            + "".join(items)
            + "</section>"
        )

    # Build story text HTML
    story_text_html = ""
    if story_text:
        story_text_html = (
            f'<section class="story-text">'
            f'<p>{_esc(html.unescape(story_text.content))}</p>'
            f'</section>'
        )

    # Build related stories HTML
    related_html = ""
    if related:
        items = []
        for r in related:
            items.append(
                f'<li><a href="/story/{_esc(r["slug"])}">{_esc(r["title"])}</a>'
                f' <span class="meta">{_esc(r["author"])} · {r["score"]} pts · {r["date"]}'
                f' · {r["similarity"]}% similar</span></li>'
            )
        related_html = (
            '<section class="related">'
            '<h2>Related Discussions</h2>'
            f'<p class="meta">Found {len(related)} related stories in {related_time_ms}ms '
            f'across {chunks_searched:,} title embeddings via pgvector HNSW</p>'
            f'<ul>{"".join(items)}</ul>'
            '</section>'
        )

    # Build JSON-LD comment array
    import json as _json
    jsonld_comments = ""
    if comments:
        comment_items = []
        for c in comments:
            item = {
                "@type": "Comment",
                "text": html.unescape(c.content),
            }
            if c.author:
                item["author"] = {
                    "@type": "Person",
                    "name": c.author,
                    "url": f"https://news.ycombinator.com/user?id={c.author}",
                }
            comment_items.append(item)
        jsonld_comments = ',\n  "comment": ' + _json.dumps(comment_items, ensure_ascii=False)

    # Build external link
    ext_link = ""
    if story.url:
        try:
            from urllib.parse import urlparse
            domain = urlparse(story.url).hostname or story.url
            ext_link = f'<a href="{_esc(story.url)}" rel="noopener">{_esc(domain)}</a> · '
        except Exception:
            pass

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Ask HN | Rivestack</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{page_url}">
<link rel="icon" type="image/svg+xml" href="{BASE_URL}/logo.svg">
<meta property="og:type" content="article">
<meta property="og:url" content="{page_url}">
<meta property="og:title" content="{title} — Ask HN">
<meta property="og:description" content="{description}">
<meta property="og:site_name" content="Rivestack">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title} — Ask HN">
<meta name="twitter:description" content="{description}">
<meta name="robots" content="index, follow">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "DiscussionForumPosting",
  "headline": "{title}",
  "text": "{_esc(story_text.content if story_text else story.title)}",
  "url": "{page_url}",
  "author": {{"@type": "Person", "name": "{_esc(story.author)}", "url": "https://news.ycombinator.com/user?id={_esc(story.author)}"}},
  "datePublished": "{story.created_at.isoformat()[:19]}Z",
  "interactionStatistic": [
    {{"@type": "InteractionCounter", "interactionType": "https://schema.org/LikeAction", "userInteractionCount": {story.score}}},
    {{"@type": "InteractionCounter", "interactionType": "https://schema.org/CommentAction", "userInteractionCount": {story.num_comments}}}
  ],
  "isPartOf": {{"@type": "WebSite", "name": "Ask HN", "url": "{BASE_URL}"}}{jsonld_comments}
}}
</script>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px 16px; color: #1a1a1a; line-height: 1.6; }}
a {{ color: #1936FE; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
h1 {{ font-size: 1.5rem; line-height: 1.3; margin-bottom: 8px; }}
.meta {{ color: #666; font-size: 0.85rem; }}
.header-meta {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }}
.comment {{ padding: 12px 0; border-bottom: 1px solid #e5e5e5; font-size: 0.9rem; }}
.comment:last-child {{ border-bottom: none; }}
.comment-author {{ font-size: 0.75rem; font-weight: 500; color: #666; margin: 0 0 4px 0; }}
.comment-body {{ margin: 0; }}
.story-text {{ background: #f0f4ff; border-radius: 8px; padding: 16px; margin: 16px 0; font-size: 0.9rem; }}
.related ul {{ list-style: none; padding: 0; }}
.related li {{ padding: 8px 12px; border: 1px solid #e5e5e5; border-radius: 8px; margin-bottom: 6px; }}
.related li a {{ font-weight: 500; }}
.cta {{ text-align: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e5e5; font-size: 0.85rem; color: #666; }}
.nav {{ margin-bottom: 24px; font-size: 0.85rem; }}
</style>
</head>
<body>
<nav class="nav"><a href="/">← Ask HN — Semantic Search</a></nav>
<article>
<h1>{title}</h1>
<div class="header-meta">
<span>{_esc(story.author)}</span>
<span>{story.score} points</span>
<span>{story.num_comments} {comment_word}</span>
<span>{_format_date(story.created_at)}</span>
</div>
<div class="meta">{ext_link}<a href="{hn_url}" rel="noopener">View on Hacker News</a></div>
{story_text_html}
{comments_html}
{related_html}
</article>
<div class="cta">
Semantic search powered by <a href="https://rivestack.io"><strong>Rivestack pgvector</strong></a>
<br><span class="meta">{total_stories:,} stories · {total_chunks:,} chunks indexed</span>
</div>
</body>
</html>"""

    return HTMLResponse(content=page_html)


@router.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    """Serve sitemap at /sitemap.xml on the public domain."""
    async with async_session() as session:
        result = await session.execute(
            select(Story.slug, Story.created_at)
            .order_by(Story.created_at.desc())
        )
        stories = result.fetchall()

    urls = [
        f'  <url>\n    <loc>{BASE_URL}/</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>'
    ]
    for row in stories:
        urls.append(
            f'  <url>\n'
            f'    <loc>{BASE_URL}/story/{row.slug}</loc>\n'
            f'    <lastmod>{row.created_at.isoformat()[:10]}</lastmod>\n'
            f'    <changefreq>monthly</changefreq>\n'
            f'    <priority>0.7</priority>\n'
            f'  </url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls) + '\n'
        '</urlset>\n'
    )
    return Response(content=xml, media_type="application/xml")


def _not_found_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Story Not Found — Ask HN | Rivestack</title>
<meta name="robots" content="noindex">
<style>
body {{ font-family: system-ui, sans-serif; text-align: center; padding: 80px 16px; color: #1a1a1a; }}
a {{ color: #1936FE; }}
</style>
</head>
<body>
<h1>Story not found</h1>
<p>This story may have been removed or the URL is incorrect.</p>
<a href="{BASE_URL}/">Back to search</a>
</body>
</html>"""
