import logging
from os import system
from quantumwerewolf.backend import Game

logger = logging.getLogger(__name__)


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

    bar_length = 24

    def ask_yesno(self, query, yes, no):
        answer = input(query + ' (yes/no) ')
        if answer == 'yes' or answer == 'y':
            if isinstance(yes, str):
                print(yes)
            else:
                yes()
        elif answer == 'no' or answer == 'n':
            if isinstance(no, str):
                print(no)
            else:
                no()
        else:
            print('invalid answer')
            self.ask_yesno(query, yes, no)

    def ask_player(self, query, invalid_players=[]):
        answer = input(query + 'Name: ')
        valid_players = self.living_players()
        for player in invalid_players:
            valid_players.remove(player)
        if not valid_players:
            return None
        if answer in valid_players:
            return answer
        else:
            print('  "{}" is not a valid choice'.format(answer))
            print('  Valid players are:')
            for i, p in enumerate(valid_players):
                print("    {}".format(p))

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
        probabilities = self.calculate_probabilities()

        header_line = f"{'player':>12s}"
        for role in self.used_roles:
            header_line += f"{role:>12s}"
        header_line += f"{'dead':>12s}"
        print(header_line)

        for i in self.print_permutation:
            p = probabilities[i]
            name = '???'
            if p['dead'] == 1:
                name = p['name']
            line = f"{str(name):>12s}"
            for role in self.used_roles:
                line += f"{100*p[role]:11.0f}%"
            line += f"{100*p['dead']:11.0f}%"
            print(line)

    def print_probability_bars(self, game_over=False):
        probabilities = self.calculate_probabilities()

        for i in self.print_permutation:
            p = probabilities[i]
            name = '???'
            if p['dead'] == 1 or game_over:
                name = p['name']
            line = f"{str(name):>12s}    "
            for role in self.used_roles:
                chance = p[role]
                letter = role[0].capitalize()
                length = round(chance * self.bar_length)
                line += f"{self.role_style_bold[role]}{letter * length}"
            line += f"{self.normal}{100*p['dead']:11.0f}% dead"
            print(line)

    def print_kill(self, player, cause=''):
        player_role = self.kill(player)
        print(f'\n  {player} was killed {cause}')
        print(f'    {player} was {self.role_preposition[player_role]}{player_role}')
        return player_role

    def process_deaths(self, killed_players):
        # kill all players that died
        hunter = None
        for player in killed_players:
            player_role = self.print_kill(player, 'during the night')
            if player_role == 'hunter':
                hunter = player

        # if hunter died and someone is still alive they must kill someone
        if hunter and self.living_players():
            print(f'    {player} must now kill another player')
            hunter_target = self.ask_player(f'\n  {self.boldgreen}[HUNTER]{self.normal} {player}, who do you shoot?\n    ')
            self.print_kill(hunter_target, 'by the hunter')

        # check for chain deaths
        if killed_players:
            killed_players = self.check_deaths()
            self.process_deaths(killed_players)

    def print_win(self):
        win, winners = self.check_win()
        if win:
            print(f"\n\n{self.bold}THE {winners.upper()} WIN!{self.normal}\n")
            self.print_probability_bars(game_over=True)
            self.stop()
        return win


def cli():

    g = CliGame()

    system('clear')

    print("Enter player name(s) separated by spaces.")
    print("Enter no name to continue.")

    # Get player names
    new_player = True
    while new_player:
        names = input("  Name(s): ")
        if names != '':
            g.add_players(names.split())
        else:
            new_player = False

    system('clear')

    print("Current Players:")
    for i, p in enumerate(g.players):
        print(" {}: {}".format(i+1, p))

    # Set the deck
    print("\nPlay with following roles?")
    for (role, count) in g.role_count.items():
        if count == 1:
            suffix = ''
        else:
            suffix = 's'
        print(" {} {}{}".format(count, role, suffix))

    def set_role(role, amount):
        def set_seer_value():
            g.set_role(role, amount)
        return set_seer_value

    def ask_roles():
        # ask for new roles
        for role in g.role_count.keys():
            if role == 'werewolf':
                g.role_count['werewolf'] = int(input('\nNumber of werewolves: '))
            else:
                g.ask_yesno(f'Include {role}?', set_role(role, 1), set_role(role, 0))

    g.ask_yesno('', "roles confirmed!",  ask_roles)

    system('clear')

    # Start game
    g.start()

    # loop turns for every player
    turn_counter = 0
    while g.started:
        turn_counter += 1
        # night
        system('clear')
        print('Night falls and all players take their actions in turns privately\n')

        start_probabilities = g.calculate_probabilities()
        start_other_werewolves = [g.other_werewolves(p) for p in g.players]
        if turn_counter > 1:
            start_other_lover = [g.other_lover(p) for p in g.players]

        for i, p in enumerate(g.players):

            # if player is dead skip turn
            if g.killed[i] == 1:
                continue

            input("{}'s turn (press ENTER to continue)".format(p))
            system('clear')
            print("{}'s turn".format(p))

            # display game and player info (role superposition)
            player_probabilities = start_probabilities[i]

            print(f'\n  {g.underline}Your role:{g.normal}')
            for role in g.used_roles:
                style = g.role_style[role]
                letter = role[0].capitalize()
                chance = player_probabilities[role]
                length = round(chance * g.bar_length)
                print(f"    {style}{role:>8s}: {100*chance:3.0f}% |{letter * length:<{g.bar_length}}|{g.normal}")

            # cupid
            if 'cupid' in g.used_roles:
                if turn_counter == 1 and 'cupid' and player_probabilities['cupid'] != 0:
                    first_lover = g.ask_player(f'\n  {g.boldblue}[CUPID]{g.normal} Who do you choose as first lover?\n    ')
                    second_lover = g.ask_player(f'  {g.boldblue}[CUPID]{g.normal} Who do you choose as second lover?\n    ', invalid_players=[first_lover])
                    g.cupid(p, first_lover, second_lover)
                    print(f'    {first_lover} and {second_lover} are now lovers')
                else:
                    # print lover probabilities
                    print(f'\n  {g.boldblue}[CUPID]{g.normal} Your lover is:')
                    player_other_lover = start_other_lover[i]
                    for player in player_other_lover:
                        name = player['name']
                        chance = player['lover']
                        if name != p:
                            length = round(chance * g.bar_length)
                            print(f'    {name:>12s}: {100*chance:3.0f}% {g.boldblue}{"L" * length}{g.normal}')

            # seer
            if 'seer' in g.used_roles and player_probabilities['seer'] != 0:
                target = g.ask_player(f'\n  {g.boldpink}[SEER]{g.normal} Whose role do you inspect?\n    ')
                target_role = g.seer(p, target)
                print(f'    {target} is {g.role_preposition[target_role]}{target_role}')

            # werewolf
            if 'werewolf' in g.used_roles and player_probabilities['werewolf'] != 0:
                # print other werewolves
                print(f'\n  {g.boldred}[WEREWOLF]{g.normal} Your fellow werewolves are:')
                player_other_werewolves = start_other_werewolves[i]
                for player in player_other_werewolves:
                    name = player['name']
                    chance = player['werewolf']
                    if name != p:
                        length = round(chance * g.bar_length)
                        print(f'    {name:>12s}: {100*chance:3.0f}% {g.boldred}{"W"*length}{g.normal}')

                # do werewolf action
                target = g.ask_player(f'\n  {g.boldred}[WEREWOLF]{g.normal} Who do you attack?\n    ')
                g.werewolf(p, target)

            input("\n(press ENTER to continue)")

            system('clear')

        # day
        input('All player have had their turn (press ENTER to continue)')
        system('clear')
        print('The day begins')

        def start_day():
            killed_players = g.check_deaths()
            g.process_deaths(killed_players)

        start_day()

        # check win before the vote
        if g.print_win():
            break

        # Show current game state
        g.print_probability_bars()

        # vote
        lynch_target = g.ask_player(f'\n  {g.boldyellow}[ALL VILLAGERS]{g.normal} Who do you lynch?\n    ')

        def end_day(lynch_target):
            g.process_deaths([lynch_target])

        end_day(lynch_target)

        # check win after the vote
        if g.print_win():
            break

        input('(press ENTER to continue)')


if __name__ == '__main__':
    cli()
