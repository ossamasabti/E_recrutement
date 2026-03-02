# Plateforme E-Recrutement – MADA JOB IN-CLICK

![Django](https://img.shields.io/badge/Django-4.2-green)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Application web de gestion des offres d’emploi et des candidatures pour les administrations publiques.  
Ce projet a été réalisé dans le cadre d’un master, avec une architecture Django (MVT) et une base de données MySQL.

---

## 📌 Fonctionnalités

- **Trois rôles utilisateurs** : Candidat, Administrateur RH, Super-Admin
- **Gestion des offres** (CRUD) par l’administrateur RH
- **Recherche et filtrage** des offres (titre, type de contrat, localisation)
- **Dépôt de candidature** avec CV et lettre de motivation
- **Suivi des candidatures** avec statuts (en attente, acceptée, refusée)
- **Tableaux de bord** personnalisés pour chaque rôle
- **Statistiques** : nombre d’offres, de candidatures, répartition par statut
- **Authentification sécurisée** (hachage des mots de passe, protection CSRF)
- **Interface responsive** (Bootstrap 5)

---

## 🛠️ Technologies utilisées

- **Backend** : Django 4.2 (Python 3.10)
- **Base de données** : MySQL 8 (avec moteur InnoDB)
- **Frontend** : HTML5, CSS3, Bootstrap 5, JavaScript léger
- **ORM** : Django ORM (abstraction SQL)
- **Outils de développement** : Git, pip, virtualenv, MySQL Workbench

---

## 🚀 Installation locale

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/ossamasabti/E_recrutement.git
   cd E_recrutement
