import json
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

placeholder_names = [
    'Alex Taylor', 'Jordan Lee', 'Casey Smith', 'Morgan Davis', 'Riley White',
    'Jamie Clark', 'Cameron Lewis', 'Quinn Wright', 'Avery Walker', 'Parker Hall',
    'Drew Allen', 'Jesse Young', 'Kendall King', 'Skyler Scott', 'Rowan Green',
    'Peyton Baker', 'Dakota Adams', 'Reese Nelson', 'Sloan Carter', 'Blake Mitchell'
]

batch = db.batch()
for i, name in enumerate(placeholder_names, start=1):
    matric = f'TEST{i:03d}'
    doc_ref = db.collection('students').document(matric)
    batch.set(doc_ref, {
        'matric_no': matric,
        'name': name,
        'department': 'Engineering Assessment',
        'has_taken': False
    })

batch.commit()
print('✅ Successfully seeded 20 test accounts (TEST001 to TEST020) for the stress test.')