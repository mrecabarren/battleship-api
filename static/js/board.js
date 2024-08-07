document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.show-board').forEach(function(element) {
        element.addEventListener('click', function(event) {
            event.preventDefault();
            let gameId = event.target.dataset.id;
            // Aquí puedes hacer una solicitud AJAX para obtener los datos del tablero
            fetch(`/api/admin/get_board/${gameId}/`)
                .then(response => response.json())
                .then(data => {
                    // Crear el contenido del modal con los datos recibidos
                    document.getElementById('modal-content').innerHTML = data.board_html;
                    // Mostrar el modal
                    document.getElementById('modal').style.display = 'block';
                });
        });
    });

    document.getElementById('modal-close').addEventListener('click', function() {
        document.getElementById('modal').style.display = 'none';
    });
});