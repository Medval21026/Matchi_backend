
from django.views import View
from rest_framework.authtoken.models import Token
from datetime import date, datetime, timedelta
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from .decorators import login_required_custom
import re
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from .models import Indisponibilites, Joueurs, Reservations, Wilaye , Moughataa,Client,Academie,Inscription,Indisponibles_tous_temps,reservationmanuel
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView
from .serializers import ReservationSerializer
from django.views.decorators.http import require_POST
import json
import hashlib
from .serializers import WilayeSerializer
from rest_framework import generics
from decimal import Decimal, InvalidOperation


from .models import Wilaye, Moughataa,Academie,Terrains
from .serializers import WilayeSerializer, MoughataaSerializer,AcademieSerializer

from .models import Wilaye, Moughataa,Periode ,Version
from .serializers import WilayeSerializer, MoughataaSerializer,IndisponibiliteSerializer
from django.views.decorators.http import require_http_methods
from .proprietaire.services.proprietaire_api import get_all_proprietaires, get_horaires_occupes, create_proprietaire, update_proprietaire, delete_proprietaire

@login_required_custom
def liste_proprietaires(request):
    proprietaires = get_all_proprietaires()
    return render(request, "pages/proprietaire.html", {"proprietaires": proprietaires})

@login_required_custom
def ajouter_proprietaire(request):
    if request.method == "POST":
        data = {
            "nom": request.POST.get("nom"),
            "prenom": request.POST.get("prenom"),
            "telephone": request.POST.get("telephone"),
            "password": request.POST.get("password"),
        }

        try:
            created = create_proprietaire(data)
            return JsonResponse({"success": True, "proprietaire": created})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Méthode non autorisée"}, status=405)
@login_required_custom
def modifier_proprietaire(request):
    if request.method == "POST":
        proprietaire_id = request.POST.get('proprietaire_id')
        if not proprietaire_id:
            return JsonResponse({'success': False, 'error': 'ID du propriétaire manquant'}, status=400)
        
        data = {
            "nom": request.POST.get("nom"),
            "prenom": request.POST.get("prenom"),
            "telephone": request.POST.get("telephone"),
            "isActive": request.POST.get("isActive") == "on"
        }
        
        # Ajouter le mot de passe seulement s'il est fourni
        password = request.POST.get("password")
        if password:
            data["password"] = password

        try:
            updated = update_proprietaire(proprietaire_id, data)
            if updated:
                return JsonResponse({"success": True, "proprietaire": updated})
            else:
                return JsonResponse({"success": False, "error": "Erreur lors de la mise à jour du propriétaire"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Méthode non autorisée"}, status=405)

@login_required_custom
def supprimer_proprietaire(request):
    if request.method == "POST":
        proprietaire_id = request.POST.get('proprietaire_id')
        if not proprietaire_id:
            return JsonResponse({'success': False, 'error': 'ID du propriétaire manquant'}, status=400)
        
        try:
            success = delete_proprietaire(proprietaire_id)
            if success:
                return JsonResponse({"success": True, "message": "Propriétaire supprimé avec succès"})
            else:
                return JsonResponse({"success": False, "error": "Erreur lors de la suppression du propriétaire"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Méthode non autorisée"}, status=405)
    
@login_required_custom
def get_moughataa(request, wilaya_id):
    moughataas = Moughataa.objects.filter(wilaye_id=wilaya_id)
    moughataa_list = [{"id": m.id, "nom_fr": m.nom_fr, "nom_ar": m.nom_ar} for m in moughataas]
    return JsonResponse({"moughataas": moughataa_list})

def inscription(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        mot_de_passe = request.POST.get('pwd')
        confPwd = request.POST.get('confPwd')
        if mot_de_passe == confPwd:
            hashed_password = make_password(mot_de_passe)
            inscription = Inscription(login=login, mot_de_passe=hashed_password, confPwd=hashed_password)
            inscription.save()
            return redirect('login')
        else:
            pass
    return render(request, 'pages/signup.html')

def login(request):
    # Si l'utilisateur est déjà connecté, rediriger vers la page d'accueil
    if request.session.get('user_id'):
        return redirect('page_acceuil')
    
    error_message = None
    
    if request.method == 'POST':
        login_value = request.POST.get('login', '').strip()
        mot_de_passe = request.POST.get('pwd', '').strip()

        if not login_value or not mot_de_passe:
            error_message = "Veuillez remplir tous les champs."
        else:
            try:
                inscription = Inscription.objects.get(login=login_value)
                if check_password(mot_de_passe, inscription.mot_de_passe):
                    # Créer la session
                    request.session['user_id'] = inscription.id
                    request.session['user_login'] = inscription.login
                    request.session.set_expiry(86400)  # Session expire après 24 heures
                    # Forcer la sauvegarde de la session
                    request.session.modified = True
                    
                    # Rediriger vers la page demandée ou la page d'accueil
                    next_url = request.GET.get('next') or request.POST.get('next')
                    if next_url and next_url != 'page_acceuil' and next_url != '/':
                        return redirect(next_url)
                    return redirect('page_acceuil')
                else:
                    error_message = "Login ou mot de passe incorrect."
            except Inscription.DoesNotExist:
                error_message = "Login ou mot de passe incorrect."
            except Exception as e:
                error_message = f"Une erreur s'est produite : {str(e)}"
    
    return render(request, 'pages/login.html', {'error_message': error_message})

def logout(request):
    request.session.flush()
    return redirect('login')

@login_required_custom
def index(request):
    return render(request, 'index.html')

@login_required_custom
def ajouter_client(request):
    return render(request, 'pages/ajouter_client.html')

@login_required_custom
def gestion_client(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        credie = request.POST.get('credie')
        numero_telephone = request.POST.get('numero_telephone')
        modepass_clair = request.POST.get('modepass_chiffre')
        modepass_chiffre = make_password(modepass_clair)

        if not re.match(r'^\d{8}$', numero_telephone):
            messages.error(request, "Le numéro de téléphone doit comporter 8 chiffres.")
            return redirect('gestion_client')

        if Client.objects.filter(numero_telephone=numero_telephone).exists():
            messages.error(request, "Un client avec ce numéro de téléphone existe déjà.")
            return redirect('gestion_client')

        try:
            new_client = Client.objects.create(
                nom=nom,
                prenom=prenom,
                credie=credie,
                numero_telephone=numero_telephone,
                modepass_chiffre=modepass_chiffre
            )
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du client : {e}")

        return redirect('gestion_client')

    clients = Client.objects.all()
    context = {
        'clients': clients,
    }
    return render(request, 'pages/gestion_client.html', context)


@login_required_custom
def modifier_client(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        credie = request.POST.get('credie')
        numero_telephone = request.POST.get('numero_telephone')
        modepass_chiffre = request.POST.get('modepass_chiffre', '')

        # Validation du numéro de téléphone
        if not re.match(r'^\d{8}$', numero_telephone):
            return JsonResponse({'error': 'Le numéro de téléphone doit comporter 8 chiffres.'}, status=400)

        try:
            client = Client.objects.get(id=client_id)
            client.nom = nom
            client.prenom = prenom
            client.credie = credie
            client.numero_telephone = numero_telephone

            if modepass_chiffre:
                client.modepass_chiffre = make_password(modepass_chiffre)

            client.save()
            return JsonResponse({'success': 'Le client a été modifié avec succès.'}, status=200)
        except Client.DoesNotExist:
            return JsonResponse({'error': 'Le client spécifié n\'existe pas.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Requête invalide'}, status=400)


@login_required_custom
def supprimer_client(request):
    client_id = request.POST.get('client_id')
    client = Client.objects.get(id=client_id)
    client.delete()
    return redirect('gestion_client')

@login_required_custom
def modifier_terrain(request, terrain_id):
    terrain_instance = get_object_or_404(Terrains, id=terrain_id)

    if request.method == 'POST':
        try:
            # Mise à jour des champs texte et numériques
            terrain_instance.nom_fr = request.POST.get('nom_fr', terrain_instance.nom_fr)
            terrain_instance.nom_ar = request.POST.get('nom_ar', terrain_instance.nom_ar)
            terrain_instance.longitude = request.POST.get('longitude', terrain_instance.longitude)
            terrain_instance.latitude = request.POST.get('latitude', terrain_instance.latitude)
            terrain_instance.lieu_fr = request.POST.get('lieu_fr', terrain_instance.lieu_fr)
            terrain_instance.lieu_ar = request.POST.get('lieu_ar', terrain_instance.lieu_ar)
            terrain_instance.nombre_joueur = request.POST.get('nombre_joueur', terrain_instance.nombre_joueur)

            # Gestion du client via numéro de téléphone
            client_numero_telephone = request.POST.get('client')
            if client_numero_telephone:
                try:
                    client = Client.objects.get(numero_telephone=client_numero_telephone)
                    if client != terrain_instance.client and Terrains.objects.filter(client=client).exists():
                        messages.error(request, "Ce client a déjà enregistré un terrain.")
                        return redirect('gestion_terrain')
                    terrain_instance.client = client
                except Client.DoesNotExist:
                    messages.error(request, "Client avec ce numéro de téléphone n'existe pas.")
                    return redirect('gestion_terrain')

            # Mise à jour des relations (Wilaye & Moughataa)
            terrain_instance.wilaye_id = request.POST.get('Wilaye', terrain_instance.wilaye_id)
            terrain_instance.moughataa_id = request.POST.get('Moughataa', terrain_instance.moughataa_id)

            # Mise à jour des booléens (avec conversion explicite)
            terrain_instance.ballon_disponible = request.POST.get('ballon_disponible') == 'True'
            terrain_instance.gazon_artificiel = request.POST.get('gazon_artificiel') == 'True'
            terrain_instance.parking = request.POST.get('parking') == 'True'
            terrain_instance.siffler = request.POST.get('siffler') == 'True'
            terrain_instance.eau = request.POST.get('eau') == 'True'
            terrain_instance.maillot_disponible = request.POST.get('maillot_disponible') == 'True'
            terrain_instance.eclairage_disponible = request.POST.get('eclairage_disponible') == 'True'
            terrain_instance.sonorisation_disponible = request.POST.get('sonorisation_disponible') == 'True'

            # Mise à jour du prix avec validation
            prix_par_heure = request.POST.get('prix_par_heure')
            if prix_par_heure:
                try:
                    terrain_instance.prix_par_heure = Decimal(prix_par_heure)
                except InvalidOperation:
                    messages.error(request, "Les prix doivent être des nombres valides.")
                    return redirect('modifier_terrain', terrain_id=terrain_id)

            # Validation et mise à jour de l'heure
            try:
                if 'heure_ouverture' in request.POST and request.POST['heure_ouverture']:
                    terrain_instance.heure_ouverture = datetime.strptime(request.POST['heure_ouverture'], "%H:%M").strftime("%H:%M")

                if 'heure_fermeture' in request.POST and request.POST['heure_fermeture']:
                    terrain_instance.heure_fermeture = datetime.strptime(request.POST['heure_fermeture'], "%H:%M").strftime("%H:%M")

            except ValueError:
                messages.error(request, "Le format de l'heure est incorrect. Utilisez HH:MM.")
                return redirect('modifier_terrain', terrain_id=terrain_id)

            # Gestion des photos
            if 'photo1' in request.FILES:
                terrain_instance.photo1 = request.FILES['photo1']
            if 'photo2' in request.FILES:
                terrain_instance.photo2 = request.FILES['photo2']
            if 'photo3' in request.FILES:
                terrain_instance.photo3 = request.FILES['photo3']

            # Sauvegarde des modifications
            terrain_instance.save()
            messages.success(request, "Le terrain a été modifié avec succès.")
            return redirect('gestion_terrain')

        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('gestion_terrain')

    # Rendu de la page de modification
    return render(request, 'pages/modifier_terrain.html', {
        'terrain': terrain_instance,
        'wilayes': Wilaye.objects.all(),
        'moughataa': Moughataa.objects.all(),
    })


@login_required_custom
def supprimer_terrain(request, terrain_id):
    terrain_instance = get_object_or_404(Terrains, id=terrain_id)
    if request.method == 'POST':
        terrain_instance.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
@login_required_custom
def page_acceuil(request):
    nombre_clients = Client.objects.count()
    nombre_jouers = Joueurs.objects.count()
    nombre_terrains = Terrains.objects.count()
    nombre_de_reservation_par_client=Reservations.objects.values(
        'terrain__client__numero_telephone'
    ).annotate(nombre=Count('id'))
    # Group by client and date_reservation
    Reservations_par_Client = Reservations.objects.values(
        'terrain__client__numero_telephone', 'date_reservation'
    ).annotate(nombre=Count('id'))
    Reservations_par_Client_list = list(Reservations_par_Client)

    # Convert date_reservation to string
    for reservation in Reservations_par_Client_list:
        reservation['date_reservation'] = reservation['date_reservation'].strftime('%Y-%m-%d')
        
    print("Reservations_par_Client_list:", Reservations_par_Client_list)  

    Reservations_par_Client_json = json.dumps(Reservations_par_Client_list)

    terrains_par_wilaya = list(Terrains.objects.values('wilaye').annotate(nombre=Count('id')))

    # Convert to JSON
    terrains_par_wilaya_json = json.dumps(terrains_par_wilaya)

    return render(request, 'pages/page_acceuil.html', {
        'nombre_clients': nombre_clients,
        'nombre_jouers': nombre_jouers,
        'nombre_de_reservation_par_client':nombre_de_reservation_par_client,
        'nombre_terrains': nombre_terrains,
        'terrains_par_wilaya_json': terrains_par_wilaya_json,
        'Reservations_par_Client_json': Reservations_par_Client_json
    })
@login_required_custom
def ajouter_terrain(request):
    return render(request, 'pages/ajouter_terrain.html')

@login_required_custom
def gestion_terrain(request):
    clients = Client.objects.all()
    wilayes = Wilaye.objects.all()
    moughataa = Moughataa.objects.all()
    terrains = Terrains.objects.all()
    context = {
        'clients': clients,
        'wilayes': wilayes,
        'moughataa': moughataa,
        'terrains': terrains,
    }

    if request.method == 'POST':
        nom_fr = request.POST.get('nom_fr')
        nom_ar = request.POST.get('nom_ar')
        lieu_ar = request.POST.get('lieu_ar')
        lieu_fr = request.POST.get('lieu_fr')

        longitude = request.POST.get('longitude')
        latitude = request.POST.get('latitude')
        nombre_joueur = request.POST.get('nombre_joueur')
        prix_par_heure = request.POST.get('prix_par_heure')
        photo1 = request.FILES.get('photo1')
        photo2 = request.FILES.get('photo2')
        photo3 = request.FILES.get('photo3')
        client_telephone = request.POST.get('client')
        heure_ouverture = request.POST.get('heure_ouverture')
        heure_fermeture = request.POST.get('heure_fermeture')
        wilaye_id = request.POST.get('Wilaye')
        moughataa_id = request.POST.get('Moughataa')
        ballon_disponible = request.POST.get('ballon_disponible') == 'True'
        maillot_disponible = request.POST.get('maillot_disponible') == 'True'
        eclairage_disponible = request.POST.get('eclairage_disponible') == 'True'
        eau = request.POST.get('eau') == 'True'
        gazon_artificiel = request.POST.get('gazon_artificiel') == 'True'
        parking = request.POST.get('parking') == 'True'
        siffler = request.POST.get('siffler') == 'True'

        # Validation des coordonnées
        try:
            longitude = float(longitude)
            latitude = float(latitude)
        except ValueError:
            messages.error(request, "Les coordonnées doivent être des nombres valides.")
            return redirect('gestion_terrain')

        # Validation du nombre de joueurs et du prix par heure
        try:
            nombre_joueur = int(nombre_joueur)
            prix_par_heure = int(prix_par_heure)
        except ValueError:
            messages.error(request, "Le nombre de joueurs et le prix par heure doivent être des nombres valides.")
            return redirect('gestion_terrain')

        try:
            client = Client.objects.get(numero_telephone=client_telephone)
        except Client.DoesNotExist:
            messages.error(request, "Client avec ce numéro de téléphone n'existe pas.")
            return redirect('gestion_terrain')

        # Vérification si le client a déjà enregistré un terrain
        if Terrains.objects.filter(client=client).exists():
            messages.error(request, "Ce client a déjà enregistré un terrain.")
            return redirect('gestion_terrain')

        try:
            nouveau_terrain = Terrains.objects.create(
                nom_fr=nom_fr,
                nom_ar=nom_ar,
                lieu_fr=lieu_fr,
                lieu_ar=lieu_ar,
                longitude=longitude,
                latitude=latitude,
                nombre_joueur=nombre_joueur,
                prix_par_heure=prix_par_heure,
                moughataa_id=moughataa_id,
                wilaye_id=wilaye_id,
                client=client,
                photo1=photo1,
                photo2=photo2,
                photo3=photo3,
                ballon_disponible=ballon_disponible,
                maillot_disponible=maillot_disponible,
                eclairage_disponible=eclairage_disponible,
                eau=eau,
                gazon_artificiel=gazon_artificiel,
                parking=parking,
                siffler=siffler,
                heure_ouverture=heure_ouverture,
                heure_fermeture=heure_fermeture,
            )
            messages.success(request, "Terrain ajouté avec succès.")
            return redirect('gestion_terrain')
        except IntegrityError:
            messages.error(request, "Erreur d'intégrité : le terrain ne peut pas être ajouté.")
            return redirect('gestion_terrain')

    return render(request, 'pages/gestion_terrain.html', context)

def headerGestion_terrain(request):
    return render(request, 'pages/headerGestion_terrain.html')

@login_required_custom
def listes_joueurs(request):
    joueurs = Joueurs.objects.all()
    return render(request, 'pages/listes_joueurs.html',{'joueurs': joueurs})

@login_required_custom
def gerer_joueur(request, joueur_id):
    joueur = get_object_or_404(Joueurs, id=joueur_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "supprimer":
            joueur.delete()
            messages.success(request, "Le joueur a été supprimé avec succès.")
            return JsonResponse({"status": "success"})  # Suppression dynamique

        elif action == "bloquer":
            joueur.is_blocked = True
            joueur.save()
            messages.success(request, "Le joueur a été bloqué.")

        elif action == "debloquer":
            joueur.is_blocked = False
            joueur.save()
            messages.success(request, "Le joueur a été débloqué.")

    return redirect('listes_joueurs')

@login_required_custom
def academie(request):
    wilayes = Wilaye.objects.all()
    moughataa = Moughataa.objects.all()
    academies=Academie.objects.all()

    if request.method == 'POST':
        nom_fr = request.POST['nom_fr']
        nom_ar = request.POST['nom_ar']
        lieu_fr = request.POST['lieu_fr']
        lieu_ar = request.POST['lieu_ar']
        longitude = request.POST['longitude']
        latitude = request.POST['latitude']
        wilaye_id = request.POST['Wilaye']  # Utilisez le bon ID
        moughataa_id = request.POST['Moughataa']  # Utilisez le bon ID
        age_group = request.POST['age_group']

        # Gérer l'upload de la photo
        photo = None
        if request.FILES.get('photo'):
            photo = request.FILES['photo']

        # Créer une nouvelle académie
        academie = Academie(
            name_fr=nom_fr,
            name_ar=nom_ar,
            location_fr=lieu_fr,
            location_ar=lieu_ar,
            longitude=float(longitude),  # Conversion explicite
            latitude=float(latitude),  # Conversion explicite
            wilaye_id=wilaye_id,  # Assurez-vous que vous utilisez l'ID ici
            moughataa_id=moughataa_id,  # Assurez-vous que vous utilisez l'ID ici
            age_group=age_group,
            photo=photo
        )
        academie.save()

        # Rediriger vers une autre page ou afficher un message de succès
        messages.success(request, "Académie ajoutée avec succès.")
        return redirect('academie')  # Remplacez par le bon nom de route

    # Contexte à passer à la page
    context = {
        'wilayes': wilayes,
        'moughataa': moughataa,
        'academies':academies# Assurez-vous que c'est moughataas
    }
    return render(request, 'pages/academie.html',context)

@login_required_custom
def ajouter_academie(request):
    return render(request, 'pages/ajouter_academie.html')
@login_required_custom
def modifier_academie(request, academie_id):
    academie_instance = get_object_or_404(Academie, id=academie_id)

    if request.method == 'POST':
        academie_instance.name_fr = request.POST.get('name_fr')
        academie_instance.name_ar = request.POST.get('name_ar')

        academie_instance.longitude = request.POST.get('longitude')
        academie_instance.latitude = request.POST.get('latitude')
        academie_instance.wilaye_id = request.POST.get('Wilaye')
        academie_instance.moughataa_id = request.POST.get('Moughataa')
        academie_instance.age_group = request.POST.get('age_group')
        academie_instance.location_fr = request.POST.get('location_fr')
        academie_instance.location_ar = request.POST.get('location_ar')

        if 'photo' in request.FILES:
            academie_instance.photo = request.FILES['photo']

        try:
            academie_instance.save()
        except Exception as e:
            messages.error(request, str(e))
            return redirect('academie')

        return redirect('academie')

    return render(request, 'pages/modifier_academie.html', {
        'academie': academie_instance,
        'wilayes': Wilaye.objects.all(),
        'moughataa': Moughataa.objects.all(),
    })


@login_required_custom
def supprimer_academie(request, academie_id):
    academie_instance = get_object_or_404(Academie, id=academie_id)
    if request.method == 'POST':
        academie_instance.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required_custom
def ajouter_credits(request, client_id):
    client = get_object_or_404(Client, id=client_id)  # Récupérer le client via son ID

    if request.method == 'POST':
        montant = int(request.POST.get('montant', 0))  # Récupérer le montant envoyé via le formulaire
        if montant > 0:
            client.credie += montant  # Ajouter le montant aux crédits existants
            client.save()  # Sauvegarder les modifications dans la base de données
        else:
            # Vous pouvez gérer une erreur ici si le montant est invalide (0 ou négatif)
            pass

        return redirect('gestion_client')  # Rediriger vers la page de détails du client

    return render(request, 'gestion_client.html', {'client': client})

@login_required_custom
def gestion_periode(request):
    if request.method == "POST":
        client_numero = request.POST.get("client")
        heure_debut = request.POST.get("heure_debut")
        heure_fin = request.POST.get("heure_fin")
        prix = request.POST.get("prix")

        try:
            # Vérifier si le client existe
            client = Client.objects.get(numero_telephone=client_numero)

            # Vérifier si un terrain est déjà associé à ce client
            terrain_instance = Terrains.objects.filter(client=client).first()
            if not terrain_instance:
                messages.error(request, "Aucun terrain associé à ce client.")
                return redirect('gestion_terrain')

            # Créer la période
            Periode.objects.create(
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                prix=prix,
                terrain=terrain_instance
            )

            messages.success(request, "Période ajoutée avec succès.")
            return redirect('gestion_periode')
        except Client.DoesNotExist:
            messages.error(request, "Client avec ce numéro de téléphone n'existe pas.")
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")

        return redirect('gestion_terrain')
    periodes = Periode.objects.all()
    return render(request, 'pages/gestion_periode.html',{'periodes': periodes})





@login_required_custom
def supprimer_periode(request, id):
    periode = get_object_or_404(Periode, id=id)

    if request.method == 'POST':
        try:
            periode.delete()
            messages.success(request, "La période a été supprimée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression : {str(e)}")

        return redirect('gestion_periode')  # Rediriger vers la vue de gestion des périodes

    # Si la méthode n'est pas POST, vous pouvez rediriger ou afficher une page de confirmation
    return redirect('gestion_periode')

@login_required_custom
def modifier_periode(request, id):
    periode = get_object_or_404(Periode, id=id)
    if request.method == "POST":
        heure_debut = request.POST.get("heure_debut_modifier")
        heure_fin = request.POST.get("heure_fin_modifier")
        prix = request.POST.get("prix_modifier")
        try:
            updated_data = {}
            if heure_debut:
                heure_debut = datetime.strptime(heure_debut, "%H:%M").strftime("%H:%M")
                updated_data['heure_debut'] = heure_debut
            if heure_fin:
                heure_fin = datetime.strptime(heure_fin, "%H:%M").strftime("%H:%M")
                updated_data['heure_fin'] = heure_fin
            if prix:
                updated_data['prix'] = prix
            Periode.objects.filter(id=id).update(**updated_data)
            messages.success(request, "Période modifiée avec succès.")
            return redirect('gestion_periode')  # Rediriger après succès
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {str(e)}")
            return redirect('gestion_periode')
    else:
        # Si ce n'est pas une requête POST, afficher la page de modification
        return render(request, 'modifier_periode.html', {'periode': periode})



@login_required_custom
def liste_heure_indisponible(request):
    if request.method == "POST":
        client_numero = request.POST.get("client")
        heure_debut = request.POST.get("heure_debut")
        heure_fin = request.POST.get("heure_fin")

        try:
            client = get_object_or_404(Client, numero_telephone=client_numero)
            terrain_instance = Terrains.objects.filter(client=client).first()

            if not terrain_instance:
                messages.error(request, "Aucun terrain associé à ce client.")
                return redirect('gestion_terrain')

            # Conversion en objets `time`
            heure_debut = datetime.strptime(heure_debut, "%H:%M").time()
            heure_fin = datetime.strptime(heure_fin, "%H:%M").time()

            # Création de la période indisponible
            Indisponibles_tous_temps.objects.create(
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                terrain=terrain_instance
            )
            messages.success(request, "heure ajoutée avec succès.")
            return redirect('liste_heure_indisponible')
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")
            return redirect('gestion_terrain')

    heures_indisponibles = Indisponibles_tous_temps.objects.all()
    return render(request, 'pages/liste_heure_indisponible.html', {'heures_indisponibles': heures_indisponibles})

@login_required_custom
def supprimer_heure_indisponible(request, heure_id):
    heure = get_object_or_404(Indisponibles_tous_temps, id=heure_id)
    heure.delete()
    messages.success(request, "L'heure indisponible a été supprimée avec succès.")
    return redirect('liste_heure_indisponible')


@login_required_custom
def modifier_heure_indisponible(request, heure_id):
    heure = get_object_or_404(Indisponibles_tous_temps, id=heure_id)

    if request.method == "POST":
        heure.heure_debut = request.POST.get("heure_debut_modifier")
        heure.heure_fin = request.POST.get("heure_fin_modifier")
        heure.save()
        messages.success(request, "L'heure indisponible a été modifiée avec succès.")
        return redirect('liste_heure_indisponible')

    return redirect('liste_heure_indisponible')


@login_required_custom
def liste_versions(request):
    versions = Version.objects.all()
    return render(request, 'pages/versions.html', {'versions': versions})

@login_required_custom
def page_synchronisation(request):
    return render(request, 'pages/synchronisation.html')

@login_required_custom
def ajouter_version(request):
    if request.method == 'POST':
        versionNumber = request.POST.get('versionNumber')
        version = Version.objects.create(versionNumber=versionNumber)
        return JsonResponse({'success': True, 'id': version.id})
    return JsonResponse({'success': False})

@login_required_custom
def modifier_version(request, id):
    version = get_object_or_404(Version, id=id)
    if request.method == 'POST':
        version.versionNumber = request.POST.get('versionNumber')
        version.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})



@login_required_custom
def supprimer_version(request, id):
    version = get_object_or_404(Version, id=id)
    version.delete()
    return JsonResponse({'success': True})

@login_required_custom
def synchroniser_horaires_occupes(request):
    """
    Synchronise les horaires occupés depuis l'API Spring Boot
    vers la table Indisponibilites
    """
    try:
        # Récupérer les horaires occupés depuis l'API
        data = get_horaires_occupes()
        horaires = data.get('horairesOccupes', [])
        
        if not horaires:
            return JsonResponse({
                'success': False, 
                'error': 'Aucun horaire occupé trouvé',
                'inserted': 0,
                'errors': 0
            })
        
        inserted_count = 0
        error_count = 0
        errors_details = []
        
        for horaire in horaires:
            try:
                # Récupérer les données
                date_str = horaire.get('date')
                heure_debut_str = horaire.get('heureDebut')
                heure_fin_str = horaire.get('heureFin')
                telephone_proprietaire = str(horaire.get('telephoneProprietaire'))
                
                # Convertir les dates et heures
                from datetime import datetime
                date_indisponibilite = datetime.strptime(date_str, '%Y-%m-%d').date()
                heure_debut = datetime.strptime(heure_debut_str, '%H:%M:%S').time()
                heure_fin = datetime.strptime(heure_fin_str, '%H:%M:%S').time()
                
                # Trouver le client avec ce numéro de téléphone
                try:
                    client = Client.objects.get(numero_telephone=telephone_proprietaire)
                except Client.DoesNotExist:
                    error_count += 1
                    errors_details.append(f"Client avec téléphone {telephone_proprietaire} non trouvé")
                    continue
                
                # Trouver le terrain associé à ce client
                try:
                    terrain = Terrains.objects.get(client=client)
                except Terrains.DoesNotExist:
                    error_count += 1
                    errors_details.append(f"Aucun terrain trouvé pour le client {telephone_proprietaire}")
                    continue
                except Terrains.MultipleObjectsReturned:
                    # Si plusieurs terrains, prendre le premier
                    terrain = Terrains.objects.filter(client=client).first()
                
                # Vérifier si l'indisponibilité existe déjà
                exists = Indisponibilites.objects.filter(
                    terrain=terrain,
                    date_indisponibilite=date_indisponibilite,
                    heure_debut=heure_debut,
                    heure_fin=heure_fin
                ).exists()
                
                if not exists:
                    # Créer l'indisponibilité
                    Indisponibilites.objects.create(
                        terrain=terrain,
                        date_indisponibilite=date_indisponibilite,
                        heure_debut=heure_debut,
                        heure_fin=heure_fin
                    )
                    inserted_count += 1
                
            except Exception as e:
                error_count += 1
                errors_details.append(f"Erreur pour {horaire.get('date', 'date inconnue')}: {str(e)}")
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'{inserted_count} horaires synchronisés avec succès',
            'inserted': inserted_count,
            'errors': error_count,
            'errors_details': errors_details[:10]  # Limiter à 10 erreurs
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la synchronisation : {str(e)}'
        }, status=500)

























