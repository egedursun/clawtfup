import logging

from flask import Blueprint, redirect, render_template, request, session, url_for

import services

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        if services.get_user_by_username(username) is not None:
            return render_template("register.html", error="Username already taken.")
        user = services.register_user(username=username, email=email, password=password)
        session["user_id"] = user.id
        session["username"] = user.username
        return redirect(url_for("posts.index"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = services.authenticate_user(username=username, password=password)
        if user is None:
            return render_template("login.html", error="Invalid username or password.")
        session["user_id"] = user.id
        session["username"] = user.username
        return redirect(url_for("posts.index"))
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("posts.index"))
