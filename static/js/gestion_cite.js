$(document).ready(function() {
    $('.ListeCite').on('click', '.site', function() {
        $(this).next('.formation_sur_cite').show();
    });

    window.closeFormationSurCite = function(button) {
        $(button).closest('.formation_sur_cite').hide();
    };

    window.afficherModalModification = function(cite_id) {
        var cite = $("#cite" + cite_id).data();
        $('#cite_id').val(cite_id);
        $('#nom_modifier').val(cite.nom);
        $('#longitude_modifier').val(cite.longitude);
        $('#latitude_modifier').val(cite.latitude);
        $('#nombre_joueur_modifier').val(cite.nombre_joueur);
        $('#lieu_modifier').val(cite.lieu);
        $('#prix_par_heure_modifier').val(cite.prix_par_heure);
        $('#client_modifier').val(cite.client_id);
        $('#Wilaye_modifier').val(cite.wilaye_id);
        $('#Moughataa_modifier').val(cite.moughataa_id);
        
        $('#ballon_disponible_true_modifier').prop('checked', cite.ballon_disponible === 'True');
        $('#ballon_disponible_false_modifier').prop('checked', cite.ballon_disponible === 'False');
        $('#maillot_disponible_true_modifier').prop('checked', cite.maillot_disponible === 'True');
        $('#maillot_disponible_false_modifier').prop('checked', cite.maillot_disponible === 'False');
        $('#eclairage_disponible_true_modifier').prop('checked', cite.eclairage_disponible === 'True');
        $('#eclairage_disponible_false_modifier').prop('checked', cite.eclairage_disponible === 'False');
        $('#sonorisation_disponible_true_modifier').prop('checked', cite.sonorisation_disponible === 'True');
        $('#sonorisation_disponible_false_modifier').prop('checked', cite.sonorisation_disponible === 'False');
        
        // Afficher le modal
        $('#modifierCiteModal').modal('show');
        var formAction = "{% url 'modifier_cite' 0 %}".replace('/0/', '/' + cite_id + '/');
        $('#modifierCiteForm').attr('action', formAction);
    };
});