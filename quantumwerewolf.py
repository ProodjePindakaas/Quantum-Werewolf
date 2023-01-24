from itertools import permutations
from random import shuffle, choice


class Game:

    def __init__(self):
        self.players = []
        self.role_count = {'werewolf': 2, 'seer': 1}
        self.player_count = 10
        self.started = False
        self.verbose = False

    # Add players to the game
    def add_players(self, *names):
        # name: the name (or list of names) of the player(s) to add

        # The game can't be ongoing
        if not self.check_started(False):
            return None

        # Add names from input and input lists
        for name in names:
            if isinstance(name, str):
                # Check if name is not already taken
                if name in self.players:
                    if sel.verbose:
                        print("Player {} already exists!".format(name))
                else:
                    self.players.append(name)
            elif isinstance(name, list):
                # unwrap list and pass to add_players again
                self.add_players(*name)
            else:
                if self.verbose:
                    print("Wrong data type: {}, must be either string or list of strings".format(type(name)))

    # Set the contents of the deck
    def set_role(self, role, amount):
        # roles: [werewolves, seers]
        self.role_count[role] = amount

    # Identify the player names with their IDs
    # def identify_players(self):
    #     self.player_count = len(self.players)
    #     idfy = [[i+1, self.players[i]] for i in range(self.player_count)]
    #     print(tabulate(idfy, headers = ["ID", "Name"]))

    # Start the game
    def start(self):
        if self.check_started(False):

            # Determine playercount or generate players if none are given
            if self.players != []:
                self.player_count = len(self.players)
            else:
                self.players = ["Player " + str(x+1) for x in range(self.player_count)]

            # Generate permutation list for anomymous printing in print_probabilities()
            self.print_permutation = list(range(self.player_count))
            shuffle(self.print_permutation)

            # Determine (valid) amount of villager in the game
            villagers = self.player_count - sum(self.role_count.values())
            if villagers < 0:
                if self.verbose:
                    print("Too few players, decrease the amount of roles!")
                return False

            # Sets the list of roles
            roles = self.role_count['werewolf'] * ["w"] + self.role_count['seer'] * ["s"] + villagers * ["v"]
            self.werewolf_count = self.role_count['werewolf']

            # Generates the list of all role permutations
            self.permutations = list(permutations(roles))

            # Set all players to be fully alive
            self.deaths = []
            for i in range(self.player_count):
                self.deaths += [[0] * self.player_count]
            self.killed = [0] * self.player_count

            # start game
            self.started = True

            if self.verbose:
                print("Game started.")

            self.calculate_probabilities()

            return True

    # Stop the game
    def stop(self):
        if self.check_started():
            self.started = False
            if self.verbose:
                print("Game stopped.")

    # Reset the game
    def reset(self):
        self.players = []
        self.role_count = {'werewolf': 2, 'seer': 1}
        if self.started:
            self.stop()
        if self.verbose:
            print("Game reset.")

    # Check if game has(n't) started and throw error otherwise
    def check_started(self, boolean=True):
        # boolean: set this to false if you want to check if you HAVEN'T started yet
        # The point of this function is to throw an error if the game hasn't started yet
        if self.started == boolean:
            return True
        else:
            if boolean:
                if self.verbose:
                    print("Please start the game first with start().")
                return False
            else:
                if self.verbose:
                    print("Please stop the game first with stop().")
                return False

    # Returns the ID corresponding to someone's name
    def ID(self, player_name):
        # name: the name of the player
        return self.players.index(player_name)

    # Returns the ID corresponding to someone's name
    def name(self, player_id):
        # name: the name of the player
        return self.players[player_id]

    # Return the role corresponding to some letter
    def role(self, letter):
        # letter: the letter who's corresponding role you want to know
        roles = ["villager", "werewolf", "seer"]
        letters = ["v", "w", "s"]
        return roles[letters.index(letter)]

    # Gives the table of probabilities
    def print_probabilities(self):
        if self.check_started():
            self.calculate_probabilities()
            print("There are {} possible permutations left.\n".format(self.nperm))
            headers = ["Player", "Villagers", "Seer", "Werewolf", "Dead"]
            print("{:>12s}{:>12s}{:>12s}{:>12s}{:>12s}".format(*headers))
            for i, j in enumerate(self.print_permutation):
                p = self.probs[j]
                if p['dead'] == 1:
                    i = p['name']
                values = [str(i), 100*p['villager'], 100*p['seer'], 100*p['werewolf'], 100*p['dead']]
                print("{:>12s}{:11.0f}%{:11.0f}%{:11.0f}%{:11.0f}%".format(*values))

    # Calculates the probabilities
    def calculate_probabilities(self):
        if self.check_started():
            self.nperm = len(self.permutations)
            transpose = list(zip(*self.permutations))
            self.probs = []
            for i, p in enumerate(self.players):
                P_villager = transpose[i].count("v") / self.nperm
                P_seer = transpose[i].count("s") / self.nperm
                P_werewolf = transpose[i].count("w") / self.nperm
                P_dead = self.death_probability(p)
                self.probs.append({'name': p,
                                   'werewolf': P_werewolf,
                                   'villager': P_villager,
                                   'seer': P_seer,
                                   'dead': P_dead})

    # Let a player take his seer action
    def seer(self, seer, target):
        # seer: name of the seer
        # target: name of the target of the seer
        if self.check_started():
            seer_id = self.ID(seer)
            target_id = self.ID(target)

            # Check if player and target are alive and player can be the seer
            assert self.killed[seer_id] != 1, "ERROR: in seer() seer {} is dead.".format(seer)
            assert self.killed[target_id] != 1, "ERROR: in seer() target {} is dead.".format(target)
            assert self.probs[seer_id]['seer'] != 0, "ERROR: in seer() {}'s seer probability is 0.".format(seer)

            # Player is allowed to take the action
            if self.verbose:
                print("{} is investigating {} ...".format(seer, target))
            p_list = [p for p in self.permutations if p[seer_id] == 's']

            # Choose an outcome
            assert len(p_list) > 0, "ERROR: seer list is empty"
            observation = choice(p_list)[target_id]
            target_role = self.role(observation)

            # Collapse the wave function
            for p in p_list:
                if p[target_id] != observation:
                    self.permutations.remove(p)

            # Report on results
            if self.verbose:
                print(f"{seer} sees that {target} is a {target_role}!")

            return target_role

    # Force someone's death (e.g., after a vote). Otherwise used only by script
    def kill(self, target):
        # target: the name of the target
        target_id = self.ID(target)
        if self.check_started():
            assert self.killed[target_id] != 1, "ERROR:in kill() target {} is already dead.".format(target)

            if self.verbose:
                print("{} was killed!".format(target))

            # Chooses an outcome
            res = choice(self.permutations)
            prole = res[target_id]
            permt = list(self.permutations)

            # Collapse the wave function
            for p in permt:
                if p[target_id] != prole:
                    self.permutations.remove(p)

            target_role = self.role(prole)

            # Report on results
            if self.verbose:
                print(f"{target} was a {target_role}!")

            # Deal with the case that the dead person is a werewolf
            if self.role(prole) == "w":
                self.werewolf_count -= 1
                for i in range(self.player_count):
                    self.deaths[i][target_id] = 0

            self.killed[target_id] = 1
            self.calculate_probabilities()

            return target_role

    # Shows the probability of death for a player
    def death_probability(self, name):
        # name: name of player
        name_id = self.ID(name)
        if self.check_started():
            dead = 0
            if self.killed[name_id] == 1:
                dead = 1
            else:
                deathn = 0
                for p in self.permutations:
                    for i in range(self.player_count):
                        if p[i] == "w" and p[name_id] != "w":
                            deathn += self.deaths[name_id][i]
                dead = deathn / len(self.permutations)
                if dead >= 1:
                    self.kill(name)
            return dead

    # Lets someone commit their werewolf action
    def werewolf(self, werewolf, target):
        # werewolf: the name of the werewolf
        # target: the name of the werewolf's target
        werewolf_id = self.ID(werewolf)
        target_id = self.ID(target)
        if self.check_started():
            assert self.killed[werewolf_id] != 1, "ERROR: in werewolf() werewolf {} is dead".format(werewolf)
            assert self.killed[target_id] != 1, "ERROR: in werewolf() target {} is dead".format(target)
            assert self.probs[werewolf_id]['werewolf'] != 0, "ERROR: in werewolf() {}'s werewolf probability is 0".format(target)

            self.deaths[target_id][werewolf_id] = 1 / self.werewolf_count
            if self.verbose:
                print("{} has mauled {}!".format(werewolf, target))

    def check_win(self):
        villager_win = True
        werewolf_win = True
        for perm in self.permutations:
            for ID, role in enumerate(perm):
                if self.killed[ID] == 0:
                    if role == 'w':
                        villager_win = False
                    else:
                        werewolf_win = False
        if villager_win:
            print('The villagers win!')
            return True
        if werewolf_win:
            print('The werewolves win!')
            return True
        return False
