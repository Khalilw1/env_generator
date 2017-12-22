## Environment Generation for Ant and Grasshoper
this repo contains the environment generation for a sample environment playground to test different 
agents.

## User Interface
The UI represents the game state form the perspectiva of a single player, Python3 is needed for the app to run. It is also advisable to use a virtual environment.

```bash
> cd generator
> pip install editable .
> export FLASK_APP=debugger
```

Before running the app, we need to create the database. We do so by running python in terminal and then running the following commands.

```python
from generator import db
db.create_all()
```

Then we proceed to running into running the app.

```bash
> flask run
> open http://127.0.0.1:5000
```


## Status
The demo shows how one could use single player mode inside an environment and multiplayer one. Every player needs to wait for all other to do a move and a when a players energy touches 0 they die in agony or no. The player can do all the basic actions describe this is mainly a proof of concept of what can be achieved with this kind of specification. The friendship feature is not yet added and is left as future work. I would be glad to introduce this to our next AI class.

### Demo
![demo](/assets/demo.gif?raw=true)

### Control
The agents use the arrows to move and in order to use the agents moves (eat, be, forage), the agents use the first character as the move representative. This means in order to eat one has to press e.