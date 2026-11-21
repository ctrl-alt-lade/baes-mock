import json
import random
import firebase_admin
from firebase_admin import credentials, firestore

with open('serviceAccountKey.json', 'r') as f:
    cred_data = json.load(f)

if 'private_key' in cred_data:
    cred_data['private_key'] = cred_data['private_key'].replace('\\n', '\n')

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_data)
    firebase_admin.initialize_app(cred)

db = firestore.client()

first_names = [
    'Alex', 'Jordan', 'Casey', 'Morgan', 'Riley', 'Jamie', 'Cameron', 'Quinn',
    'Avery', 'Parker', 'Drew', 'Jesse', 'Kendall', 'Skyler', 'Rowan', 'Peyton',
    'Dakota', 'Reese', 'Sloan', 'Blake', 'Taylor', 'Sam', 'Chris', 'Dana', 'Ellis'
]
last_names = [
    'Taylor', 'Lee', 'Smith', 'Davis', 'White', 'Clark', 'Lewis', 'Wright',
    'Walker', 'Hall', 'Allen', 'Young', 'King', 'Scott', 'Green', 'Baker',
    'Adams', 'Nelson', 'Carter', 'Mitchell', 'Perez', 'Roberts', 'Turner', 'Evans'
]

batch = db.batch()

# Seeds TEST001 to TEST100 without affecting real student matric numbers
for i in range(1, 201):
    matric = f'TEST{i:03d}'
    doc_ref = db.collection('students').document(matric)
    batch.set(doc_ref, {
        'matric_no': matric,
        'name': f"{random.choice(first_names)} {random.choice(last_names)}",
        'department': 'Mechatronics Engineering',
        'has_taken': False
    })

batch.commit()
print('✅ Seeded 100 test accounts (TEST001 to TEST100). Real student records untouched.')