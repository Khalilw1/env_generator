"""Creation of the app and matching the blueprints."""
from random import randint
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='sqlite:////tmp/generator.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    DEBUG=True,
    SEND_FILE_MAX_AGE_DEFAULT=0
))
app.config.from_envvar('GENERATOR_SETTINGS', silent=True)
db = SQLAlchemy(app)
socketio = SocketIO(app)

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

    @staticmethod
    def populate():
        spring = Season(name='spring', production=10)
        summer = Season(name='summer', production=17)
        fall = Season(name='fall', production=12)
        winter = Season(name='winter', production=7)

        if Season.query.first() is None:
            db.session.add(spring)
            db.session.add(fall)
            db.session.add(winter)
            db.session.add(summer)
            db.session.commit()

class Environment(db.Model):
    __tablename__ = 'environment'
    id = db.Column(db.Integer, nullable=True, primary_key=True)
    height = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    cycle = db.Column(db.Integer, nullable=False)
    t = db.Column(db.Integer, nullable=False)
    season_desc = db.Column(db.Enum('spring', 'summer', 'fall', 'winter'),
                            db.ForeignKey('season.name'))
    season = db.relationship('Season', backref="envs", lazy=True)
    cells = db.relationship('Cell', backref='environment', lazy=True)
    agents = db.relationship('Agent', backref='environment', lazy=True)
    nrequest_daily = db.Column(db.Integer, nullable=True)

    def __init__(self, height=randint(5, 10), width=0, cycle=20, t=0, **kwargs):
        super(Environment, self).__init__(**kwargs)
        self.height = height
        print(width)
        if width != 0:
            self.width = width
        else:
            self.width = height
        self.cycle = cycle
        self.t = t
        self.season = Season.query.filter_by(name='spring').first()
        if self.season is None:
            Season.populate()
        self.season = Season.query.filter_by(name='spring').first()
        self.season_desc = self.season.name
        self.nrequest_daily = 0
        self.cells = []
        for i in range(0, self.height):
            for j in range(0, self.width):
                self.cells.append(Cell(i * width + j, 0, 0, randint(5, 10), 0, self.id))

        self.generate_initial()

    def generate_initial(self):
        production_cap = randint(1, self.height * self.width)
        for i in range(self.height):
            if production_cap == 0:
                break
            for j in range(self.width):
                if production_cap == 0:
                    break
                cell = self.cells[i * self.width + j]

                if cell.newly >= self.season.production:
                    continue

                should_fill = randint(0, 1)
                if not should_fill:
                    continue
                production_cap = production_cap - 1
                quantity = randint(1, self.season.production - cell.newly)

                # TODO(khalil): add methods for this type of operations :- cell.produce(quantity).
                cell.newly += quantity

    def simulate(self):
        self.t += 1
        if self.t == self.cycle:
            # change season to next one
            self.t = 0
            if self.season.name == 'spring':
                self.season = Season.query.filter_by(name='summer').first()
            elif self.season.name == 'summer':
                self.season = Season.query.filter_by(name='fall').first()
            elif self.season.name == 'fall':
                self.season = Season.query.filter_by(name='winter').first()
            elif self.season.name == 'winter':
                self.season = Season.query.filter_by(name='spring').first()
            self.season_desc = self.season.name

        for i in range(self.height):
            for j in range(self.width):
                cell = self.cells[i * self.width + j]
                if cell.newly == 0 and not cell.seeded:
                    # if the cell become empty just now seed in once in a randomn cell on the grid.
                    cell.seeded = True
                    cap = self.height + self.width
                    while cap > 0:
                        seedi = randint(0, self.height - 1)
                        seedj = randint(0, self.width - 1)

                        production_cap = self.season.production

                        rcell = self.cells[seedi * self.width + seedj]
                        production_cap -= rcell.newly

                        if production_cap > 0:
                            seed_amount = randint(1, production_cap)
                            rcell.newly += seed_amount
                            rcell.seeded = False
                            db.session.commit()
                            break

                        cap = cap - 1
        db.session.commit()

    def broadcast(self):
        self.nrequest_daily += 1
        print(len(Agent.query.filter_by(envid=self.id).all()))

        log = {
            'id': self.id,
            'remaining': len(Agent.query.filter_by(envid=self.id).all()) - self.nrequest_daily
        }
        if self.nrequest_daily >= len(Agent.query.filter_by(envid=self.id).all()):
            agents = Agent.query.filter_by(envid=self.id).all()
            dead = []
            for agent in agents:
                if agent.energy == 0:
                    dead.append(agent.id)
            log['dead'] = dead

            self.nrequest_daily = 0
            self.simulate()
        socketio.emit('refresh', log)


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

    has_played = db.Column(db.Boolean)


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    envid = db.Column(db.Integer, db.ForeignKey('environment.id'), nullable=False)

    def show(self, cell):
        """Returns what the agent can see and depends on what type of agent."""
        raise NotImplementedError

    def eat(self):
        """Consume one unit of stored food to increase energy level."""
        if self.has_played:
            return False
        if self.energy < self.eat_cost:
            return

        environment = Environment.query.filter_by(id=self.envid).first()
        cell = environment.cells[self.i * environment.width + self.j]

        if cell.stored == 0:
            return
        cell.stored -= 1
        self.energy = self.energy + cell.energy

        self.energy = self.energy - self.eat_cost

        environment.broadcast()
        self.has_played = True

        db.session.commit()

    def move(self, deltai, deltaj):
        """Agent moves in one of the eight 2-d directions with sanity checking of new postition."""
        if self.has_played:
            return False
        if abs(deltai) > 1 or abs(deltaj) > 1:
            return False
        environment = Environment.query.filter_by(id=self.envid).first()

        if self.i + deltai >= environment.height or self.j + deltaj >= environment.width:
            return False
        if self.i + deltai < 0 or self.j + deltaj < 0:
            return False

        if self.energy < self.move_cost:
            return False

        self.i = self.i + deltai
        self.j = self.j + deltaj

        self.energy = self.energy - self.move_cost

        environment.broadcast()
        self.has_played = True

        db.session.commit()
        return True

    def be(self):
        if self.has_played:
            return False
        environment = Environment.query.filter_by(id=self.envid).first()

        self.energy = max(self.energy - self.be_cost, 0)

        environment.broadcast()
        self.has_played = True

        db.session.commit()
        return True

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'agent'
    }

class Ant(Agent):
    forage_cost = db.Column(db.Integer)

    def show(self, cell):
        return {
            'newly': cell.newly,
            'stored': cell.stored
        }

    def forage(self):
        """Forage takes a cell and adds stored by reducing a newly."""
        if self.has_played:
            return False
        if self.energy < self.forage_cost:
            return False

        environment = Environment.query.filter_by(id=self.envid).first()
        cell = environment.cells[self.i * environment.width + self.j]
        if cell.newly > 0:
            cell.stored += 1
            cell.newly -= 1
        else:
            return False

        self.energy = self.energy - self.forage_cost

        environment.broadcast()
        self.has_played = True

        db.session.commit()

        return True


    __mapper_args__ = {
        'polymorphic_identity':'ant'
    }

class Grasshopper(Agent):
    sing_cost = db.Column(db.Integer)

    def show(self, cell):
        return {
            'stored': cell.stored
        }

    __mapper_args__ = {
        'polymorphic_identity':'grasshopper'
    }

@app.route('/')
def home():
    return render_template('home.html', users=User.query.all())

@app.route('/<username>/create')
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

        agents = len(Agent.query.filter_by(envid=environment.id).all())
        hoppers = len(Agent.query.filter_by(envid=environment.id, type='grasshopper').all())
        ants = len(Agent.query.filter_by(envid=environment.id, type='ant').all())

        assert agents == hoppers + ants

        if hoppers < ants:
            # create a grasshoper for the current player otherwise create an ant.
            agent = Grasshopper(sing_cost=2, max_energy=100, energy=90, be_cost=1, eat_cost=1,
                                move_cost=2, envid=environment.id, user_id=user.id,
                                has_played=False,
                                i=randint(0, environment.height - 1),
                                j=randint(0, environment.width - 1))
        else:
            agent = Ant(forage_cost=2, max_energy=100, energy=90, be_cost=1, eat_cost=1,
                        move_cost=2, envid=environment.id, user_id=user.id,
                        has_played=False,
                        i=randint(0, environment.height - 1),
                        j=randint(0, environment.width - 1))

        user.agent = agent

        db.session.add(agent)
        db.session.commit()
    else:
        environment = Environment.query.filter_by(id=agent.envid).first()

    cell = environment.cells[agent.i * environment.width + agent.j]
    percepts = agent.show(cell)
    return render_template('dashboard.html',
                           user=user,
                           agent=agent,
                           environment=environment,
                           percepts=percepts,
                           grid=True
                          )

@app.route('/<username>/move', methods=['POST'])
def move(username):
    if request.method == 'POST':
        print('move has been sent and should be processed')
        deltai = int(request.form['deltai'])
        deltaj = int(request.form['deltaj'])

        user = User.query.filter_by(username=username).first()
        agent = user.agent
        agent.move(deltai, deltaj)
        db.session.commit()
    return ('', 204)

@app.route('/<username>/forage', methods=['POST'])
def forage(username):
    if request.method == 'POST':
        print('forage request emmited by an ant I hope.')

        user = User.query.filter_by(username=username).first()
        agent = user.agent
        if agent.type != 'ant':
            return 'Grasshopper cannot forage.'
        agent.forage()
        db.session.commit()
    return ('', 204)

@app.route('/<username>/eat', methods=['POST'])
def eat(username):
    if request.method == 'POST':
        print('eat request emmited by an ant I hope.')

        user = User.query.filter_by(username=username).first()
        agent = user.agent
        agent.eat()
        db.session.commit()
    return ('', 204)

@app.route('/<username>/be', methods=['POST'])
def be(username):
    if request.method == 'POST':
        print('be request emmited by an ant I hope.')

        user = User.query.filter_by(username=username).first()
        agent = user.agent
        agent.be()
        db.session.commit()
    return ('', 204)

@app.route('/<username>/refresh', methods=['GET'])
def refresh(username):
    user = User.query.filter_by(username=username).first()
    agent = user.agent
    agent.has_played = False
    environment = Environment.query.filter_by(id=agent.envid).first()
    cell = environment.cells[agent.i * environment.width + agent.j]
    percepts = agent.show(cell)

    db.session.commit()
    return render_template('environment.html',
                           user=user,
                           agent=agent,
                           environment=environment,
                           percepts=percepts)


@app.route('/<username>/erase')
def erase(username):
    user = User.query.filter_by(username=username).first()
    agent = user.agent
    db.session.delete(user)
    db.session.delete(agent)
    db.session.commit()
    return render_template('over.html')

if __name__ == '__main__':
    socketio.run(app)
