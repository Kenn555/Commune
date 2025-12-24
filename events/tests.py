from django.test import TestCase

from events.models import Category

# Create your tests here.
# Category.objects.create(
#     name="Autre",
#     slug="autre",
#     color="#000000",
#     text_color="#ffffff",
#     description="Autre",
# )
Category.objects.create(
    name="Festivale",
    slug="festivale",
    color="#F54040",
    text_color="#ffffff",
    description="Festivale",
)
Category.objects.create(
    name="ShowKeys",
    slug="showkeys",
    color="#65A3FF",
    text_color="#000000",
    description="Artiste + Playback",
)
Category.objects.create(
    name="Artiste Simple",
    slug="simplesingle",
    color="#0059FF",
    text_color="#ffffff",
    description="Artiste Simple + Groupe",
)
Category.objects.create(
    name="Artiste Vedette",
    slug="popularsingle",
    color="#0047A3",
    text_color="#ffffff",
    description="Artiste Vedette + Groupe",
)
Category.objects.create(
    name="Morengy",
    slug="morengy",
    color="#0047A3",
    text_color="#ffffff",
    description="Morengy",
)
Category.objects.create(
    name="Kermesse",
    slug="kermesse",
    color="#FF7300",
    text_color="#000000",
    description="Kermesse - Fête populaire - Jeux",
)
Category.objects.create(
    name="Culturel",
    slug="cultural",
    color="#008011",
    text_color="#FFFFFF",
    description="Culturel (Fomba)",
)
Category.objects.create(
    name="Inauguration",
    slug="inauguration",
    color="#D0FF00",
    text_color="#000000",
    description="Inauguration (Fitokanana)",
)
Category.objects.create(
    name="Abattage",
    slug="abattage",
    color="#D505FF",
    text_color="#FFFFFF",
    description="Abattage de zébu",
)

print(list(Category.objects.all().values_list("name")))