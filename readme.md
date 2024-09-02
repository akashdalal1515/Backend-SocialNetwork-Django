Social Networking Application API

-- Overview

This project is a social networking application built using Django and Django REST Framework. It includes functionality for user management, friend requests, and user search. The application uses SQLite as its database and JWT for authentication.

Features

- User Signup and Login**: Users can sign up and log in using email and password.
- Search Users**: Search users by email or name.
- Friend Requests**: Send, accept, and reject friend requests.
- List Friends**: View a list of friends.
- Pending Friend Requests**: View pending friend requests.

steps to Run - 
1. Clone the Repository
2. Create a Virtual Environment -
python -m venv venv
source venv\Scripts\activate  # On linux use `venv/bin/activate`
3. Install Dependencies
pip install -r requirements.txt
4. Apply Migrations 
python manage.py migrate
5. Run the Development Server
python manage.py runserver
6. To Build docker image file
docker build -t social_network .
7. To build docker compose images
docker-compose build
8. To run docker compose 
docker-compose up -d
9. To stop docker compose 
docker-compose down -d


