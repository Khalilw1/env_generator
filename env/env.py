from enum import Enum
import random


class Season(Enum):
    """Season is a representation of the human year's seasonal episodes."""

    SPRING = 0
    SUMMER = 1
    FALL = 2
    WINTER = 3

    def next(self):
        season = self.value
        season = (season + 1) % len(Season.__members__.items())
        return Season(season)

class Cell(object):
    def __init__(self):
        self._newly = 0
        self._stored = 0

    def get_newly(self):
        return self._newly

    def get_stored(self):
        return self._stored

    def produce(self, quantitiy):
        self._newly = self._newly + quantitiy

class Environment(object):
    def __init__(self, N, M, cycle, food_per_season):
        self._N = N
        self._M = M
        self._cycle = cycle
        self._env = [[Cell() for j in range(self._M)] for i in range(self._N)]
        self._t = 0
        self._season = Season.SPRING
        self._food_per_season = food_per_season

        self._generate_init_env()

    def _generate_init_env(self):
        production_cap = random.randint(
            1,
            self._N * self._M
        )
        for i in range(self._N):
            if production_cap == 0:
                break
            for j in range(self._M):
                if production_cap == 0:
                    break
                
                cell = self._env[i][j]
                
                if cell.get_newly() == self._food_per_season[self._season.value]:
                    continue
                
                should_fill = random.randint(0, 1)
                if not should_fill:
                    continue
                
                production_cap = production_cap - 1
                quantitiy = random.randint(0,
                                           self._food_per_season[self._season.value]
                                           - cell.get_newly())
                cell.produce(quantitiy)
                

    def simulate(self):
        self._t = self._t + 1
        if self._t == self.cycle:
            self._t = 0
            
    @property
    def N(self):
        return self._N

    @property
    def M(self):
        return self._M

    def get_cell(self, x, y):
        return self._env[x][y]

class Ant(object):
    def __init__(self, env):
        self._x = random.randint(0, env.N - 1)
        self._y = random.randint(0, env.M - 1)
        print(self._x, self._y)
        self._env = env
       
    def show_newly(self):
        return self._env.get_cell(self._x, self._y).get_newly()
      
    def show_stored(self):
        return self._env.get_cell(self._x, self._y).get_stored()

    def forage(self):
        self._env.get_cell(self._x, self._y)



agent = Ant(Environment(5,5, 10, [200, 2300, 200, 299]))
print(agent)


print(agent.show_newly())