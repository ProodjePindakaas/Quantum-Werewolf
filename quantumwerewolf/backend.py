"""The Module's docstring"""

from itertools import permutations
from random import shuffle, choice
from functools import wraps
from typing import Callable, List, Tuple, Union
from math import sqrt
import logging

logger = logging.getLogger(__name__)


class Player:

    def __init__(self, index, name):
        self.index = index
        self.name = name
        self.killed = False
        self.logger = logging.getLogger(__name__)
        # can put lover list here


class Game:
    """Object keeping track of game state."""

    default_roles = {
            'werewolf': 2,
            'seer': 1,
            'hunter': 0,
            'cupid': 0,
            }

    def __init__(self):
        self.players = []
        self.role_count = Game.default_roles.copy()
        self.player_count = 0
        self.started = False
        self.logger = logging.getLogger(__name__)
        # optional rules
        self.werewolf_cannot_eat_werewolf = False
        self.max_permutations = 20

    # HELPER FUNCTIONS

    def started(value: bool = True) -> Callable:
        """Return decorator that return decorated function that only runs when the game has started (or not).

        Arguments:
            value: bool -- required value of Game.started for the decorated function to run (default: True)
        """
        def decorator(function: Callable) -> Callable:
            @wraps(function)
            def wrapper(self, *args: object, **kwargs: object) -> object:
                if self.started == value:
                    return function(self, *args, **kwargs)
                else:
                    raise ValueError(f'Game.started equal {self.started} when it should be {value}')
            return wrapper
        return decorator

    def _id(self, player_name: str) -> int:
        """Return index of a player name.

        Arguments:
            player_name: str -- name of a player in Game.players
        """
        return self.player_ids[player_name]

    def _name(self, player_id: int) -> str:
        """Return the name of a player index.

        Arguments:
            player_id: str -- index of player in Game.add_players
        """
        return self.players[player_id]

    def expected_total_deviation(self):
        """Return the total expected role ratio deviation.

            $$ TD = \\sum_{role} \\sqrt{p_{role} (1 - p_{role})} $$
        """
        ratios = [count / self.player_count for count in self.role_count.values()]
        deviations = [sqrt(p * (1 - p)) for p in ratios]
        return sum(deviations)

    # SETUP METHODS

    @started(False)
    def add_players(self, *names: Union[str, List[str]]) -> None:
        """Add players to the Game.players list.

        Arguments:
            names: str | List[str] -- names of players or lists of names of players.
        """
        self.logger.debug(f"running add_players({names})")
        # Add names from input and input lists
        for name in names:
            if isinstance(name, str):
                # Check if name is not already taken
                if name in self.players:
                    # TODO: check if logging is applicatble
                    self.logger.warning("Player {} already exists!".format(name))
                else:
                    self.players.append(name)
                    self.logger.info(f"Adding player {name}")
            elif isinstance(name, list):
                # unwrap list and pass to add_players again
                self.add_players(*name)
            else:
                raise ValueError("Wrong data type: must be either string or list of strings")

    @started(False)
    def set_role(self, role: str, amount: int) -> None:
        """Set the amount of players to assign a given role to at the start of the game.

        Arguments:
            role: str -- name of a role
            amount: int -- the amount of players with the given role
        """
        self.logger.debug(f"running set_role({role}, {amount})")
        self.role_count[role] = amount
        self.logger.info(f'Setting amount of {role} role to {amount}')

    @started(False)
    def start(self) -> bool:
        """Start the game and return succes boolean."""
        self.logger.debug("running start()")

        # Determine playercount
        self.player_count = len(self.players)
        self.logger.info(f"number of players is {self.player_count}")
        if self.player_count == 0:
            self.logger.warning('No players in current game. Failed to start game.')
            return False

        # create lookup dictionary of player ids
        self.logger.info('Creating Lookup dictionary for player indices')
        self.player_ids = {player: player_id for player_id, player in enumerate(self.players)}

        # Generate permutation list for anomymous printing in print_probabilities()
        self.print_permutation = list(range(self.player_count))
        shuffle(self.print_permutation)
        self.logger.info(f'Random player order in tables is {self.print_permutation}')

        # Determine (valid) amount of villager in the game
        villager_count = self.player_count - sum(self.role_count.values())
        self.logger.info(f'Number of villagers is {villager_count}')
        if villager_count < 0:
            self.logger.warning("Too many roles for number of players. Failed to start game.")
            return False
        self.role_count['villager'] = villager_count

        # Sets the list of roles
        self.used_roles = [role for role, count in self.role_count.items() if count > 0]
        self.logger.info(f'Roles used in game are {self.used_roles}')

        self.werewolf_count = self.role_count['werewolf']
        self.logger.info(f'Number of live werewolves is {self.werewolf_count}')

        # Generates the list of all role permutations
        self.logger.info('Generating all role permutations')
        roles = [role for role, count in self.role_count.items() for _ in range(count)]
        self.logger.debug(f'role frequencies: {roles}')
        # full permutation game
        self.permutations = {p: True for p in permutations(roles)}
        # random subset game
        # self.permutations = {p: True for p in permutations(roles) if random() < self.permutation_fraction}
        # optimal deviation game
        # n_permutations =  (self.expected_total_deviation() / optimal_total_deviation) ** 2
        # self.permutations = {shuffle(roles).copy(): True for _ in range(n_permutations)}
        self.logger.debug(f'number of permutations: {len(self.permutations)}')

        # Set all players to be fully alive
        self.logger.info('Initializing attacked and killed list')
        self.deaths = []
        for i in range(self.player_count):
            self.deaths += [[0] * self.player_count]
        self.killed = [False] * self.player_count

        # create list of cupid lovers
        self.logger.info('Initializing cupids lovers list')
        self.lovers_list = {}

        # start game
        self.logger.info('Set Game.started to True and turn to 0')
        self.started = True
        self.turn_counter = 0

        return True

    @started()
    def stop(self) -> None:
        """Stop the game."""
        self.logger.debug("running stop()")
        self.started = False
        # TODO: delete game state objects?
        self.logger.info("Game stopped.")
        return True

    def reset(self) -> None:
        """Set all values to default and stop the game if started."""
        self.logger.debug("running reset()")
        self.players = []
        self.player_count = 0
        self.role_count = Game.default_roles.copy()
        if self.started:
            self.stop()
        self.logger.info("Game reset.")

    # GAME INFO METHODS

    @started()
    def valid_permutations(self) -> List[List[str]]:
        """Return all possible game states."""
        return [p for p in self.permutations if self.permutations[p]]

    def living_players(self) -> List[str]:
        """Return all players that are still alive."""
        return [player for player_id, player in enumerate(self.players) if self.killed[player_id] == 0]

    @started()
    def check_deaths(self) -> List[str]:
        """Return names of players that have died but are not marked as such."""
        self.logger.debug("running check_deaths()")
        killed_players = []
        for player_id, player in enumerate(self.players):
            p_dead = self.death_probability(player)
            if self.killed[player_id] == 0 and p_dead >= 1:
                killed_players.append(player)
        return killed_players

    @started()
    def role_probabilities(self) -> Tuple[dict, ...]:
        """Return table of probability per role per player."""
        self.logger.debug("running role_probabilities()")
        p_list = self.valid_permutations()
        transpose = list(zip(*p_list))
        probs = []
        for i, p in enumerate(self.players):
            player_probs = {'name': p}
            for role in self.used_roles:
                player_probs[role] = transpose[i].count(role) / len(p_list)
            player_probs['dead'] = self.death_probability(p)
            probs.append(player_probs)
        return tuple(probs)

    # computes the probability of death for a player TODO: rewrite to calculate all probabilities at once
    def death_probability(self, player: str) -> float:
        """ Return the probability that a player has died.

        Arguments:
            player: str -- Player for which to compute the death probability.
        """
        self.logger.debug(f"running death_probability({player})")
        # name: name of player
        player_id = self._id(player)
        if self.killed[player_id] == 1:
            return 1

        total_attacks = 0
        p_list = self.valid_permutations()
        for p in p_list:
            # check for lover in permutation
            lover_id = self._lover(p, player_id)

            # count attacks by werewolves in this permutation
            werewolf_attacks = self._werewolf_attack(p, player_id)

            # count attacks by werewolves on lover in this permutation
            lover_werewolf_attacks = 0
            if lover_id is not None:
                if self.killed[lover_id] == 1:
                    lover_werewolf_attacks = 1  # TODO: rename this as it also checks if lover is killed by other means
                else:
                    lover_werewolf_attacks = self._werewolf_attack(p, lover_id)

            total_attacks += max(werewolf_attacks, lover_werewolf_attacks)

        P_dead = total_attacks / len(p_list)

        return P_dead

    @started()
    def other_werewolves(self, werewolf: str) -> List[dict]:
        """Returns a table of players and their probabilities to be a werewolf simultaneously as a given werewolf.

        Arguments:
            werewolf: str -- name of player assumed to be a werewolf.
        """
        self.logger.debug(f"running other_werewolves({werewolf})")
        # Gives the probabilities of all other players being a werewolf
        werewolf_id = self._id(werewolf)
        p_list = self.valid_permutations()
        projection = [p for p in p_list if p[werewolf_id] == 'werewolf']

        if not projection:
            return []

        n_projection = len(projection)
        transpose = list(zip(*projection))

        probs = []
        for i, p in enumerate(self.players):
            P_werewolf = transpose[i].count("werewolf") / n_projection
            probs.append({'name': p, 'werewolf': P_werewolf})

        return probs

    @started()
    def other_lover(self, player: str) -> List[dict]:
        """Return table of players and their probabilities to be the lover of a given player.

        Arguments:
            player: str -- name of player
        """
        self.logger.debug(f"running other_lover({player})")
        player_id = self._id(player)

        lover_count_list = [0] * self.player_count
        p_list = self.valid_permutations()
        if self.lovers_list:
            if self.role_count['cupid'] > 0:
                for p in p_list:
                    cupid_id = p.index('cupid')
                    lover1, lover2 = self.lovers_list[cupid_id]
                    if player_id == lover1:
                        lover_count_list[lover2] += 1
                    elif player_id == lover2:
                        lover_count_list[lover1] += 1

        probs = []
        for i, p in enumerate(self.players):
            P_lover = lover_count_list[i] / len(p_list)
            probs.append({'name': p, 'lover': P_lover})

        return probs

    @started()
    def check_win(self) -> Tuple[bool, str]:
        """Return wether any win condition is met and if so the faction that won."""
        all_dead = True
        villager_win = True
        werewolf_win = True
        lover_win = True

        p_list = self.valid_permutations()
        for p in p_list:
            lovers = ()
            if 'cupid' in p:
                cupid_id = p.index('cupid')
                lovers = self.lovers_list[cupid_id]
            for ID, role in enumerate(p):
                if self.killed[ID] == 0:
                    all_dead = False
                    if role == 'werewolf':
                        villager_win = False
                    else:
                        werewolf_win = False
                    if ID not in lovers:
                        lover_win = False

        if all_dead:
            self.logger.info('the game is a tie')
            return True, None
        if villager_win:
            self.logger.info('The villagers win')
            return True, 'villagers'
        if werewolf_win:
            self.logger.info('The werewolves win')
            return True, 'werewolves'
        if lover_win:
            self.logger.info('The lovers win')
            return True, 'lovers'
        return False, None

    # TODO: research if player loop and role loop need to be reversed
    @started()
    def process_night(self, actions):
        self.logger.debug(f"running process_night({actions})")
        for player, player_actions in actions.items():
            for role, args in player_actions.items():
                if role == 'cupid':
                    self.cupid(player, *args)
                elif role == 'seer':
                    self.seer(player, *args)
                elif role == 'werewolf':
                    self.werewolf(player, args)

    # ROLE ACTIONS

    @started()
    def cupid(self, cupid: str, lover1: str, lover2: str) -> None:
        """Perform cupid action for a player. Records the lover pair in Game.lovers_list."""
        self.logger.debug(f"running cupid({cupid}, {lover1}, {lover2})")
        cupid_id = self._id(cupid)
        lovers = (self._id(lover1), self._id(lover2))
        self.lovers_list[cupid_id] = lovers

    @started()
    def seer(self, seer: str, target: str, target_role: str = None, project: bool = True) -> str:
        """Perform the seer action for a players. Return target's role and collapse game state..

        Arguments:
            seer: str -- name of playerperforming the seer action.
            target: str -- name of target of the seer action
        """
        self.logger.debug(f"running seer({seer}, {target}, target_role={target_role}, project={project})")
        seer_id = self._id(seer)
        target_id = self._id(target)

        # Check if player and target are alive and player can be the seer
        assert self.killed[seer_id] != 1, "ERROR: in seer() seer {} is dead.".format(seer)
        assert self.killed[target_id] != 1, "ERROR: in seer() target {} is dead.".format(target)
        # assert self.probs[seer_id]['seer'] != 0, "ERROR: in seer() {}'s seer probability is 0.".format(seer)

        # Player is allowed to take the action
        self.logger.info("{} is investigating {} ...".format(seer, target))
        p_list = self.valid_permutations()
        projection = [p for p in p_list if p[seer_id] == 'seer']

        if projection:
            # Choose an outcome
            if target_role is None:
                target_role = choice(projection)[target_id]

            # Collapse the wave function
            if project:
                for p in projection:
                    if p[target_id] != target_role:
                        self.permutations[p] = False

        # Report on results
        self.logger.info(f"{seer} sees that {target} is a {target_role}!")

        return target_role

    @started()
    def werewolf(self, werewolf, target):
        """Perform werewolf action for a player. Mark the attack in Game.deaths.
        Optionally collapses the game to exclude werewolves targeting werewolves. [CAUSES PROBLEMS]

        Arguments:
            werewolf: str -- name of the player performing the werewolf action
            target: str -- name of target of the werewolf action

        kill chance is 1 over number of werewolves still alive.
        If werewolves may not eat other werewolves then all permutations in which acting player and target are both werewolves are no longer possible.
        """
        self.logger.debug(f"running werewolf({werewolf}, {target})")
        assert werewolf != target, "ERRROR: in werwwolf() werewolf == target."
        werewolf_id = self._id(werewolf)
        target_id = self._id(target)
        assert self.killed[werewolf_id] != 1, "ERROR: in werewolf() werewolf {} is dead".format(werewolf)
        assert self.killed[target_id] != 1, "ERROR: in werewolf() target {} is dead".format(target)
        # assert self.probs[werewolf_id]['werewolf'] != 0, "ERROR: in werewolf() {}'s werewolf probability is 0".format(target)

        self.deaths[target_id][werewolf_id] = 1 / self.werewolf_count

        if self.werewolf_cannot_eat_werewolf:
            # project such that target and werewolf can't be both werewolves
            p_list = self.valid_permutations()
            for p in p_list:
                if p[werewolf_id] == 'werewolf' and p[target_id] == 'werewolf':
                    self.permutations[p] = False

    @started()
    def kill(self, target: str) -> str:
        """Kill and identify a player. Return the player's role and collapses the game state.

        Arguments:
            target: str -- name of player to kill.
        """
        self.logger.debug(f"running kill({target})")
        target_id = self._id(target)
        assert self.killed[target_id] != 1, "ERROR:in kill() target {} is already dead.".format(target)

        self.logger.info("{} was killed!".format(target))

        # Chooses an outcome
        p_list = self.valid_permutations()
        result = choice(p_list)
        target_role = result[target_id]

        # Collapse the wave function
        for p in p_list:
            if p[target_id] != target_role:
                self.permutations[p] = False

        # Report on results
        self.logger.info(f"{target} was a {target_role}!")

        # Deal with the case that the dead person is a werewolf
        if target_role == "werewolf":
            self.werewolf_count -= 1
            for i in range(self.player_count):
                self.deaths[i][target_id] = 0

        self.killed[target_id] = 1

        return target_role

    def _lover(self, permutation: List[str], player_id: int) -> int:
        """Return the index of the lover of a player in a given permutation if they exits, otherwise returns None.

        Arguments:
            permutation: List[str] -- permutation in which to check for lover.
            player_id: int -- index of player for which to check lover.
        """
        if self.role_count['cupid'] == 0 or not self.lovers_list:
            return None
        lover_id = None
        cupid_id = permutation.index('cupid')
        lover1, lover2 = self.lovers_list[cupid_id]
        if player_id == lover1:
            lover_id = lover2
        elif player_id == lover2:
            lover_id = lover1
        return lover_id

    def _werewolf_attack(self, permutation: List[str], player_id: int) -> int:
        """Return the total sum of werewolf attacks of a player in a given permutation.

        Arguments:
            permutation: List[str] -- permutation in which to sum the werewolf attacks.
            player_id: int -- index of player for which to check werewolf attacks.
        """
        werewolf_attacks = 0
        for i in range(self.player_count):
            if permutation[i] == "werewolf" and permutation[player_id] != "werewolf":
                werewolf_attacks += self.deaths[player_id][i]
        return werewolf_attacks

    # TODO
    """
    # count attacks by werewolves in this permutation
    def _werewolf_attacks(self, permutation):
        werewolf_attacks = [0] * self.player_count
        for i in range(self.player_count):
            if permutation[i] == "werewolf":
                werewolf_attacks += self.deaths[player_id][i]
        return werewolf_attacks

    # computes the probability of death for a player TODO: rewrite to calculate all probabilities at once
    def death_probabilities(self):
        # name: name of player
        P_dead = [1 if self.killed[player_id] else 0 for player_id in range(self.player_count)]

        # compute total werewolf death probabilities
        p_list = self.valid_permutations()
        for p in p_list:
            pass

        return P_dead
    """
