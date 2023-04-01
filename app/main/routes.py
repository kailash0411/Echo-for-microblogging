from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, CommentForm
from app.models import User, Post, Comment
from app.translate import translate
from app.main import bp

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    post_form = PostForm()
    if post_form.validate_on_submit():
        post = Post(body=post_form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is live now!')
        return redirect(url_for('main.view_post', post_id=post.id))
    posts = current_user.followed_posts()
    return render_template('index.html', title='Home', posts=posts, post_form=post_form)

@bp.route('/posts/<int:post_id>', methods=['GET'])
@login_required
def view_post(post_id):
    post = Post.query.get(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template('_post.html', post=post, comments=comments)

@bp.route('/posts', methods=['GET', 'POST'])
@login_required
def add_post():
    post_form = PostForm()
    if post_form.validate_on_submit():
        post = Post(body=post_form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is live now!')
        return redirect(url_for('main.add_post'))
    return render_template('_post.html')

@bp.route('/add_comment/<int:post_id>', methods=['GET','POST'])
@login_required
def add_comment(post_id):
    comment_form = CommentForm()
    post = Post.query.get(post_id)
    if comment_form.validate_on_submit():
        comment = Comment(content=comment_form.comment.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is live now!')
        return redirect(url_for('main.index'))
    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template('_post.html', post=post, comment_form=comment_form , comments=comments)
    
@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc())
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts, form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        if form.username.data != current_user.username:
            current_user.username = form.username.data
            db.session.commit()
        if current_user.about_me != form.about_me.data:
            current_user.about_me = form.about_me.data
            db.session.commit()
        return redirect(url_for('main.user', username=current_user.username))
           
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title="Edit Profile", form=form)

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f'User {username} not found')
            return redirect(url_for('main.index'))
        elif user == current_user:
            flash('You can not follow yourself')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are now following {username}')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))

@bp.route('/unfollow/<username>', methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f'User {username} not found')
            return redirect(url_for('main.index'))
        elif user == current_user:
            flash('You can not unfollow yourself')
            return redirect(url_for('main.user', username=username))   
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are no longer following {username}')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                          next_url=next_url, prev_url=prev_url)

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)