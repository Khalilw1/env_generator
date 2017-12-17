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
