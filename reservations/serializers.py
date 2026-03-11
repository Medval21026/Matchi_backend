from rest_framework import serializers


from .models import Client, DemandeReservation, Joueurs, Periode, Terrains, Reservations,Moughataa,Indisponibilites,Wilaye,Academie

from django.contrib.auth.hashers import make_password


class AbsoluteImageField(serializers.ImageField):
    """ImageField qui retourne toujours une URL absolue (compatible R2 et local)."""
    def to_representation(self, value):
        if not value:
            return None
        url = value.url
        if url.startswith('http'):
            return url
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(url)
        return url


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
        extra_kwargs = {
            'modepass_chiffre': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['modepass_chiffre'] = make_password(validated_data['modepass_chiffre'])
        return super().create(validated_data)


class TerrainSerializer(serializers.ModelSerializer):
    photo1 = AbsoluteImageField(required=False)
    photo2 = AbsoluteImageField(required=False)
    photo3 = AbsoluteImageField(required=False)

    class Meta:
        model = Terrains
        fields = '__all__'
class IndisponibiliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indisponibilites
        fields = '__all__'
class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservations
        fields = ['id', 'terrain', 'joueur', 'date_reservation', 'heure_debut', 'heure_fin']



class WilayeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wilaye
        fields = ['code_wilaye', 'nom_wilaye_Ar', 'nom_wilaye_fr']

class TerrainsSerializer(serializers.ModelSerializer):
    wilaye = WilayeSerializer()
    photo1 = AbsoluteImageField(required=False)
    photo2 = AbsoluteImageField(required=False)
    photo3 = AbsoluteImageField(required=False)

    class Meta:
        model = Terrains
        fields = '__all__'
class MoughataaSerializer(serializers.ModelSerializer):
    wilaye = WilayeSerializer()

    class Meta:
        model = Moughataa
        fields = '__all__'
class AcademieSerializer(serializers.ModelSerializer):
    photo = AbsoluteImageField(required=False)

    class Meta:
        model = Academie
        fields = '__all__'

class JoueurSerializer(serializers.ModelSerializer):
    wilaye = WilayeSerializer()  # Inclure les détails de la wilaya
    moughataa = MoughataaSerializer()  # Inclure les détails de la moughataa
    photo_de_profile = AbsoluteImageField(required=False)

    class Meta:
        model = Joueurs
        fields = '__all__'

    def create(self, validated_data):
        # Hash the password before saving the user
        validated_data['password'] = make_password(validated_data['password'])
        joueur = Joueurs.objects.create(**validated_data)
        return joueur

class DemandeReservationSerializer(serializers.ModelSerializer):
    joueur = JoueurSerializer()
    class Meta:
      model = DemandeReservation
      fields = ['id', 'joueur','date_reservation', 'heure_debut', 'heure_fin', 'status']

class ReservationSerializer_client(serializers.ModelSerializer):
    joueur = JoueurSerializer()  # Inclure le joueur lié à la réservation

    class Meta:
        model = Reservations
        fields = ['date_reservation', 'heure_debut', 'heure_fin', 'joueur']

class PeriodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Periode
        fields = ['heure_debut', 'heure_fin', 'prix', 'terrain',]