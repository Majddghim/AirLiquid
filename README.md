# AirLiquid – Fleet Management System

A Flask-based web application for managing AirLiquid's company vehicles, employees, and car registration documents (carte grise). It provides separate interfaces for admins and employees.

---

## Project Structure

```
AirLiquid/
├── app.py
├── blueprints/
│   ├── auth/
│   ├── dashboard/
│   ├── employer/
│   ├── car/
│   └── guest/
├── entities/
├── services/
├── tools/
├── static/
└── templates/
```

---

## `app.py`

Entry point of the Flask application. Sets up the app, registers all blueprints, and defines two root routes (`/` → redirect to login, `/dashboard` → admin dashboard). Also includes a custom JSON provider to serialize Python `datetime` objects.

---

## `blueprints/`

The web/API layer. Each sub-directory is a Flask Blueprint handling a specific domain.

| File | What it has |
|------|-------------|
| `auth/__init__.py` | Initializes and exports `auth_bp` (registered at `/auth`). |
| `auth/views.py` | **`AuthViews`** – admin login (`POST /auth/login`) and logout (`GET /auth/logout`). Reads credentials from JSON body, checks against the database, and sets `session['user_id']`. |
| `dashboard/__init__.py` | Initializes and exports `dashboard_bp` (registered at `/dashboard`). |
| `dashboard/views.py` | **`DashboardViews`** – eight admin-only page routes: dashboard home, employee page, vehicle page, profile, add-employee form, add-vehicle form (with/without pre-filled employee id), employee list, and car list. All routes require an active session. |
| `employer/__init__.py` | Initializes and exports `employe_bp` (registered at `/employe`). |
| `employer/views.py` | **`employe`** – three employee-data API routes: `POST /employe/ajout-employe` (add a new employee), `GET /employe/get-employes` (paginated/searchable list), `GET /employe/get-all-employes` (full list). |
| `car/__init__.py` | Initializes and exports `car_bp` (registered at `/car`). |
| `car/views.py` | **`CarViews`** – five vehicle API routes: `POST /car/ajout-voiture` (add vehicle + file upload for carte grise), `POST /car/extract-data` (mock AI extraction of document data), `GET /car/get-voitures` (paginated/searchable list), `GET /car/get-all-voitures` (full list), `DELETE /car/supprimer-voiture/<id>` (delete vehicle). |
| `guest/__init__.py` | Initializes and exports `guest_bp` (registered at `/guest`). |
| `guest/views.py` | **`GuestViews`** – employee (non-admin) portal: `GET /guest/login` page, `POST /guest/login` (employee authentication), `GET /guest/home` (employee's personal vehicle list), `GET /guest/logout`. |

---

## `entities/`

The domain-model layer. Each file defines a plain Python class representing a database record.

| File | What it has |
|------|-------------|
| `admin.py` | **`Admin`** class – fields: `id`, `username`, `email`, `password_hash`, `status`, `created_at`. Represents an admin account. |
| `employe.py` | **`Employe`** class – fields: `id`, `nom`, `prenom`, `email`, `telephone`, `poste`, `departement`, `status`, `created_at`, `updated_at`. Represents an employee record. |
| `car.py` | **`Car`** class – fields: `id`, `status`, `acquisition_date`, `notes`, `created_at`, `updated_at`. Represents a vehicle in the `cars` table. |
| `carte_grise.py` | **`CarteGrise`** class – fields: `id`, `car_id`, `model`, `year`, `plate_number`, `owner_name`, `chassis_number`, `registration_date`, `expiration_date`, `file_path`, and verification/extraction metadata. Represents a vehicle's registration document. |

---

## `services/`

The business-logic layer. Each file contains a service class that talks to the database via `tools/database_tools.py`.

| File | What it has |
|------|-------------|
| `admin.py` | **`AdminService`** – retrieves admin accounts (`get_admin_by_email`) and employee accounts for the guest portal (`get_employe_by_email`). Used by both `auth` and `guest` blueprints for authentication. |
| `employe.py` | **`EmployeService`** – full CRUD for employees: `add_employe`, `get_employe_by_id`, `get_employe_by_email`, `get_all_employes`, `get_employe_by_name` (paginated search), `delete_employe`, and `get_count_employe_something`. |
| `voiture.py` | **`VoitureService`** – full CRUD for vehicles and their carte grise: `ajouter_voiture` (transactional insert into `cars` + `carte_grises`), `get_voiture_by_id`, `get_all_voitures`, `get_voitures_paginated` (searchable), `supprimer_voiture`, `mettre_a_jour_statut_voiture`, `check_plate_exists`, and `lister_voitures_par_employe` (active assignments). |

---

## `tools/`

| File | What it has |
|------|-------------|
| `database_tools.py` | **`DatabaseTools`** – manages the MySQL connection (`localhost`, db: `airliquide_flotte`). Provides `find_connection()` (returns connection + DictCursor) and `execute_request()` (runs a SQL query and returns `'success'` or an error). |
