A super normal random number generator for settlers of catan.

I have always run in Ipython like,

```
In [1]: from super_normal import simulate_game

In [2]: from super_normal import SuperNormalGame

In [3]: game = SuperNormalGame(normalizer=2, game_name='blame_tristan')

In [4]: game.role_and_plot()
Dice total: 7, red die value: 3, barbarian die: barbarians
After 1 rounds. x or + represent roles, - is represents number of rules under expected, + the number over
 2:
 3:
 4:
 5:
 6:
 7: +
 8:
 9:
10:
11:
12:

In [5]: game.role_and_plot()
Dice total: 11, red die value: 6, barbarian die: barbarians
After 2 rounds. x or + represent roles, - is represents number of rules under expected, + the number over
 2:
 3:
 4:
 5:
 6:
 7: +
 8:
 9:
10:
11: +
12:

In [6]: game.barb_counts
Out[6]: Counter({'barbarians': 2})

```

There are many helper functions in the code to check stats and what not.