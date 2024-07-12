# ToDO - Page that helps you remember your tasks!

<br>

## What is the purpose of this project?
The purpose of this project is to demonstrate my skills in using [Flask](https://flask.palletsprojects.com/en/3.0.x/) and related libraries. I aimed to create a webpage that functions as a to-do list. The focus is on backend mechanics rather than UI design, so the website's appearance may not be impressive

## Features
- User registration and login with email confirmation.
- Secure password handling using hashed passwords.
- Task management with options to add, edit, delete, and mark tasks as done.
- User-specific settings for customizing task colors.
- Integration with CKEditor for rich text input capabilities.

## Project structure

```bash
To_do_flask_page/
│
├── templates/ # HTML templates
├── static/ # Static files (CSS, JS)
├── main.py # Main application script
├── instance/ # Database location (not included in the repository)
├── forms.py # WTForms definitions
├── requirements.txt # Python dependencies
├── README.md # This readme file
├── .env # Environment variables (not included in the repository)
└── .gitignore # Git ignore file
```

## How does it work?
The website allows users to create accounts stored in a database, ensuring each user has their own set of tasks. Tasks are stored in a separate table in database linked to the user's account. Additionally, there is a settings table in database that stores color preferences for tasks.

## How to run it on your copmuter?
It's simple. First, clone the repository with:

```bash
git clone https://github.com/Vronst/To_do_flask_page.git
```
then install requirements:
```bash
pip install -r requirements.txt
```
next, create a .env file with the following variables:
```py
EMAIL=your_email@gmail.com
PASSWORD=your_email_password
SALT=your_salt_string
FLASK_KEY=your_flask_secret_key
DB_URI=your_database_uri
```
Now, simply type in the terminal (in the project directory):
```bash
python main.py
```

and open your web browser and navigate to http://localhost:5000 to access the application.

---

 Feel free to customize this project further and enhance its functionality. Happy coding!