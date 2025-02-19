import cProfile
import pstats

from engine.basilisk import BasiliskEngine
from engine.evaluators import V0Evaluator
from rungame import Game

# evaluate_material = 5.262
# _evaluate_piece_position = 2.449
# get_legal_moves = 5.337 - 4.266
# push= 2.805 -2.377
# is_castling = 0.315
# pop = 1.254 - 0.423


if __name__ == '__main__':
    with cProfile.Profile() as pr:
        Game(BasiliskEngine(V0Evaluator()), BasiliskEngine(V0Evaluator())).play(time_limit=1., move_limit=10)

        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()
