#! python3
# chess.py - chess study helpers

import collections
import datetime
import math
import typing


class ProcChessComPgnFile:
    """Class to extract data from Chess.com .pgn files."""

    # Tokens for start and end of time control description
    TOKEN_START_TIMECTRL = '[timecontrol '
    TOKEN_END_TIMECTRL = ']'
    # Tokens for start and end of clock's visor description
    TOKEN_START_CLOCK = r'{[%clk '
    TOKEN_END_CLOCK = ']}'
    # Clock's visor description formats
    CLOCK_FORMATS = ('%H:%M:%S.%f', '%H:%M:%S')

    def __init__(self, path_pgn: str):
        self._load_pgn(path_pgn)
        self._extract_time_ctrl()
        self._extract_hist_clock()
        self._extract_time_per_move()

    def _build_time_by_clock(self, clock_desc: str) -> datetime.time:
        """
        Build datetime.time instance by clock description.

        :param clock_desc: clock description
        :raise ValueError: if clock format is unknown
        :return: datetime.time instance
        """
        for fmt in self.CLOCK_FORMATS:
            try:
                return datetime.datetime.strptime(clock_desc, fmt).time()
            except ValueError:
                continue
        raise ValueError(f'unrecognized clock format "{clock_desc}"')

    def _extract_hist_clock(self) -> None:
        """Extract historical clock's visor time."""
        self.hist_clock_black = []
        self.hist_clock_white = []
        move_id = 1
        start = 0
        while True:
            start = self.pgn.find(self.TOKEN_START_CLOCK, start)
            if start == -1:
                break
            start += len(self.TOKEN_START_CLOCK)
            end = self.pgn.find(self.TOKEN_END_CLOCK, start)
            time_ = self._build_time_by_clock(self.pgn[start:end])
            if move_id % 2:
                self.hist_clock_white.append(time_)
            else:
                self.hist_clock_black.append(time_)
            start = end
            move_id += 1
        self.num_moves_black = len(self.hist_clock_black)
        self.num_moves_white = len(self.hist_clock_white)

    def _extract_time_ctrl(self) -> None:
        """Extract seconds the players receives at beginning and per
        move."""
        start = (self.pgn.index(self.TOKEN_START_TIMECTRL)
                 + len(self.TOKEN_START_TIMECTRL))
        end = self.pgn.index(self.TOKEN_END_TIMECTRL, start)
        timectrl_desc = self.pgn[start:end].replace('"', '')
        if '+' in timectrl_desc:
            self.secs_start, self.secs_incr = map(int, timectrl_desc.split('+'))
        else:
            self.secs_start = int(timectrl_desc)
            self.secs_incr = 0

    def _extract_time_per_move(self) -> None:
        """Extract time per move."""
        self.time2moves_black = collections.defaultdict(list)
        self.time2moves_white = collections.defaultdict(list)
        self.hist_mtime_black = []
        self.hist_mtime_white = []
        h, r = divmod(self.secs_start, 3600)
        m, s = divmod(r, 60)
        today = datetime.date.today()
        dt_start = datetime.datetime.combine(
            today, datetime.time(hour=h, minute=m, second=s)
        )
        td_incr = datetime.timedelta(seconds=self.secs_incr)
        time2moves_hmtime_hclock = (
            (self.time2moves_black, self.hist_mtime_black, self.hist_clock_black),
            (self.time2moves_white, self.hist_mtime_white, self.hist_clock_white)
        )
        for time2moves, hmtime, hclock in time2moves_hmtime_hclock:
            start = dt_start
            for move_id, clock_time in enumerate(hclock, 1):
                start += td_incr
                end = datetime.datetime.combine(today, clock_time)
                move_time = (start - end).total_seconds()
                time2moves[math.ceil(move_time)].append(move_id)
                hmtime.append(move_time)
                start = end

    @staticmethod
    def _fmt_time_per_move(seconds: float) -> str:
        """
        Format time per move.

        :param seconds: time in seconds
        :return: seconds formated as %hr%min%sec
        """
        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        desc = ''
        if h:
            desc = f'{int(h)}hr'
        if m:
            desc = f'{desc}{int(m)}min'
        if s:
            desc = f'{desc}{math.ceil(s)}sec'
        return desc

    def _load_pgn(self, path_pgn: str) -> None:
        """Load pgn file content."""
        with open(path_pgn) as f:
            self.pgn = f.read().replace('\n', ' ').lower()

    def _print_hist(self, desc: str, hist: list, print_move_id: bool = True,
                    fmt_func: typing.Callable[[typing.Any], str] = str) -> None:
        """
        Prints historical data.

        :param desc: player and/or historical data description
        :param hist: historical data to print
        :param print_move_id: if True, prints move's identification
        :param fmt_func: function to format historical data record as
            string (default str)
        """
        if print_move_id:
            def fmt_move(move_id: int) -> str:
                return f'[move {move_id}] '
        else:
            def fmt_move(move_id: int) -> str:
                return ''
        print(f'{len(hist)} records for {desc}')
        for i, hi in enumerate(hist, 1):
            print(f'{fmt_move(i)}{fmt_func(hi)}')

    def _print_moves_by_time(self, white: bool) -> None:
        """
        Prints moves by time.

        :param white: if True, prints white moves
        """
        if white:
            desc = 'white'
            num_moves_match = self.num_moves_white
            d_view = self.time2moves_white.items()
        else:
            desc = 'black'
            num_moves_match = self.num_moves_black
            d_view = self.time2moves_black.items()
        spent_time = 0
        approx_rec_time = self.secs_start + num_moves_match*self.secs_incr
        print(f'{num_moves_match} {desc} moves sorted by worst time'
              f' (approximate {self._fmt_time_per_move(approx_rec_time)}'
              ' received)')
        for time_, moves in sorted(d_view, key=lambda kv: kv[0], reverse=True):
            num_moves_time = len(moves)
            desc_perc = f'{round(time_/approx_rec_time * 100, 2)}%'
            print(f'{num_moves_time} move(s) spent'
                  f' {self._fmt_time_per_move(time_)} (about {desc_perc}) each'
                  f' (move(s): {moves})')
            spent_time += num_moves_time * time_
        print(f'approximate {self._fmt_time_per_move(spent_time)} spent')

    def print_black_hist_clock(self) -> None:
        """Prints black historical clock's visor."""
        self._print_hist('black historical clock\'s visor',
                         self.hist_clock_black)

    def print_black_hist_time_per_move(self, sort_by_worst: bool = False
                                       ) -> None:
        """
        Prints black historical time per move.

        :param sort_by_worst: if True, prints historical time per move
            sorted by worst time (default sorted by move id)
        """
        if not sort_by_worst:
            self._print_hist('black historical time per move',
                             self.hist_mtime_black,
                             fmt_func=self._fmt_time_per_move)
            return

        hist_mtime_sorted = sorted(enumerate(self.hist_mtime_black, 1),
                                   key=lambda i_t: i_t[1], reverse=True)
        self._print_hist(
            'black historical time per move sorted by worst time',
            hist_mtime_sorted, False,
            lambda i_t: f'[move {i_t[0]}] {self._fmt_time_per_move(i_t[1])}'
        )

    def print_black_moves_by_time(self) -> None:
        """Prints black moves by time."""
        self._print_moves_by_time(False)

    def print_timectrl_desc(self) -> None:
        """Prints time control description."""
        print(f'Time Control: {self._fmt_time_per_move(self.secs_start)}'
              f' + {self._fmt_time_per_move(self.secs_incr)}')

    def print_white_hist_clock(self) -> None:
        """Prints white historical clock's visor."""
        self._print_hist('white historical clock\'s visor',
                         self.hist_clock_white)

    def print_white_hist_time_per_move(self, sort_by_worst: bool = False
                                       ) -> None:
        """
        Prints white historical time per move.

        :param sort_by_worst: if True, prints historical time per move
            sorted by worst time (default sorted by move id)
        """
        if not sort_by_worst:
            self._print_hist('white historical time per move',
                             self.hist_mtime_white,
                             fmt_func=self._fmt_time_per_move)
            return

        hist_mtime_sorted = sorted(enumerate(self.hist_mtime_white, 1),
                                   key=lambda i_t: i_t[1], reverse=True)
        self._print_hist(
            'white historical time per move sorted by worst time',
            hist_mtime_sorted, False,
            lambda i_t: f'[move {i_t[0]}] {self._fmt_time_per_move(i_t[1])}'
        )

    def print_white_moves_by_time(self) -> None:
        """Prints white moves by time."""
        self._print_moves_by_time(True)


if __name__ == '__main__':
    p = ProcChessComPgnFile('C:\\Users\\Vitor\\Downloads\\ConvestPro\\'
                            'chesscom_example.pgn')
    p.print_timectrl_desc()
    # p.print_black_hist_clock()
    # p.print_black_hist_time_per_move(False)
    # p.print_black_hist_time_per_move(True)
    p.print_black_moves_by_time()
    # p.print_white_hist_clock()
    # p.print_white_hist_time_per_move(False)
    # p.print_white_hist_time_per_move(True)
    p.print_white_moves_by_time()
