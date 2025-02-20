import cProfile
import pstats

from engine.basilisk import BasiliskEngine
from engine.evaluators import V0Evaluator
from rungame import Game

# evaluate_material = 7.446
# _evaluate_piece_position = 1.441
# get_legal_moves = 6.396
# push=  2.699 -2.322
# is_castling = 0.364
# pop = 0.928 - 0.405

from rungame import play_game

if __name__ == '__main__':
    with cProfile.Profile() as pr:
        Game(BasiliskEngine(V0Evaluator()), BasiliskEngine(V0Evaluator())).play(time_limit=1., move_limit=10)

        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()
