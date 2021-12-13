from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import IngredientsFilter, RecipeFilter
from .models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                     ShoppingList, Tag)
from .permissions import IsAuthorOrAdmin
from .serializers import (AddRecipeSerializer, FavouriteSerializer,
                          IngredientsSerializer, ShoppingListSerializer,
                          ShowRecipeFullSerializer, TagsSerializer)


class RetriveAndListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    pass


class IngredientsViewSet(RetriveAndListViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientsFilter
    pagination_class = None


class TagsViewSet(RetriveAndListViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = ShowRecipeFullSerializer
    permission_classes = [IsAuthorOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ShowRecipeFullSerializer
        return AddRecipeSerializer

    @action(detail=True, permission_classes=[IsAuthorOrAdmin])
    def favorite(self, request, pk):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = FavouriteSerializer(data=data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        recipe = get_object_or_404(Recipe, id=pk)
        try:
            Favorite.objects.get(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Favorite.DoesNotExist:
            return Response(
                'Нет данного рецепта в избранном',
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, permission_classes=[IsAuthorOrAdmin])
    def shopping_cart(self, request, pk):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = ShoppingListSerializer(data=data,
                                            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        try:
            recipe = Recipe.objects.get(id=pk)
            shopping_list = ShoppingList.objects.get(
                user=request.user,
                recipe=recipe,
            )
            shopping_list.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Recipe.DoesNotExist:
            return Response(
                'Нет данного рецепта в списке покупок',
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ShoppingList.DoesNotExist:
            return Response(
                'Нет данного рецепта в списке покупок',
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user_shopping_list = request.user.shopping_list.all()
        to_buy = get_ingredients_list(user_shopping_list)
        return download_file_response(to_buy, 'to_buy.txt')


def get_ingredients_list(recipes_list):
    ingredients_dict = {}
    list_to_buy = []
    for recipe in recipes_list:
        ingredients = RecipeIngredients.objects.filter(recipe=recipe.recipe)
        for ingredient in ingredients:
            name = ingredient.ingredient.name
            amount = ingredient.amount
            measurement_unit = ingredient.ingredient.measurement_unit
            if name in ingredients_dict:
                ingredients_dict[name]['amount'] += amount
            else:
                ingredients_dict[name] = {
                    'meas': measurement_unit,
                    'amount': amount,
                }
    for key, value in ingredients_dict.items():
        list_to_buy.append(
            f'{key} - {value["amount"]} {value["meas"]}.\n',
        )
    return list_to_buy


def download_file_response(list_to_download, filename):
    response = HttpResponse(list_to_download, 'Content-Type: text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
