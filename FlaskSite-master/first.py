from flask import Flask,  render_template, redirect
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from forms.login import LoginForm
from forms.user import RegisterForm
from mysql.connector import Error
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'LKfkhds872w98feihw'
login_manager = LoginManager()
login_manager.init_app(app)


def create_connection(host_name, user_name, user_password, db_name):  # функции внешнего подключения к бд
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")


@app.route('/')
@app.route('/index')
def index():
    return render_template('base.html', title='Заголовок')


@app.route("/problems")
@login_required
def problems():
    try:
        if str(current_user).split(',')[0] == '9':
            connection = create_connection("141.8.192.151", "f0514491_ugmkbase", "UGMKbase", "f0514491_ugmkbase")
            select_users = "SELECT * FROM reports"
            lst_problem = execute_read_query(connection, select_users)
            lst_problem = [f'Сотрудник {user[1]} из {user[2]} уведомил о проблеме типа {user[3]}' for user in lst_problem]
        else:
            return redirect('/')

    except Error as e:
        print(e)
    return render_template("problems.html", list_prof=lst_problem)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/problems")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


if __name__ == '__main__':
    db_session.global_init("db/UGMK.db")
    app.run(debug=True)
