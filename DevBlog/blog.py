from flask import Flask, render_template, flash, redirect, url_for,session,logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

#user login decorator
def login_required(f): # it's the decorator which provides security to the functions. If an operation must be done after login, this decorator must be added to the function.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ("logged_in" in session): # if session["looged_in"] is true, it means user already logged in.
            return f(*args, **kwargs)
        else:  #Else, flash pops up and system redirects user to login
            flash("Please login to see this page", "danger")
            return redirect (url_for("login"))
    return decorated_function



# user register form
class RegisterForm(Form):
    name = StringField("Name Surname:", validators=[validators.length(min = 4, max = 25), validators.DataRequired(message= "Please fill in the blank")]) # minimum 4 maximum 25 chars must be entered, data is required
    username = StringField("Username:", validators=[validators.length(min = 4, max = 35), validators.DataRequired(message= "Please fill in the blank")]) # minimum 4 maximum 35 chars must be entered, data is required
    email = StringField("Email Adress:", validators=[validators.Email(message= "Please enter valid e-mail adress")]) # checks whether it is email or not
    password = PasswordField("Password:", validators=[ # The password input will be encrypted by using PasswordField class
        validators.DataRequired(message= "Please enter a password."), 
        validators.EqualTo(fieldname = "confirm", message="Password doesn't match") # system checks whether the inputs are same with variable entered in fieldname by using EqualTo method.
    ])
    confirm = PasswordField("Confirm password:")

# user login form
class LoginForm(Form):
    username = StringField("Username:", validators=[validators.length(min = 4, max = 35), validators.DataRequired("Please enter a username")])
    password = PasswordField("Password:", validators=[validators.DataRequired("Please enter password")])

# Article form
class ArticleForm(Form):
    title = StringField("Article title:", validators=[validators.length(min = 5, max = 30)])
    content = TextAreaField("Article content", validators=[validators.length(min=10)])



app = Flask(__name__)
app.secret_key = "devblog" # secret key is required, so we can create some random secret key.

app.config["MYSQL_HOST"] = "localhost" # server host is given
app.config["MYSQL_USER"] = "root" 
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app) #connection created between flask and MySQL

@app.route("/") #main page
def index():
    return render_template("index.html")


@app.route("/about") #about page
def about():
    return render_template("about.html")

#Register
@app.route("/register", methods = ["GET", "POST"]) # each time we load the website, two kinds of request can be done, get and post. If we take data from db, it is get request, if we put or update data from the db, it is post request.
def register():
    form = RegisterForm(request.form)
    print(form)
    if (request.method == "POST" and form.validate() == True): # if it is post request and all the requirements are satisfied in the form (validate), it will be redirected to the page with "about" extension.
        name = form.name.data # data entered to the name input is taken. And other inputs are taken too.
        username = form.username.data
        email = form.email.data
        password =  sha256_crypt.encrypt(form.password.data) # password is encrypted and put to the database. Just for security.

        cursor = mysql.connection.cursor() # cursor is created for sql
        ask = "INSERT INTO USERS(name, email,username, password) VALUES(%s,%s,%s,%s)" 
        cursor.execute(ask, (name, email, username, password)) # data is put to the db.

        mysql.connection.commit()  # important -> if you insert or, generally, change anything in the database, this function must be used.

        cursor.close() # close the cursor for any case
        
        flash("You are registered successfully!", "success") # this is a flash message, will pop up right after it is called. 
        
        return redirect(url_for("login")) 
    
    
    else:
        return render_template("register.html", form = form) # if it's get request or validations are not satisfied, it will open register page and print type of form on console


#login process
@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form) # an object of LoginForm class is created. 
    
    if (request.method == "POST"):
        username = form.username.data # data is taken from the input blanks
        password_entered = form.password.data

        cursor = mysql.connection.cursor() # mysql cursor is created to move in the database

        ask = "SELECT * FROM users WHERE username = %s" # select all the data of usernames from users table

        result = cursor.execute(ask, (username,)) # data will be taken as dictionary, and that dict is put to the result.

        if (result > 0): # if result is above 0, it means entered username exist in the database
            data = cursor.fetchone() # cursor fetches the user's info
            real_password = data["password"] # password is taken from the database
            
            if sha256_crypt.verify(password_entered, real_password): # "verify" method checks whether passwords match or not. If it matches, success message will flash
                flash("Logged in successfully", "success")
                
                session["logged_in"] = True # when the user logs in, session["logged_in"] becomes true. This will be used in the manipulation of navbar.
                session["username"] = username

                return redirect(url_for("index"))
            
            else: 
                flash("Wrong password entered", "danger")
                return redirect(url_for("login"))

        else: # if size of dictionary is 0, it means there is no username like this in the database.
            flash("User doesn't exist!", "danger")
            return redirect (url_for("login"))

    return render_template("login.html", form = form) # in the case if the request is 'get'.


#logout process
@app.route("/logout")
def logout():
    session.clear() # when logout button clicked, the session will be cleaned for future use
    return redirect(url_for("index")) # and will be redirected to main page

#dashboard
@app.route("/dashboard")
@login_required #login_required decorator is called to enhance the security. If we don't use this decorator and a user adds /dashboard extension to the url, it will be redirected to dashboard, which is not preferred.
def dashboard():
    cursor = mysql.connection.cursor()

    ask = "SELECT * FROM articles WHERE author = %s"

    result = cursor.execute(ask, (session["username"],))

    if result > 0:
        articles = cursor.fetchall()

        return render_template("dashboard.html", articles = articles)
    
    else:
        return render_template("dashboard.html")


#add article
@app.route("/addarticle", methods = ["GET", "POST"]) 
def addarticle():
    form = ArticleForm(request.form) # form object is created from ArticleForm class

    if (request.method == "POST" and form.validate()):
        title = form.title.data #input data are taken.
        content = form.content.data

        cursor = mysql.connection.cursor() # cursor of mysql is created

        ask = "INSERT INTO articles(title, author, content) VALUES(%s,%s,%s)" # insertion request.

        cursor.execute(ask, (title, session["username"], content)) 

        mysql.connection.commit()

        cursor.close()

        flash("Article is added successfully", "success")

        return redirect(url_for("index"))

    return render_template("addarticle.html", form = form)


@app.route("/articles")
@login_required
def articles(): 
    cursor = mysql.connection.cursor()

    ask = "SELECT * FROM articles" # all articles are taken from database

    result = cursor.execute(ask)

    if (result > 0): # if result is 0, no articles exist
        articles = cursor.fetchall()

        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")
    
    cursor.close()


#detail page
@app.route("/article/<string:id>") #dynamic url is used for id.
def article(id):

    cursor = mysql.connection.cursor()

    ask = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(ask, (id,)) # article from certain id is taken

    if result > 0: 
        article = cursor.fetchone()
        return render_template("article.html", article = article) # article is taken and is sent to article.html
    else:
        return render_template("article.html")
    
    cursor.close()


#delete article
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    ask = "SELECT * FROM articles WHERE author = %s and id = %s"

    result = cursor.execute(ask, (session["username"], id))

    if result > 0:
        ask2 = "DELETE FROM articles WHERE id = %s" # delete request.
        
        cursor.execute(ask2, (id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Either there is no article like this or you do not have permission to delete.", "danger")
        return redirect(url_for("index")) #everything which is done in this function was used and explained in the previous functions.


#Update article
@app.route("/edit/<string:id>", methods = ["GET", "POST"]) # both requests will be used here.
@login_required
def update(id):
    if request.method == "GET": # if it's get request (data is taken from database) this if will work.
        cursor = mysql.connection.cursor()

        ask = "SELECT * FROM articles WHERE id = %s and author = %s"
        result = cursor.execute(ask, (id, session["username"]))

        if result == 0: 
            flash("Either there is no article like this or you do not have permission to update.", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm() # an object is created from ArticleForm class
            form.title.data = article["title"] # to the content of blanks in the page, the name and content of article will be put.
            form.content.data = article["content"]
            return render_template("update.html", form = form) 
    else:
        #POST request. It means some updates will be done on database.
        form = ArticleForm(request.form) # new form will be created.

        newTitle = form.title.data
        newContent = form.content.data # new data, which the content and title is updated.

        ask2 = "UPDATE articles SET title = %s, content = %s WHERE id = %s" # update request.
        cursor = mysql.connection.cursor()
        cursor.execute(ask2, (newTitle, newContent, id))
        mysql.connection.commit()

        flash("Article is updated successfully", "success")
        return redirect(url_for("dashboard"))
        

#Search url
@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET": 
        return redirect(url_for("index")) 
    else:
        keyword = request.form.get("keyword") # searched word.

        cursor = mysql.connection.cursor()

        ask = "SELECT * FROM articles WHERE title LIKE '%" + keyword + "%'" # if the title contains the keyword, it will be taken.
        result = cursor.execute(ask)

        if result == 0:
            flash("There is no article which includes searched word.", "warning")
            return redirect(url_for("articles"))

        else:
            articles = cursor.fetchall()

            return render_template("articles.html", articles = articles)

if __name__ == "__main__":
    app.run(debug=True)