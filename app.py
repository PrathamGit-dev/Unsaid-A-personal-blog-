from flask import Flask, render_template, request, flash, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json
from datetime import datetime
import pymysql
from werkzeug.utils import redirect
import math

pymysql.install_as_MySQLdb()

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    author = db.Column(db.String(20), nullable=False)
    tagline = db.Column(db.String(12), nullable=True)


@app.route("/post/<string:slug>", methods=['GET'])
def post_route(slug):
    post = Posts.query.filter_by(slug=slug).first()

    return render_template('post.html', params=params, post=post)


@app.route("/about")
def about():
    post = Posts.query.filter_by(sno=15).first()
    return render_template('about.html', params=params, post=post)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts) / int(params['max_post']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    length = len(posts)
    maximum = int(params['max_post'])
    k = length - ((page - 1) * 3) - 1
    if k - maximum < 0:
        posts = posts[k::-1]
    else:
        posts = posts[k:k - maximum:-1]

    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    if "user" in session and session['user'] == params['admin_user']:
        return render_template('index2.html', params=params, posts=posts, prev=prev, next=next)
    else:
        return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if "user" in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        posts = posts[::-1]

        return render_template("dashboard.html", params=params, posts=posts)
    else:
        return redirect("/signin")


@app.route("/signin", methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        usernam = request.form.get('uname')
        upass = request.form.get('upass')
        if usernam == params['admin_user'] and upass == params['admin_pass']:
            session['user'] = usernam
            return redirect("/dashboard")
        else:
            return redirect("/")
    return render_template("signin.html", params=params)


@app.route("/index", methods=['GET', 'POST'])
def index():
    posts = Posts.query.all()
    if "user" in session and session['user'] == params['admin_user']:
        return render_template("index2.html", params=params, posts=posts)
    else:
        return render_template("index.html", params=params, posts=posts)


@app.route("/add", methods=['GET', 'POST'])
def add():
    # print(sno)
    if "user" in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            # if request.method == 'POST':
            # print("entered")
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            author = request.form.get('author')
            date = datetime.now()
            post = Posts(title=box_title, slug=slug, content=content, tagline=tagline, date=date, author=author)
            db.session.add(post)
            db.session.commit()
            return redirect("/post/" + slug)
        return render_template("add.html", params=params)

    return redirect("/signin")


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if "user" in session and session['user'] == params['admin_user']:
        post = Posts.query.get(sno)
        if request.method == 'POST':
            post.title = request.form.get('title')
            post.tagline = request.form.get('tagline')
            post.slug = request.form.get('slug')
            post.content = request.form.get('content')
            post.author = request.form.get('author')
            # img_file = request.form.get('img_file')
            post.date = datetime.now()
            db.session.commit()
            flash('Post edited', 'success')
            return redirect('/post/' + post.slug)
        return render_template('edit.html', params=params, post=post, sno=sno)
    else:
        return redirect("/signin")


@app.route("/delete/<string:sno>")
def delete(sno):
    post = Posts.query.get(sno)
    db.session.delete(post)
    db.session.commit()
    return redirect("/dashboard")


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + phone
                          )
    return render_template('contact.html', params=params)


app.run(debug=True)
