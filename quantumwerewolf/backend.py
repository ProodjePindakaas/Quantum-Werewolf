"""The Module's docstring"""

from itertools import permutations
from random import shuffle, choice
from functools import wraps
from typing import Callable, List, Tuple, Union
import logging


class Player:

    def __init__(self, index, name):
        self.index = index
        self.name = name
        self.killed = False
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
        # optional rules
        self.werewolf_cannot_eat_werewolf = True

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

    @started(False)
    def add_players(self, *names: Union[str, List[str]]) -> None:
        """Add players to the Game.players list.

        Arguments:
            names: str | List[str] -- names of players or lists of names of players.
        """
        # Add names from input and input lists
        for name in names:
            if isinstance(name, str):
                # Check if name is not already taken
                if name in self.players:
                    logging.warning("Player {} already exists!".format(name))
                else:
                    self.players.append(name)
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
        self.role_count[role] = amount

    @started(False)
    def start(self) -> bool:
        """Start the game and return succes boolean."""

        # Determine playercount
        logging.info('Determining player count')
        self.player_count = len(self.players)
        if self.player_count == 0:
            logging.warning('No players in current game. Failed to start game.')
            return False

        # create lookup dictionary of player ids
        logging.info('Creating Lookup dictionary for player indices')
        self.player_ids = {player: player_id for player_id, player in enumerate(self.players)}

        # Generate permutation list for anomymous printing in print_probabilities()
        logging.info('Generating random permutation of players for anonimity in tables')
        self.print_permutation = list(range(self.player_count))
        shuffle(self.print_permutation)

        # Determine (valid) amount of villager in the game
        logging.info('Determining amount of villagers')
        villager_count = self.player_count - sum(self.role_count.values())
        if villager_count < 0:
            logging.warning("Too many roles for number of players. Failed to start game.")
            return False
        self.role_count['villager'] = villager_count

        # Sets the list of roles
        logging.info('Setting the list of roles used')
        self.used_roles = [role for role, count in self.role_count.items() if count > 0]
        logging.info('Determining the number of living werewolves')
        self.werewolf_count = self.role_count['werewolf']

        # Generates the list of all role permutations
        logging.info('Generating all role permutations')
        roles = [role for role, count in self.role_count.items() for _ in range(count)]
        self.permutations = {p: True for p in permutations(roles)}

        # Set all players to be fully alive
        logging.info('Initializing death tracking')
        self.deaths = []
        for i in range(self.player_count):
            self.deaths += [[0] * self.player_count]
        self.killed = [False] * self.player_count

        # create list of cupid lovers
        logging.info('Initializing cupids lover tracking')
        self.lovers_list = {}

        # start game
        logging.info('Set Game.started to True')
        self.started = True

        logging.info('Returning success')
        return True

    @started
    def stop(self) -> None:
        """Stop the game."""
        self.started = False
        # TODO: delete game state objects?
        logging.info("Game stopped.")
        return True

    def reset(self) -> None:
        """Set all values to default and stop the game if started."""
        self.players = []
        self.player_count = 0
        self.role_count = Game.default_roles.copy()
        if self.started:
            self.stop()
        logging.info("Game reset.")

    @started
    def valid_permutations(self) -> List[List[str]]:
        """Return all possible game states."""
        return [p for p in self.permutations if self.permutations[p]]

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

    def living_players(self) -> List[str]:
        """Return all players that are still alive."""
        return [player for player_id, player in enumerate(self.players) if self.killed[player_id] == 0]

    @started
    def calculate_probabilities(self) -> Tuple[dict, ...]:
        """Return table of probability per role per player."""
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

    @started
    def cupid(self, cupid: str, lover1: str, lover2: str) -> None:
        """Perform cupid action for a player. Records the lover pair in Game.lovers_list."""
        cupid_id = self._id(cupid)
        lovers = (self._id(lover1), self._id(lover2))
        self.lovers_list[cupid_id] = lovers

    @started
    def seer(self, seer: str, target: str) -> str:
        """Perform the seer action for a players. Return target's role and collapse game state..

        Arguments:
        seer: str -- name of playerperforming the seer action.
        target: str -- name of target of the seer action
        """
        seer_id = self._id(seer)
        target_id = self._id(target)

        # Check if player and target are alive and player can be the seer
        assert self.killed[seer_id] != 1, "ERROR: in seer() seer {} is dead.".format(seer)
        assert self.killed[target_id] != 1, "ERROR: in seer() target {} is dead.".format(target)
        assert self.probs[seer_id]['seer'] != 0, "ERROR: in seer() {}'s seer probability is 0.".format(seer)

        # Player is allowed to take the action
        logging.info("{} is investigating {} ...".format(seer, target))
        p_list = [p for p in self.permutations if p[seer_id] == 'seer' and self.permutations[p]]

        # Choose an outcome
        assert p_list, "ERROR: seer list is empty"
        target_role = choice(p_list)[target_id]

        # Collapse the wave function
        for p in p_list:
            if p[target_id] != target_role:
                self.permutations[p] = False

        # Report on results
        logging.info(f"{seer} sees that {target} is a {target_role}!")

        return target_role

    @started
    def kill(self, target: str) -> str:
        """Kill and identify a player. Return the player's role and collapses the game state.

        Arguments:
            target: str -- name of player to kill.
        """
        target_id = self._id(target)
        assert self.killed[target_id] != 1, "ERROR:in kill() target {} is already dead.".format(target)

        logging.info("{} was killed!".format(target))

        # Chooses an outcome
        p_list = [p for p in self.permutations if self.permutations[p]]
        result = choice(p_list)
        target_role = result[target_id]

        # Collapse the wave function
        for p in p_list:
            if p[target_id] != target_role:
                self.permutations[p] = False

        # Report on results
        logging.info(f"{target} was a {target_role}!")

        # Deal with the case that the dead person is a werewolf
        if target_role == "werewolf":
            self.werewolf_count -= 1
            for i in range(self.player_count):
                self.deaths[i][target_id] = 0

        self.killed[target_id] = 1

        return target_role

    @started
    def check_deaths(self) -> List[str]:
        """Return names of players that have died since last check."""
        killed_players = []
        for player_id, player in enumerate(self.players):
            p_dead = self.death_probability(player)
            if self.killed[player_id] == 0 and p_dead >= 1:
                killed_players.append(player)
        return killed_players

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

    # computes the probability of death for a player TODO: rewrite to calculate all probabilities at once
    def death_probability(self, player: str) -> float:
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

    @started
    def werewolf(self, werewolf, target):
        """Perform werewolf action for a player. Mark the attack in Game.deaths.
        Optionally collapses the game to exclude werewolves targeting werewolves.

        Arguments:
            werewolf: str -- name of the player performing the werewolf action
            target: str -- name of target of the werewolf action

        kill chance is 1 over number of werewolves still alive.
        If werewolves may not eat other werewolves then all permutations in which acting player and target are both werewolves are no longer possible.
        """
        werewolf_id = self._id(werewolf)
        target_id = self._id(target)
        assert self.killed[werewolf_id] != 1, "ERROR: in werewolf() werewolf {} is dead".format(werewolf)
        assert self.killed[target_id] != 1, "ERROR: in werewolf() target {} is dead".format(target)
        assert self.probs[werewolf_id]['werewolf'] != 0, "ERROR: in werewolf() {}'s werewolf probability is 0".format(target)

        self.deaths[target_id][werewolf_id] = 1 / self.werewolf_count

        if self.werewolf_cannot_eat_werewolf:
            # project such that target and werewolf can't be both werewolves
            p_list = self.valid_permutations()
            for p in p_list:
                if p[werewolf_id] == 'werewolf' and p[target_id] == 'werewolf':
                    self.permutations[p] = False

    @started
    def other_werewolves(self, werewolf: str) -> List[dict]:
        """Returns a table of players and their probabilities to be a werewolf simultaneously as a given werewolf.

        Arguments:
            werewolf: str -- name of player assumed to be a werewolf.
        """
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

    @started
    def other_lover(self, player: str) -> List[dict]:
        """Return table of players and their probabilities to be the lover of a given player.

        Arguments:
            player: str -- name of player
        """
        player_id = self._id(player)
        lover_count_list = [0] * self.player_count

        p_list = self.valid_permutations()
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

    @started
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
            logging.info('the game is a tie')
            return True, None
        if villager_win:
            logging.info('The villagers win')
            return True, 'villagers'
        if werewolf_win:
            logging.info('The werewolves win')
            return True, 'werewolves'
        if lover_win:
            logging.info('The lovers win')
            return True, 'lovers'
        return False, None
