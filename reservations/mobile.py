from django.views import View
from rest_framework.authtoken.models import Token
from datetime import date, datetime, timedelta
import re
from django.db.models import Q,F
from django.shortcuts import render, redirect, get_object_or_404
from .models import DemandeReservation, Indisponibilites, Joueurs,Version,VersionClient, Periode, Reservations, Wilaye , Moughataa,Client, reservationmanuel,Indisponibles_tous_temps
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView
from .serializers import DemandeReservationSerializer, ReservationSerializer
from django.views.decorators.http import require_POST
import json
import hashlib
from .serializers import WilayeSerializer,ReservationSerializer_client,PeriodeSerializer
from rest_framework import generics
from datetime import time as dt_time
from .models import Wilaye, Moughataa,Academie
from .serializers import WilayeSerializer, MoughataaSerializer,AcademieSerializer

from .models import Wilaye, Moughataa
from .serializers import WilayeSerializer, MoughataaSerializer,IndisponibiliteSerializer
from django.views.decorators.http import require_http_methods
import requests
import google.auth
import time
from google.oauth2 import service_account
import google.auth.transport.requests
import logging
from datetime import datetime

from django.utils.timezone import now


# import re
# from .models import cite as CiteModel  # Renommer l'import pour éviter les conflits de noms

def index(request):
    return render(request, 'index.html')
def ajouter_client(request):
    return render(request, 'pages/ajouter_client.html')
def gestion_client(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        numero_telephone = request.POST.get('numero_telephone')
        modepass_clair = request.POST.get('modepass_chiffre')
        modepass_chiffre = make_password(modepass_clair)
        if not re.match(r'^\d{8}$', numero_telephone):
            return redirect('gestion_client')
        new_client = Client.objects.create(
            nom=nom,
            prenom=prenom,
            numero_telephone=numero_telephone,
            modepass_chiffre=modepass_chiffre
        )
        return redirect('gestion_client')
    clients = Client.objects.all()
    context = {
        'clients': clients,
    }
    return render(request, 'pages/gestion_client.html', context)
def modifier_client(request):
    client_id = request.POST.get('client_id')
    nom = request.POST.get('nom')
    prenom = request.POST.get('prenom')
    numero_telephone = request.POST.get('numero_telephone')
    modepass_chiffre = request.POST.get('modepass_chiffre', '')
    if not re.match(r'^\d{8}$', numero_telephone):
        return redirect('gestion_client')

    client = Client.objects.get(id=client_id)
    client.nom = nom
    client.prenom = prenom
    client.numero_telephone = numero_telephone
    if modepass_chiffre:
        client.modepass_chiffre = make_password(modepass_chiffre)
    client.save()
    return redirect('gestion_client')
def supprimer_client(request):
    client_id = request.POST.get('client_id')
    client = Client.objects.get(id=client_id)
    client.delete()
    return redirect('gestion_client')

@api_view(['GET'])
def get_user_info(request):
    client_id = request.query_params.get('client_id')
    if client_id is None:
        return Response({'error': 'Client ID non fourni'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        client = Client.objects.get(id=client_id)
        serializer = ClientSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Client.DoesNotExist:
        return Response({'error': 'Client non trouvé'}, status=status.HTTP_404_NOT_FOUND)


from .models import Client, Terrains
from .serializers import ClientSerializer, JoueurSerializer, TerrainSerializer,ReservationSerializer
from django.contrib.auth.hashers import check_password
from rest_framework import generics
from django.contrib.auth.hashers import make_password



def hash_password(password: str) -> str:
    # Utilise pbkdf2_sha256 pour hacher le mot de passe avec 720000 itérations
    hashed_password = make_password(password, hasher='pbkdf2_sha256')
    return hashed_password

class ChangePlayerPasswordView(APIView):
    def post(self, request):
        numero_telephone = request.data.get('numero_telephone')
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Vérifier que tous les champs sont fournis
        if not all([numero_telephone, old_password, new_password]):
            return Response({'error': 'Tous les champs sont obligatoires.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Rechercher le joueur par son numéro de téléphone
            joueur = Joueurs.objects.filter(numero_telephone=numero_telephone).first()
            if not joueur:
                return Response({'error': 'Joueur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

            # Vérifier si l'ancien mot de passe est correct
            if not check_password(old_password, joueur.password):
                return Response({'error': 'Ancien mot de passe incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

            # Mettre à jour le mot de passe
            joueur.password = make_password(new_password)
            joueur.save()

            return Response({'message': 'Le mot de passe a été changé avec succès.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def register_client(request):
    serializer = ClientSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_client(request):
    numero_telephone = request.data.get('numero_telephone')
    modepass_chiffre = request.data.get('modepass_chiffre')
    try:
        client = Client.objects.get(numero_telephone=numero_telephone)
        if check_password(modepass_chiffre, client.modepass_chiffre):
            return Response({'message': 'Login successful', 'client_id': client.id}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
    except Client.DoesNotExist:
        print(";;;;;;;;;;;;;;;;")
        return Response({'error': 'Client does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e :
        print("--------------------------------------------------",e)



@api_view(['POST'])
def getPassword(request):
    id = request.data.get('client')
    try:
        client = Client.objects.get(id=id)
        print(client.modepass_chiffre)
        mot=client.modepass_chiffre
        return Response(mot)

    except Exception as e :
        print("--------------------------------------------------",e)
        return Response("Client does not exist", status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def changePassword(request):
    id = request.data.get('client')
    pwd=request.data.get('pwd')
    pwd_hash=hash_password(pwd)
    try:
        client = Client.objects.get(id=id)
        client.modepass_chiffre=pwd_hash
        client.save()
        return Response({"message":"done"})

    except Exception as e :
        print("--------------------------------------------------",e)
        return Response({"message":"error"},  status=status.HTTP_400_BAD_REQUEST)






@api_view(['POST'])
def add_player(request):
    numero_telephone = request.data.get('numero_telephone')
    password = request.data.get('password')
    nom_joueur = request.data.get('nom')
    prenom_joueur = request.data.get('prenom')

    # Validation des champs obligatoires
    if not password:
        return Response(
            {"error": "Le mot de passe est obligatoire."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier si le numéro existe déjà
    if Joueurs.objects.filter(numero_telephone=numero_telephone).exists():
        return Response(
            {"error": "Le numéro de téléphone est déjà enregistré."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Hasher le mot de passe (obligatoire pour la sécurité)
    hashed_password = make_password(password)

    # Création du joueur avec le mot de passe haché
    # La méthode save() du modèle vérifiera que le mot de passe est déjà haché
    # et ne le hachera pas à nouveau
    joueur = Joueurs.objects.create(
        nom_joueur=nom_joueur,
        prenom_joueur=prenom_joueur,
        password=hashed_password,
        numero_telephone=numero_telephone
    )

    return Response({"message": "Joueur créé avec succès !"}, status=status.HTTP_201_CREATED)








class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

class TerrainsCreateView(generics.CreateAPIView):
    queryset = Terrains.objects.all()
    serializer_class = TerrainSerializer
class ClientListView(generics.ListAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
@api_view(['GET'])
def get_terrain_info(request, client_id):
    try:
        terrain = Terrains.objects.filter(client_id=client_id).first()
        if not terrain:
            return Response({'error': 'Terrain non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TerrainSerializer(terrain)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['GET'])
def get_all_terrains(request):
    try:
        # Récupérer tous les terrains avec les objets liés
        terrains = Terrains.objects.all().select_related('wilaye', 'moughataa')
        terrain_list = []

        # Parcourir chaque terrain et construire la réponse
        for terrain in terrains:
            terrain_data = {
                'id': terrain.id,
                'nom_fr': terrain.nom_fr,
                'nom_ar': terrain.nom_ar,
                'longitude': terrain.longitude,
                'latitude': terrain.latitude,
                'nombre_joueur': terrain.nombre_joueur,
                'lieu_fr': terrain.lieu_fr,
                'lieu_ar': terrain.lieu_ar,
                'photo1': request.build_absolute_uri(terrain.photo1.url) if terrain.photo1 else None,
                'photo2': request.build_absolute_uri(terrain.photo2.url) if terrain.photo2 else None,
                'photo3': request.build_absolute_uri(terrain.photo3.url) if terrain.photo3 else None,
                'prix_par_heure': terrain.prix_par_heure,
                'client': terrain.client.nom,  # Utiliser le nom du client au lieu de l'ID
                'wilaye_nom_fr': terrain.wilaye.nom_wilaye_fr if terrain.wilaye else None,
                'wilaye_nom_ar': terrain.wilaye.nom_wilaye_Ar if terrain.wilaye else None,
                'moughataa_nom_fr': terrain.moughataa.nom_fr if terrain.moughataa else None,
                'moughataa_nom_ar': terrain.moughataa.nom_ar if terrain.moughataa else None,
                'heure_ouverture': terrain.heure_ouverture,
                'heure_fermeture': terrain.heure_fermeture,
                'ballon_disponible': terrain.ballon_disponible,
                'maillot_disponible': terrain.maillot_disponible,
                'eclairage_disponible': terrain.eclairage_disponible,
                'siffler': terrain.siffler,
                'parking': terrain.parking,
                'eau': terrain.eau,
                'gazon_artificiel': terrain.gazon_artificiel,
                'client_id':terrain.client.id
            }
            terrain_list.append(terrain_data)

        return Response(terrain_list, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class TerrainViewSet(viewsets.ModelViewSet):
    queryset = Terrains.objects.all()
    serializer_class = TerrainSerializer





from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime


@api_view(['GET'])
def get_terrinbyclient(request, client_id):
    try:
        client = get_object_or_404(Client, pk=client_id)
        terrain = Terrains.objects.filter(client=client).first()  # Filter by client, get the first match

        if terrain is not None:
            return Response({"id": terrain.id}, status=200)
        else:
            return Response({"error": "No terrain found for this client."}, status=404)

    except Exception as e:
        print("Exception:", e)
        return Response({"error": str(e)}, status=400)




@api_view(['GET'])
def heures_disponibles(request, client_id, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        client = get_object_or_404(Client, pk=client_id)
        terrains = Terrains.objects.filter(client=client)

        heures_disponibles = []

        for terrain in terrains:
            heure_ouverture = terrain.heure_ouverture.hour
            heure_fermeture = terrain.heure_fermeture.hour

            print(f"Terrain: {terrain.nom_fr}, Heure d'ouverture: {heure_ouverture}, Heure de fermeture: {heure_fermeture}")
# Gestion des horaires avant et après minuit
            if heure_fermeture < heure_ouverture:
                soir = list(range(heure_ouverture, 24))  # Ex: 22h à 23h
                matin = list(range(0, heure_fermeture))  # Ex: 00h à 5h
                all_hours = soir + matin  # Assure l'ordre chronologique
            else:
                all_hours = list(range(heure_ouverture, heure_fermeture))

            # Réorganiser les heures pour garantir l'ordre correct
            if heure_fermeture < heure_ouverture:
                all_hours = sorted(all_hours, key=lambda h: (h < heure_ouverture, h))
            else:
                all_hours = sorted(all_hours)

            print(f"Liste des heures générées (ordonnées): {all_hours}")


            reservations = Reservations.objects.filter(terrain=terrain, date_reservation=date_obj)
            indisponibilites = Indisponibilites.objects.filter(terrain=terrain, date_indisponibilite=date_obj)

            heures_reservees = {hour for res in reservations for hour in range(res.heure_debut.hour, res.heure_fin.hour)}
            heures_indisponibles = {hour for ind in indisponibilites for hour in range(ind.heure_debut.hour, ind.heure_fin.hour)}

            print(f"Heures réservées: {heures_reservees}")
            print(f"Heures indisponibles: {heures_indisponibles_tous_temps}")

            # Construire la liste des heures avec état
            heures_libres2 = [
                {'heure': hour, 'etat': 'reservé'} if hour in heures_reservees else
                {'heure': hour, 'etat': 'indisponible'} if hour in heures_indisponibles else
                {'heure': hour, 'etat': 'libre'}
                for hour in all_hours
            ]
            print(heures_libres2)

            # Utiliser l'ordre défini par all_hours pour le tri
            heures_libres2 = sorted(heures_libres2, key=lambda x: all_hours.index(x['heure']))
            print(heures_libres2)

            heures_disponibles.append({
                'terrain': terrain.id,
                'heures_libres': heures_libres2
            })

        return Response(heures_disponibles, status=status.HTTP_200_OK)

    except Exception as e:
        print("Erreur: ", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









class TerrainsListView(APIView):
    def get(self, request):
        terrains = Terrains.objects.all()
        serializer = TerrainSerializer(terrains, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from datetime import datetime, timedelta
from django.utils.timezone import now
@api_view(['GET'])
def heures_disponibles(request, client_id, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        client = get_object_or_404(Client, pk=client_id)
        terrains = Terrains.objects.filter(client=client)

        heures_disponibles = []
        for terrain in terrains:
            current_time = datetime.now().time()
            heure_ouverture = terrain.heure_ouverture
            heure_fermeture = terrain.heure_fermeture

            # Debugging current time, opening, and closing time
            print(f"Terrain: {terrain.nom_fr}")
            print(f"Heure d'ouverture: {heure_ouverture}, Heure de fermeture: {heure_fermeture}")
            print(f"Heure actuelle: {current_time}")

            # Check today's date and whether hours need to be restricted based on the current time
            if date_obj == datetime.now().date():
                start_hour = max(heure_ouverture.hour, current_time.hour)
            else:
                start_hour = heure_ouverture.hour

            # Handle case where closing time is after midnight
            if heure_fermeture.hour < heure_ouverture.hour:
                print("Closing time is after midnight")
                hours_before_midnight = set(range(start_hour, 24))  # From opening to midnight
                hours_after_midnight = set(range(0, heure_fermeture.hour))  # From midnight to closing
                all_hours = hours_before_midnight.union(hours_after_midnight)
            else:
                all_hours = set(range(start_hour, heure_fermeture.hour))

            if date_obj == datetime.now().date():
                all_hours = [hour for hour in all_hours if hour >= current_time.hour]
            # Debugging all_hours to check the number of hours
            print(f"Generated all_hours: {all_hours}")
            print(f"Number of hours in all_hours: {len(all_hours)}")

            heures_reservees = set()
            heures_indisponibles = set()

            # Fetch reservations and filter out accepted ones
            reservations = DemandeReservation.objects.filter(terrain=terrain, date_reservation=date_obj, status='Acceptée')
            for reservation in reservations:
                heures_reservees.update(range(reservation.heure_debut.hour, reservation.heure_fin.hour))

            # Fetch manual reservations (reservationmanuel) for the client associated with the terrain
            client_associé = terrain.client
            reservations_manuel = reservationmanuel.objects.filter(client_id=client_associé.id, date_reservation=date_obj)
            for reservation in reservations_manuel:
                debut = reservation.heure_debut.hour
                fin = reservation.heure_fin.hour

                # If the reservation spans across midnight
                if fin > debut:
                    heures_reservees.update(range(debut, fin))
                else:
                    heures_reservees.update(range(debut, 24))  # From 23h to 23:59
                    heures_reservees.update(range(0, fin))
            indisponibilites = Indisponibilites.objects.filter(terrain=terrain, date_indisponibilite=date_obj)

            for indisponibilite in indisponibilites:
                print("indisponible ", indisponibilite.heure_debut.hour)

                debut = indisponibilite.heure_debut.hour
                fin = indisponibilite.heure_fin.hour

                if fin > debut:
                    heures_indisponibles.update(range(debut, fin))
                else:
                    # Fix: Ensure range() always produces an iterable
                    heures_indisponibles.update(range(debut, 24))  # From debut to midnight
                    heures_indisponibles.update(range(0, fin))     # From midnight to fin


            print("list indisponibles for",date_obj," : ",heures_indisponibles)

            heures_libres2 = []

            for hour in all_hours:
                if hour in heures_reservees:
                    heures_libres2.append({'heure': hour, 'etat': 'reservé'})
                elif hour in heures_indisponibles:
                    heures_libres2.append({'heure': hour, 'etat': 'indisponible'})
                else:
                    heures_libres2.append({'heure': hour, 'etat': 'libre'})

            heures_disponibles.append({
                'terrain': terrain.id,
                'heures_libres': heures_libres2
            })
            print("the finale horrair ",heures_disponibles)

        return Response(heures_disponibles, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error : ------------- ", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JoueurCreateView(APIView):
    def post(self, request):
        serializer = JoueurSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class JoueursListView(generics.ListCreateAPIView):
    queryset = Joueurs.objects.filter(visible=True)

    serializer_class = JoueurSerializer

def joueur_detail(request, joueur_id):
    joueur = get_object_or_404(Joueurs, id=joueur_id)

    # Sérialiser les objets Wilaye et Moughataa
    wilaye_data = WilayeSerializer(joueur.wilaye).data if joueur.wilaye else None
    moughataa_data = MoughataaSerializer(joueur.moughataa).data if joueur.moughataa else None

    joueur_data = {
        'id': joueur.id,
        'nom_joueur': joueur.nom_joueur,
        'prenom_joueur': joueur.prenom_joueur,
        'numero_telephone': joueur.numero_telephone,
        'poste': joueur.poste,
        'age': joueur.age,
        'photo_de_profile': joueur.photo_de_profile.url if joueur.photo_de_profile else None,
        'height': joueur.height,
        'weight': joueur.weight,
        'visible': joueur.visible,
        'moughataa':moughataa_data,
        'wilaye': wilaye_data,  # Utiliser les données sérialisées'moughataa': moughataa_data,  # Utiliser les données sérialisées
    }

    return JsonResponse(joueur_data)

@api_view(['POST'])
def faire_reservation(request):
    joueur_id = request.data.get('joueur_id')
    terrain_id = request.data.get('terrain_id')
    date_reservation_str = request.data.get('date_reservation')
    heure_debut_str = request.data.get('heure_debut')
    heure_fin_str = request.data.get('heure_fin')

    joueur = get_object_or_404(Joueurs, pk=joueur_id)
    terrain = get_object_or_404(Terrains, pk=terrain_id)

    try:
        date_reservation = datetime.fromisoformat(date_reservation_str)
        heure_debut = datetime.strptime(heure_debut_str, '%H:%M:%S').time()
        heure_fin = datetime.strptime(heure_fin_str, '%H:%M:%S').time()
    except ValueError:
        return Response({'error': 'Invalid date or time format. Must be in ISO 8601 and HH:MM:SS format respectively.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create a new reservation instance
    reservation = Reservations(
        joueur=joueur,
        terrain=terrain,
        date_reservation=date_reservation.date(),
        heure_debut=heure_debut,
        heure_fin=heure_fin
    )
    reservation.save()

    return Response({'message': 'Reservation successful'}, status=status.HTTP_201_CREATED)
@api_view(['POST'])
def annuler_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservations, pk=reservation_id)
    reservation.delete()
    return Response({'success': 'Réservation annulée avec succès'}, status=status.HTTP_204_NO_CONTENT)
@api_view(['GET'])
def get_reservations(request, joueur_id):
    reservations = Reservations.objects.filter(joueur_id=joueur_id).select_related('terrain')
    data = []
    for reservation in reservations:
        data.append({
            'terrain_name': reservation.terrain.nom,
            'location': reservation.terrain.lieu,
            'date_reservation': reservation.date_reservation.isoformat(),
            'heure_debut': reservation.heure_debut.strftime('%H:%M'),
            'heure_fin': reservation.heure_fin.strftime('%H:%M'),
            'price': reservation.terrain.prix_par_heure,
            'payment_method': 'amanty',
        })
    return JsonResponse(data, safe=False)

class ReservationsJoueurView(APIView):

    def get(self, request, joueur_id):
        joueur = get_object_or_404(Joueurs, id=joueur_id)  # Récupérer le joueur par son ID

        reservations = Reservations.objects.filter(joueur=joueur)

        serializer = ReservationSerializer(reservations, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def joueur_reservations(request, joueur_id):
    try:
        # Récupérer les réservations pour le joueur spécifié
        reservations = Reservations.objects.filter(joueur_id=joueur_id)
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)
    except Reservations.DoesNotExist:
        return Response({'error': 'Aucune réservation trouvée pour ce joueur.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def ActiveDesactive(request, joueur_id):
    try:
        # Récupérer le joueur spécifié par son ID
        joueur = Joueurs.objects.get(id=joueur_id)  # Use 'id' if it's the primary key
        value = request.data.get('visible', joueur.visible)  # Get 'visible' from the request, default to current value

        # Mettre à jour la visibilité du joueur
        joueur.visible = value
        joueur.save()  # Save the changes to the database

        return Response({"message": "ok", "visible": joueur.visible}, status=status.HTTP_200_OK)

    except Joueurs.DoesNotExist:
        return Response({"error": "Player not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def list_reservations(request):
    try:
        reservations = Reservations.objects.all()
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PATCH'])
def update_player(request, player_id):
    try:
        joueur = get_object_or_404(Joueurs, pk=player_id)

        # Mise à jour des champs avec les données fournies dans la requête
        if 'nom_joueur' in request.data:
            joueur.nom_joueur = request.data['nom_joueur']
        if 'prenom_joueur' in request.data:
            joueur.prenom_joueur = request.data['prenom_joueur']
        if 'numero_telephone' in request.data:
            joueur.numero_telephone = request.data['numero_telephone']
        if 'poste' in request.data:
            joueur.poste = request.data['poste']
        if 'age' in request.data:
            joueur.age = request.data['age']
        if 'height' in request.data:
            joueur.height = request.data['height']
        if 'weight' in request.data:
            joueur.weight = request.data['weight']
        if 'wilaye' in request.data:
            wilaye_id = request.data['wilaye']
            joueur.wilaye = get_object_or_404(Wilaye, pk=wilaye_id)
        if 'moughataa' in request.data:
            moughataa_id = request.data['moughataa']
            joueur.moughataa = get_object_or_404(Moughataa, pk=moughataa_id)

        # Sauvegarder les changements
        joueur.save()

        return Response({'message': 'Player updated successfully'}, status=status.HTTP_200_OK)

    except Joueurs.DoesNotExist:
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)




import os
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string

@api_view(['POST'])
def uploadProfileImage(request, player_id):
    print("Données de la requête:", request.data)
    print("Fichiers de la requête:", request.FILES)

    try:
        player = Joueurs.objects.get(pk=player_id)
        print("Joueur trouvé:", player)

        image = request.FILES.get('photo_de_profile')
        if image:
            print("Image reçue:", image)
            player.photo_de_profile = image
            player.save()
            print("Image enregistrée:", player.photo_de_profile.url)
            return Response({'message': 'Image uploaded successfully'}, status=status.HTTP_200_OK)
        else:
            print("Erreur : image manquante")
            return Response({'error': 'No image uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    except Joueurs.DoesNotExist:
        print("Erreur : joueur non trouvé")
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Erreur :", e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def client_reservations(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    reservations = Reservations.objects.filter(terrain__client=client).select_related('terrain', 'joueur')
    data = []
    for reservation in reservations:
        data.append({
            'terrain': reservation.terrain.nom,
            'joueur': f'{reservation.joueur.nom_joueur} {reservation.joueur.prenom_joueur}',
            'date_reservation': reservation.date_reservation,
            'heure_debut': reservation.heure_debut,
            'heure_fin': reservation.heure_fin,
        })
    return JsonResponse(data, safe=False)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class AddIndisponibiliteView(View):
    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)

            heure_indisponible = str(body.get('heure_indisponible'))
            date_indisponibilite = str(body.get('date_indisponibilite'))
            heure_fin_srt = str(body.get('heure_fin'))
            terrain_id = body.get('terrain')
            id_jour = body.get('id_jour')  # Récupérer l'ID du joueur

            print("\n\n\n============================================", heure_indisponible)

            # Convert ISO time strings to datetime.time objects
            heure_debut = datetime.strptime(heure_indisponible, "%H:%M:%S").time()
            heure_fin = datetime.strptime(heure_fin_srt, "%H:%M:%S").time()

            # Exemple de création d'une nouvelle indisponibilité
            try:
                Indisponibilites.objects.get(
                    heure_debut=heure_debut,
                    terrain_id=terrain_id,
                    date_indisponibilite=date_indisponibilite
                ).delete()
            except Indisponibilites.DoesNotExist:
                # Create a new entry if no existing one is found
                indisponibilite_data = {
                    'heure_debut': heure_debut,
                    'heure_fin': heure_fin,
                    'terrain_id': terrain_id,
                    'date_indisponibilite': date_indisponibilite
                }
                # Ajouter id_jour si fourni
                if id_jour:
                    try:
                        joueur = Joueurs.objects.get(id=id_jour)
                        indisponibilite_data['id_jour'] = joueur
                    except Joueurs.DoesNotExist:
                        pass  # Si le joueur n'existe pas, on crée l'indisponibilité sans id_jour
                
                Indisponibilites.objects.create(**indisponibilite_data)

            return JsonResponse({'message': 'Indisponibilité ajoutée avec succès'}, status=201)

        except ValueError as ve:
            print("error : =========================== ", ve)
            return JsonResponse({'error': f'Valeur incorrecte pour heure_indisponible: {ve}'}, status=400)

        except Exception as e:
            print("error : =========================== ", e)
            return JsonResponse({'error': str(e)}, status=500)
@api_view(['POST'])
def login_joueur(request):
    numero_telephone = request.data.get('numero_telephone')
    password = request.data.get('password')
    print("tel : " ,numero_telephone)
    print("pwd : " ,password)

    try:
        joueur = Joueurs.objects.get(numero_telephone=numero_telephone)
        print("pwd is ",joueur.password)
        print(check_password(password,joueur.password))
        if  check_password(password,joueur.password):
            response_data = {
                'id': joueur.id,
                'nom_joueur': joueur.nom_joueur,
                'prenom_joueur': joueur.prenom_joueur,
                'numero_telephone': joueur.numero_telephone,
                'poste': joueur.poste,
                'age': joueur.age,
                'height': joueur.height,
                'weight': joueur.weight,
                'photo_de_profile': joueur.photo_de_profile.url if joueur.photo_de_profile else None,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            print("Invalid password")
            return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
    except Joueurs.DoesNotExist:
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def DemandsCount(request):
    client_id = request.data.get('client')  # Get the 'client' ID from the request
    print("client is ",client_id)

    try:
        # Fetch the client
        client = Client.objects.get(id=client_id)

        # Get the first terrain for the client
        terrain = Terrains.objects.filter(client=client).first()

        if terrain is None:
            return Response({'count': 0, 'error': 'No terrain found for the specified client'}, status=status.HTTP_404_NOT_FOUND)
        date_actuelle = now().date()
        # Count the number of reservations for the given terrain
        demands_count = DemandeReservation.objects.filter(terrain=terrain,date_reservation=date_actuelle,status='En attente').count()

        return Response({'count': demands_count}, status=status.HTTP_200_OK)

    except Client.DoesNotExist:
        print("client not found===========")

        return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("\n \n Error : ",e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)




class WilayeList(generics.ListAPIView):
    queryset = Wilaye.objects.all()
    serializer_class = WilayeSerializer

def get_moughataas(request, code_wilaye):
    try:
        moughataas = Moughataa.objects.filter(wilaye__code_wilaye=code_wilaye)
        moughataa_list = [
            {
                "id": moughataa.id,
                "nom_fr": moughataa.nom_fr,
                "nom_ar": moughataa.nom_ar,
                "wilaye": moughataa.wilaye.code_wilaye
            }
            for moughataa in moughataas
        ]
        return JsonResponse({"moughataas": moughataa_list}, safe=False)
    except Moughataa.DoesNotExist:
        return JsonResponse({"error": "Wilaye not found or no moughataas available"}, status=404)
# Récupérer la liste des académies
class AcademieListCreateAPIView(generics.ListCreateAPIView):
    queryset = Academie.objects.all()
    serializer_class = AcademieSerializer


@api_view(["PATCH"])
def update_token(request):
    try:
        # Parse the JSON data
        data = json.loads(request.body)
        client_id = data.get('client_id')
        token = data.get('fcm_token')

        # Debugging : Afficher les données reçues
        print(f"Data received: client_id={client_id}, fcm_token={token}")

        if not client_id or not token:
            return JsonResponse({'error': 'Numéro de téléphone ou token manquant'}, status=400)

        # Get the client
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return JsonResponse({'error': 'Client non trouvé'}, status=404)

        # Update the FCM token
        client.fcm_token = token
        client.save()

        return JsonResponse({'message': 'Token mis à jour avec succès'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
def heures_disponibles_jouers(request, terrain_id, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        terrain = get_object_or_404(Terrains, pk=terrain_id)

        current_time = datetime.now().time()
        heure_ouverture = terrain.heure_ouverture
        heure_fermeture = terrain.heure_fermeture

        # Déterminer l'heure de début (éviter les heures passées si aujourd'hui)
        if date_obj == datetime.now().date():
            start_hour = max(heure_ouverture.hour, current_time.hour)
        else:
            start_hour = heure_ouverture.hour

        # Construction des horaires disponibles
        all_hours = []

        # Cas où l'heure de fermeture est avant l'heure d'ouverture (ex: 23h à 02h)
        if heure_fermeture.hour < heure_ouverture.hour:
            matin = list(range(heure_ouverture.hour, 24))  # De l'heure d'ouverture à 23h
            soir = list(range(0, heure_fermeture.hour))    # De 00h à l'heure de fermeture
            all_hours = matin + soir
        else:
            all_hours = list(range(heure_ouverture.hour, heure_fermeture.hour))

        if date_obj == datetime.now().date():
            all_hours = [hour for hour in all_hours if hour >= current_time.hour]
        # Récupération des heures réservées et indisponibles
        heures_reservees = set()
        heures_indisponibles = set()

        def ajouter_heures_occupees(queryset, heures_set):
            for item in queryset:
                debut = item.heure_debut.hour
                fin = item.heure_fin.hour

                if fin > debut:  # Cas normal : même journée
                    heures_set.update(range(debut, fin))
                else:  # Cas traversant minuit (ex: 23h → 01h)
                    heures_set.update(range(debut, 24))  # De 23h à 23:59
                    heures_set.update(range(0, fin))    # De 00h à 01h

        # Vérification des réservations et indisponibilités
        demandes_reservation = DemandeReservation.objects.filter(terrain=terrain, date_reservation=date_obj, status='Acceptée')
        ajouter_heures_occupees(demandes_reservation, heures_reservees)

        indisponibilites = Indisponibilites.objects.filter(terrain=terrain, date_indisponibilite=date_obj)
        ajouter_heures_occupees(indisponibilites, heures_indisponibles)

        indisponibilites_tous_les_jours = Indisponibles_tous_temps.objects.filter(terrain=terrain)
        ajouter_heures_occupees(indisponibilites_tous_les_jours, heures_indisponibles)
        # Vérification des réservations manuelles via le client du terrain
        client_associé = terrain.client
        reservations_manuel = reservationmanuel.objects.filter(client_id=client_associé.id, date_reservation=date_obj)
        for reservation in reservations_manuel:
            debut = reservation.heure_debut.hour
            fin = reservation.heure_fin.hour

            if fin > debut:
                heures_reservees.update(range(debut, fin))
            else:
                heures_reservees.update(range(debut, 24))  # De 23h à 23:59
                heures_reservees.update(range(0, fin))    # De 00h à 01h

            print(f"Reservation manuelle: {debut}h - {fin}h")

        # Filtrer les heures libres
        heures_libres2 = [{'heure': hour, 'etat': 'libre'} for hour in all_hours if hour not in heures_reservees and hour not in heures_indisponibles]

        return Response([{
            'terrain': terrain.id,
            'heures_libres': heures_libres2
        }], status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from datetime import datetime

# Variables globales pour la gestion du cache du jeton d'accès et de son expiration
access_token_cache = None
token_expiration_time = None

def get_firebase_access_token():
    global access_token_cache, token_expiration_time

    # Vérification si le jeton est encore valide
    if access_token_cache and token_expiration_time and token_expiration_time > time.time():
        print("Le jeton d'accès est toujours valide.")
        return access_token_cache

    # Chemin vers le fichier de compte de service
    service_account_file = os.path.join(os.path.dirname(__file__), 'matchi-8543f-firebase-adminsdk-fbsvc-6c13949ae6.json')

    if not os.path.exists(service_account_file):
        print("Le fichier de compte de service est introuvable.")
        return None

    try:
        # Chargement des informations d'identification à partir du fichier de compte de service
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/firebase.messaging']
        )

        # Rafraîchir les informations d'identification pour obtenir un nouveau jeton si nécessaire
        request = Request()
        credentials.refresh(request)

        # Récupération du jeton d'accès
        access_token = credentials.token

        # Mise à jour du cache avec l'heure d'expiration
        access_token_cache = access_token
        if credentials.expiry:
            token_expiration_time = credentials.expiry.timestamp()
        else:
            # Si pas d'expiration définie, mettre 1 heure par défaut
            token_expiration_time = time.time() + 3600

        print(f"Access Token généré: {access_token}")
        return access_token
    except Exception as e:
        print(f"Une erreur s'est produite: {e}")
        return None

@api_view(['POST'])
def create_reservation_request(request):
    joueur_id = request.data.get('joueur_id')
    terrain_id = request.data.get('terrain_id')
    date_reservation = request.data.get('date_reservation')
    heure_debut = request.data.get('heure_debut')
    heure_fin = request.data.get('heure_fin')

    try:
        joueur = Joueurs.objects.get(id=joueur_id)

        # Vérifier si le joueur est bloqué
        if joueur.is_blocked:
            return Response({'error': 'Votre compte est bloqué. Vous ne pouvez pas effectuer de réservation.'},
                            status=status.HTTP_403_FORBIDDEN)

        terrain = Terrains.objects.get(id=terrain_id)

        # Convertir les heures en format datetime pour la comparaison
        format_heure = "%H:%M"
        date_reservation_obj = datetime.strptime(date_reservation, "%Y-%m-%d")
        heure_debut_obj = datetime.strptime(heure_debut, format_heure)
        heure_fin_obj = datetime.strptime(heure_fin, format_heure)

        indisponible = Indisponibilites.objects.filter(
            terrain=terrain,
            date_indisponibilite=date_reservation_obj
        ).filter(
            Q(heure_debut__lt=heure_fin_obj) &
            Q(heure_fin__gt=heure_debut_obj)
        ).exists()

        if indisponible:
            return Response(
                {'error': 'Ce terrain est indisponible à cet horaire.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier si une réservation existe déjà
        if DemandeReservation.objects.filter(
            joueur=joueur,
            terrain=terrain,
            date_reservation=date_reservation_obj,
            heure_debut=heure_debut_obj
        ).exists():
                return Response({'error': 'Vous avez déjà une réservation à cette heure.'},
                    status=status.HTTP_400_BAD_REQUEST)

        # Créer la demande de réservation
        demande = DemandeReservation(
            joueur=joueur,
            terrain=terrain,
            date_reservation=date_reservation_obj,
            heure_debut=heure_debut_obj,
            heure_fin=heure_fin_obj
        )
        demande.save()

        # Envoyer une notification au client
        messages_a_envoyer = [
            {
                'joueur_name': joueur.nom_joueur,
                'terrain_name': terrain.nom_fr
            }
        ]
        send_multiple_notifications_client(terrain.client.fcm_token, messages_a_envoyer)

        return Response({'message': 'Demande de réservation créée avec succès.'},
                        status=status.HTTP_201_CREATED)

    except Joueurs.DoesNotExist:
        return Response({'error': 'Joueur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
    except Terrains.DoesNotExist:
        return Response({'error': 'Terrain non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def send_notification_to_client(fcm_token, joueur_name, terrain_name):
    """
    Envoie une notification au client via Firebase Cloud Messaging.
    """
    if not fcm_token:
        print("FCM token manquant, notification non envoyée.")
        return

    try:
        access_token = get_firebase_access_token()
        if not access_token:
            print("Impossible de récupérer le token Firebase.")
            return

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; UTF-8',
        }

        notification = {
            "message": {
                "token": fcm_token,
                "notification": {
                    "title": "Nouvelle réservation طلب حجز جديد",
                    "body": f"Le joueur {joueur_name} a demandé à réserver le terrain {terrain_name}.",
                },
                "data": {
                    "type": "reservation",
                    "joueur_name": joueur_name,
                    "terrain_name": terrain_name
                }
            }
        }

        project_id = 'matchi-8543f'
        url = f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send'

        print(f"Envoi de la requête à {url} avec les données : {notification}")

        response = requests.post(url, headers=headers, json=notification, timeout=30)
        if response.status_code == 200:
            print("Notification envoyée avec succès au client.")
        else:
            print(f"Échec de l'envoi de la notification: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        print("Timeout lors de l'envoi de la notification au client.")
    except requests.exceptions.RequestException as e:
        print(f"Erreur de requête lors de l'envoi de la notification au client: {e}")
    except Exception as e:
        print(f"Erreur inattendue lors de l'envoi de la notification au client: {e}")



class DemandeReservationClientView(APIView):
    def get(self, request, client_id):
        client = get_object_or_404(Client, id=client_id)

        date_actuelle = now().date()
        heure_actuelle = now().time()

        demandes = DemandeReservation.objects.filter(
            terrain__client=client
        ).filter(
            # Réservations futures
            Q(date_reservation__gt=date_actuelle)

            # Aujourd'hui et heure normale
            | Q(
                date_reservation=date_actuelle,
                heure_fin__gt=heure_actuelle
            )

            # ✅ CAS SPÉCIAL 23h (TOUJOURS AFFICHER)
            | Q(
                date_reservation=date_actuelle,
                heure_debut=dt_time(23, 0)
            )
        ).order_by('date_reservation', 'heure_debut')

        serializer = DemandeReservationSerializer(demandes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@csrf_exempt
def update_fcm_token_joueur(request, joueur_id):
    if request.method == 'PATCH':  # Utiliser PATCH au lieu de POST
        try:
            data = json.loads(request.body)
            fcm_token = data.get('fcm_token')  # Récupérer le token FCM dans le corps de la requête

            # Récupérer le joueur correspondant à l'ID
            joueur = Joueurs.objects.filter(id=joueur_id).first()

            if joueur:
                # Mettre à jour le token FCM
                joueur.fcm_tokenjoueur = fcm_token
                joueur.save()

                return JsonResponse({'message': 'FCM token updated successfully'}, status=200)
            else:
                return JsonResponse({'error': 'Joueur not found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Only PATCH requests are allowed'}, status=405)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_reservation_status(request, reservation_id):
    try:
        demande = DemandeReservation.objects.get(id=reservation_id)
        print(f"Demande de réservation récupérée : {demande.id}, Terrain: {demande.terrain.nom_fr}")

        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        new_status = body_data.get('status')

        # ✅ Ajouter "Annulée"
        if new_status not in ['En attente', 'Acceptée', 'Refusée', 'Confirmée', 'Annulée']:
            return JsonResponse({'success': False, 'message': 'Statut invalide'}, status=400)

        terrain = demande.terrain
        client = terrain.client

        # Trouver la période tarifaire
        if demande.heure_debut.hour == 23:
            periode = Periode.objects.filter(terrain=terrain).filter(
                Q(heure_debut__gte=dt_time(23, 0), heure_fin__lte=dt_time(23, 59))
            ).first()
        else:
            periode = Periode.objects.filter(terrain=terrain).filter(
                Q(heure_debut__lte=demande.heure_debut, heure_fin__gte=demande.heure_fin)
            ).first()

        if not periode:
            periode = Periode.objects.filter(terrain=terrain).filter(
                Q(heure_debut__gte=dt_time(23, 0), heure_fin__lte=dt_time(1, 0)) |
                Q(heure_debut__gte=dt_time(0, 0), heure_fin__lt=dt_time(5, 0))
            ).first()

        prix_applique = float(periode.prix) if periode else float(terrain.prix_par_heure or 0)
        reduction = 0.05 * prix_applique

        # =========================
        # ✅ ACCEPTÉE
        # =========================
        if new_status == 'Acceptée':
            if demande.status == 'Acceptée':
                return JsonResponse({'success': False, 'message': 'Cette demande est déjà acceptée.'}, status=400)

            joueur = demande.joueur

            conflits = Reservations.objects.filter(
                terrain=terrain,
                date_reservation=demande.date_reservation,
                heure_debut__lt=demande.heure_fin,
                heure_fin__gt=demande.heure_debut
            ).exists() or reservationmanuel.objects.filter(
                date_reservation=demande.date_reservation,
                heure_debut__lt=demande.heure_fin,
                heure_fin__gt=demande.heure_debut
            ).exists()

            if conflits:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette heure et date sont déjà acceptées pour un autre joueur.'
                }, status=400)

            if client.credie < reduction:
                return JsonResponse({
                    'success': False,
                    'message': 'Crédit insuffisant pour accepter la réservation.'
                }, status=400)

            # Créer la réservation
            reservation = Reservations.objects.create(
                joueur=joueur,
                terrain=terrain,
                date_reservation=demande.date_reservation,
                heure_debut=demande.heure_debut,
                heure_fin=demande.heure_fin
            )
            print(f"Réservation créée pour la demande : {demande.id}")
            
            # Créer l'indisponibilité correspondante avec le joueur
            # Désactiver temporairement le signal pour éviter les doublons Kafka
            from django.db.models.signals import post_save, pre_delete
            from .signals import indisponibilite_saved, indisponibilite_deleted
            from .services.kafka_service import KafkaService
            
            post_save.disconnect(indisponibilite_saved, sender=Indisponibilites)
            try:
                indisponibilite = Indisponibilites.objects.create(
                    terrain=terrain,
                    id_jour=joueur,  # Associer le joueur à l'indisponibilité
                    date_indisponibilite=demande.date_reservation,
                    heure_debut=demande.heure_debut,
                    heure_fin=demande.heure_fin
                )
                # Appeler Kafka manuellement
                KafkaService.send_indisponibilite_event('CREATE', indisponibilite)
                print(f"Indisponibilité créée pour la réservation : {indisponibilite.uuid}")
            finally:
                # Réactiver le signal
                post_save.connect(indisponibilite_saved, sender=Indisponibilites)

        # =========================
        # ✅ CONFIRMÉE
        # =========================
        elif new_status == 'Confirmée':
            if demande.status == 'Confirmée':
                return JsonResponse({'success': False, 'message': 'Cette demande est déjà confirmée.'}, status=400)

            client.credie -= int(reduction)
            client.save()

        # =========================
        # ✅ ANNULÉE (nouveau)
        # =========================
        elif new_status == 'Annulée':
            # Supprimer les réservations
            Reservations.objects.filter(
                joueur=demande.joueur,
                terrain=demande.terrain,
                date_reservation=demande.date_reservation,
                heure_debut=demande.heure_debut
            ).delete()
            
            # Récupérer les indisponibilités avant suppression pour envoyer les messages Kafka
            from django.db.models.signals import pre_delete
            from .signals import indisponibilite_deleted
            from .services.kafka_service import KafkaService
            
            indisponibilites_a_supprimer = Indisponibilites.objects.filter(
                terrain=demande.terrain,
                date_indisponibilite=demande.date_reservation,
                heure_debut=demande.heure_debut,
                heure_fin=demande.heure_fin,
                id_jour=demande.joueur
            )
            
            # Désactiver temporairement le signal pour éviter les doublons
            pre_delete.disconnect(indisponibilite_deleted, sender=Indisponibilites)
            try:
                for indisponibilite in indisponibilites_a_supprimer:
                    # Appeler Kafka manuellement avant suppression
                    KafkaService.send_indisponibilite_event('DELETE', indisponibilite)
                
                # Supprimer les indisponibilités
                indisponibilites_a_supprimer.delete()
                print("Réservation et indisponibilité annulées et supprimées.")
            finally:
                # Réactiver le signal
                pre_delete.connect(indisponibilite_deleted, sender=Indisponibilites)

        # =========================
        # ✅ REFUSÉE seulement
        # =========================
        elif new_status == 'Refusée':
            # Supprimer les réservations
            Reservations.objects.filter(
                joueur=demande.joueur,
                terrain=demande.terrain,
                date_reservation=demande.date_reservation,
                heure_debut=demande.heure_debut
            ).delete()
            
            # Récupérer les indisponibilités avant suppression pour envoyer les messages Kafka
            from django.db.models.signals import pre_delete
            from .signals import indisponibilite_deleted
            from .services.kafka_service import KafkaService
            
            indisponibilites_a_supprimer = Indisponibilites.objects.filter(
                terrain=demande.terrain,
                date_indisponibilite=demande.date_reservation,
                heure_debut=demande.heure_debut,
                heure_fin=demande.heure_fin,
                id_jour=demande.joueur
            )
            
            # Désactiver temporairement le signal pour éviter les doublons
            pre_delete.disconnect(indisponibilite_deleted, sender=Indisponibilites)
            try:
                for indisponibilite in indisponibilites_a_supprimer:
                    # Appeler Kafka manuellement avant suppression
                    KafkaService.send_indisponibilite_event('DELETE', indisponibilite)
                
                # Supprimer les indisponibilités
                indisponibilites_a_supprimer.delete()
                print("Réservation et indisponibilité refusées et supprimées.")
            finally:
                # Réactiver le signal
                pre_delete.connect(indisponibilite_deleted, sender=Indisponibilites)

        # =========================
        # UPDATE STATUS
        # =========================
        demande.status = new_status
        demande.save()

        # =========================
        # 🔕 Notification (pas pour confirmée)
        # =========================
        if new_status != 'Confirmée':
            messages_a_envoyer = [
                {
                    'status': new_status,
                    'terrain_name': demande.terrain.nom_fr,
                    'heure_debut': demande.heure_debut,
                    'heure_fin': demande.heure_fin
                }
            ]

            send_multiple_notifications(
                demande.joueur.fcm_tokenjoueur,
                messages_a_envoyer
            )





        return JsonResponse({
            'success': True,
            'message': f'Statut de la demande mis à jour : {new_status}',
            'demande_id': demande.id,
            'nouveau_statut': new_status
        }, status=200)

    except DemandeReservation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Demande de réservation non trouvée'}, status=404)
    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Erreur inattendue: {str(e)}'}, status=500)


from datetime import time as dt_time
import requests

def send_multiple_notifications(fcm_token, messages_info):

    if not fcm_token:
        print("FCM token manquant")
        return

    access_token = get_firebase_access_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8',
    }

    # ✅ format sécurisé
    def format_time(t):
        if isinstance(t, dt_time):
            return t.strftime("%H:%M")
        return ""

    url = "https://fcm.googleapis.com/v1/projects/matchi-8543f/messages:send"

    for info in messages_info:
        status = str(info.get('status', ''))
        terrain_name = info.get('terrain_name', '')

        heure_debut = info.get('heure_debut')
        heure_fin = info.get('heure_fin')

        hd = format_time(heure_debut)
        hf = format_time(heure_fin)

        body = f"{terrain_name} {status}"

        if hd and hf:
            body += f" {hd}-{hf}"

        data = {
            "message": {
                "token": fcm_token,
                "notification": {
                    "title": "Réservation",
                    "body": body
                }
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                print(f"Notification envoyée : {body}")
            else:
                print(f"Erreur FCM {response.status_code}: {response.text}")

        except Exception as e:
            print(f"Erreur envoi notification: {e}")

def send_multiple_notifications_client(fcm_token, messages_info):
    """
    Envoie plusieurs notifications au client via Firebase Cloud Messaging.
    """
    if not fcm_token:
        print("FCM token manquant, notification non envoyée.")
        return

    try:
        access_token = get_firebase_access_token()
        if not access_token:
            print("Impossible de récupérer le token Firebase.")
            return

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; UTF-8',
        }

        project_id = 'matchi-8543f'
        url = f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send'

        for info in messages_info:
            joueur_name = info.get('joueur_name', '')
            terrain_name = info.get('terrain_name', '')

            notification = {
                "message": {
                    "token": fcm_token,
                    "notification": {
                        "title": "Nouvelle réservation طلب حجز جديد",
                        "body": f"Le joueur {joueur_name} a demandé à réserver le terrain {terrain_name}.",
                    },
                    "data": {
                        "type": "reservation",
                        "joueur_name": joueur_name,
                        "terrain_name": terrain_name
                    }
                }
            }

            print(f"Envoi de la requête à {url} avec les données : {notification}")

            try:
                response = requests.post(url, headers=headers, json=notification, timeout=30)
                if response.status_code == 200:
                    print(f"Notification envoyée avec succès au client : {joueur_name} - {terrain_name}")
                else:
                    print(f"Échec de l'envoi de la notification: {response.status_code} - {response.text}")
            except requests.exceptions.Timeout:
                print("Timeout lors de l'envoi de la notification au client.")
            except requests.exceptions.RequestException as e:
                print(f"Erreur de requête lors de l'envoi de la notification au client: {e}")
            except Exception as e:
                print(f"Erreur inattendue lors de l'envoi de la notification au client: {e}")

    except Exception as e:
        print(f"Erreur inattendue lors de l'envoi des notifications au client: {e}")


def nombre_reservations_confirmees(request, client_id):
    try:
        # Récupérer le client
        client = Client.objects.get(id=client_id)

        # Obtenir la date actuelle
        date_actuelle = datetime.now().date()
        print(f"Date actuelle : {date_actuelle}")

        # Obtenir toutes les réservations acceptées (DemandeReservation)
        reservations = DemandeReservation.objects.filter(
            terrain__client=client,
            status="Acceptée",
            date_reservation=date_actuelle  # Filtrer dès la requête
        )
        print("Réservations acceptées aujourd'hui :", list(reservations))

        # Compter les demandes confirmées
        demandes_confirmees = reservations.count()

        # Obtenir toutes les réservations manuelles pour aujourd'hui
        reservations_manuelles = reservationmanuel.objects.filter(
            client=client,
            date_reservation=date_actuelle
        )
        print("Réservations manuelles aujourd'hui :", list(reservations_manuelles))

        # Compter les réservations manuelles
        reservations_manuelles_count = reservations_manuelles.count()

        # Additionner les deux
        total_reservations = demandes_confirmees + reservations_manuelles_count

        # Retourner la réponse sous forme de JSON
        return JsonResponse({
            'client_id': client.id,
            'client_nom': client.nom,
            'demandes_confirmees': total_reservations  # Total incluant les deux types
        })

    except Client.DoesNotExist:
        return JsonResponse({'error': 'Client non trouvé'}, status=404)


@api_view(['GET'])
def heures_disponibles_for_player(request, terrain_id, date):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        terrain = get_object_or_404(Terrains, pk=terrain_id)

        heures_disponibles = []
        current_time = datetime.now().time()
        heure_ouverture = terrain.heure_ouverture
        heure_fermeture = terrain.heure_fermeture

        print(f"Terrain: {terrain.nom_fr}")
        print(f"Heure d'ouverture: {heure_ouverture}, Heure de fermeture: {heure_fermeture}")
        print(f"Heure actuelle: {current_time}")

        # Déterminer l'heure de début en fonction de la date actuelle
        if date_obj == datetime.now().date():
            start_hour = max(heure_ouverture.hour, current_time.hour + (current_time.minute > 0))
        else:
            start_hour = heure_ouverture.hour

        all_hours = []
        current_hour = start_hour

        while True:
            if date_obj == datetime.now().date() and current_hour < current_time.hour:
                current_hour += 1
                continue
            all_hours.append(current_hour)
            current_hour += 1
            if current_hour == 24:  # Gérer le passage à minuit
                current_hour = 0
            if current_hour == heure_fermeture.hour:
                break

        print(f"Generated all_hours: {all_hours}")

        heures_reservees = set()
        heures_indisponibles = set()

        reservations = Reservations.objects.filter(terrain=terrain, date_reservation=date_obj)
        indisponibilites = Indisponibilites.objects.filter(terrain=terrain, date_indisponibilite=date_obj)

        for reservation in reservations:
            heures_reservees.update(range(reservation.heure_debut.hour, reservation.heure_fin.hour))

        for indisponibilite in indisponibilites:
            heures_indisponibles.update(range(indisponibilite.heure_debut.hour, indisponibilite.heure_fin.hour))

        heures_libres2 = []

        for hour in all_hours:
            formatted_hour = f"{hour:02d}:00"  # Assurer un affichage en 24h

            if hour in heures_reservees:
                heures_libres2.append({'heure': formatted_hour, 'etat': 'reservé'})
            elif hour in heures_indisponibles:
                heures_libres2.append({'heure': formatted_hour, 'etat': 'indisponible'})
            else:
                heures_libres2.append({'heure': formatted_hour, 'etat': 'libre'})

        heures_disponibles.append({
            'terrain': terrain.id,
            'heures_libres': heures_libres2
        })

        return Response(heures_disponibles, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error : ------------- ", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




def calcul_prix(terrain, heure_debut, heure_fin):
    """
    Calcule le prix d'une réservation en fonction du terrain et de l'heure.
    Gère le créneau spécial 23h et les périodes traversant minuit.
    """
    # Cas spécial 23h
    if heure_debut.hour == 23:
        periode = Periode.objects.filter(
            terrain=terrain,
            heure_debut__lte=dt_time(23, 0),
            heure_fin__gte=dt_time(23, 0)
        ).first()
    else:
        # Cherche la période normale
        periode = Periode.objects.filter(
            terrain=terrain,
            heure_debut__lte=heure_debut,
            heure_fin__gte=heure_fin
        ).first()

    if not periode:
        # Cas traversant minuit ou période spéciale
        periode = Periode.objects.filter(
            terrain=terrain
        ).filter(
            Q(heure_debut__gte=dt_time(23, 0), heure_fin__lte=dt_time(1, 0)) |
            Q(heure_debut__gte=dt_time(0, 0), heure_fin__lt=dt_time(5, 0))
        ).first()

    # Si aucune période trouvée, utiliser prix par défaut du terrain
    if periode:
        prix_applique = float(periode.prix)
    else:
        prix_applique = float(terrain.prix_par_heure or 0)

    return prix_applique

from django.utils import timezone

def get_reservations_par_joueur(request, joueur_id):
    joueur = get_object_or_404(Joueurs, id=joueur_id)

    now = timezone.now()
    today = now.date()
    current_time = now.time()

    reservations_data = []

    # 1️⃣ Réservations confirmées (non expirées)
    # Inclure toutes les réservations futures et celles d'aujourd'hui qui ne sont pas encore expirées
    # Cas spécial : les réservations 23h-00h d'aujourd'hui ne sont pas expirées tant qu'on n'a pas dépassé 23h59
    
    # Réservations 23h-00h d'aujourd'hui - toujours inclure (elles expirent après 23h59)
    reservations_23h_today = Reservations.objects.filter(
        joueur=joueur,
        date_reservation=today,
        heure_debut__hour=23,
        heure_fin__hour=0
    )
    
    # Réservations futures
    reservations_future = Reservations.objects.filter(
        joueur=joueur,
        date_reservation__gt=today
    )
    
    # Réservations d'aujourd'hui (non 23h-00h) qui ne sont pas encore expirées
    reservations_today = Reservations.objects.filter(
        joueur=joueur,
        date_reservation=today
    ).exclude(
        heure_debut__hour=23,
        heure_fin__hour=0
    ).filter(
        heure_fin__gte=current_time
    )
    
    # Réservations passées (hier et avant) - exclure celles qui sont expirées
    # Mais garder les réservations 23h-00h d'hier si on est juste après minuit (00h-00h59)
    reservations_past = Reservations.objects.none()
    if current_time.hour == 0:
        # Si on est juste après minuit, inclure les réservations 23h-00h d'hier
        yesterday = today - timedelta(days=1)
        reservations_23h_yesterday = Reservations.objects.filter(
            joueur=joueur,
            date_reservation=yesterday,
            heure_debut__hour=23,
            heure_fin__hour=0
        )
        reservations_past = reservations_23h_yesterday
    
    # Combiner toutes les réservations
    reservations = (reservations_23h_today | reservations_future | reservations_today | reservations_past)\
        .select_related('terrain')\
        .order_by('date_reservation', 'heure_debut')

    for reservation in reservations:
        prix = calcul_prix(
            reservation.terrain,
            reservation.heure_debut,
            reservation.heure_fin
        )

        reservations_data.append({
            'terrain_Ar': reservation.terrain.nom_ar,
            'terrain_fr': reservation.terrain.nom_fr,
            'lieu_Ar': reservation.terrain.lieu_ar,
            'lieu_fr': reservation.terrain.lieu_fr,
            'prix': prix,
            'date_reservation': reservation.date_reservation,
            'heure_debut': reservation.heure_debut,
            'heure_fin': reservation.heure_fin,
            'status': 'Acceptée'
        })

    # 2️⃣ Demandes en attente NON expirées seulement
    # Cas spécial : réservation 23h-00h (minuit)
    # Une réservation 23h-00h d'aujourd'hui n'est pas expirée tant qu'on est encore le jour de la réservation
    # Elle expire seulement après 23h59, donc elle doit être incluse pour tous les jours (pas seulement à 23h)
    
    # Inclure TOUTES les réservations 23h-00h d'aujourd'hui (peu importe l'heure actuelle, tant qu'on est encore aujourd'hui)
    demandes_23h_today = DemandeReservation.objects.filter(
        joueur=joueur,
        status='En attente',
        date_reservation=today,
        heure_debut__hour=23,
        heure_fin__hour=0
    )
    
    # Inclure les réservations 23h-00h des jours futurs
    demandes_23h_future = DemandeReservation.objects.filter(
        joueur=joueur,
        status='En attente',
        date_reservation__gt=today,
        heure_debut__hour=23,
        heure_fin__hour=0
    )
    
    # Combiner toutes les réservations 23h-00h
    demandes_23h = demandes_23h_today | demandes_23h_future

    # Demandes normales (non expirées) - exclure les créneaux 23h-00h qui sont gérés séparément
    demandes_normales = DemandeReservation.objects.filter(
        joueur=joueur,
        status='En attente'
    ).filter(
        Q(date_reservation__gt=today) |
        Q(date_reservation=today, heure_fin__gte=current_time)
    ).exclude(
        heure_debut__hour=23,
        heure_fin__hour=0
    )

    # Combiner les deux querysets
    demandes = (demandes_23h | demandes_normales).select_related('terrain').order_by('-date_demande')

    for demande in demandes:
        prix = calcul_prix(
            demande.terrain,
            demande.heure_debut,
            demande.heure_fin
        )

        reservations_data.append({
            'terrain_Ar': demande.terrain.nom_ar,
            'terrain_fr': demande.terrain.nom_fr,
            'lieu_Ar': demande.terrain.lieu_ar,
            'lieu_fr': demande.terrain.lieu_fr,
            'prix': prix,
            'date_reservation': demande.date_reservation,
            'heure_debut': demande.heure_debut,
            'heure_fin': demande.heure_fin,
            'status': demande.status
        })

    # 🔥 Trier tout
    reservations_data.sort(key=lambda x: (x['date_reservation'], x['heure_debut']))

    return JsonResponse({
        'joueur': joueur.nom_joueur,
        'reservations': reservations_data
    })












class ClientReservationsView(APIView):
    def get(self, request, client_id):
        try:
            client = Client.objects.get(id=client_id)
            reservations = Reservations.objects.filter(terrain__client=client)
            serializer = ReservationSerializer_client(reservations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

class DeletePlayerView(APIView):
  # Assurez-vous que l'utilisateur est authentifié

    def delete(self, request, player_id):
        try:
            player = Joueurs.objects.get(id=player_id)
            player.delete()
            return Response({"message": "Joueur supprimé avec succès."}, status=status.HTTP_204_NO_CONTENT)
        except Joueurs.DoesNotExist:
            return Response({"error": "Joueur non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class DemandeReservationViewSet(viewsets.ViewSet):
    def list(self, request, joueur_id=None):
        # Récupérer les demandes de réservation acceptées pour un joueur
        demandes = DemandeReservation.objects.filter(joueur_id=joueur_id, status='Acceptée').order_by('-date_demande')

        # Créer une liste de dictionnaires pour les demandes
        demandes_data = []
        for demande in demandes:
            demandes_data.append({
                'id': demande.id,
                'terrain_ar': demande.terrain.nom_ar,
                'terrain_fr': demande.terrain.nom_fr,
                # ou utilisez d'autres champs que vous souhaitez afficher
                'joueur': demande.joueur.id,
                'date_reservation': demande.date_reservation.isoformat(),
                'heure_debut': demande.heure_debut.strftime('%H:%M'),
                'heure_fin': demande.heure_fin.strftime('%H:%M'),
                'status': demande.status,
                'date_demande': demande.date_demande.isoformat(),
                'read': demande.read
            })

        return JsonResponse(demandes_data, safe=False)

    def mark_as_read(self, request, pk=None):
        # Marquer une demande comme lue
        try:
            demande = DemandeReservation.objects.get(pk=pk)
            demande.read = True
            demande.save()
            return JsonResponse({'status': 'Demande marquée comme lue'})
        except DemandeReservation.DoesNotExist:
            return JsonResponse({'error': 'Demande non trouvée'}, status=404)

class ReservationManuelCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extraire les données de la requête
        nom = request.data.get("nom")
        date_reservation = request.data.get("date_reservation")
        heure_debut = request.data.get("heure_debut")
        heure_fin = request.data.get("heure_fin")
        numero_tel = request.data.get("numero_tel")
        client_id = request.data.get("client_id")  # Récupérer l'ID du client

        # Validation des données
        if not all([nom, date_reservation, heure_debut, heure_fin, numero_tel, client_id]):
            return Response({"error": "Tous les champs sont obligatoires."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Vérifier si le client existe
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({"error": "Client non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Conversion de la date et des heures
            date_reservation = datetime.strptime(date_reservation, "%Y-%m-%d").date()
            heure_debut = datetime.strptime(heure_debut, "%H:%M:%S").time()
            heure_fin = datetime.strptime(heure_fin, "%H:%M:%S").time()

            # Vérifier si une réservation existe déjà pour cette date et ces horaires pour le client
            existing_reservation = reservationmanuel.objects.filter(
                client=client,
                date_reservation=date_reservation,
                heure_debut=heure_debut,
                heure_fin=heure_fin
            ).exists()
            if existing_reservation:
                return Response({"error": "Une réservation existe déjà à cette date et heure pour ce client"}, status=status.HTTP_400_BAD_REQUEST)
            # Récupérer les terrains associés au client
            terrains_du_client = Terrains.objects.filter(client=client)
            # Vérifier si une réservation existe déjà pour l'un de ces terrains à la même date et heure
            existing_terrain_reservation = Reservations.objects.filter(
                terrain__in=terrains_du_client,
                date_reservation=date_reservation,
                heure_debut=heure_debut,
                heure_fin=heure_fin
            ).exists()
            if existing_terrain_reservation:
                return Response({"error": "Une réservation existe déjà à cette date et heure pour ce client"}, status=status.HTTP_400_BAD_REQUEST)
            terrains_du_cliente = Terrains.objects.filter(client=client)
            indisponibilites_existantes = Indisponibilites.objects.filter(
                terrain__in=terrains_du_cliente,
                date_indisponibilite=date_reservation,
                heure_debut=heure_debut,
            )

            if indisponibilites_existantes.exists():
                return JsonResponse({'error': 'Une réservation existe déjà à cette date et heure pour ce client'}, status=400)

            # Création de la réservation
            reservation = reservationmanuel.objects.create(
                nom=nom,
                date_reservation=date_reservation,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                numero_tel=numero_tel,
                client=client  # Associer le client
            )

            # Retourner la réponse avec les données créées
            return Response({
                "id": reservation.id,
                "nom": reservation.nom,
                "date_reservation": reservation.date_reservation,
                "heure_debut": reservation.heure_debut,
                "heure_fin": reservation.heure_fin,
                "numero_tel": reservation.numero_tel,
                "client": reservation.client.id
            }, status=status.HTTP_201_CREATED)

        except ValueError:
            return Response({"error": "Format de date ou d'heure invalide."}, status=status.HTTP_400_BAD_REQUEST)




# Configuration du logger
logger = logging.getLogger(__name__)
class ReservationManuelListView(APIView):
    def get(self, request, client_id):
        # Vérifier si le client existe
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return JsonResponse({"error": "Client non trouvé"}, status=404)

        # Récupérer les réservations valides pour ce client
        # Exclure les réservations avec une date de réservation passée et trier en ordre croissant
        reservations = reservationmanuel.objects.filter(
            client=client,
            date_reservation__gte=now()  # Inclure uniquement les réservations futures ou aujourd'hui
        ).order_by('date_reservation', 'heure_debut')

        # Si aucune réservation trouvée pour ce client
        if not reservations.exists():
            return JsonResponse({"message": "Aucune réservation trouvée pour ce client."}, status=404)

        # Préparer les données à retourner dans la réponse
        data = [
            {
                "id": reservation.id,
                "nom": reservation.nom,
                "date_reservation": reservation.date_reservation.strftime("%Y-%m-%d"),
                "heure_debut": reservation.heure_debut.strftime("%H:%M:%S"),
                "heure_fin": reservation.heure_fin.strftime("%H:%M:%S"),
                "numero_tel": reservation.numero_tel,
                "client_id": reservation.client.id,
            }
            for reservation in reservations
        ]

        # Logs pour débogage
        logger.debug(f"Réservations récupérées pour le client {client_id} : {data}")

        # Retourner les données sous forme de JSON
        return JsonResponse(data, safe=False, status=200)

@api_view(['POST'])
def change_password_joueur(request):
    player_id = request.data.get('player_id')
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    try:
        # Récupérer le joueur via son ID
        player = Joueurs.objects.get(id=player_id)

        # Vérifier si l'ancien mot de passe est correct
        if not check_password(current_password, player.password):
            return Response({'success': False, 'message': 'Mot de passe actuel incorrect'}, status=400)

        # Hacher et enregistrer le nouveau mot de passe
        player.password = make_password(new_password)
        player.save()

        return Response({'success': True, 'message': 'Mot de passe mis à jour avec succès'})
    except Joueurs.DoesNotExist:
        return Response({'success': False, 'message': 'Joueur introuvable'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def mark_demandes_as_read(request, joueur_id):
    if request.method == 'POST':
        try:
            # Vérifie si le joueur existe
            joueur = get_object_or_404(Joueurs, id=joueur_id)

            # Met à jour toutes les demandes pour le joueur
            DemandeReservation.objects.filter(joueur=joueur, read=False).update(read=True)

            return JsonResponse({'message': 'Demandes marquées comme lues avec succès.'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)

class PeriodeCreateAPIView(generics.CreateAPIView):
    queryset = Periode.objects.all()
    serializer_class = PeriodeSerializer  # Ajouter le serializer

    def create(self, request, *args, **kwargs):
        data = request.data
        terrain_id = kwargs.get('terrain_id')
        terrain = get_object_or_404(Terrains, id=terrain_id)

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save(terrain=terrain)
            return Response(
                {
                    "message": "Période créée avec succès",
                    "periode": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from rest_framework.renderers import JSONRenderer

@api_view(['GET'])
def get_periodes(request, terrain_id):
    # Récupérer le terrain avec l'ID fourni
    terrain = get_object_or_404(Terrains, id=terrain_id)

    # Récupérer toutes les périodes associées à ce terrain
    periodes = Periode.objects.filter(terrain=terrain)

    # Créer une liste pour stocker les données des périodes
    periode_data = [
        {
            'heure_debut': periode.heure_debut,
            'heure_fin': periode.heure_fin,
            'prix': str(periode.prix),  # Convertir le prix en chaîne de caractères
            'terrain_nom_fr': periode.terrain.nom_fr,  # Nom du terrain
        }
        for periode in periodes
    ]

    response = Response(periode_data, status=status.HTTP_200_OK)
    response.accepted_renderer = JSONRenderer()  # Ajout du renderer explicite
    response.accepted_media_type = "application/json"
    response.renderer_context = {'request': request}
    return response

@csrf_exempt
def cancel_reservation(request, reservation_id):
    if request.method == 'POST':
        try:
            reservation = reservationmanuel.objects.get(id=reservation_id)
            reservation.delete()
            return JsonResponse({'message': 'Réservation annulée avec succès'}, status=200)
        except reservationmanuel.DoesNotExist:
            return JsonResponse({'error': 'Réservation introuvable'}, status=404)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def get_version(request):
    try:
        version = Version.objects.last()  # ou .first() selon ton ordre
        if version:
            return JsonResponse({"versionNumber": version.versionNumber})
        else:
            return JsonResponse({"error": "Aucune version trouvée"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
    
@csrf_exempt
@require_http_methods(["PATCH"])
def change_password(request, phone_number):
    try:
        # Récupérer les données du corps de la requête
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        new_password = body_data.get('password')

        if not new_password:
            return JsonResponse({'error': 'Le mot de passe est requis'}, status=400)

        # Récupérer le joueur par ID
        joueur = Joueurs.objects.get(numero_telephone=phone_number)
        print(f"Joueur trouvé : {joueur.nom_joueur} {joueur.prenom_joueur}")

        # Hacher le mot de passe avant de le stocker
        joueur.password = make_password(new_password)
        joueur.save()

        return JsonResponse({'message': 'Mot de passe mis à jour avec succès'}, status=200)

    except Joueurs.DoesNotExist:
        return JsonResponse({'error': 'Joueur non trouvé'}, status=404)
    except Exception as e:
        # Logger l'erreur côté serveur
        print(f"Erreur inattendue : {str(e)}")
        return JsonResponse({'error': f'Erreur inattendue : {str(e)}'}, status=500)




@api_view(['GET'])
def get_latest_versions(request):
    """
    Récupère les dernières versions pour Matchi et Client en une seule requête.
    Peut également publier un événement Kafka si nécessaire.
    """
    try:
        # Récupérer les dernières versions
        latest_matchi = Version.objects.order_by('-versionNumber').first()
        latest_client = VersionClient.objects.order_by('-versionNumber').first()
        
        response_data = {}
        
        if latest_matchi:
            response_data['matchi_version'] = latest_matchi.versionNumber
        else:
            response_data['matchi_version'] = None
            
        if latest_client:
            response_data['client_version'] = latest_client.versionNumber
        else:
            response_data['client_version'] = None
        
        # Si aucune version trouvée
        if not latest_matchi and not latest_client:
            return JsonResponse({'error': 'Aucune version trouvée'}, status=404)
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de la récupération des versions: {str(e)}'}, status=500)

@api_view(['GET'])
def get_latest_version_matchi(request):
    """
    Récupère uniquement la dernière version Matchi (conservé pour compatibilité).
    """
    latest = Version.objects.order_by('-versionNumber').first()
    if latest:
        return JsonResponse({'versionNumber': latest.versionNumber})
    return JsonResponse({'error': 'No versions found'}, status=404)

@api_view(['GET'])
def get_latest_version_client(request):
    """
    Récupère uniquement la dernière version Client (conservé pour compatibilité).
    """
    latest = VersionClient.objects.order_by('-versionNumber').first()
    if latest:
        return JsonResponse({'versionNumber': latest.versionNumber})
    return JsonResponse({'error': 'No versions found'}, status=404)

@api_view(['GET'])
def check_numero(request, numero_telephone):
    existe = Joueurs.objects.filter(numero_telephone=numero_telephone).exists()
    return Response({"action": existe})