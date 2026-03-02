# shell.py - Test de connexion MySQL pour Django
import os
import django
import sys

# 1. Configurer Django
print("⚙️ Configuration de Django...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'E_recrutement.settings')
try:
    django.setup()
    print("✅ Django configuré avec succès")
except Exception as e:
    print(f"❌ Erreur configuration Django: {e}")
    sys.exit(1)

# 2. Tester la connexion MySQL
print("\n🔗 Test de connexion MySQL...")
try:
    from django.db import connection
    
    # Ouvrir la connexion
    cursor = connection.cursor()
    print("✅ Curseur MySQL créé")
    
    # Tester la version
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"✅ Version MySQL: {version[0]}")
    
    # Lister les bases de données
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    print(f"\n📊 Bases de données disponibles ({len(databases)}):")
    for db in databases:
        print(f"  - {db[0]}")
    
    # Vérifier notre base
    cursor.execute("USE erecrutement_db")
    print("\n🗃️ Base 'erecrutement_db' sélectionnée")
    
    # Lister les tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    if tables:
        print(f"✅ Tables dans 'erecrutement_db' ({len(tables)}):")
        for table in tables:
            print(f"  • {table[0]}")
    else:
        print("⚠️  Aucune table trouvée. Avez-vous fait les migrations?")
        print("   Exécutez: python manage.py migrate")
    
    # Fermer la connexion
    cursor.close()
    print("\n✅ Test terminé avec succès!")
    
except Exception as e:
    print(f"❌ Erreur MySQL: {e}")
    print("\n🔧 Vérifiez:")
    print("   1. MySQL est-il démarré?")
    print("   2. Les paramètres dans settings.py sont-ils corrects?")
    print("   3. La base 'erecrutement_db' existe-t-elle?")