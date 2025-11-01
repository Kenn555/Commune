from django.urls import path

from civil import views


app_name = "civil"
urlpatterns = [
    path("", views.index, name='index'),
    # Naissance
    path("birth/", views.birth_list, name='birth'),
    path("birth/register/", views.birth_register, name='birth-register'),
    path("birth/save/", views.birth_save, name='birth-save'),
    path("birth/modify/<int:birth_id>/", views.birth_modify, name='birth-modify'),
    path("birth/delete/<int:birth_id>/", views.birth_delete, name='birth-delete'),    
    # URLs pour les certificats
    path('certificate/<str:type_cert>/<int:pk>/preview/<int:many>', views.certificate_preview, name='certificate-preview'),
    path('certificate/create/<str:menu>/<int:pk>/<int:many>/', views.certificate_creation, name='certificate-creation'),
    path('certificate/<int:pk>/validate/', views.certificate_validate, name='certificate-validate'),
    path('certificate/<int:pk>/delete/', views.CertificateDeleteView.as_view(), name='certificate-delete'),
    # Détails de Certificat
    path("detail/<int:birth_id>/", views.birth_detail, name='birth-detail'),
    # Décès
    path("death/", views.death, name='death'),
    path("death/register/", views.death_register, name='death-register'),
    path("death/save/", views.death_save, name='death-save'),
    # Mariage
    path("marriage/", views.marriage, name='marriage'),
    path("marriage/register/", views.marriage_register, name='marriage-register'),
    # Gestion d'enregistrement
    path("regmanager/", views.register_manager, name='register-manager'),
    # URLs pour l'autocomplete
    path('autocomplete/person/', views.PersonAutocomplete.as_view(), name='person-autocomplete'),
    path('autocomplete/father/', views.FatherAutocomplete.as_view(), name='father-autocomplete'),
    path('autocomplete/mother/', views.MotherAutocomplete.as_view(), name='mother-autocomplete'),
    # URL pour récupérer les détails d'une personne
    path('api/person/<int:person_id>/', views.get_person_details, name='person-details'),
    path('api/search_person/<str:type>/<str:q_name>/', views.search_persons, name='search-person'),
]
