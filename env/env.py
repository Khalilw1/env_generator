""" Environment representation with food scattered across in a random manner.
"""
import argparse
from enum import Enum
import random

class Season(Enum):
    """Season is a representation of the human year's seasonal episodes."""
    SPRING = 0
    SUMMER = 1
    FALL = 2
    WINTER = 3

    def next(self):
        """Returns the next enum according to integer order and is cyclic."""
        season = self.value
        season = (season + 1) % len(Season.__members__.items())
        return Season(season)

class Cell(object):
    """Environment's representation of cell with the newly and stored food."""
    def __init__(self):
        self._newly = 0
        self._stored = 0
        #TODO(@khalil): Discuss this matter and see how energy food provides should be calculated.
        self._energy = random.randint(1, 10)

    def get_newly(self):
        """Get newly."""
        return self._newly

    def get_stored(self):
        """Get stored."""
        return self._stored

    def produce(self, quantitiy):
        """Add quantity to the ammount of newly produced food."""
        self._newly = self._newly + quantitiy

    def store(self, quantitiy):
        """Add ammount quantity to the stored food."""
        self._stored = self._stored + quantitiy

    def consume(self):
        """Agents can eat food and thus decrease ammount of stored food."""
        self._stored = self._stored - 1

    def decrease_newly(self, quantitiy):
        """Decrease the newly by the giving quantity."""
        self._newly = self._newly - quantitiy

    def get_food_energy(self):
        """Get energy."""
        return self._energy

class Environment(object):
    """Environment generated and interface for interaction."""
    def __init__(self, height, width, cycle, food_per_season):
        self._height = height
        self._width = width
        self._cycle = cycle
        self._env = [[Cell() for j in range(self._height)] for i in range(self._height)]
        self._seeded = [[False for j in range(self._height)] for i in range(self._height)]
        self._t = 0
        self._season = Season.SPRING
        self._food_per_season = food_per_season

        self._generate_init_env()

    def _generate_init_env(self):

        production_cap = random.randint(1, self._height * self._width)

        for i in range(self._height):
            if production_cap == 0:
                break
            for j in range(self._width):
                if production_cap == 0:
                    break

                cell = self._env[i][j]

                if cell.get_newly() == self._food_per_season[self._season.value]:
                    continue

                should_fill = random.randint(0, 1)
                if not should_fill:
                    continue

                production_cap = production_cap - 1
                quantitiy = random.randint(
                    0,
                    self._food_per_season[self._season.value] - cell.get_newly()
                )
                cell.produce(quantitiy)


    def simulate(self):
        """One unit of time simulation."""
        self._t = self._t + 1
        if self._t == self._cycle:
            # End of a season, start of the next one. Year is also cyclic that is WINTER -> SPRING.
            self._t = 0
            self._season = self._season.next()

        # When the ammount of newly produced food in a cell is over and the cell can seed we 
        # randomly choose another spot where some random ammount of newly produced food should 
        # be stored.
        for i in range(self._height):
            for j in range(self._width):
                if self._env[i][j].get_newly() == 0 and not self._seeded[i][j]:
                    # if the cell become empty just now seed in once in a randomn cell on the grid.
                    self._seeded[i][j] = True
                    cap = self._height + self._width
                    while cap > 0:
                        seedi = random.randint(0, self._height - 1)
                        seedj = random.randint(0, self._width - 1)

                        production_cap = self._food_per_season[self._season.value]

                        production_cap -= self._env[seedi][seedj].get_newly()

                        if production_cap > 0:
                            seed_amount = random.randint(1, production_cap)
                            self._env[seedi][seedj].produce(seed_amount)
                            self._seeded[seedi][seedj] = False
                            break

                        cap = cap - 1

    @property
    def height(self):
        """Get height."""
        return self._height

    @property
    def width(self):
        """Get width."""
        return self._width

    def get_cell(self, i, j):
        """returns the cell at provided position."""
        return self._env[i][j]

class Agent(object):
    """Parent class for every type of agent present in our environment."""
    def __init__(self, max_energy, initial_energy, env, be_cost, eat_cost, move_cost):
        self._max_energy = max_energy
        self._energy = initial_energy

        self._be_cost = be_cost
        self._eat_cost = eat_cost
        self._move_cost = move_cost

        self._env = env
        self._i = random.randint(0, env.height - 1)
        self._j = random.randint(0, env.width - 1)

    def show(self):
        """Returns what the agent can see and depends on what type of agent."""
        raise NotImplementedError

    def move(self, deltai, deltaj):
        """Agent moves in one of the eight 2-d directions with sanity checking of new postition."""
        if abs(deltai) > 1 or abs(deltaj) > 1:
            return
        if self._i + deltai >= self._env.height or self._j + deltaj >= self._env.width:
            return

        self._i = self._i + deltai
        self._j = self._j + deltaj

        self._energy = self._energy - self._move_cost

        self._env.simulate()

    def eat(self):
        """Consume one unit of stored food to increase energy level."""
        cell = self._env.get_cell(self._i, self._j)
        if cell.get_stored() == 0:
            return
        cell.consume()
        self._energy = self._energy + cell.get_food_energy()

        self._energy = self._energy - self._eat_cost

        self._env.simulate()

    def skip(self):
        """Skip the day without doing any actions."""
        self._energy = self._energy - self._be_cost
        self._env.simulate()

class GrassHoper(Agent):
    """GrassHoper agent type who has ability to sing."""
    def __init__(self, max_energy, initial_energy, env, be_cost, eat_cost, move_cost, sing_cost):
        super().__init__(max_energy, initial_energy, env, be_cost, eat_cost, move_cost)
        self._sing_cost = sing_cost

    def show(self):
        return {'stored': self.show_stored()}

    def show_stored(self):
        """Show the number of stored food on the current cell."""
        return self._env.get_cell(self._i, self._j).get_stored()

    def sing(self):
        """Sing action basically a useless time skipping version for grasshoper."""
        self._energy = self._energy - self._sing_cost
        self._env.simulate()

class Ant(Agent):
    """The ant agent and its access API."""
    def __init__(self, max_energy, initial_energy, env, be_cost, eat_cost, move_cost, forage_cost):
        super().__init__(max_energy, initial_energy, env, be_cost, eat_cost, move_cost)
        self._forage_cost = forage_cost

    def show(self):
        return {'stored': self.show_stored(), 'newly': self.show_newly()}

    def show_newly(self):
        """Show the number of newly produces food on the current cell."""
        return self._env.get_cell(self._i, self._j).get_newly()

    def show_stored(self):
        """Show the number of stored food on the current cell."""
        return self._env.get_cell(self._i, self._j).get_stored()

    def forage(self):
        """Forage takes a cell and does something."""
        cell = self._env.get_cell(self._i, self._j)
        if cell.get_newly() > 0:
            cell.store(1)
            cell.decrease_newly(1)

        self._energy = self._energy - self._forage_cost

        self._env.simulate()



def parse():
    """Parse command line args to get constants for the environment and agents."""
    parser = argparse.ArgumentParser(conflict_handler='resolve')

    # Environment specific control flags.
    parser.add_argument('-spring', '--spring_threshold', type=int, default=6,
                        help='The maximum ammount of newly generated food for spring season')
    parser.add_argument('-summer', '--summer_threshold', type=int, default=7,
                        help='The maximum ammount of newly generated food for summer season')
    parser.add_argument('-fall', '--fall_threshold', type=int, default=5,
                        help='The maximum ammount of newly generated food for fall season')
    parser.add_argument('-winter', '--winter_threshold', type=int, default=2,
                        help='The maximum ammount of newly generated food for winter season')
    parser.add_argument('-w', '--width', type=int, default=5, help='width of the 2-d environment')
    parser.add_argument('-h', '--height', type=int, default=5, help='height of the 2-d environment')
    parser.add_argument('-c', '--cycle', type=int, default=10,
                        help='seasonnal cycle length of the environment')

    # Agent specific control flags.
    parser.add_argument('-e', '--energy', type=int, default=20,
                        help='initial energy level of the agents')
    parser.add_argument('-m', '--max_energy', type=int, default=20,
                        help='maximum energy an agent tries to reach continuously')

    parser.add_argument('-be', '--be', type=int, default=1,
                        help='cost needed to stay alive without doing any action')
    parser.add_argument('-eat', '--eat', type=int, default=2, help='cost needed to eat')
    parser.add_argument('-sing', '--sing', type=int, default=3, help='cost needed to sing')
    parser.add_argument('-move', '--move', type=int, default=4, help='cost needed to move')
    parser.add_argument('-forage', '--forage', type=int, default=5, help='cost needed to forage')

    args = parser.parse_args()

    # Instatiate our to special {ant, grasshoper} agents.
    ant = Ant(args.max_energy, args.energy,
              Environment(args.height, args.width, args.cycle,
                          [args.spring_threshold, args.summer_threshold,
                           args.fall_threshold, args.winter_threshold]),
              args.be, args.eat, args.move,
              args.forage)

    grasshoper = GrassHoper(args.max_energy, args.energy,
                            Environment(args.height, args.width, args.cycle,
                                        [args.spring_threshold, args.summer_threshold,
                                         args.fall_threshold, args.winter_threshold]),
                            args.be, args.eat, args.move,
                            args.forage)
    print(ant)

    print(ant.show())
    ant.eat()
    print(grasshoper.show())
    grasshoper.eat()

if __name__ == '__main__':
    parse()
