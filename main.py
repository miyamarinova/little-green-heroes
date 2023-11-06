import secrets

from flask import Flask, render_template, make_response, session, request, url_for, redirect, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import forms_store
from datetime import datetime
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user, logout_user,login_user,UserMixin
import json


import stripe

publishable_key = 'pk_test_51NNbJzJOl87lc95Gsi3ZfrtHMZH3teFPXsM26oz1z1JCHIswKEdEXKFVB4dTR5BYi3Zv5DNSo0SsA8ugL4HwxNkI00Mk0Ffcj0'
stripe.api_key = 'sk_test_51NNbJzJOl87lc95G3r1I4L3rGLHhIn9kUJBLUauWuiwkftdKeFgxeFZZ3cFT4VSfaCa3sP4DAMe9tvSBLAm6J6ec00X98ApIc4'

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

#-------------------- setup SQL DB -----------------------#
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'static/images')
app.config['SECRET_KEY'] = '07249389we9n'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

db = SQLAlchemy(app)
Bootstrap(app)
bcrypt = Bcrypt(app)

migrate = Migrate(app,db, render_as_batch=True)

with app.app_context():
    if db.engine.url.drivername == "sqlite":
        migrate.init_app(app,db,render_as_batch=True)
    else:
        migrate.init_app(app,db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_customer'
login_manager.needs_refresh_message_category = 'danger'
login_manager.login_message = u"Please login first"


@login_manager.user_loader
def user_loader(user_id):
    return Register.query.get(user_id)

class Register(db.Model, UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String,unique=False)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String,unique=True)
    password = db.Column(db.String, unique=False)
    country = db.Column(db.String)
    state = db.Column(db.String)
    city = db.Column(db.String)
    zipcode = db.Column(db.String)
    address = db.Column(db.String)
    phone = db.Column(db.String)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return '<Register %r>' % self.name

class JsonEcodeDict(db.TypeDecorator):
    impl = db.Text
    def process_bind_param(self,value,dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)
    def process_result_value(self,value,dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)

class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice = db.Column(db.String(20),nullable=False)
    status = db.Column(db.String(20), default='Pending')
    customer_id = db.Column(db.Integer,db.ForeignKey("register.id"))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.Column(JsonEcodeDict)

    def __repr__(self):
        return '<CustomerOrder %r>' % self.invoice

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String,unique=True)
    password = db.Column(db.String)

class Addproduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    price = db.Column(db.Numeric(10,2))
    desc = db.Column(db.Text)

    image_1 = db.Column(db.String(150), default='image.jpg')
    def __repr__(self):
        return '<Addproduct %r>' % self.title


class Cart(db.Model):
    __tablename__ = "cart"
    cart_id = db.Column(db.Integer,db.ForeignKey("addproduct.id"),primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.String(100))

def save_img(picture_file):
    picture_name = picture_file.filename
    picture_path = os.path.join(app.root_path, 'static/images', picture_file)
    picture_file.save(picture_path)
    return picture_name

with app.app_context():
    db.create_all()

def MagerDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2,list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items()) + list(dict2.items()))
    return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/addproduct', methods=['POST','GET'])
def addproduct():
    form = forms_store.AddproductForm(request.form)
    if request.method == 'POST':
        name = form.name.data
        price = form.price.data
        desc = form.description.data
        image_1 = photos.save(request.files.get('image_1'))
        
        addpro = Addproduct(name=name,price=price,desc=desc,image_1=image_1)
        db.session.add(addpro)
        db.session.commit()
        flash(f"New product has been added, {name}", "success")
        return render_template('products.html')
    return render_template('addproduct.html',title='Add Product page', form=form)

@app.route('/onlineshop', methods=['POST', 'GET'])
def onlineshop():
    products = Addproduct.query.all()
    return render_template('products.html',title='Our Products', products=products)

@app.route('/<int:id>')
def single_page(id):
    product = Addproduct.query.get_or_404(id)
    return render_template('single_page.html',product=product)

@app.route('/addcart',methods=['POST'])
def AddCart():
    try:
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        product = Addproduct.query.filter_by(id=product_id).first()
        if product_id and quantity and request.method == 'POST':
            DictItems = {product_id: {'name': product.name, 'price': product.price, 'quantity': quantity, 'image':product.image_1}}
            if 'Shoppingcart' in session:
                print(session['Shoppingcart'])
                if product_id in session['Shoppingcart']:
                    for key, item in session['Shoppingcart'].items():
                        if int(key) == int(product_id):
                            session.modified = True
                            item['quantity'] += 1
                else:
                    session['Shoppingcart'] = MagerDicts(session['Shoppingcart'], DictItems)
                    return redirect(request.referrer)
            else:
                session['Shoppingcart'] = DictItems
                return redirect(request.referrer)
    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)

@app.route('/cart')
def getcart():
    if 'Shoppingcart' not in session:
        flash(f"You must be registered customer, please sign in or loge in!", "dangerous")
        return redirect('products.html')
    total = 0
    for product in session['Shoppingcart'].items():
        total += float(product[1]['price']) * int(product[1]['quantity'])
        print(product)

    return render_template('cart.html', total=total)

@app.route('/updatecart/<int:code>',methods=['POST'])
def updatecart(code):
    if 'Shoppingcart' not in session and len(session['Shoppingcart']) <= 0:
        return redirect(url_for('onlineshop'))
    if request.method == 'POST':
        quantity = request.form.get('quantity')
        try:
            session.modified= True
            for key, item in session['Shoppingcart'].items():
                if int(key) == code:
                    item['quantity'] = quantity
                    return redirect(url_for('getcart'))

        except Exception as e:
            print(e)
            return redirect(url_for('getcart'))


@app.route('/deleteitem/<int:id>',methods=['POST','GET'])
def delete_item(id):
    if 'Shoppingcart' not in session and len(session['Shoppingcart']) <= 0:
        return redirect(url_for('getcart'))
    try:
        session.modified = True
        for key, item in session['Shoppingcart'].items():
            if int(key) == id:
                session['Shoppingcart'].pop(key, None)
                return redirect(url_for('getcart'))
    except Exception as e:
        print(e)
        return redirect(url_for('getcart'))

@app.route('/clearcart')
def clearcart():
    try:
        session.pop('Shoppingcart', None)
        return redirect(url_for('onlineshop'))
    except Exception as e:
        print(e)

@app.route('/registercustomer', methods=['POST', 'GET'])
def register_customer():
    form = forms_store.CustomerRegisterForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        register = Register(name=form.name.data, username=form.username.data, email=form.email.data, password=hash_password, country=form.country.data,state=form.state.data,
                            city=form.city.data, zipcode=form.zipcode.data, address=form.address.data,
                            phone=form.phone.data)

        db.session.add(register)
        db.session.commit()
        
        flash(f'Welcome {form.name.data}! Thank you for registering', 'success')
        
        # login_user(register)
        return redirect(url_for('login'))
    return render_template('register_customer.html',form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = forms_store.LoginForm()
    if form.validate_on_submit():
        user = Register.query.filter_by(email=form.email.data.lower()).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['email'] = form.email.data
            flash(f'Welcome, {user.name}', 'success')
            login_user(user)
            next = request.args.get('next')
            return redirect(next or url_for('home'))
        else: 
            flash('Wrong email or password!', 'danger')
            return redirect(url_for('login'))
    return render_template("login.html", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/getorder',methods=['PUT','GET'])
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        try:
            order = CustomerOrder(invoice=invoice, customer_id=customer_id,orders=session['Shoppingcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('Your order has been sent.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            print(e)
            flash('Something get wrong!')
            return redirect(url_for('getcart'))

@app.route('/orders/<invoice>')
@login_required
def customer_orders(invoice):
    if current_user.is_authenticated:
        total = 0
        subtotal = 0
        customer_id = current_user.id
        customer = Register.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id,invoice=invoice).order_by(CustomerOrder.id.desc()).first()
        for _key,product in orders.orders.items():
            subtotal += float(product['price']) * int(product['quantity'])
            total = ("%.2f" % (1.00 * subtotal))

    else:
        return redirect(url_for('login_customer'))
    return render_template('order.html',invoice=invoice,total=total,customer=customer,orders=orders)

@app.route('/payment',methods=['POST','GET'])
@login_required
def payment():
    invoice = request.form.get('invoice')
    amount = request.form.get('amount')

    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        source=request.form['stripeToken'],
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        description='Little Green Heroes',
        amount='3000',
        currency='usd',
    )
    orders = CustomerOrder.query.filter_by(customer_id=current_user.id,invoice=invoice,status='Paid').order_by(CustomerOrder.id.desc()).first()
    db.session.commit()
    return redirect(url_for('thankyou'))

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')



if __name__ == '__main__':
    app.run(debug=True)