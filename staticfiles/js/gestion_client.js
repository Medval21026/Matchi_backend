$(document).ready(function() {
    // Fonctionnalité de recherche
    $('#searchCite').on('input', function() {
        var searchValue = $(this).val().toLowerCase();
        $('.information_sur_client').each(function() {
            var tel = $(this).find('.F_client p:contains("Tél:")').text().toLowerCase();
            if (tel.includes(searchValue)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    // Fonctionnalité pour modifier un client
    $('.btn-modifier').on('click', function() {
        var clientId = $(this).data('client-id');
        var clientNom = $(this).data('client-nom');
        var clientPrenom = $(this).data('client-prenom');
        var clientCredie = $(this).data('client-credie');
        var clientTelephone = $(this).data('client-telephone');

        $('#edit_client_id').val(clientId);
        $('#edit_nom').val(clientNom);
        $('#edit_prenom').val(clientPrenom);
        $('#edit_credie').val(clientCredie);
        $('#edit_numero_telephone').val(clientTelephone);
        $('#edit_modepass_chiffre').val('');
    });

    // Soumission du formulaire de modification
    $('#editClientForm').on('submit', function(event) {
        event.preventDefault();
        var clientId = $('#edit_client_id').val();
        var nom = $('#edit_nom').val();
        var prenom = $('#edit_prenom').val();
        var credie = $('#edit_credie').val();
        var numeroTelephone = $('#edit_numero_telephone').val();
        var modepassChiffre = $('#edit_modepass_chiffre').val();

        $.ajax({
            url: '{% url "modifier_client" %}', 
            method: 'POST',
            data: {
                client_id: clientId,
                nom: nom,
                prenom: prenom,
                credie: credie,
                numero_telephone: numeroTelephone,
                modepass_chiffre: modepassChiffre,
                csrfmiddlewaretoken: '{{ csrf_token }}'
            },
            success: function(response) {
                location.reload();
            },
            error: function(response) {
                alert('Une erreur est survenue lors de la modification du client.');
            }
        });
    });

    // Fonctionnalité pour supprimer un client
    $('.btn-supprimer').on('click', function() {
        var clientId = $(this).data('client-id');
        var supprimerClientUrl = '{{ url "supprimer_client" }}'; // Dans le template, juste avant l'appel à JS

        if (confirm('Êtes-vous sûr de vouloir supprimer ce client ?')) {
            $.ajax({
                url: supprimerClientUrl,
                method: 'POST',
                data: {
                    client_id: clientId,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                },
                success: function(response) {
                    $('#client' + clientId).remove();
                },
                error: function(response) {
                    alert('Une erreur est survenue lors de la suppression du client.');
                }
            });
        }
    });
});
