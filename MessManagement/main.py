import base64
import calendar
import json
from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from datetime import date
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# CONNECT TO DB

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mess.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

admin = Admin(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# arr = ['static/images/1.jpg', 'static/images/2.jpg', 'static/images/3.jpg', 'static/images/4.jpg']


##CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    mis = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    menu_selections = relationship("UserMenuSelect", back_populates="menu_users")


db.create_all()


# admin.add_view(ModelView(User, db.session))


class Menu(db.Model):
    __tablename__ = "menus"
    id = db.Column(db.Integer, primary_key=True)
    dishName = db.Column(db.String(100))
    dishpicture = db.Column(db.LargeBinary)
    mealcategory = db.Column(db.String(100))
    price = db.Column(db.Integer)
    date_created = db.Column(db.Date, default=datetime.date.today)


db.create_all()


# admin.add_view(ModelView(Menu, db.session))


class Admin(db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    adminid = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

db.create_all()


class UserMenuSelect(db.Model):
    __tablename__ = "UserMenuSelect"
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.String(250), nullable=False)
    itemsQuantity = db.Column(db.String(250), nullable=False)
    month = db.Column(db.String(250), nullable=False)
    date = db.Column(db.Date, default=datetime.date.today)
    price = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_users = relationship("User", back_populates="menu_selections")


db.create_all()


@app.route('/')
def home():
    return render_template("loginindex.html", logged_in=current_user.is_authenticated)


@app.route('/addmenu', methods=['GET', 'POST'])
def addmenu():
    if request.method == 'POST':
        file = request.files['file']

        upload = Menu(
            dishName=request.form.get('dishname'),
            dishpicture=file.read(),
            mealcategory=request.form.get('mealcategory'),
            price=request.form.get('price')
        )

        db.session.add(upload)
        db.session.commit()
        return redirect(url_for('filter_meals'))

    return render_template('addmenu.html')


@app.route('/images', methods=['GET', 'POST'])
def filter_meals():
    # Retrieve the selected meal category and date from the form data
    meal_category = request.form.get('mealcategory')
    date = request.form.get('date')
    query = Menu.query.filter(and_(Menu.mealcategory == meal_category, Menu.date_created == date))

    # Query the database to filter meals based on the selected criteria

    # Render the HTML template with the filtered meals and return it as a response
    return render_template('imageAddmore.html', filteredImages=query)


@app.route('/getbill', methods=['GET', 'POST'])
def get_bill():
    if request.method == "POST":
        filter_ = request.form.get('date')
        print(filter_)
        # query = Menu.query.filter(UserMenuSelect.month == filter_)
        mbf = db.session.query(func.sum(UserMenuSelect.price)).filter(and_(UserMenuSelect.items == 'mbf',
                                                                           or_(UserMenuSelect.month == filter_,
                                                                               UserMenuSelect.date == filter_),
                                                                           UserMenuSelect.user_id == current_user.id)).scalar()
        ebf = db.session.query(func.sum(UserMenuSelect.price)).filter(and_(UserMenuSelect.items == 'ebf',
                                                                           or_(UserMenuSelect.month == filter_,
                                                                               UserMenuSelect.date == filter_),
                                                                           UserMenuSelect.user_id == current_user.id)).scalar()
        dinner = db.session.query(func.sum(UserMenuSelect.price)).filter(and_(UserMenuSelect.items == 'dinner',
                                                                              or_(UserMenuSelect.month == filter_,
                                                                                  UserMenuSelect.date == filter_),
                                                                              UserMenuSelect.user_id == current_user.id)).scalar()
        lunch = db.session.query(func.sum(UserMenuSelect.price)).filter(and_(UserMenuSelect.items == 'lunch',
                                                                             or_(UserMenuSelect.month == filter_,
                                                                                 UserMenuSelect.date == filter_),
                                                                             UserMenuSelect.user_id == current_user.id)).scalar()
        mbf = mbf or 0
        ebf = ebf or 0
        dinner = dinner or 0
        lunch = lunch or 0
        return render_template('bill.html', filter_=filter_, current_user=current_user, mbf=mbf, ebf=ebf, dinner=dinner,
                               lunch=lunch)

    return render_template('generatebill.html', current_user=current_user)


@app.route('/images')
def get_images():
    images = Menu.query.all()
    return render_template('imageAddmore.html', images=images)


@app.template_filter('b64encode')
def b64encode_filter(s):
    if s:
        return base64.b64encode(s).decode('utf-8')
    else:
        return ""


@app.route('/menu', methods=["GET", "POST"])
def menu():
    allmenu = Menu.query.all()
    studata = json.load(open("static/StudataSYTY.json", 'r', encoding="utf-8"))
    username = studata[str(current_user.mis)]["Student Name"]
    today = date.today()
    day_month_year = today.strftime("%d %B, %Y")

    # Store the data in the database
    if request.method == "POST":
        menu_selections = Menu.query.filter_by(mealcategory=request.form.get('menu_selection')).filter(Menu.date_created==date.today())
        menu_cat = request.form.get('menu_selection')
        item_names = request.form.getlist('item')
        items_Quantity = [value for value in request.form.getlist('quantity') if value]
        print(items_Quantity)
        print(item_names)
        prices = request.form.getlist('prices')
        print(prices)
        for name, quantity, price in zip(item_names, items_Quantity, prices):
            selected_menu = UserMenuSelect(items=name, itemsQuantity=int(quantity),
                                           month=calendar.month_name[date.today().month],
                                           price=int(price) * int(quantity),
                                           user_id=current_user.id)
            db.session.add(selected_menu)
            # date=calendar.month_name[date.today().month]

        db.session.commit()
        return render_template("index.html", username=username, logged_in=True, menu_cat=menu_cat,
                               menu_selections=menu_selections, day_month_year=day_month_year)

    return render_template("index.html", username=username, logged_in=True, allmenu=allmenu)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(mis=request.form.get('mis')).first():
            # User already exists
            flash("You've already signed up with that mis, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        mis = request.form.get('mis')

        studata = json.load(open("static/StudataSYTY.json", 'r', encoding="utf-8"))
        if mis in studata:
            new_user = User(
                mis=mis,
                name=request.form.get('name'),
                password=hash_and_salted_password,
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('menu'))
        return render_template("loginindex.html")

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mis = request.form.get('mis')
        password = request.form.get('password')

        user = User.query.filter_by(mis=mis).first()
        # mis doesn't exist or password incorrect.
        if not user:
            flash("That mis does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('menu'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/admin', methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        adminid = request.form.get('adminid')
        print(adminid)
        password = request.form.get('password')

        user = Admin.query.filter_by(adminid=adminid).first()
        # mis doesn't exist or password incorrect.
        if not user:
            flash("That admin does not exist, please try again.")
            return redirect(url_for('admin'))
        elif not (user.password == password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('get_images'))

    return render_template("admin.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    total = db.session.query(func.sum(UserMenuSelect.price)).scalar()
    todaytotal = db.session.query(func.sum(UserMenuSelect.price)).filter((UserMenuSelect.date == date.today())).scalar()
    if request.method == "POST":
        filter_ = request.form.get('cat')

        print(filter_)
        cats = db.session.query(UserMenuSelect, User.mis, User.name).join(User,
                                                                          UserMenuSelect.user_id == User.id).filter(
            and_(UserMenuSelect.items == filter_, UserMenuSelect.date == date.today())).all()
        cats = cats or 0
        print(cats)
        return render_template('dashboard.html', total=total, todaytotal=todaytotal, cats=cats)

    return render_template('dashboard.html', total=total, todaytotal=todaytotal)


@app.route('/aboutus')
def about_us():
    return render_template('aboutus.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
