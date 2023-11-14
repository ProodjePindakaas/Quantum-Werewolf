"""
UNIT TESTS
- test calculation of role probabilities
- test calculation of death probabilities
    - werewolf attacks only
    - werewolf attacks and lovers
    - other kills
- test werewolf action
    - test computation of fellow werewolves
- test seer action
- test hunter action
- test cupid action
    - test computation of lovers
- test win condition check

"""

from quantumwerewolf.backend import Game
from math import factorial
from unittest import TestCase, main
import logging


class TestGame(TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.ERROR)
        self.game = Game()

    def tearDown(self):
        del self.game

    def test_add_players(self):
        # test add_players
        # check if player list is initially empty
        self.assertFalse(self.game.players)

        # check individual name addition
        self.game.add_players('Alice')
        self.assertEqual(self.game.players, ['Alice'])

        self.game.add_players('Bob')
        self.assertEqual(self.game.players, ['Alice', 'Bob'])

        # check list name addition
        self.game.add_players(['Craig', 'David'])
        self.assertEqual(self.game.players, ['Alice', 'Bob', 'Craig', 'David'])

    def test_set_role(self):
        # test set role
        # check initial role counts
        roles = ['werewolf', 'seer', 'hunter', 'cupid']
        self.assertEqual(list(self.game.role_count.keys()), roles)
        self.assertEqual(self.game.role_count['werewolf'],  2)
        self.assertEqual(self.game.role_count['seer'],  1)
        self.assertEqual(self.game.role_count['hunter'],  0)
        self.assertEqual(self.game.role_count['cupid'],  0)

        # check role count change
        for r in roles:
            self.game.set_role(r, 683)
            self.assertEqual(self.game.role_count[r], 683)

    def test_start_succesful(self):
        # test succesful start
        names = ['Alice', 'Bob', 'Craig', 'David']
        self.game.add_players(names)
        self.assertTrue(self.game.start())

        # test state of game
        self.assertTrue(self.game.started)

        # test assignment of player count
        self.assertEqual(self.game.player_count, len(names))

        # test creation of player_ids dict
        ids = [self.game.player_ids[name] for name in names]
        self.assertEqual(ids, list(range(self.game.player_count)))

        # test print permutation is valid permutatiom
        self.assertEqual(sorted(self.game.print_permutation), list(range(self.game.player_count)))
        # test villager calculation

        # test role list
        self.assertEqual(sum(self.game.role_count.values()), 4)
        self.assertEqual(self.game.role_count['werewolf'], 2)
        self.assertEqual(self.game.role_count['seer'], 1)
        self.assertEqual(self.game.role_count['hunter'], 0)
        self.assertEqual(self.game.role_count['cupid'], 0)
        self.assertEqual(self.game.role_count['villager'], 1)

        # test number of permutations
        n_perm = factorial(self.game.player_count)
        for i in self.game.role_count.values():
            n_perm /= factorial(i)

        self.assertEqual(len(self.game.permutations), n_perm)

    def test_start_fail(self):
        # test no players
        self.assertFalse(self.game.start())
        # test too few players
        self.game.add_players('Alice')
        self.assertFalse(self.game.start())


class TestGameStarted(TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.WARNING)
        self.game = Game()
        self.names = ['Alice', 'Bob', 'Craig', 'David']
        self.game.add_players(self.names)
        self.game.start()

    def tearDown(self):
        del self.game

    def test_add_players_error(self):
        self.assertRaises(ValueError, self.game.add_players, 'Alice')

    def test_set_role_error(self):
        self.assertRaises(ValueError, self.game.set_role, 'werewolf', 683)

    def test_name_id(self):
        # test _id method
        player_ids = [self.game._id(player) for player in self.game.players]
        self.assertEqual(player_ids, list(range(self.game.player_count)))

        # test _name method
        player_names = [self.game._name(index) for index in range(self.game.player_count)]
        self.assertEqual(player_names, self.names)

    def test_living_players(self):
        self.assertEqual(self.game.living_players(), self.names)

        self.game.killed[0] = True
        self.names.remove('Alice')
        self.assertEqual(self.game.living_players(), self.names)

        self.game.killed[1] = True
        self.names.remove('Bob')
        self.assertEqual(self.game.living_players(), self.names)

    def test_death_probability(self):
        # test all players are valid input

        # test output is probabiltiy

        # test without lovers

        # test with lovers
        pass

    def test_calculate_probabilities(self):
        # check results at start of the a game
        result_start = self.game.calculate_probabilities()
        for player_result in result_start:
            self.assertIn('name', player_result)
            self.assertIn(player_result['name'], self.game.players)
            self.assertEqual(player_result['werewolf'], 2/4)
            self.assertEqual(player_result['seer'], 1/4)
            # self.assertEqual(player_result['hunter'], 0)
            # self.assertEqual(player_result['cupid'], 0)
            self.assertEqual(player_result['villager'], 1/4)
            self.assertEqual(player_result['dead'], 0)

    def test_kill(self):
        pass

    def test_seer(self):
        pass

    def test_werewolf(self):
        pass

    def test_cupid(self):
        pass


if __name__ == '__main__':
    main()
