from django.contrib import admin
from django.urls import include, path
from . import mobile,views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('index', views.index , name='index'),
    path('get-moughataa/<int:wilaya_id>/', views.get_moughataa, name='get_moughataa'),
    path('client/<int:client_id>/ajouter_credits/', views.ajouter_credits, name='ajouter_credits'),
    path('ajouter_terrain', views.ajouter_terrain, name='ajouter_terrain'),
    path('gestion_client', views.gestion_client, name='gestion_client'),
    path('gestion_terrain', views.gestion_terrain, name='gestion_terrain'),
    path('modifier_client', views.modifier_client, name='modifier_client'),
    path('supprimer_client', views.supprimer_client, name='supprimer_client'),
    path('ajouter_client', views.ajouter_client, name='ajouter_client'),
    path('modifier_terrain/<int:terrain_id>/', views.modifier_terrain, name='modifier_terrain'),
    path('supprimer_terrain/<int:terrain_id>/', views.supprimer_terrain, name='supprimer_terrain'),
    path('joueur/gerer/<int:joueur_id>/', views.gerer_joueur, name='gerer_joueur'),
    path('gestion_proprietaire', views.liste_proprietaires, name='gestion_proprietaire'),
    path('ajouter_proprietaire', views.ajouter_proprietaire, name='ajouter_proprietaire'),
    path('modifier_proprietaire', views.modifier_proprietaire, name='modifier_proprietaire'),
    path('supprimer_proprietaire', views.supprimer_proprietaire, name='supprimer_proprietaire'),
    
    path('gestion_wilaya', views.gestion_wilaya, name='gestion_wilaya'),
    path('ajouter_wilaya', views.ajouter_wilaya, name='ajouter_wilaya'),
    path('modifier_wilaya', views.modifier_wilaya, name='modifier_wilaya'),
    path('supprimer_wilaya', views.supprimer_wilaya, name='supprimer_wilaya'),
    
    path('gestion_moughataa', views.gestion_moughataa, name='gestion_moughataa'),
    path('ajouter_moughataa', views.ajouter_moughataa, name='ajouter_moughataa'),
    path('modifier_moughataa', views.modifier_moughataa, name='modifier_moughataa'),
    path('supprimer_moughataa', views.supprimer_moughataa, name='supprimer_moughataa'),

    path('listes_joueurs', views.listes_joueurs, name='listes_joueurs'),
    path('inscription', views.inscription, name='inscription'),
    path('academie', views.academie, name='academie'),
    path('ajouter_academie', views.ajouter_academie, name='ajouter_academie'),
    path('modifier_academie/<int:academie_id>/', views.modifier_academie, name='modifier_academie'),
    path('supprimer_academie/<int:academie_id>/', views.supprimer_academie, name='supprimer_academie'),
    path('', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('page_acceuil/', views.page_acceuil, name='page_acceuil'),
    path('index', mobile.index , name='index'),
#    path('ajouter_cite', mobile.ajouter_cite , name='ajouter_cite'),
    path('gestion_client', mobile.gestion_client , name='gestion_client'),
#    path('gestion_cite', mobile.gestion_cite , name='gestion_cite'),
#    path('modifier_client/', mobile.modifier_client, name='modifier_client'),
    path('supprimer_client/', mobile.supprimer_client, name='supprimer_client'),
    path('ajouter_client/', mobile.ajouter_client, name='ajouter_client'),
#    path('modifier_cite/<int:cite_id>/', mobile.modifier_cite, name='modifier_cite'),
#    path('supprimer_cite/<int:cite_id>/', mobile.supprimer_cite, name='supprimer_cite'),
    # path('', mobile.page_acceuil , name='page_acceuil'),
    path('register/', mobile.register_client, name='register_client'),
    path('login/', mobile.login_client, name='login_client'),
    path('getPassword/', mobile.getPassword, name='getPassword'),
    path('changePassword/', mobile.changePassword, name='changePassword'),
    path('CheckNumero/<str:numero_telephone>/', mobile.check_numero, name='CheckNumero'),



    path('registerr/', mobile.ClientCreateView.as_view(), name='register_client'),
    path('add_terrain/', mobile.TerrainsCreateView.as_view(), name='add_terrain'),
    path('clients/', mobile.ClientListView.as_view(), name='list_clients'),
    path('get_user_info/', mobile.get_user_info, name='get_user_info'),
    path('get_terrain_info/<int:client_id>/', mobile.get_terrain_info, name='get_terrain_info'),
    path('get_all_terrains/', mobile.get_all_terrains, name='get_all_terrains'),

    path('heures-disponibles/<int:client_id>/<str:date>/', mobile.heures_disponibles, name='heures_disponibles'),
    path('heures-disponibles-jouer/<int:terrain_id>/<str:date>/', mobile.heures_disponibles_jouers, name='heures_disponibles_jouers'),
    path('terrains/', mobile.TerrainsListView.as_view(), name='terrains-list'),
    # path('terrains/<int:terrain_id>/available-schedules/', mobile.terrain_heures_disponibles, name='available_schedules'),
    path('joueurs/', mobile.JoueursListView.as_view(), name='joueurs-list'),
    path('joueurs/<int:joueur_id>/', mobile.joueur_detail, name='joueur_details'),
    path('faire_reservation/', mobile.faire_reservation, name='faire_reservation'),
    path('annuler_reservation/<int:reservation_id>/', mobile.annuler_reservation, name='annuler_reservation'),
    path('get_reservations/<int:joueur_id>/', mobile.get_reservations, name='get_reservations'),

    path('joueurs/<int:player_id>/update/', mobile.update_player, name='update_player'),
    path('joueurs/<int:player_id>/uploadProfileImage/', mobile.uploadProfileImage, name='uploadProfileImage'),
    # /joueurs/$playerId/uploadProfileImage/
    path('joueurs/register/', mobile.JoueurCreateView.as_view(), name='joueur-register'),
    path('client/<int:client_id>/reservations/', mobile.client_reservations, name='client_reservations'),
    path('add-indisponibilite/', mobile.AddIndisponibiliteView.as_view(), name='add_indisponibilite'),
    path('wilayes/', mobile.WilayeList.as_view(), name='wilaye-list'),
    path('moughataas/<int:code_wilaye>/', mobile.get_moughataas, name='get_moughataas'),
    path('ActiveDesactive/<int:joueur_id>/', mobile.ActiveDesactive, name='ActiveDesactive'),
    path('academies/', mobile.AcademieListCreateAPIView.as_view(), name='academie-list-create'),
    path('gestion_periode',views.gestion_periode, name='gestion_periode'),
    path('supprimer_periode/<int:id>/', views.supprimer_periode, name='supprimer_periode'),
    path('modifier_periode/<int:id>/', views.modifier_periode, name='modifier_periode'),
    path('liste_heure_indisponible', views.liste_heure_indisponible, name='liste_heure_indisponible'),
    path('supprimer_heure/<int:heure_id>/', views.supprimer_heure_indisponible, name='supprimer_heure_indisponible'),
    path('modifier_heure_indisponible/<int:heure_id>/', views.modifier_heure_indisponible, name='modifier_heure_indisponible'),
    path('versions/', views.liste_versions, name='liste_versions'),
    path('versions/add/', views.ajouter_version, name='ajouter_version'),
    path('versions/update/<int:id>/', views.modifier_version, name='modifier_version'),
    path('versions/delete/<int:id>/', views.supprimer_version, name='supprimer_version'),








    # **************************************************************************( mobile APIs)********************************************************************

    path('AddPlayer/', mobile.add_player, name='AddPlayer'),
    path("LoginPlayer/", mobile.login_joueur, name='LoginPlayer'),
    path('update-token/', mobile.update_token, name='update_token'),
    path('create_reservation_request/', mobile.create_reservation_request, name='create_reservation_request'),
    path('client/<int:client_id>/demandes-reservation/', mobile.DemandeReservationClientView.as_view(), name='demandes-reservation-client'),
    path('updateFCMToken_joueur/<int:joueur_id>/', mobile.update_fcm_token_joueur, name='update_fcm_token_joueur'),
    path('reservations/<int:reservation_id>/', mobile.update_reservation_status, name='update_reservation_status'),
    path('get_terrinbyclient/<int:client_id>/', mobile.get_terrinbyclient, name='get_terrinbyclient'),

    path('client/<int:client_id>/reservations_confirmees/', mobile.nombre_reservations_confirmees, name='reservations_confirmees'),
    path('DemandsCount', mobile.DemandsCount, name='/DemandsCount'),
    path('reservations/joueur/<int:joueur_id>/', mobile.get_reservations_par_joueur, name='get_reservations_par_joueur'),
    path('clients/<int:client_id>/reservations/', mobile.ClientReservationsView.as_view(), name='client-reservations'),
    path('delete-player/<int:player_id>/', mobile.DeletePlayerView.as_view(), name='delete_player'),
    path('demandes/<int:joueur_id>/', mobile.DemandeReservationViewSet.as_view({'get': 'list'}), name='demande-list'),
    path('demandes/read/<int:pk>/', mobile.DemandeReservationViewSet.as_view({'post': 'mark_as_read'}), name='demande-mark-as-read'),
    path('reservationmanuel/create/', mobile.ReservationManuelCreateAPIView.as_view(), name='reservationmanuel-create'),
    path('reservations-manuel/<int:client_id>/', mobile.ReservationManuelListView.as_view(), name='reservations-manuel-list'),
    path('change-passwordjoueur/', mobile.change_password_joueur, name='change_password'),
    path('demandes/<int:joueur_id>/mark_read/', mobile.mark_demandes_as_read, name='mark_demandes_as_read'),
    path('terrain/<int:terrain_id>/periode/create/', mobile.PeriodeCreateAPIView.as_view(), name='api_create_periode'),
    path('terrain/<int:terrain_id>/periodes/', mobile.get_periodes, name='get_periodes'),
    path('cancel_reservation/<int:reservation_id>/', mobile.cancel_reservation, name='cancel_reservation'),
    path('api/version/', mobile.get_version, name='get_version'),
    path('change_password/<str:phone_number>/', mobile.change_password, name='change_password'),
    # Nouvelle route unifiée pour obtenir les deux versions
    path('api/get_latest_versions/', mobile.get_latest_versions, name='get_latest_versions'),
    # Routes individuelles conservées pour compatibilité
    path('api/get_latest_version/matchi', mobile.get_latest_version_matchi, name='get_latest_version_matchi'),
    path('api/get_latest_version/client', mobile.get_latest_version_client, name='get_latest_version_client'),

]









if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


































