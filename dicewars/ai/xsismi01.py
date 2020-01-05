import logging
from dicewars.ai.utils import possible_attacks
from dicewars.ai.utils import probability_of_holding_area, probability_of_successful_attack, attack_succcess_probability

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
import copy

THRESHOLD = 0.4

class AI:
    """
    Agent using Expectiminimax strategy
    """
    def __init__(self, player_name, board, players_order):
        """
        Parameters
        ----------
        game : Game
        """
        self.player_name = player_name
        self.logger = logging.getLogger('AI')

    def ai_turn(self, board, nb_moves_this_turn, nb_turns_this_game, time_left):
        """
        AI agent's turn
        """
        self.board = board
        self.playersCount = self.board.nb_players_alive()

        # self.logger.critical(time_left)

        if self.playersCount == 2:
            best_turn = self.expectiMinMax()
            if best_turn[0] is not None:
                return BattleCommand(best_turn[0], best_turn[1])
        else:
            turns = self.best_turn()

            if turns:
                turn = turns[0]
                area_name = turn[0]
                self.logger.debug("Possible turn: {}".format(turn))
                hold_prob = turn[2]
                self.logger.debug("{0}->{1} attack and hold probabiliy {2}".format(area_name, turn[1], hold_prob))

                return BattleCommand(area_name, turn[1])

            if turns:
                turn = turns[0]
                area_name = turn[0]
                self.logger.debug("Possible turn: {}".format(turn))
                hold_prob = turn[2]
                self.logger.debug("{0}->{1} attack and hold probabiliy {2}".format(area_name, turn[1], hold_prob))

                return BattleCommand(area_name, turn[1])

        self.logger.debug("No more plays.")
        return EndTurnCommand()

    def updateBoardAttack(self, board, source, target):
        sourceName = source.get_name()
        targetName = target.get_name()
        newBoard = copy.deepcopy(board)
        newBoard.get_area(targetName).set_owner(sourceName)
        newBoard.get_area(targetName).set_dice(source.get_dice() - 1)
        newBoard.get_area(sourceName).set_dice(1)
        return newBoard

    def updateBoardDefence(self, board, defender, attacker):
        targetName = attacker.get_name()
        newBoard = copy.deepcopy(board)
        newBoard.get_area(targetName).set_dice(1)
        return newBoard

    def updateBoard(self, board, source, target):
        sourceName = source.get_name()
        targetName = target.get_name()
        newBoard = copy.deepcopy(board)
        newBoard.get_area(targetName).set_owner(sourceName)
        newBoard.get_area(targetName).set_dice(source.get_dice() - 1)
        newBoard.get_area(sourceName).set_dice(1)
        return newBoard

    def best_turn(self):
        """Get a list of preferred moves
        This list is sorted with respect to hold probability in descending order.
        It includes all moves that either have hold probability higher or equal to 20 %
        or have strength of eight dice.
        """
        turns = []

        for source, target in possible_attacks(self.board, self.player_name):
            area_name = source.get_name()
            atk_power = source.get_dice()
            atk_prob = probability_of_successful_attack(self.board, area_name, target.get_name())
            hold_prob = atk_prob * probability_of_holding_area(self.board, target.get_name(), atk_power - 1, self.player_name)
            if hold_prob >= 0.2 or atk_power == 8:
                newBoard = self.updateBoard(self.board, source, target)
                turns.append([area_name, target.get_name(), self.expectiMax3(newBoard, target)])

        return sorted(turns, key=lambda turn: turn[2], reverse=True)

    def expectiMax3(self, board, area):
        values=[]
        if area.get_dice() < 2:
            return 0.0

        for target in self.possible_attacks_from_area(board, area, self.player_name): 
            atk_power = area.get_dice()
            if atk_power < 2:
                continue

            attack_possibility_value = attack_succcess_probability(area.get_dice(), target.get_dice())
            if attack_possibility_value >= 0.2 or atk_power == 8:
                newBoard = self.updateBoardAttack(board, area, target) # ze sme zautocili a vyhrali
                areaAttacked = newBoard.get_area(target.get_name()) # areaAttacked bude mat get_dice() - 1 kociek
                val = attack_possibility_value * self.expectiMin3(newBoard, areaAttacked) * areaAttacked.get_dice() 
                values.append(val)

        if not values:
            return 0.0
        
        return max(values)

    def expectiMin3(self, board, area):
        values = []
        for adj in area.get_adjacent_areas():
            adjacent_area = board.get_area(adj)
            if adjacent_area.get_owner_name() != self.player_name:
                enemy_dice = adjacent_area.get_dice()
                if enemy_dice == 1:
                    continue
                lose_prob = attack_succcess_probability(enemy_dice, area.get_dice())
                if lose_prob >= 0.2 or area.get_dice() == 8:        
                    newBoard = self.updateBoardDefence(board, area, adjacent_area) # ze na nas zautocili a vyhrali sme a s area nic nestane, oni budu mat get_dice() == 1
                    areaThatAttacked = newBoard.get_area(adjacent_area.get_name()) # areaAttacked bude mat get_dice() == 1 kocku
                    val = (1 - lose_prob) * self.expectiMax3(newBoard, areaThatAttacked) * areaThatAttacked.get_dice() 
                    values.append(val)

        if not values:
            return 1.0 # tu by som mozno dal jednotku
        
        return min(values)

    def expectiMinMax(self):
        best_turn = (None, None, 0.0)

        for area in self.board.get_player_border(self.player_name):
            exp = self.expectiMax2(self.board, area)
            if exp[1] > best_turn[2]:
                best_turn = (area.get_name(), exp[0], exp[1])

        return best_turn

    def expectiMax2(self, board, area):
        best_move = (None, 0.0)
        atk_power = area.get_dice()
        if not area.can_attack():
            return best_move

        for target in self.possible_attacks_from_area(board, area, self.player_name): 
            attack_possibility_value = attack_succcess_probability(atk_power, target.get_dice())
            if attack_possibility_value >= THRESHOLD or atk_power == 8:
                newBoard = self.updateBoardAttack(board, area, target) # ze sme zautocili a vyhrali
                areaAttacked = newBoard.get_area(target.get_name()) # areaAttacked bude mat get_dice() - 1 kociek
                val = attack_possibility_value * self.expectiMin2(newBoard, areaAttacked, self.playersCount) * areaAttacked.get_dice() 
                if val > best_move[1]:
                    best_move = (target.get_name(), val)
        
        return best_move

    def expectiMin2(self, board, area, expectiMinLayers):
        values = []
        area_dice = area.get_dice()

        for adjacent_area in self.possible_attacks_from_area(board, area, self.player_name):
            enemy_dice = adjacent_area.get_dice()
            if not adjacent_area.can_attack():
                continue
            lose_prob = attack_succcess_probability(enemy_dice, area_dice)
            if lose_prob <= THRESHOLD:        # tu ma byt snad lose_prob <= 0.2 nieeeee? ze je to 80% sanca ze oni prehraju
                newBoard = self.updateBoardDefence(board, area, adjacent_area) # ze na nas zautocili a vyhrali sme a s area nic nestane, oni budu mat get_dice() == 1
                areaThatAttacked = newBoard.get_area(adjacent_area.get_name()) # areaAttacked bude mat get_dice() == 1 kocku
                if expectiMinLayers == 0:
                    expectiVal = self.expectiMax2(newBoard, area)[1]
                else: 
                    expectiVal = self.expectiMin2(newBoard, area, expectiMinLayers - 1)

                val = (1 - lose_prob) * expectiVal * areaThatAttacked.get_dice() 
                values.append(val)
            else:
                # predpokladam, ze sme bitku prehrali, zobrali nam ho
                values.append(0.0001)
        
        return min(values) if values else 1.0

   

    def possible_attacks_from_area(self, board, area, player_name):
        neighbours = area.get_adjacent_areas()

        for adj in neighbours:
            adjacent_area = board.get_area(adj)
            if adjacent_area.get_owner_name() != player_name:
                yield adjacent_area