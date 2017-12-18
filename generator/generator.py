"""Creation of the app and matching the blueprints."""
from random import randint
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='sqlite:////tmp/generator.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    DEBUG=True,
    SEND_FILE_MAX_AGE_DEFAULT=0
))
app.config.from_envvar('GENERATOR_SETTINGS', silent=True)

db = SQLAlchemy(app)

class User(db.Model):
    """User model that encapsulate our user instance and to which agent it is linked."""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    agent = db.relationship('Agent', uselist=False, backref='user')

    def __repr__(self):
        return '<User %r>' % self.username

class Cell(db.Model):
    __tablename__ = 'cell'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    coordinate = db.Column(db.Integer, nullable=False)
    newly = db.Column(db.Integer, nullable=False)
    stored = db.Column(db.Integer, nullable=False)
    energy = db.Column(db.Integer, nullable=False)
    seeded = db.Column(db.Boolean, nullable=False)
    envid = db.Column(db.Integer, db.ForeignKey('environment.id'), nullable=False)

    def __init__(self, coordinate, newly, stored, energy, seeded, envid, **kwargs):
        super(Cell, self).__init__(**kwargs)

        self.coordinate = coordinate
        self.newly = newly
        self.stored = stored
        self.energy = energy
        self.seeded = seeded
        self.envid = envid

class Season(db.Model):
    __tablename__ = 'season'
    name = db.Column(db.Enum('spring', 'summer', 'fall', 'winter'), nullable=False,
                     primary_key=True)
    production = db.Column(db.Integer, nullable=False)
    envs = db.relationship('Environment', backref='season', lazy=True)

class Environment(db.Model):
    __tablename__ = 'environment'
    id = db.Column(db.Integer, nullable=True, primary_key=True)
    height = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    cycle = db.Column(db.Integer, nullable=False)
    t = db.Column(db.Integer, nullable=False)
    season_desc = db.Column(db.Enum('spring', 'summer', 'fall', 'winter'),
                            db.ForeignKey('season.name'))
    cells = db.relationship('Cell', backref='environment', lazy=True)
    agents = db.relationship('Agent', backref='environment', lazy=True)

    def __init__(self, height=5, width=5, cycle=20, t=0, **kwargs):
        super(Environment, self).__init__(**kwargs)
        self.height = height
        self.width = width
        self.cycle = cycle
        self.t = t

        self.cells = []

        for i in range(0, height):
            for j in range(0, width):
                self.cells.append(Cell(i * height + j, 0, 0, randint(5, 10), 0, self.id))


class Agent(db.Model):
    __tablename__ = 'agent'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    max_energy = db.Column(db.Integer, nullable=False)
    energy = db.Column(db.Integer, nullable=False)

    be_cost = db.Column(db.Integer, nullable=False)
    eat_cost = db.Column(db.Integer, nullable=False)
    move_cost = db.Column(db.Integer, nullable=False)

    i = db.Column(db.Integer, nullable=False)
    j = db.Column(db.Integer, nullable=False)


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    envid = db.Column(db.Integer, db.ForeignKey('environment.id'), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'agent'
    }

class Ant(Agent):
    forage_cost = db.Column(db.Integer)

    __mapper_args__ = {
        'polymorphic_identity':'ant'
    }

class Grasshopper(Agent):
    sing_cost = db.Column(db.Integer)

    __mapper_args__ = {
        'polymorphic_identity':'grasshopper'
    }



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/<username>')
def dashboard(username):
    """Create a user and agent for username given the counts of all the ants and grasshopper."""
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    environment = None
    agent = user.agent
    if user.agent is None:
        print('No agent assigned to ' + username)
        environments = Environment.query.all()

        options = len(environments)

        target = randint(0, options)
        if target == 0:
            # create a new environment and host this agent in it.
            environment = Environment()
            db.session.add(environment)
            db.session.commit()
        else:
            environment = environments[target - 1]

        print(environment.id)

        agents = len(Agent.query.filter_by(envid=environment.id).all())
        hoppers = len(Agent.query.filter_by(envid=environment.id, type='grasshopper').all())
        ants = len(Agent.query.filter_by(envid=environment.id, type='ant').all())

        assert agents == hoppers + ants

        if hoppers < ants:
            # create a grasshoper for the current player otherwise create an ant.
            agent = Grasshopper(sing_cost=2, max_energy=100, energy=90, be_cost=1, eat_cost=1,
                                move_cost=2, envid=environment.id, user_id=user.id,
                                i=randint(0, environment.height), j=randint(0, environment.width))
        else:
            agent = Ant(forage_cost=2, max_energy=100, energy=90, be_cost=1, eat_cost=1,
                        move_cost=2, envid=environment.id, user_id=user.id,
                        i=randint(0, environment.height), j=randint(0, environment.width))

        user.agent = agent

        print(agent.type)

        db.session.add(agent)
        db.session.commit()
    else:
        environment = Environment.query.filter_by(id=agent.envid).first()

    return render_template('dashboard.html', user=user, agent=agent, environment=environment)