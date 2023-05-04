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

from quantumwerewolf import Game


# test add_players
def test_add_players():
    g = Game()
    # check if player list is initially empty
    assert not g.players

    # check individual name addition
    g.add_players('Alice')
    assert g.players == ['Alice']
    g.add_players('Bob')
    assert g.players == ['Alice', 'Bob']

    # check list name addition
    g.add_players(['Craig', 'David'])
    assert g.players == ['Alice', 'Bob', 'Craig', 'David']

    return True


# test set role
def test_set_role():
    g = Game()

    # check initial role counts
    roles = ['werewolf', 'seer', 'hunter', 'cupid']
    assert list(g.role_count.keys()) == roles
    assert g.role_count['werewolf'] == 2
    assert g.role_count['seer'] == 1
    assert g.role_count['hunter'] == 0
    assert g.role_count['cupid'] == 0

    # check role count change
    for r in roles:
        g.set_role(r, 683)
        assert g.role_count[r] == 683

    return True


# test _name and _id methods
def test_name_id():
    g = Game()
    names = ['Alice', 'Bob', 'Craig', 'David']
    g.add_players(names)
    g.start()

    # test ids
    player_ids = [g._id(player) for player in g.players]
    assert player_ids == list(range(g.player_count))

    # test names
    player_names = [g._name(player_id) for player_id in range(g.player_count)]
    assert player_names == names


if __name__ == '__main__':
    test_add_players()
    test_set_role()
    test_name_id()
