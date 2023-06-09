from rest_framework import serializers
from rest_framework.serializers import ValidationError
from drf_writable_nested.serializers import WritableNestedModelSerializer

from .models import Pereval, Coords, Image, User, Level


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class CoordsSerializer(serializers.ModelSerializer):
    height = serializers.IntegerField(default=0)

    class Meta:
        model = Coords
        fields = '__all__'


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['title', 'data']


class PerevalSerializer(WritableNestedModelSerializer):
    user = UserSerializer(required=False)
    coords = CoordsSerializer(required=False)
    level = LevelSerializer(required=False)
    images = ImageSerializer(many=True, required=False)

    class Meta:
        model = Pereval
        fields = ['pk', 'status', 'beauty_title', 'title', 'other_titles', 'connect',
                  'add_time', 'user', 'coords', 'level', 'images']
        read_only_fields = ['pk', 'status', 'add_time']

    def get_fields(self):
        """ Fields to display in request body """
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.method == 'PATCH':
            fields.pop('status')
            fields.pop('add_time')

        return fields

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        email = user_data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create(**user_data)

        try:
            coords_data = validated_data.pop('coords')
            coords = Coords.objects.create(**coords_data)

            level_data = validated_data.pop('level')
            level = Level.objects.create(**level_data)

            images_data = validated_data.pop('images')
            pereval = Pereval.objects.create(**validated_data, user=user, coords=coords, level=level)

            for image_data in images_data:
                Image.objects.create(pereval=pereval, **image_data)

        except KeyError:
            raise ValidationError("Data is missing")

        return pereval

    def validate(self, attrs):
        user_data = attrs.get('user')
        if not user_data:
            raise ValidationError("User data is missing.")

        if self.instance:
            user = self.instance.user
        else:
            try:
                user = User.objects.get(email=user_data.get('email'))
            except User.DoesNotExist:
                user = None

        if user is not None:
            if user.fam != user_data.get('fam') or \
                    user.name != user_data.get('name') or user.otc != user_data.get('otc') or \
                    user.phone != user_data.get('phone'):
                raise ValidationError("User information cannot be changed.")

        super().validate(attrs)

        return attrs
