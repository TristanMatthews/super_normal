import math
from collections import Counter
from copy import deepcopy
from datetime import datetime
import csv
import os
import math_helper_functions as mhf

BARB_DIE_VALUES = ['yellow', 'green', 'blue', 'barbarians', 'barbarians', 'barbarians']

DEBUG = False


class DiceRole:

    def __init__(self, value, red_value=None, barb_die=None, undo=False):
        self.value = value
        self.red_value = red_value
        self.barb_die = barb_die
        self.undo = undo

    def __repr__(self):
        value = "Dice total: {}, red die value: {}, barbarian die: {}".format(self.value, self.red_value, self.barb_die)
        if self.undo:
            value += " Undo: True"
        return value

class ProbabiltiyHandlerBase:
    """
    A normalizer of 0 will mean there is no special effect and just normal dice.
    A normalizer of 1 will use a normal logistic to modify the Gaussian.
    """

    # TODO: Generalize this,              2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
    BASE_ODDS = [value / 36 for value in [1, 2, 3, 4, 5, 6, 5, 4,  3,  2,  1]]

    def __init__(self, normalizer=0):
        self.normalizer = normalizer

    def get_expected_counts(self, value_counts=None, total_counts=None):
        if total_counts is None:
            total_counts = sum(value_counts.values())
        return {index + 2: self.BASE_ODDS[index] * total_counts for index in range(11)}

    def get_expected_count_percent(self, value_counts):
        total_counts = sum(value_counts.values())
        return [value_counts.get(index + 2, 0) / (odds * total_counts) for index, odds in enumerate(self.BASE_ODDS)]

    def get_weighted_odds(self, value_counts):
        if value_counts:
            expected_count_percent = self.get_expected_count_percent(value_counts)
            weighted_probs = []
            for index, percent_of_expected in enumerate(expected_count_percent):
                weighted_probs.append(2 * mhf.logistic(1 - percent_of_expected, self.normalizer) * self.BASE_ODDS[index])
        else:
            weighted_probs = self.BASE_ODDS
        total_weighted_probs = sum(weighted_probs)
        normalized_weighted_odds = [value / total_weighted_probs for value in weighted_probs]
        return normalized_weighted_odds

    def generate_value_cdf(self, value_counts):
        weighted_odds = self.get_weighted_odds(value_counts)
        if DEBUG:
            import pdb; pdb.set_trace()
        return mhf.convert_odds_to_cdf(weighted_odds)

    def generate_red_die_cdf(self, value, barb_counts):
        if value < 7:
            odds = [1 / (value - 1)] * (value - 1) + [0] * (7 - value)
        else:
            odds = [0] * (value - 7) + [1 / (13 - value)] * (13 - value)
        return mhf.convert_odds_to_cdf(odds)

    def generate_barb_die_cdf(self, barb_counts):
        return [1/6 * value for value in range(1, 7)]


class SuperNormalGame:

    DEFAULT_SAVE_FOLDER = 'super_normal_games'

    def __init__(self, normalizer=1, probability_handler=ProbabiltiyHandlerBase, game_name=None, simulate=False):

        self.probability_handler = probability_handler(normalizer)
        self.role_log = []
        self.value_counts = Counter()
        self.barb_counts = Counter()
        self.red_counts = Counter()

        if game_name is None:
            game_name = datetime.isoformat(datetime.now())
        self.game_name = game_name
        self.simulate = simulate

    def _generate_new_dice_role(self):
        value_cdf = self.probability_handler.generate_value_cdf(self.value_counts)
        dice_total = mhf.get_index_from_cdf(value_cdf) + 2
        red_die_cdf = self.probability_handler.generate_red_die_cdf(dice_total, self.barb_counts)
        red_die_value = mhf.get_index_from_cdf(red_die_cdf) + 1
        barb_die_cdf = self.probability_handler.generate_barb_die_cdf(self.barb_counts)
        barb_die_value = BARB_DIE_VALUES[mhf.get_index_from_cdf(barb_die_cdf)]

        return DiceRole(dice_total, red_die_value, barb_die_value)

    def _add_role(self, dice_role, save_state=True):

        self.role_log.append(dice_role)

        count = 1
        if dice_role.undo:
            count = -1

        self.value_counts[dice_role.value] += count
        self.barb_counts[dice_role.barb_die] += count
        if dice_role.barb_die != 'barbarians':
            self.red_counts[(dice_role.red_value, dice_role.barb_die)] += count
        if not self.simulate:
            self.save_game_state()

    def role(self, quite=False):
        dice_role = self._generate_new_dice_role()
        if not quite:
            print(dice_role)

        self._add_role(dice_role)

    def undo_role(self, index=None, offset=-1, quite=False, force=False):
        if index is not None:
            offset = index - len(self.role_log)
        undo_role = deepcopy(self.role_log[offset])
        # check if the role has already been undo.
        if undo_role.undo:
            if not force:
                raise Exception("To undo your undo call again with force.")
        undo_role.undo = not undo_role.undo
        if not quite:
            print(undo_role)
        self._add_role(undo_role)

    def get_expected_counts(self):
        return self.probability_handler.get_expected_counts(value_counts=self.value_counts)

    def get_count_percents(self):
        return self.probability_handler.get_expected_count_percent(self.value_counts)

    def get_weighted_devation_from_normal(self):
        count_percents = self.get_count_percents()
        return sum([abs(1 - count_percents[index]) * odds for index, odds in enumerate(self.probability_handler.BASE_ODDS)]) / 11

    def _get_save_game_path(self):
        return os.path.join(self.DEFAULT_SAVE_FOLDER, "{}.csv".format(self.game_name))

    def save_game_state(self):
        """Save out all roles to a CSV"""

        # check if save directory exists
        if not os.path.isdir(self.DEFAULT_SAVE_FOLDER):
            os.mkdir(self.DEFAULT_SAVE_FOLDER)

        # write out game state
        with open(self._get_save_game_path(), 'w') as csv_file:
            role_log_writer = csv.writer(csv_file, delimiter=',')
            for role in self.role_log:
                role_log_writer.writerow([role.value, role.red_value, role.barb_die, role.undo])

    def load_game_state_from_file(self, file_path):
        roles_list = []

        with open(file_path, 'r') as csv_file:
            role_log_reader = csv.reader(csv_file, delimiter=",")
            for line in role_log_reader:
                # FIXME: the way a handle False here is fobar.
                roles_list.append(DiceRole(line[0], red_value=line[1], barb_die=line[2], undo=line[3]!="False"))

        # Read the whole thing before adding. Adding will default try to save the state and update the file.
        for role in roles_list:
            self._add_role(role, save_state=False)


    def plot_roles(self):

        print("After {} rounds. x or + represent roles, - is represents number of rules under expected, + the number over".format(
                sum(self.value_counts.values())))

        scale_factor = math.ceil(max(self.value_counts.values()) / 40)
        expected_values = self.get_expected_counts()

        for value in range(2, 13):
            scaled_expected_value = round(expected_values[value] / scale_factor)
            scaled_counts = self.value_counts[value] // scale_factor

            over_production = 0
            under_production = 0
            if scaled_expected_value >= scaled_counts:
                under_production = scaled_expected_value - scaled_counts
                display_counts = scaled_counts
            else:
                over_production = scaled_counts - scaled_expected_value
                display_counts = scaled_expected_value

            print("{:2}: {}".format(value, "x" * display_counts + under_production * "-" + over_production * "+"))

    def role_and_plot(self):
        self.role()
        self.plot_roles()


def simulate_game(normalizer=2, n_roles=100):
    """Simulate a game."""
    game = SuperNormalGame(normalizer=normalizer, game_name="test_game", simulate=True)
    for i in range(n_roles):
        game.role(quite=True)
    print("Simulated game with normalizer {}".format(normalizer))
    game.plot_roles()
    print(game.barb_counts,  game.barb_counts['barbarians'] / sum(game.barb_counts.values()))

    return game

def simulate_spread(n_roles=100):
    """Simulate a spread of games to see what normalizer feels right to you."""
    for nor in [0, .5, 1, 2, 5, 10, 100]:
        for i in range(3):
            simulate_game(nor, n_roles)

def kill_all_of_some_value(game, value):
    """
    Take a game and turn the total value count for some value to zero.

    This is useful for simulation to watch that value come back near normal.
    """

    # count the number of valid sixes.
    value_count = sum([1 for role in game.role_log if role.value == value and not role.undo])

    # find a six.
    for index in range(len(game.role_log)):
        if game.role_log[index].value == value and not game.role_log[index].undo:
            break
    for six in range(value_count):
        game.undo_role(index=index)

