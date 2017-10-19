"""Environment representation for the cigale and fourmi agents.
"""

import enum
import random
import threading
import time

class Season(enum.Enum):
    SPRING = 1
    SUMMER = 2
    FALL = 3
    WINTER = 4

    def next(self):
        id = self.value
        id += 1
        if id == 5:
            id = 1
        return Season(id)

class Fruit(object):
    def __init__(self, life_span):
        self._life_span = life_span
        self._age = 1
        self._has_seeded = False

    # decay decreases the life span of the fruit and returns true if the fruit
    # is still alive; otherwise, false is returned.
    def grow(self):
        if self._age < self._life_span:
            self._age += 1
            return True
        return False

    # can_seed return true if the fruit is able to seed and produce new fruits
    # of the same type. The check can be changed but it has to only return true
    # once for a fruit's life cyle.
    def can_seed(self):
        return self._age >= self._life_span // 2 and not self._has_seeded

    def seeded(self):
        self._has_seeded = True

    def get_life_span(self):
        return self._life_span

    def is_dead(self):
        return self._age == self._life_span

    def __str__(self):
        return str(self._life_span - self._age)

class ForestGenerator(object):
    # growth represents the rate at which food propagates inside the forest.
    # This first value means how many seeds will a single food item produce in
    # random directions. The second value represents percentage of fill inside
    # the grid. This percentage can be thought of as a cap not to be exceeded.
    growth = {
        Season.SPRING: [4, 0.5],
        Season.SUMMER: [3, 0.7],
        Season.FALL:   [2, 0.4],
        Season.WINTER: [1, 0.3],
    }

    def __init__(self, height, width):
        self._height = height
        self._width = width
        self._env = [[None for x in range(self._width)] for y in
                     range(self._height)]
        self._season = Season.SPRING
        self._day = 0

        self._lock = threading.Lock()
        
        self._populate() # initialize the grid with food randomly placed.
    
    # Items on the environment are represented with their life span and zero is
    # the current square is empty.
    def __str__(self):
        grid = ""
        for y in range(self._height):
            for x in range(self._width):
                if self._env[y][x] is None:
                    grid += " -1"
                    continue
                grid += " " + str(self._env[y][x])
            grid += "\n"
        return grid

    def _populate(self):
        fruits_to_generate = random.randint(
            1,
            int(self._height * self._width * ForestGenerator.growth[self._season][1])
        )

        while fruits_to_generate > 0:
            x = random.randint(0, self._width - 1)
            y = random.randint(0, self._height - 1)

            if self._env[y][x] is not None:
                continue
            self._env[y][x] = Fruit(random.randint(20, 50))
            fruits_to_generate -= 1

    # Idea for the start method is to launch a thread that will simulate
    # periodically a unit of time in this universe. In this approach the choice
    # for the unit is very important.
    def start(self):
        day = 0
        year = 0
        while True:
            print("%d / %d Season: %s, Filled: %f" %
                  (day, year, self._season, self._fill_percentage()))
            thread = threading.Thread(target=self._simulate)
            thread.start()
            thread.join()
            day += 1
            if day == 80:
                year += 1
                day = 0
            if day % 20 == 0:
                self._season = self._season.next()
            time.sleep(0.25)

    # simulate one unit of time in this forest environment.
    def _simulate(self):
        self._lock.acquire()
        for y in range(self._height):
            for x in range(self._width):
                if self._env[y][x] is not None:
                    if self._env[y][x].can_seed():
                        self._seed(y, x)

        for y in range(self._height):
            for x in range(self._width):
                if self._env[y][x] is not None:
                    self._env[y][x].grow()
                    if self._env[y][x].is_dead():
                        self._env[y][x] = None
        # log the new state of the board after after every day simulated.
        print(self)
        self._lock.release()

    def _seed(self, y, x):
        seeds = self.growth[self._season][0]
        diry = [0, 1, -1]
        dirx = [0, 1, -1]
        available = list()
        for dy in diry:
            for dx in dirx:
                if y + dy >= self._height or y + dy < 0:
                    continue
                if x + dx >= self._width or x + dx < 0:
                    continue
                if self._env[y + dy][x + dx] is None:
                    available.append((y + dy, x + dx))
        random.shuffle(available)

        could_seed = False
        for i in range(min(len(available), seeds)):
            if self._fill_percentage() >= self.growth[self._season][1]:
                break
            ny, nx = available[i]
            self._env[ny][nx] = Fruit(self._env[y][x].get_life_span())
            could_seed = True

        if could_seed:
            self._env[y][x].seeded()


    def _fill_percentage(self):
        used = 0
        for y in range(self._height):
            for x in range(self._width):
                if self._env[y][x] is not None:
                    used += 1
        return used / (self._height * self._width)


env = ForestGenerator(15, 15)
env.start()
