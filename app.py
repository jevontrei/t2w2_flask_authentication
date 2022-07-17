from flask import Flask, jsonify
app = Flask(__name__)

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

@app.cli.command("drop")
def drop_db():
    db.drop_all()
    print("Tables dropped") 

class Card(db.Model):
    # define the table name for the db
    __tablename__= "CARDS"
    # Set the primary key, we need to define that each attribute is also a column in the db table, remember "db" is the object we created in the previous step.
    id = db.Column(db.Integer,primary_key=True)
    # Add the rest of the attributes. 
    title = db.Column(db.String())
    description = db.Column(db.String())
    date = db.Column(db.Date())
    status = db.Column(db.String())
    priority = db.Column(db.String())



@app.route("/")
def hello():
  return "Hello World!"

