from flask import Flask
from flask import render_template
from flask import request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz #for timezones
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
db=SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db.init_app(app)
app.app_context().push()
app.secret_key = "for_encryption_decryption_purposes"
app.config['UPLOAD_FOLDER'] = 'static'
#database models

class user(db.Model):
  __tabename__= 'user'
  user_id=db.Column(db.Integer, primary_key=True ,autoincrement=True)
  user_name=db.Column(db.String, unique=True, nullable=False)
  password=db.Column(db.String, nullable=False)

class blog(db.Model):
  __tablename__='blog'
  blog_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
  blog_title=db.Column(db.String, unique=True, nullable=False)
  blog_content=db.Column(db.String, nullable=False)
  blog_imagepath=db.Column(db.String)
  blog_timestamp=db.Column(db.String, nullable=False)
  blog_author=db.Column(db.String, nullable=False)
  

class followers_list(db.Model):
  __tablename__='followers_list'
  follow_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
  being_followed=db.Column(db.Integer, db.ForeignKey(user.user_id))
  follower=db.Column(db.Integer, db.ForeignKey(user.user_id))

db.create_all()


#CONTROLLERS

@app.route('/',methods=["GET","POST"])
def login():
  if request.method == "GET" :
    return render_template('login.html')
  elif request.method == "POST" :
    u_name=request.form['name']
    pwd=request.form['password']
    user_data=user.query.filter(user.user_name == u_name and user.password == pwd).first()
    if user_data != None :
      session["user"] = u_name
      return redirect(url_for('index'))
    else:
      return "<p>Username or password is incorrect.</p> <br> <a href='/'>Try again?</a> "



@app.route('/register',methods=["GET","POST"])
def register():
  if request.method == "GET" :
    return render_template('register.html')
  elif request.method == "POST" :
    user_data=user.query.all()
    user_names=[user.user_name for user in user_data]
    if request.form['name'] not in user_names :
      if request.form['password'] == request.form['confirm_password'] :
        new_user=user(user_name=request.form['name'],password=request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        return "<p>new user registered</p>  <br> <a href='/'> login page</a>"
      else:
        return "<p>make sure both the passwords are same</p> <br> <a href='/register'>Try a different password</a>"
    else:
      return "<p>Username is already taken.</p> <br> <a href='/register'>Try a different user name</a>"


@app.route('/home')
def index():
  if "user" in session :
    blogs=blog.query.order_by(blog.blog_timestamp.desc()).all()
    blog_authors = user.query.all()
    current_user = user.query.filter(user.user_name == session["user"]).first()
    return render_template('home.html',blog_data=blogs, blog_authors=blog_authors, user = current_user)
  else:
    return redirect(url_for('login'))

@app.route('/create_blog',methods=["GET","POST"])
def blog_creation():
  if "user" in session :
    if request.method == "GET" :
      cur_user = user.query.filter(user.user_name == session["user"]).first()
      return render_template('create_blog.html', user=cur_user)
    elif request.method == "POST" :
      title=request.form['title']
      content=request.form['content']
      time_now=datetime.now(pytz.timezone('Asia/Calcutta'))
      formatted_datetime = time_now.strftime("%d/%m/%Y %H:%M")
      img=request.files['image']
      img_path=""
      if img.filename != '' :
        imgfile = secure_filename(img.filename)
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], imgfile))
        img_path=(os.path.join(app.config['UPLOAD_FOLDER'], imgfile))
      new_blog=blog(blog_title=title, blog_content=content, blog_imagepath=img_path, blog_timestamp=formatted_datetime, blog_author=session["user"])
      db.session.add(new_blog)
      db.session.commit()
      return "<p>blog posted successfully</p>  <br> <a href='/home'> Home</a>"
  else:
    return redirect(url_for('login'))

@app.route('/edit_blog/<int:blog_id>', methods=["GET","POST"])
def blog_editing(blog_id):
  if "user" in session :
    if request.method == "GET" :
      cur_user = user.query.filter(user.user_name == session["user"]).first()
      cur_blog = blog.query.filter(blog.blog_id == blog_id).first()
      return render_template('edit_blog.html', blog = cur_blog, user=cur_user)
    elif request.method == "POST" :
      cur_blog = blog.query.filter(blog.blog_id == blog_id).first()
      cur_blog.blog_title = request.form['title']
      cur_blog.blog_content = request.form['content']
      time_now=datetime.now(pytz.timezone('Asia/Calcutta'))
      formatted_datetime = time_now.strftime("%d/%m/%Y %H:%M")
      cur_blog.blog_timestamp = formatted_datetime
      del_imagepath = cur_blog.blog_imagepath
      os.remove(del_imagepath)
      img=request.files['image']
      img_path=""
      if img.filename != '' :
        imgfile = secure_filename(img.filename)
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], imgfile))
        img_path=(os.path.join(app.config['UPLOAD_FOLDER'], imgfile))
      cur_blog.blog_imagepath = img_path
      db.session.add(cur_blog)
      db.session.commit()
      return redirect(url_for('index'))
  else :
    return redirect(url_for('login'))
      
@app.route('/delete_blog/<int:blog_id>')
def delete_blog(blog_id):
  del_blog = blog.query.filter(blog.blog_id == blog_id).first()
  del_imagepath = del_blog.blog_imagepath
  os.remove(del_imagepath)
  db.session.delete(del_blog)
  db.session.commit()
  return redirect(url_for('index'))
    

@app.route('/profile/<int:u_id>')
def profile(u_id):
  if "user" in session :
    cur_user=user.query.filter(user.user_id == u_id).first() 
    user_blogs=blog.query.filter(blog.blog_author == cur_user.user_name).all()
    following=followers_list.query.filter(followers_list.follower == cur_user.user_id).all()
    following_id=[follow.being_followed for follow in following]
    followers=followers_list.query.filter(followers_list.being_followed == cur_user.user_id).all()
    return render_template('profile.html', authors_blog=user_blogs, following=len(following), followers=len(followers), following_id=following_id, user=cur_user ,post_count = len(user_blogs))
  else:
    return redirect(url_for('login'))


@app.route('/search',methods=["GET","POST"])
def search():
  if "user" in session :  
    if request.method == "GET" :
      current_user = user.query.filter(user.user_name == session["user"]).first()
      return render_template('search.html', cur_user= current_user)
    elif request.method == "POST" :
      word=request.form["search"]
      word = word + "%"
      searched_users=user.query.filter(user.user_name.like(word)).all()
      current_user = user.query.filter(user.user_name == session["user"]).first()
      cr_usr_following = followers_list.query.filter(followers_list.follower == current_user.user_id).all()
      cr_usr_following_id = [u.being_followed for u in cr_usr_following]
      return render_template('search_results.html', search_results = searched_users, following_deets = cr_usr_following_id , cur_user = current_user)
  else:
    return redirect(url_for('login'))

@app.route('/follow/<int:u_id>')
def follow(u_id):
  if "user" in session :
    current_user=user.query.filter(user.user_name == session["user"]).first()
    follower_id=current_user.user_id
    follow = followers_list(being_followed = u_id, follower=follower_id)
    db.session.add(follow)
    db.session.commit()
    return redirect(url_for('index'))
  else:
    return redirect(url_for('login'))

@app.route('/unfollow/<int:u_id>')
def unfollow(u_id):
  if "user" in session :
    current_user=user.query.filter(user.user_name == session["user"]).first()
    follower_id = current_user.user_id
    unfollow=followers_list.query.filter(followers_list.being_followed == u_id and followers_list.follower == follower_id).first()
    db.session.delete(unfollow)
    db.session.commit()
    return redirect(url_for('index'))
  else:
    return redirect(url_for('login'))


@app.route('/followers/<int:u_id>')
def followers(u_id):
  if "user" in session :
    #current user info
    cur_user = user.query.filter(user.user_name == session['user']).first()
    cur_usr_following =followers_list.query.filter(followers_list.follower == cur_user.user_id).all()
    following_id = [f.being_followed for f in cur_usr_following]
    #followers info
    follows = followers_list.query.filter(followers_list.being_followed == u_id).all()
    followers_id = [f.follower for f in follows]
    user_profile = user.query.filter(user.user_id == u_id).first()
    followers_details =[]
    for id in followers_id :
      id_details = user.query.filter(user.user_id == id).first()
      followers_details.append(id_details)
    return render_template('followers.html', followers_deets = followers_details , cur_user = cur_user, followers_id = followers_id, following_id = following_id, user_profile = user_profile)
  else:
    return redirect(url_for('login'))
  
@app.route('/following/<int:u_id>')
def following(u_id):
  if "user" in session :
    cur_user = user.query.filter(user.user_name == session['user']).first()
    following = followers_list.query.filter(followers_list.follower == u_id).all()
    following_id = [f.being_followed for f in following]
    user_profile = user.query.filter(user.user_id == u_id).first()
    following_details = []
    for id in following_id :
      id_details = user.query.filter(user.user_id == id).first()
      following_details.append(id_details)
    return render_template('following.html', following_deets = following_details , cur_user = cur_user, user_profile = user_profile)
  else:
    return redirect(url_for('login'))
  


@app.route('/logout')
def logout():
  if "user" in session :
    session.pop("user")
  return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)


