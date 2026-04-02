import logging

from models import Comment, Like, Post, Reference, User, db, slugify

logger = logging.getLogger(__name__)


def _unique_slug(base_slug):
    slug = base_slug
    counter = 1
    while Post.query.filter_by(slug=slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


# --- User ---

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def register_user(username, email, password):
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info("Registered user %r", username)
    return user


def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return None
    if not user.check_password(password):
        return None
    return user


def get_user_by_id(user_id):
    return db.get_or_404(User, user_id)


# --- Post ---

def get_all_posts():
    return Post.query.order_by(Post.created_at.desc()).all()


def get_post_by_slug(slug):
    return Post.query.filter_by(slug=slug).first_or_404()


def create_post(author_id, title, body, summary=None):
    base_slug = slugify(title)
    slug = _unique_slug(base_slug)
    post = Post(
        author_id=author_id,
        title=title,
        slug=slug,
        body=body,
        summary=summary,
    )
    db.session.add(post)
    db.session.commit()
    logger.info("Created post slug=%r", slug)
    return post


def update_post(post_id, title, body, summary=None):
    post = db.get_or_404(Post, post_id)
    post.title = title
    post.body = body
    post.summary = summary
    db.session.commit()
    logger.info("Updated post id=%d", post_id)
    return post


# --- Comment ---

def get_comments(post_id):
    return (
        Comment.query
        .filter_by(post_id=post_id)
        .order_by(Comment.created_at)
        .all()
    )


def add_comment(post_id, author_id, body):
    comment = Comment(post_id=post_id, author_id=author_id, body=body)
    db.session.add(comment)
    db.session.commit()
    logger.info("Added comment to post id=%d", post_id)
    return comment


# --- Like ---

def toggle_like(user_id, post_id):
    existing = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    if existing is not None:
        db.session.delete(existing)
        db.session.commit()
        return False
    like = Like(user_id=user_id, post_id=post_id)
    db.session.add(like)
    db.session.commit()
    return True


def like_count(post_id):
    return Like.query.filter_by(post_id=post_id).count()


def user_has_liked(user_id, post_id):
    return Like.query.filter_by(user_id=user_id, post_id=post_id).first() is not None


# --- Reference ---

def add_reference(post_id, title, url):
    ref = Reference(post_id=post_id, title=title, url=url)
    db.session.add(ref)
    db.session.commit()
    logger.info("Added reference to post id=%d", post_id)
    return ref


def remove_reference(reference_id):
    ref = db.get_or_404(Reference, reference_id)
    db.session.delete(ref)
    db.session.commit()
