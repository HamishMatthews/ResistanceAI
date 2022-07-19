import random
import statistics as stat

from agent import Agent

'''
Author: Hamish Matthews 22477496
'''

# chance of being a spy for each number of players
spy_array = [0.4, 0.33, 0.43, 0.37, 0.33, 0.4]


class Amogus(Agent):

    def __init__(self, name='Smart'):
        '''
        Initialises the agent.
        Nothing to do here.
        '''
        self.name = name

    def new_game(self, number_of_players, player_number, spy_list):
        '''
        initialises the game, informing the agent of the
        number_of_players, the player_number (an id number for the agent in the game),
        and a list of agent indexes which are the spies, if the agent is a spy, or empty otherwise
        '''
        self.number_of_players = number_of_players
        self.index = player_number
        self.spies = spy_list
        self.players = []
        for i in range(number_of_players):
            self.players.append(Player(i, number_of_players, spy_list))
        self.others = [i for i in self.players if i.index is not self.index]
        self.spy = self.index in self.spies
        self.game = Game()

    def is_spy(self):
        '''
            returns True iff the agent is a spy
            '''
        return self.index in self.spies

    def round_outcome(self, rounds_complete, missions_failed):
        '''
        basic informative function, where the parameters indicate:
        rounds_complete, the number of rounds (0-5) that have been completed
        missions_failed, the number of missions (0-3) that have failed.
        '''

        pass

    def game_outcome(self, spies_win, spies):
        '''
        basic informative function, where the parameters indicate:
        spies_win, True iff the spies caused 3+ missions to fail
        spies, a list of the player indexes for the spies.
        '''

    def propose_mission(self, team_size, betrayals_required=1):

        # always include myself and another spy if required
        me = [self.players[self.index]]
        # sort players by suspicious level
        others = self.others
        if self.spy and betrayals_required == 2:
            other_spies = [self.players[s] for s in self.spies if s is not self.index] # add a random spy to accompany me in 4th round
            me.append(random.choice(other_spies))
        elif self.spy:
            others = set(others) - set([p for p in self.players if self.players.index in self.spies])
        # add least suspicious players to team or most if spy
        others = sorted(others, key=lambda e: e.sus_level, reverse=self.spy)
        result = me + others
        # restrict length
        result = [i.index for i in result][:team_size]
        return result

    def vote(self, team, leader):
        # update variables
        self.game.leader = leader
        self.game.tries += 1
        self.game.team = team

        # always vote for own team
        if leader == self.index:
            return True
        # if it is the first turn and first try then approve
        if self.game.turn == 1 and self.game.tries == 1:
            return True

        # As a spy, vote yes to all missions that include 1 or more spies
        if self.spy:
            spy_count = len([p for p in team if p in self.spies])
            if spy_count > 0:
                return True
            return False

        # As resistance, always pass the fifth try.
        if self.game.tries == 5:
            return True

        # If I'm not on the team and it's a team of 3
        if len(team) == 3 and self.index not in team:
            return False

        # if no losses then approve mission
        if self.game.losses == 0:
            return True
        # disapprove if leader not in team
        if self.game.leader not in team:
            return False

        average_sus = stat.mean([i.sus_level for i in self.players])
        team_sus = stat.mean([self.players[i].sus_level for i in team])
        #print(f"average sus: {average_sus}, team_sus: {team_sus}")
        # reject the team if it has a overly suspicious history
        if team_sus > average_sus:
            return False
        # else return true
        return True

    def vote_outcome(self, team, leader, votes):
        # update variables
        self.game.team = team
        self.game.leader = leader
        me = [p for p in self.players if self.players.index(p) == self.index]

        # leader didn't choose himself
        self.players[leader].sus_level += 2

        for p1 in self.get_other_players():
            # suspicious if first round and player votes no
            if p1 not in votes and self.game.turn == 1 and self.game.tries == 1:
                self.players[p1].sus_level += 2

            # suspicious if 5th tries and player against
            if self.game.tries == 5 and p1 not in votes:
                self.players[p1].sus_level += 5

            # player is outside team of 3 but approves
            if p1 in votes and len(team) == 3 and p1 not in team:
                self.players[p1].sus_level += 2

            # player in team but disapproves team
            if p1 in team and p1 not in votes:
                self.players[p1].sus_level -= 5

        # record the votes
        self.game.votes.append(votes)
        self.game.team = None

    def mission_outcome(self, team, leader, betrayals, mission_success):

        # update variables
        self.game.team = team
        self.game.leader = leader

        # betrayals multiplier
        mult = (betrayals % 1) * 3

        if mission_success:
            self.game.wins += 1
        else:
            self.game.losses += 1
        if not mission_success:
            for p in team:
                self.players[p].failed_missions.append(team)
                failed_count = len(self.players[p].failed_missions)
                # failed one mission - slightly suspicious
                if failed_count == 1:
                    self.players[p].sus_level += 2 * mult
                # failed two mission - more suspicious
                elif failed_count == 2:
                    self.players[p].sus_level += 10 * mult
                # punish people who voted in favour
                if p in self.game.votes[-1]:
                    self.players[p].sus_level += 1
            # punish leader
            self.players[leader].sus_level += 5 * mult

        # reward successful mission in moderation
        else:
            for p in team:
                self.players[p].successful_missions.append(team)
                success_count = len(self.players[p].successful_missions)
                # cleared one mission - lucky
                if success_count == 1:
                    self.players[p].sus_level += 2
                # cleared two mission - good player
                elif success_count == 2:
                    self.players[p].sus_level += 5
                # punish people who voted against a successful team
                if p not in self.game.votes[-1]:
                    self.players[p].sus_level += 1
                # reward people who voted in favor
                if p in self.game.votes[-1]:
                    self.players[p].sus_level -= 1
            # reward leader slightly for success
            self.players[leader].sus_level -= 5



    def betray(self, team, leader):

        # update variables
        self.game.team = team
        self.game.leader = leader
        if not self.is_spy():
            return False
        spy_count = len([p for p in self.game.team if p in self.spies])
        #only betray if 1 spy or last turn or 2 spies and you are not the leader
        return spy_count == 1 or self.is_last_turn() or (spy_count == 2 and leader != self.index)

    # get the index of all the other players
    def get_other_players(self):
        return [x.index for x in self.others]

    def is_last_turn(self):
        return (self.game.losses == 2) or (self.game.wins == 2)

# player object
class Player(object):  # Player object, data and analysis
    def __init__(self, player_number, number_of_players, spy_list):
        self.index = player_number
        self.sus_level = 0
        self.spy = player_number in spy_list
        self.failed_missions = []
        self.successful_missions = []


# game tracking
class Game:
    def __init__(self):
        self.team = None
        self.leader = None
        self.wins = 0
        self.losses = 0
        self.turn = 0
        self.tries = 0
        self.votes = []
