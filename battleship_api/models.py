from django.db import models
from django.forms.models import model_to_dict
import random
from functools import reduce


ERROR_TYPES = (
    ("O", "OUT OF BOUNDS"),
    ("R", "REPEATED"),
)

DELTAS = [(-1, 0), (0, -1), (1, 0), (0, 1)]


class Game(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()

    board_rows = models.IntegerField(default=10)
    board_cols = models.IntegerField(default=10)
    ships_form = models.TextField(null=True, blank=True, default=None)

    resettable = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return f'{self.id}: {self.board_rows}x{self.board_cols} {self.ships.count()} [{self.start}]'

    @property
    def short_name(self):
        return f'{self.id}:[{self.board_rows}x{self.board_cols}] {self.ships.count()}'

    @property
    def ship_count(self):
        return self.ships.count()

    @property
    def ships_spaces(self):
        return self.ships_form.count('X')

    def to_dict(self):
        return {
            'id': self.id,
            'start': self.start,
            'end': self.end,
            'board_rows': self.board_rows,
            'board_cols': self.board_cols,
            'ships': self.ships_form
        }

    def check_play(self, play):
        return 0 <= play.shot_row < self.board_rows and 0 <= play.shot_col < self.board_cols

    def evaluate(self, play):
        board = self.__generate_board()
        shots_board = self.__generate_shots_board(play.player)

        shot_result = 0 if board[play.shot_row][play.shot_col] in ['-', ' '] else 1
        shots_board[play.shot_row] = f'{shots_board[play.shot_row][:play.shot_col]}{shot_result}{shots_board[play.shot_row][play.shot_col + 1:]}'

        # check sunken
        if shot_result == 1:
            ship_idx = int(board[play.shot_row][play.shot_col])
            ship = self.ships.all()[ship_idx]
            sf = self.__turn_form(ship.form, ship.turn)
            sf_rows = sf.split(',')
            sunken = True
            for r in range(len(sf_rows)):
                for c in range(len(sf_rows[r])):
                    if sf_rows[r][c] == 'X':
                        if shots_board[ship.row + r][ship.col + c] == '-':
                            sunken = False

            if sunken:
                shot_result = 2

        # check finished
        hits_count = reduce(lambda x, y: x + y.count('1'), shots_board, 0)

        if self.ships_spaces == hits_count:
            return 3

        return shot_result

    def put_ships(self):
        ships_dict = []
        ships_form_list = self.ships_form.split('|')
        ships_dict = self.__add_next_ship(ships_dict, ships_form_list, 0)

        for sd in ships_dict:
            ship = Ship.objects.create(game=self,
                                       form=sd['form'],
                                       row=sd['row'],
                                       col=sd['col'],
                                       turn=sd['turn'])
            ship.save()

    def __add_next_ship(self, ships_dict, ships_form, ship_idx):
        if ship_idx >= len(ships_form):
            return ships_dict

        initial_turn = random.randint(0, 3)
        ship_form = ships_form[ship_idx]
        current_board = self.__generate_board(ships_dict)

        for dt in range(4):
            ship_turn = (initial_turn + dt) % 4
            sf = self.__turn_form(ship_form, ship_turn)
            sf_rows = sf.split(',')

            initial_row = random.randint(0, self.board_rows - len(sf_rows))
            initial_col = random.randint(0, self.board_cols - len(sf_rows[0]))

            for dr in range(self.board_rows - len(sf_rows)):
                for dc in range(self.board_cols - len(sf_rows[0])):
                    ship_row = (initial_row + dr) % (self.board_rows - len(sf_rows))
                    ship_col = (initial_col + dc) % (self.board_cols - len(sf_rows[0]))

                    if self.__validate_position(current_board, ship_row, ship_col, sf):
                        ships_dict.append({'form': ship_form, 'row': ship_row, 'col': ship_col, 'turn': ship_turn})
                        result = self.__add_next_ship(ships_dict, ships_form, ship_idx + 1)
                        if result is not None:
                            return result

        return None

    def __turn_form(self, ship_form, turn):
        rows = ship_form.split(',')
        while turn > 0:
            rows = [''.join([r[i] for r in reversed(rows)]) for i in range(len(rows[0]))]
            turn -= 1

        return ','.join(rows)

    def __validate_position(self, board, row, col, ship_form):
        sf_rows = ship_form.split(',')
        for r in range(len(sf_rows)):
            for c in range(len(sf_rows[r])):
                if sf_rows[r][c] == 'X':
                    if board[row + r][col + c] != '-':
                        return False

        return True

    def __generate_board(self, ships_dict=None):
        board = ['-' * self.board_cols for _ in range(self.board_rows)]

        if ships_dict is None:
            ships_dict = map(lambda s: model_to_dict(s), self.ships.all())

        for idx, ship in enumerate(ships_dict):
            sf = self.__turn_form(ship['form'], ship['turn'])
            sf_rows = sf.split(',')
            row = ship['row']
            col = ship['col']

            for r in range(len(sf_rows)):
                for c in range(len(sf_rows[r])):
                    if sf_rows[r][c] == 'X':
                        board[row + r] = f'{board[row + r][:col + c]}{idx}{board[row + r][col + c + 1:]}'

        for r in range(self.board_rows):
            for c in range(self.board_cols):
                if board[r][c] not in ['-', ' ']:
                    for dr, dc in DELTAS:
                        if 0 <= r + dr < self.board_rows and 0 <= c + dc < self.board_cols and board[r + dr][c + dc] == '-':
                            board[r + dr] = board[r + dr][:c + dc] + ' ' + board[r + dr][c + dc + 1:]

        return board

    def __generate_shots_board(self, player):
        shots_board = ['-' * self.board_cols for _ in range(self.board_rows)]

        for play in player.plays.filter(game=self).exclude(result__isnull=True).all():
            shot_result = 0 if play.result == 0 else 1
            shots_board[play.shot_row] = f'{shots_board[play.shot_row][:play.shot_col]}{shot_result}{shots_board[play.shot_row][play.shot_col + 1:]}'

        return shots_board


class Ship(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='ships')
    form = models.TextField()
    row = models.IntegerField(default=0)
    col = models.IntegerField(default=0)
    turn = models.IntegerField(default=0)

    def __str__(self):
        return f'[{self.game}] {self.form} ({self.row},{self.col})'


class Player(models.Model):
    name = models.CharField(max_length=200)
    key = models.CharField(max_length=10)
    play_count = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.name}'

    def last_valid_play(self, game):
        plays = self.plays.filter(game=game,
                                  result__isnull=False,
                                  is_valid=True).order_by('-created').all()
        return plays[0] if len(plays) > 0 else None

    def game_plays_count(self, game):
        return self.plays.filter(game=game).count()

    def add_play(self):
        self.play_count += 1
        self.save()


class Play(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='plays')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='plays')
    shot_row = models.IntegerField(default=0)
    shot_col = models.IntegerField(default=0)
    result = models.IntegerField(null=True, default=None)

    is_valid = models.BooleanField(default=True)
    error_type = models.CharField(max_length=1, choices=ERROR_TYPES, null=True, default=None)

    finished = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return f'{self.player} - {self.game} - {self.created}'


class Tournament(models.Model):
    name = models.CharField(max_length=200)
    games = models.ManyToManyField(
        Game, blank=True, related_name='tournaments'
    )
    players = models.ManyToManyField(
        Player, blank=True, related_name='players'
    )

    def __str__(self):
        return f'{self.name} - {self.games_count} - {self.players_count}'

    @property
    def games_count(self):
        return self.games.count()

    @property
    def players_count(self):
        return self.players.count()


class GamesSummary(Game):
    class Meta:
        proxy = True
        verbose_name = 'Game Summary'
        verbose_name_plural = 'Games Summary'
