import logging

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

import services

logger = logging.getLogger(__name__)

bp = Blueprint("posts", __name__)


def _current_user_id():
    return session.get("user_id")


@bp.route("/")
def index():
    posts = services.get_all_posts()
    return render_template("index.html", posts=posts)


@bp.route("/posts/<slug>")
def detail(slug):
    post = services.get_post_by_slug(slug)
    comments = services.get_comments(post.id)
    likes = services.like_count(post.id)
    user_id = _current_user_id()
    liked = services.user_has_liked(user_id, post.id) if user_id is not None else False
    return render_template(
        "post.html", post=post, comments=comments, likes=likes, liked=liked
    )


@bp.route("/posts/new", methods=["GET", "POST"])
def new_post():
    user_id = _current_user_id()
    if user_id is None:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        summary = request.form.get("summary") or None
        post = services.create_post(
            author_id=user_id, title=title, body=body, summary=summary
        )
        ref_titles = request.form.getlist("ref_title")
        ref_urls = request.form.getlist("ref_url")
        for ref_title, ref_url in zip(ref_titles, ref_urls):
            if ref_title and ref_url:
                services.add_reference(post_id=post.id, title=ref_title, url=ref_url)
        return redirect(url_for("posts.detail", slug=post.slug))
    return render_template("new_post.html")


@bp.route("/posts/<slug>/edit", methods=["GET", "POST"])
def edit_post(slug):
    post = services.get_post_by_slug(slug)
    user_id = _current_user_id()
    if user_id is None or user_id != post.author_id:
        abort(403)
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        summary = request.form.get("summary") or None
        services.update_post(post_id=post.id, title=title, body=body, summary=summary)
        return redirect(url_for("posts.detail", slug=slug))
    return render_template("edit_post.html", post=post)


@bp.route("/posts/<slug>/comments", methods=["POST"])
def add_comment(slug):
    user_id = _current_user_id()
    if user_id is None:
        return redirect(url_for("auth.login"))
    post = services.get_post_by_slug(slug)
    body = request.form["body"]
    services.add_comment(post_id=post.id, author_id=user_id, body=body)
    return redirect(url_for("posts.detail", slug=slug))


@bp.route("/posts/<slug>/like", methods=["POST"])
def toggle_like(slug):
    user_id = _current_user_id()
    if user_id is None:
        return redirect(url_for("auth.login"))
    post = services.get_post_by_slug(slug)
    services.toggle_like(user_id=user_id, post_id=post.id)
    return redirect(url_for("posts.detail", slug=slug))
