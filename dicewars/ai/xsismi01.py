import logging
from dicewars.ai.utils import possible_attacks
from dicewars.ai.utils import probability_of_holding_area, probability_of_successful_attack, attack_succcess_probability

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand
import copy

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

        best_turn = self.best_turn()
        return BattleCommand(area_name, best_turn) if best_turn is not None else EndTurnCommand()

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

    def best_turn(self):
        best = 0.0
        target_name = None

        for source, target in possible_attacks(self.board, self.player_name):
            area_name = source.get_name()
            atk_power = source.get_dice()
            atk_prob = probability_of_successful_attack(self.board, area_name, target.get_name())
            hold_prob = atk_prob * probability_of_holding_area(self.board, target.get_name(), atk_power - 1, self.player_name)
            newBoard = self.updateBoardAttack(self.board, source, target)
            new_value = self.expectiMax(newBoard, target)
            if new_value > best:
                best = new_value
                target_name = target.get_name()

        return target_name

    def expectiMax(self, board, area):
        atk_power = area.get_dice()
        if atk_power < 2:
            return 0.0
        values = []

        for target in self.possible_attacks_from_area(board, area, self.player_name): 
            attack_possibility_value = attack_succcess_probability(atk_power, target.get_dice())
            if attack_possibility_value >= 0.2 or atk_power == 8:
                newBoard = self.updateBoardAttack(board, area, target) # ze sme zautocili a vyhrali
                areaAttacked = newBoard.get_area(target.get_name()) # areaAttacked bude mat get_dice() - 1 kociek
                val = attack_possibility_value * self.expectiMin(newBoard, areaAttacked, self.playersCount) * areaAttacked.get_dice() 
                values.append(val)
        
        return max(values) if values else 0.0

    def expectiMin(self, board, area, expectiMinLayers):
        values = []
        area_dice = area.get_dice()

        for adjacent_area in self.possible_attacks_from_area(board, area, self.player_name):
            enemy_dice = adjacent_area.get_dice()
            if enemy_dice == 1:
                continue
            lose_prob = attack_succcess_probability(enemy_dice, area_dice)
            if lose_prob <= 0.2 or area_dice == 8:        # tu ma byt snad lose_prob <= 0.2 nieeeee? ze je to 80% sanca ze oni prehraju
                newBoard = self.updateBoardDefence(board, area, adjacent_area) # ze na nas zautocili a vyhrali sme a s area nic nestane, oni budu mat get_dice() == 1
                areaThatAttacked = newBoard.get_area(adjacent_area.get_name()) # areaAttacked bude mat get_dice() == 1 kocku
                if expectiMinLayers == 0:
                    expectiVal = self.expectiMax(newBoard, areaThatAttacked) 
                else: 
                    expectiVal = self.expectiMin(newBoard, areaThatAttacked, expectiMinLayers - 1)

                val = (1 - lose_prob) * expectiVal * areaThatAttacked.get_dice() 
                values.append(val)
        
        return min(values) if values else 1.0

    def possible_attacks_from_area(self, board, area, player_name):
        neighbours = area.get_adjacent_areas()

        for adj in neighbours:
            adjacent_area = board.get_area(adj)
            if adjacent_area.get_owner_name() != player_name:
                yield adjacent_area