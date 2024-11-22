import logging
from os import system, get_terminal_size
from quantumwerewolf.backend import Game

logger = logging.getLogger(__name__)
logging.basicConfig(filename='debug.log', level=logging.DEBUG)


# TODO: take Game class as mutable gamestate instead of subclassing
class CliGame(Game):

    # Define colors
    normal = '\033[0;0m'
    bold = '\033[1m'
    underline = '\033[4m'
    red = '\033[0;31m'
    boldred = '\033[1;31m'
    pink = '\033[0;35m'
    boldpink = '\033[1;35m'
    yellow = '\033[0;33m'
    boldyellow = '\033[1;33m'
    green = '\033[0;32m'
    boldgreen = '\033[1;32m'
    blue = '\033[0;34m'
    boldblue = '\033[1;34m'

    role_style = {
        'villager': yellow,
        'werewolf': red,
        'seer': pink,
        'hunter': green,
        'cupid': blue,
        }

    role_style_bold = {
        'villager': boldyellow,
        'werewolf': boldred,
        'seer': boldpink,
        'hunter': boldgreen,
        'cupid': boldblue,
        }

    role_preposition = {
        'villager': 'a ',
        'werewolf': 'a ',
        'seer': 'the ',
        'hunter': 'the ',
        'cupid': '',
        }

    name_length = 12

    def __init__(self):
        super().__init__()
        columns = get_terminal_size().columns
        if columns < 69:
            if columns < 45:
                print(f"{self.boldred}WARNING: screen is too narrow for the game{self.normal}")
                self.bar_length = 12
            else:
                self.bar_length = columns - 33
        else:
            self.bar_length = 36

    def ask_yesno(self, query, yes, no):
        self.logger.debug(f'running ask_yesno({query}, {yes}, {no})')
        answer = input(query + ' (yes/no) ')
        if answer == 'yes' or answer == 'y':
            if callable(yes):
                return yes()
            else:
                return yes
        elif answer == 'no' or answer == 'n':
            if callable(no):
                return no()
            else:
                return no
        else:
            print('invalid answer')
            return self.ask_yesno(query, yes, no)

    def ask_player(self, query, invalid_players=[]):
        answer = input(query + 'Name: ')

        if answer.isdecimal():
            i = int(answer) - 1
            if i in range(self.player_count):
                answer = self.players[i]

        valid_players = self.living_players()
        for player in invalid_players:
            valid_players.remove(player)

        if not valid_players:
            return None

        if answer in valid_players:
            return answer
        else:
            print(f'    {self.red}"{answer}" is not a valid choice{self.normal}')
            print('    Valid players are:')
            for i, p in enumerate(valid_players):
                print("      {}".format(p))

            return self.ask_player(query, invalid_players=invalid_players)

    def ask_number(self, query, valid_numbers=None):
        answer = input(query)
        if answer.isdigit():
            return int(answer)
        else:
            print('  "{}" is not a valid choice'.format(answer))
            return self.ask_number(query)

    # Gives the table of probabilities
    def print_probability_table(self):
        probabilities = self.role_probabilities()

        header_line = f"{'player':>{self.name_length}s}"
        for role in self.used_roles:
            header_line += f"{role:>12s}"
        header_line += f"{'dead':>12s}"
        print(header_line)

        for i in self.print_permutation:
            p = probabilities[i]
            name = '???'
            if p['dead'] == 1:
                name = p['name']
            line = f"{str(name):>{self.name_length}s}"
            for role in self.used_roles:
                line += f"{100*p[role]:11.0f}%"
            line += f"{100*p['dead']:11.0f}%"
            print(line)

    def print_probability_bars(self, game_over=False):
        probabilities = self.role_probabilities()

        for i in self.print_permutation:
            p = probabilities[i]
            name = '???'
            if p['dead'] == 1 or game_over:
                name = p['name']
            line = f"{str(name):>{self.name_length}}    "
            total_chance = 0.0
            total_length = 0
            for role in self.used_roles:
                letter = role[0].capitalize()
                chance = p[role]
                total_chance += chance
                total_length_new = round(total_chance * self.bar_length)
                length = total_length_new - total_length
                total_length = total_length_new
                line += f"{self.role_style_bold[role]}{letter * length}"
            line += f"{self.normal}{100*p['dead']:11.0f}% dead"
            print(line)

    def print_kill(self, player, cause=''):
        player_role = self.kill(player)
        print(f'\n  {player} was killed {cause}')
        print(f'    {player} was {self.role_preposition[player_role]}{player_role}\n')
        return player_role

    # TODO: move to backend
    def process_deaths(self, killed_players):
        # kill all players that died
        hunter = None
        for player in killed_players:
            player_role = self.print_kill(player, '')
            if player_role == 'hunter':
                hunter = player

        # check for chain deaths
        if killed_players:
            killed_players = self.check_deaths()
            self.process_deaths(killed_players)

        # if hunter died and someone is still alive they must kill someone
        if hunter and self.living_players():
            print(f'    {hunter} must now kill another player')
            hunter_target = self.ask_player(f'\n  {self.boldgreen}[HUNTER]{self.normal} {hunter}, who do you shoot?\n    ')
            self.print_kill(hunter_target, 'by the hunter')
            killed_players = self.check_deaths()
            self.process_deaths(killed_players)

    def print_win(self):
        win, winners = self.check_win()
        if win:
            if winners is None:
                print("THE GAME IS A TIE!")
            else:
                print(f"\n\n{self.bold}THE {winners.upper()} WIN!{self.normal}\n")
            self.print_probability_bars(game_over=True)
            self.stop()
        return win

    def get_players(self):
        # Get player names
        print("Enter player names")
        print("Enter no name to continue.")
        new_player = True
        while new_player:
            name = input(f"  Name player {self.player_count + 1}: ")
            if name == '':
                if self.player_count < 3:
                    print(f'\033[F{self.red}  This game needs at least 3 players to play! Add more players.{self.normal}\033[K')
                else:
                    new_player = False
            elif not name.isalpha():
                print(f"\033[F{self.red}  Name may only contain letters!{self.normal}\033[K")
            elif len(name) > self.name_length:
                print(f"\033[F{self.red}  Name cannot be longer than 12 characters!{self.normal}\033[K")
            else:
                if not self.add_player(name):
                    print(f"\033[F{self.red}  Name {name} already in use!{self.normal}\033[K")

    def print_players(self):
        # display players
        print("Current Players:")
        for i, p in enumerate(self.players):
            print(f"{i+1:3d}: {p}")

    def print_live_players(self):
        # display live players
        print(f"  {self.underline}Live Players:{self.normal}")
        live_players = self.living_players()
        for i, p in enumerate(self.players):
            if p in live_players:
                print(f"  {i+1:3d}: {p}")

    def print_deck(self, hide_unused=False):
        for (role, count) in self.deck.items():
            if count == 0:
                if hide_unused:
                    continue
                else:
                    name = role
                    count = 'no'
            elif count == 1:
                name = role
            elif count > 1:
                if role == 'werewolf':
                    name = 'werewolves'
                else:
                    name = role + 's'
            print(f"{count:>4} {name}")

    def get_deck(self):
        self.logger.debug('running get_deck()')

        def ask_deck():
            self.logger.debug('running ask_deck()')
            # ask for new roles
            print('')
            deck = {}
            for role in self.default_deck.keys():
                if role == 'werewolf':
                    deck['werewolf'] = self.ask_number('Number of werewolves: ')
                elif role == 'villager':
                    continue
                else:
                    deck[role] = self.ask_yesno(f'Include {role}?', 1, 0)

            # check for valid deck
            if self.set_deck(deck):
                self.logger.debug('Received asked deck. Returning False.')
                return False
            else:
                print(f"{self.red}Too many roles for numer of players. Try again.{self.normal}")
                self.logger.debug('Deck not valid. Asking again.')
                return ask_deck()

        self.set_suggested_deck()

        deck_confirmed = False
        while deck_confirmed is False:
            print("\nPlay with following roles?")
            self.print_deck()
            deck_confirmed = self.ask_yesno('', True, ask_deck)

    # TODO: move to backend
    def start_day(self):
        killed_players = self.check_deaths()
        self.process_deaths(killed_players)

    # TODO: move to backend
    def end_day(self, lynch_target):
        self.process_deaths([lynch_target])

    def get_player_actions(self, player, player_role_probabilities, player_other_werewolves, player_other_lover):
        self.logger.debug(f"running get_player_actions({player}, {player_role_probabilities}, {player_other_werewolves}, {player_other_lover})")
        player_actions = {}
        # cupid
        if 'cupid' in self.used_roles:
            if self.turn_counter == 1 and player_role_probabilities['cupid'] != 0:
                # query cupid action
                first_lover = self.ask_player(f'\n  {self.boldblue}[CUPID]{self.normal} Who do you choose as first lover?\n    ')
                second_lover = self.ask_player(f'  {self.boldblue}[CUPID]{self.normal} Who do you choose as second lover?\n    ', invalid_players=[first_lover])
                player_actions['cupid'] = (first_lover, second_lover)
                print(f'  {self.boldblue}[CUPID]{self.normal} {first_lover} and {second_lover} are now lovers.')
            elif self.turn_counter > 1:
                # print lover probabilities
                print(f'\n  {self.boldblue}[CUPID]{self.normal} Your lover is:')
                for p in player_other_lover:
                    name = p['name']
                    chance = p['lover']
                    if name != player:
                        length = round(chance * self.bar_length)
                        print(f'    {name:>{self.name_length}}: {100*chance:3.0f}% {self.boldblue}{"L" * length}{self.normal}')

        # seer
        if 'seer' in self.used_roles and player_role_probabilities['seer'] != 0:
            target = self.ask_player(f'\n  {self.boldpink}[SEER]{self.normal} Whose role do you inspect?\n    ')
            target_role = self.seer(player, target, project=False)
            player_actions['seer'] = (target, target_role)
            print(f'  {self.boldpink}[SEER]{self.normal} You see that {target} is {self.role_preposition[target_role]}{target_role}.')

        # werewolf
        if 'werewolf' in self.used_roles and player_role_probabilities['werewolf'] != 0:
            invalid_players = [player]
            # print other werewolves
            print(f'\n  {self.boldred}[WEREWOLF]{self.normal} Your fellow werewolves are:')
            for p in player_other_werewolves:
                name = p['name']
                chance = p['werewolf']
                if name != player:
                    length = round(chance * self.bar_length)
                    print(f'    {name:>{self.name_length}}: {100*chance:3.0f}% {self.boldred}{"W"*length}{self.normal}')
                if chance == 1 and p in self.living_players():
                    invalid_players.append(p)

            if self.living_players() != invalid_players:
                # do werewolf action
                target = self.ask_player(f'\n  {self.boldred}[WEREWOLF]{self.normal} Who do you attack?\n    ', invalid_players=invalid_players)
                player_actions['werewolf'] = (target)

        return player_actions

    def print_player_role(self, player_probabilities):
        # display game and player info (role superposition)
        print(f'\n  {self.underline}Your role:{self.normal}')
        for role in self.used_roles:
            style = self.role_style[role]
            letter = role[0].capitalize()
            chance = player_probabilities[role]
            length = round(chance * self.bar_length)
            print(f"    {style}{role:>8s}: {100*chance:3.0f}% |{letter * length:<{self.bar_length}}|{self.normal}")


def cli():

    system('clear')

    g = CliGame()
    g.get_players()

    system('clear')

    g.print_players()
    g.get_deck()

    system('clear')

    g.start()

    # loop turns for every player
    while g.started:
        g.turn_counter += 1

        # night
        system('clear')
        print('Night falls and all players take their actions in turns privately\n')

        start_probabilities = g.role_probabilities()

        # collect all player actions
        actions = {}
        for player_id, player in enumerate(g.players):
            player_role_probabilities = start_probabilities[player_id]
            player_other_lover = g.other_lover(player)
            player_other_werewolves = g.other_werewolves(player)

            # if player is dead skip turn
            if g.killed[player_id] == 1:
                continue

            input(f"{player}'s turn (press ENTER to continue)")
            system('clear')
            print(f"{player}'s turn\n")

            g.print_live_players()

            g.print_player_role(player_role_probabilities)

            player_actions = g.get_player_actions(player, player_role_probabilities, player_other_werewolves, player_other_lover)

            # pass the actions for the player
            actions[player] = player_actions

            input("\n(press ENTER to continue)")

            system('clear')

        # process actions
        g.logger.debug(g.valid_permutations())
        g.process_night(actions)
        g.logger.debug(g.valid_permutations())

        # day
        input('All player have had their turn (press ENTER to continue)')
        system('clear')
        print('The day begins')

        g.start_day()

        # check win before the vote
        if g.print_win():
            break

        # Show current game state
        g.print_probability_bars()

        # vote
        lynch_target = g.ask_player(f'\n  {g.boldyellow}[ALL VILLAGERS]{g.normal} Who do you lynch?\n    ')

        g.end_day(lynch_target)

        # check win after the vote
        if g.print_win():
            break

        input('(press ENTER to continue)')


if __name__ == '__main__':
    cli()
