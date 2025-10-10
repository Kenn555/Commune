from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from civil.models import ActeNaissance  # Importez vos modèles ici
from finances.models import Transaction
from events.models import Evenement
from social.models import DossierSocial
from mines.models import Permis

User = get_user_model()

def create_groups_and_permissions():
    # Création des groupes
    admin_group, _ = Group.objects.get_or_create(name='Administrateurs')
    civil_group, _ = Group.objects.get_or_create(name='État Civil')
    finance_group, _ = Group.objects.get_or_create(name='Finances')
    social_group, _ = Group.objects.get_or_create(name='Affaires Sociales')
    mines_group, _ = Group.objects.get_or_create(name='Mines')
    
    # Permissions pour l'état civil
    civil_content_type = ContentType.objects.get_for_model(ActeNaissance)
    view_acte = Permission.objects.get_or_create(
        codename='view_actenaissance',
        name='Peut consulter les actes de naissance',
        content_type=civil_content_type,
    )[0]
    add_acte = Permission.objects.get_or_create(
        codename='add_actenaissance',
        name='Peut créer des actes de naissance',
        content_type=civil_content_type,
    )[0]
    
    # Permissions pour les finances
    finance_content_type = ContentType.objects.get_for_model(Transaction)
    view_transaction = Permission.objects.get_or_create(
        codename='view_transaction',
        name='Peut consulter les transactions',
        content_type=finance_content_type,
    )[0]
    add_transaction = Permission.objects.get_or_create(
        codename='add_transaction',
        name='Peut créer des transactions',
        content_type=finance_content_type,
    )[0]

    # Attribution des permissions aux groupes
    civil_group.permissions.add(view_acte, add_acte)
    finance_group.permissions.add(view_transaction, add_transaction)
    
    # Les administrateurs ont toutes les permissions
    admin_group.permissions.add(
        view_acte, add_acte,
        view_transaction, add_transaction
    )

def is_in_group(user, group_name):
    """Vérifie si un utilisateur appartient à un groupe donné"""
    return user.groups.filter(name=group_name).exists()

def has_civil_permission(user):
    """Vérifie si un utilisateur a les permissions d'état civil"""
    return user.has_perm('civil.view_actenaissance') or is_in_group(user, 'Administrateurs')

def has_finance_permission(user):
    """Vérifie si un utilisateur a les permissions de finances"""
    return user.has_perm('finances.view_transaction') or is_in_group(user, 'Administrateurs')
