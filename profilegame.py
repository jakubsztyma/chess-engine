import cProfile
import pstats

from rungame import play_game

# _evaluate_material = 2.858 / 24.461
# piece_type_at = 3.486 / 24.461
# get_legal_moves = 10.616 - 7.902 / 38.135
# get_legal_moves = 7.888 - 5.615 / 27.617


if __name__ == '__main__':
    with cProfile.Profile() as pr:
        play_game()

        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()
