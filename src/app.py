"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

jwt=JWTManager(app)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_KEY")
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/register',methods=["POST"])
def create_user():
    body=request.json
    email = body.get("email",None)
    password = body.get("password",None)
    
    
    if email is None or password is None:
        return jsonify({
            "error":"Email and password is required"
        }),400
        
    password_hash= generate_password_hash(password)
    
    new_user = User(email=email,password=password_hash,is_active=True)
    
    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify({
            "msg":"User created"
        }),200
        
    except Exception as error:
        print (error)
        db.session.rollback()
        return jsonify({
            "error":"Internal server error"
        },500) 
 
@app.route("/login",methods=["POST"])
def login():
    body= request.json
    email = body.get("email")
    password = body.get("password")
    
    if email is None or password is None:
        return jsonify({
            "error":"Email and password is required"
        }),400
    
    user= User.query.filter_by(email=email).one_or_none()
    
    if user is None:
        return jsonify({
            "error":"User not found"
        }),404
        
    password_match = check_password_hash(user.password,password)
    
    if not password_match:
        return jsonify({
            "error":"Invalid password"
        }),401
      
    auth_token = create_access_token({
        "email": user.email,
        "id":user.id
    }) 
    
    return jsonify({
        'auth_token':auth_token
    }),200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
