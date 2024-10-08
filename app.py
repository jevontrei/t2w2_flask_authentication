from datetime import timedelta, date

from marshmallow.validate import Length

from flask import Flask, jsonify, request, abort
app = Flask(__name__)

from flask_marshmallow import Marshmallow
ma = Marshmallow(app)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"] = "Backend best end" 

from flask_sqlalchemy import SQLAlchemy 

# set the database URI via SQLAlchemy, 
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://db_dev:123456@localhost:5432/trello_clone_db"

# to avoid the deprecation warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#create the database object
db = SQLAlchemy(app)

# create app's cli command named create, then run it in the terminal as "flask create", 
# it will invoke create_db function
@app.cli.command("create")
def create_db():
    db.create_all()
    print("Tables created")

@app.cli.command("seed")
def seed_db():
    from datetime import date
    
    # create the card object
    card1 = Card(
        # set the attributes, not the id, SQLAlchemy will manage that for us
        title = "Start the project",
        description = "Stage 1, creating the database",
        status = "To Do",
        priority = "High",
        date = date.today()
    )
    # Add the object as a new row to the table
    db.session.add(card1)

    card2 = Card(
        # set the attributes, not the id, SQLAlchemy will manage that for us
        title = "SQLAlchemy and Marshmallow",
        description = "Stage 2, integrate both modules in the project",
        status = "Ongoing",
        priority = "High",
        date = date.today()
    )
    # Add the object as a new row to the table
    db.session.add(card2)
    
    # commit the changes
    db.session.commit()
    print("Table seeded") 
    

    # seed cli command, below card1 and card2
    admin_user = User(
        email = "admin@email.com",
        password = bcrypt.generate_password_hash("password123").decode("utf-8"),
        admin = True
    )
    db.session.add(admin_user)

    user1 = User(
        email = "user1@email.com",
        password = bcrypt.generate_password_hash("123456").decode("utf-8")
    )
    db.session.add(user1)
    
    # commit the changes
    db.session.commit()
    print("Table seeded") 


@app.cli.command("drop")
def drop_db():
    db.drop_all()
    print("Tables dropped") 

# MODEL DECLARATION AREA

class Card(db.Model):
    # define the table name for the db
    __tablename__= "cards"
    
    # Set the primary key, we need to define that each attribute is also a column in the db table, remember "db" is the object we created in the previous step.
    id = db.Column(db.Integer,primary_key=True)
    
    # Add the rest of the attributes. 
    title = db.Column(db.String())
    description = db.Column(db.String())
    date = db.Column(db.Date())
    status = db.Column(db.String())
    priority = db.Column(db.String())

# create the Card Schema with Marshmallow, it will provide the serialization needed for converting the data into JSON
class CardSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ("id", "title", "description", "date", "status", "priority")

# single card schema, when one card needs to be retrieved
card_schema = CardSchema()

# multiple card schema, when many cards need to be retrieved
cards_schema = CardSchema(many=True)


   
# model definition area, below Card model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    admin = db.Column(db.Boolean(), default=False)
    
    
# schema definition area, below Schema model
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
    
    # set the password's length to a minimum of 6 characters
    password = ma.String(validate=Length(min=6))

user_schema = UserSchema()
users_schema = UserSchema(many=True)


@app.route("/")
def hello():
  return "Hello World!"

@app.route("/cards", methods=["GET"])
def get_cards():
    # get all the cards from the database table
    stmt = db.select(Card)
    cards = db.session.scalars(stmt)
    
    # Convert the cards from the database into a JSON format and store them in result
    result = cards_schema.dump(cards)
    
    # return result in JSON format
    return jsonify(result)

# route declaration area, below /cards
@app.route("/auth/register", methods=["POST"])
def auth_register():
    # The request data will be loaded in a user_schema converted to JSON. request needs to be imported from
    user_fields = user_schema.load(request.json)
    
    # Find the user:
    stmt = db.select(User).filter_by(email=user_fields['email'])
    user = db.session.scalar(stmt)
    if user:
        # return an abort msg to inform user. That will end the request:
        return abort(400, description="Email already registered")
    
    # Create the user object
    user = User()
    
    # Add the email attribute
    user.email = user_fields["email"]
    
    # Add the password attribute hashed by bcrypt
    user.password = bcrypt.generate_password_hash(user_fields["password"]).decode("utf-8")
    
    #set the admin attribute to false
    user.admin = False
    
    # Add it to the database and commit the changes
    db.session.add(user)
    db.session.commit()
    
    #create a variable that sets an expiry date
    expiry = timedelta(days=1)
    
    #create the access token
    access_token = create_access_token(identity=str(user.id), expires_delta=expiry)
    
    # return the user email and the access token
    return jsonify({"user":user.email, "token": access_token })
    
    # Return the user to check the request was successful
    # return jsonify(user_schema.dump(user))
   
# routes declaration area, below /auth/register
@app.route("/auth/login", methods=["POST"])
def auth_login():
    # get the user data from the request
    user_fields = user_schema.load(request.json)
    
    # find the user in the database by email
    stmt = db.select(User).filter_by(email=user_fields['email'])
    user = db.session.scalar(stmt)
    
    # there is not a user with that email or if the password is no correct send an error
    if not user or not bcrypt.check_password_hash(user.password, user_fields["password"]):
        return abort(401, description="Incorrect username and password")
    
    
    # create a variable that sets an expiry date
    expiry = timedelta(days=1)
   
    # create the access token
    access_token = create_access_token(identity=str(user.id), expires_delta=expiry)
   
    # return the user email and the access token
    return jsonify({"user":user.email, "token": access_token }) 

@app.route("/cards", methods=["POST"])
# Decorator to make sure the jwt is included in the request
@jwt_required()
def card_create():
    # Create a new card
    card_fields = card_schema.load(request.json)

    new_card = Card()
    new_card.title = card_fields["title"]
    new_card.description = card_fields["description"]
    new_card.status = card_fields["status"]
    new_card.priority = card_fields["priority"]
    
    # not taken from the request, generated by the server
    new_card.date = date.today()
    
    # add to the database and commit
    db.session.add(new_card)
    db.session.commit()
    
    #return the card in the response
    return jsonify(card_schema.dump(new_card))  

# add the id to let the server know the card we want to delete
@app.route("/cards/<int:id>", methods=["DELETE"])
@jwt_required()
# Includes the id parameter
def card_delete(id):
    # get the user id invoking get_jwt_identity
    user_id = get_jwt_identity()
    
    # Find it in the db
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)
    
    # Make sure it is in the database
    if not user:
        return abort(401, description="Invalid user")
    
    # Stop the request if the user is not an admin
    if not user.admin:
        return abort(401, description="Unauthorised user")
    
    # find the card
    stmt = db.select(Card).filter_by(id=id)
    card = db.session.scalar(stmt)
    
    # return an error if the card doesn't exist
    if not Card:
        return abort(400, description= "Card doesn't exist")
    
    # Delete the card from the database and commit
    db.session.delete(card)
    db.session.commit()
    
    # return the card in the response
    return jsonify(card_schema.dump(card))