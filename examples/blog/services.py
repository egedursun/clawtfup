import logging

from models import Post, db

logger = logging.getLogger(__name__)


def get_all_posts():
    return Post.query.order_by(Post.created_at.desc()).all()


def get_post(post_id):
    return db.get_or_404(Post, post_id)


def create_post(title, body):
    post = Post(title=title, body=body)
    db.session.add(post)
    db.session.commit()
    logger.info("Created post id=%d", post.id)
    return post
