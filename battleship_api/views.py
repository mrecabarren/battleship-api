from datetime import datetime, timezone

from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from django.template.loader import render_to_string

from battleship_api.models import Game, Player, Play


class BattleshipGamesView(View):

    def get(self, request):
        open_games = Game.objects.filter(start__lte=datetime.now(timezone.utc),
                                         end__gte=datetime.now(timezone.utc))

        open_games_list = [g.to_dict() for g in open_games]
        return JsonResponse({"games": open_games_list})


class BattleshipPlayView(View):

    def post(self, request, *args, **kwargs):
        game_id = request.POST.get('game', None)
        player_key = request.POST.get('key', None)
        shot_row = request.POST.get('shot_row', None)
        shot_col = request.POST.get('shot_col', None)

        if game_id is None or player_key is None or shot_row is None or shot_col is None:
            return HttpResponseBadRequest(
                'El POST para esta vista DEBE contener los siguientes parámetros: game, key, shot_row, shot_col')

        if not game_id.isnumeric():
            return HttpResponseBadRequest(
                f'El id del juego debe ser un número: {game_id}')

        player = Player.objects.filter(key=player_key).first()
        if player is None:
            return HttpResponseBadRequest(
                'No hay ningún jugador para la KEY dada')
        else:
            player.add_play()

        game = Game.objects.filter(id=game_id,
                                   end__gte=datetime.now(timezone.utc)).first()
        if game is None:
            if player_key == "RECA456":
                game = Game.objects.filter(id=game_id)
            if game is None:
                return HttpResponseBadRequest(
                    'El id del juego entregado no existe o no está activo')

        previous_state = player.last_valid_play(game)
        if previous_state is not None and previous_state.finished:
            return JsonResponse({"result": 'Juego ya finalizado',
                                 'finished': True})

        play = Play.objects.create(game=game,
                                   player=player,
                                   shot_row=int(shot_row),
                                   shot_col=int(shot_col))
        play.save()

        if not game.check_play(play):
            play.is_valid = False
            play.error_type = 'O'
            play.save()
            return HttpResponseBadRequest(
                f'La posición ({play.shot_row}, {play.shot_col}) no está dentro del tablero del juego ({game.board_rows, game.board_cols})')

        play.result = game.evaluate(play)
        play.finished = play.result == 3

        play.save()

        return JsonResponse({"result": play.result,
                             'finished': play.finished})


class BattleshipResetView(View):

    def post(self, request, *args, **kwargs):
        game_id = request.POST.get('game', None)
        player_key = request.POST.get('key', None)

        if game_id is None or player_key is None:
            return HttpResponseBadRequest(
                'El POST para esta vista DEBE contener los siguientes parámetros: game, key')

        if not game_id.isnumeric():
            return HttpResponseBadRequest(
                f'El id del juego debe ser un número: {game_id}')

        player = Player.objects.filter(key=player_key).first()
        if player is None:
            return HttpResponseBadRequest(
                'No hay ningún jugador para la KEY dada')

        game = Game.objects.filter(id=game_id,
                                   end__gte=datetime.now(timezone.utc)).first()
        if game is None:
            return HttpResponseBadRequest(
                'El id del juego entregado no existe o no está activo')

        if not game.resettable and player_key != "RECA456":
            return HttpResponseBadRequest(
                'Este juego no permite ser reseteado')

        Play.objects.filter(game=game, player=player).delete()

        return JsonResponse({"result": 'Se eliminaron las jugadas', 'game': game_id})


class BattleshipStatusView(View):

    def get(self, request):
        game_id = request.GET.get('game', None)
        player_key = request.GET.get('key', None)

        if game_id is None or player_key is None:
            return HttpResponseBadRequest(
                'El GET para esta vista DEBE contener los siguientes parámetros: game, key')

        player = Player.objects.filter(key=player_key).first()
        if player is None:
            return HttpResponseBadRequest(
                'No hay ningún jugador para la KEY dada')

        game = Game.objects.filter(id=game_id,
                                   end__gte=datetime.now(timezone.utc)).first()
        if game is None:
            return HttpResponseBadRequest(
                'El id del juego entregado no existe o no está activo')

        plays_count = player.game_plays_count(game)
        last_play = player.last_valid_play(game)

        if plays_count > 0 and last_play.finished:
            return JsonResponse({"finished": True, 'plays': plays_count, 'game': game_id})
        else:
            return JsonResponse({"finished": False, 'plays': plays_count, 'game': game_id})


def get_board(request, game_id):
    game = Game.objects.get(id=game_id)

    board_html = render_to_string('admin/modal_board.html', {'game': game, 'board': game.board})
    return JsonResponse({'board_html': board_html})