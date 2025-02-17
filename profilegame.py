import cProfile
import pstats

from rungame import play_game

# _evaluate_material = 2.858 / 24.461


if __name__ == '__main__':
    with cProfile.Profile() as pr:
        play_game()

        ps = pstats.Stats(pr).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats()
