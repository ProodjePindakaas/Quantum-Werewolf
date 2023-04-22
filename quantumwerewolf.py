from itertools import permutations
from random import shuffle, choice


class Game:

    def __init__(self):
        self.players = []
        self.role_count = {
            'werewolf': 2,
            'seer': 1,
            'hunter': 0,
            'cupid': 0,
            }
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
                    if self.verbose:
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
            villager_count = self.player_count - sum(self.role_count.values())
            if villager_count < 0:
                if self.verbose:
                    print("Too few players, decrease the amount of roles!")
                return False
            self.role_count['villager'] = villager_count

            # Sets the list of roles
            self.used_roles = [role for role, count in self.role_count.items() if count > 0]
            self.werewolf_count = self.role_count['werewolf']

            # Generates the list of all role permutations
            roles = [role for role, count in self.role_count.items() for _ in range(count)]
            self.permutations = list(permutations(roles))

            # Set all players to be fully alive
            self.deaths = []
            for i in range(self.player_count):
                self.deaths += [[0] * self.player_count]
            self.killed = [0] * self.player_count

            # create list of cupid lovers
            self.lovers_list = {}

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
        self.role_count = {
            'werewolf': 2,
            'seer': 1,
            'hunter': 0,
            }
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

    # Calculates the probabilities
    def calculate_probabilities(self):
        if self.check_started():
            self.nperm = len(self.permutations)
            transpose = list(zip(*self.permutations))
            self.probs = []
            for i, p in enumerate(self.players):
                player_probs = {'name': p}
                for role in self.used_roles:
                    player_probs[role] = transpose[i].count(role) / self.nperm
                player_probs['dead'] = self.death_probability(p)
                self.probs.append(player_probs)
            return self.probs

    # Let a player take their cupid action
    def cupid(self, cupid, lover1, lover2):
        if self.check_started():
            cupid_id = self.ID(cupid)
            lovers = (self.ID(lover1), self.ID(lover2))
            self.lovers_list[cupid_id] = lovers

    # Let a player take their seer action
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
            p_list = [p for p in self.permutations if p[seer_id] == 'seer']

            # Choose an outcome
            assert len(p_list) > 0, "ERROR: seer list is empty"
            target_role = choice(p_list)[target_id]

            # Collapse the wave function
            for p in p_list:
                if p[target_id] != target_role:
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
            result = choice(self.permutations)
            target_role = result[target_id]
            permt = list(self.permutations)

            # Collapse the wave function
            for p in permt:
                if p[target_id] != target_role:
                    self.permutations.remove(p)

            # Report on results
            if self.verbose:
                print(f"{target} was a {target_role}!")

            # Deal with the case that the dead person is a werewolf
            if target_role == "werewolf":
                self.werewolf_count -= 1
                for i in range(self.player_count):
                    self.deaths[i][target_id] = 0

            self.killed[target_id] = 1
            self.calculate_probabilities()

            return target_role

    # Checks for players that were killed during last turn
    def check_deaths(self):
        killed_players = []
        for player_id, player in enumerate(self.players):
            p_dead = self.death_probability(player)
            if self.killed[player_id] == 0 and p_dead >= 1:
                killed_players.append(player)
        return killed_players

    # Shows the probability of death for a player
    def death_probability(self, name):
        # name: name of player
        name_id = self.ID(name)
        if self.killed[name_id] == 1:
            P_dead = 1
        else:
            total_attacks = 0
            for p in self.permutations:
                # check for lover in permutation
                lover_id = None
                if 'cupid' in p:
                    cupid_id = p.index('cupid')
                    if cupid_id in self.lovers_list:
                        lover1, lover2 = self.lovers_list[cupid_id]
                        if name_id == lover1:
                            lover_id = lover2
                        elif name_id == lover2:
                            lover_id = lover1

                werewolf_attacks = 0
                # count attacks by werewolves in this permutation
                for i in range(self.player_count):
                    if p[i] == "werewolf" and p[name_id] != "werewolf":
                        werewolf_attacks += self.deaths[name_id][i]

                lover_werewolf_attacks = 0
                # count attacks by werewolves on lover in this permutation
                if lover_id is not None:
                    for i in range(self.player_count):
                        if p[i] == "werewolf" and p[lover_id] != "werewolf":
                            lover_werewolf_attacks += self.deaths[lover_id][i]

                total_attacks += max(werewolf_attacks, lover_werewolf_attacks)

            P_dead = total_attacks / len(self.permutations)
        return P_dead

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

    # Gives the probabilities of all other players being a werewolf
    def other_werewolves(self, werewolf):
        werewolf_id = self.ID(werewolf)
        projection = [p for p in self.permutations if p[werewolf_id] == 'werewolf']

        if not projection:
            return []

        n_projection = len(projection)
        transpose = list(zip(*projection))

        probs = []
        for i, p in enumerate(self.players):
            P_werewolf = transpose[i].count("werewolf") / n_projection
            probs.append({'name': p, 'werewolf': P_werewolf})

        return probs

    # Gives the probabilities of all players being your lover
    def other_lover(self, player):
        player_id = self.ID(player)

        lover_count_list = [0] * self.player_count
        for p in self.permutations:
            if 'cupid' in p:
                cupid_id = p.index('cupid')
                lover1, lover2 = self.lovers_list[cupid_id]
                if player_id == lover1:
                    lover_count_list[lover2] += 1
                elif player_id == lover2:
                    lover_count_list[lover1] += 1

        probs = []
        for i, p in enumerate(self.players):
            P_lover = lover_count_list[i] / len(self.permutations)
            probs.append({'name': p, 'lover': P_lover})

        return probs

    def check_win(self):
        all_dead = True
        villager_win = True
        werewolf_win = True
        lover_win = True
        for perm in self.permutations:
            lovers = ()
            if 'cupid' in perm:
                cupid_id = perm.index('cupid')
                lovers = self.lovers_list[cupid_id]
            for ID, role in enumerate(perm):
                if self.killed[ID] == 0:
                    all_dead = False
                    if role == 'werewolf':
                        villager_win = False
                    else:
                        werewolf_win = False
                    if ID not in lovers:
                        lover_win = False

        if all_dead:
            if self.verbose:
                print('It is a tie!')
            return True, 'noone'
        if villager_win:
            if self.verbose:
                print('The villagers win!')
            return True, 'villagers'
        if werewolf_win:
            if self.verbose:
                print('The werewolves win!')
            return True, 'werewolves'
        if lover_win:
            if self.verbose:
                print('The lovers win!')
            return True, 'lovers'
        return False, None
