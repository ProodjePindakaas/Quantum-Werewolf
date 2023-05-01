from os import system
from quantumwerewolf import Game


def ask_yesno(query, yes, no):
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
        ask_yesno(query, yes, no)


def ask_player(query, invalid_players=[]):
    answer = input(query + 'Name: ')
    valid_players = g.living_players()
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
            if g.killed[i] == 0:
                print("    {}".format(p))

        return ask_player(query, invalid_players=invalid_players)


# Gives the table of probabilities
def print_probability_table():
    probabilities = g.calculate_probabilities()

    header_line = f"{'player':>12s}"
    for role in g.used_roles:
        header_line += f"{role:>12s}"
    header_line += f"{'dead':>12s}"
    print(header_line)

    for i in g.print_permutation:
        p = probabilities[i]
        name = '???'
        if p['dead'] == 1:
            name = p['name']
        line = f"{str(name):>12s}"
        for role in g.used_roles:
            line += f"{100*p[role]:11.0f}%"
        line += f"{100*p['dead']:11.0f}%"
        print(line)


def print_probability_bars():
    probabilities = g.calculate_probabilities()

    for i in g.print_permutation:
        p = probabilities[i]
        name = '???'
        if p['dead'] == 1:
            name = p['name']
        line = f"{str(name):>12s}    "
        for role in g.used_roles:
            chance = p[role]
            letter = role[0].capitalize()
            length = round(chance * bar_length)
            line += f"{role_style_bold[role]}{letter * length}"
        line += f"{normal}{100*p['dead']:11.0f}% dead"
        print(line)


if __name__ == "__main__":

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

    bar_length = 20

    g = Game()

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
                ask_yesno(f'Include {role}?', set_role(role, 1), set_role(role, 0))

    ask_yesno('', "roles confirmed!",  ask_roles)

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

        start_probabilities = g.probs
        start_other_werewolves = [g.other_werewolves(p) for p in g.players]
        if turn_counter > 1:
            start_other_lover = [g.other_lover(p) for p in g.players]

        for i, p in enumerate(g.players):
            if g.killed[i] == 1:
                continue

            input("{}'s turn (press ENTER to continue)".format(p))
            system('clear')
            print("{}'s turn".format(p))

            # display game and player info (role superposition)
            player_probabilities = start_probabilities[i]

            print(f'\n  {underline}Your role:{normal}')
            for role in g.used_roles:
                style = role_style[role]
                letter = role[0].capitalize()
                chance = player_probabilities[role]
                length = round(chance * bar_length)
                print(f"    {style}{role:>8s}: {100*chance:3.0f}% {letter * length}{normal}")

            # cupid
            if 'cupid' in g.used_roles:
                if turn_counter == 1 and 'cupid' and player_probabilities['cupid'] != 0:
                    first_lover = ask_player(f'\n  {boldblue}[CUPID]{normal} Who do you choose as first lover?\n    ')
                    second_lover = ask_player(f'  {boldblue}[CUPID]{normal} Who do you choose as second lover?\n    ', invalid_players=[first_lover])
                    g.cupid(p, first_lover, second_lover)
                    print(f'    {first_lover} and {second_lover} are now lovers')
                else:
                    # print lover probabilities
                    print(f'\n  {boldblue}[CUPID]{normal} Your lover is:')
                    player_other_lover = start_other_lover[i]
                    for player in player_other_lover:
                        name = player['name']
                        chance = player['lover']
                        if name != p:
                            length = round(chance * bar_length)
                            print(f'    {name:>12s}: {100*chance:3.0f}% {boldblue}{"L" * length}{normal}')

            # seer
            if 'seer' in g.used_roles and player_probabilities['seer'] != 0:
                target = ask_player(f'\n  {boldpink}[SEER]{normal} Whose role do you inspect?\n    ')
                target_role = g.seer(p, target)
                print(f'    {target} is {role_preposition[target_role]}{target_role}')

            # werewolf
            if 'werewolf' in g.used_roles and player_probabilities['werewolf'] != 0:
                # print other werewolves
                print(f'\n  {boldred}[WEREWOLF]{normal} Your fellow werewolves are:')
                player_other_werewolves = start_other_werewolves[i]
                for player in player_other_werewolves:
                    name = player['name']
                    chance = player['werewolf']
                    if name != p:
                        length = round(chance * bar_length)
                        print(f'    {name:>12s}: {100*chance:3.0f}% {boldred}{"W"*length}{normal}')

                # do werewolf action
                target = ask_player(f'\n  {boldred}[WEREWOLF]{normal} Who do you attack?\n    ')
                g.werewolf(p, target)

            input("\n(press ENTER to continue)")

            system('clear')

        # day
        input('All player have had their turn (press ENTER to continue)')
        system('clear')
        print('The day begins')

        def print_kill(player):
            player_role = g.kill(player)
            print(f'  {player} was killed during the night')
            print(f'    {player} was {role_preposition[player_role]}{player_role}')
            if player_role == 'hunter' and g.living_players():
                print(f'    {player} must now kill another player')
                hunter_target = ask_player(f'\n  {boldgreen}[HUNTER]{normal} {player}, who do you shoot?\n    ')
                hunter_target_role = g.kill(hunter_target)
                print(f'  {hunter_target} was killed by the hunter')
                print(f'    {hunter_target} was {role_preposition[hunter_target_role]}{hunter_target_role}')
                process_deaths()

        def process_deaths():
            # check who died since last check
            killed_players = g.check_deaths()

            # kill all players that died
            for player in killed_players:
                print_kill(player)

        process_deaths()

        # check win before the vote
        win, winners = g.check_win()
        if win:
            print(f"\nThe {winners} win!")
            break

        # Show current game state
        print_probability_bars()

        # vote
        lynch_target = ask_player(f'\n  {boldyellow}[ALL VILLAGERS]{normal} Who do you lynch?\n    ')
        print_kill(lynch_target)

        input('(press ENTER to continue)')

        # check win after the vote
        win, winners = g.check_win()
        if win:
            print(f"\nThe {winners} win!")
            break

        print_probability_bars()
