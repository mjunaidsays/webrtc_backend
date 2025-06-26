from fastapi import APIRouter, HTTPException, Request
import jwt
import datetime
import os
import base64
import json

router = APIRouter()

APP_ID = 'vpaas-magic-cookie-4d98055dcb7a4e7e818e22aa1b84781d'
KID = 'vpaas-magic-cookie-4d98055dcb7a4e7e818e22aa1b84781d/dc43f2'
PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), '../../..', 'Jitsi API Keys', 'Key 6_20_2025, 3_54_22 PM.pk')

@router.post('/')
async def get_jaas_jwt(request: Request):
    data = await request.json()
    room = data.get('room')
    user_name = data.get('user_name', 'guest')
    if not room:
        raise HTTPException(status_code=400, detail='Room is required')
    
    now = datetime.datetime.utcnow()
    exp = now + datetime.timedelta(minutes=30)  # 30 min expiry for security
    payload = {
        'aud': 'jitsi',
        'iss': 'chat',
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp()),
        'nbf': int(now.timestamp()),
        'sub': APP_ID,
        'context': {
            'features': {
                'livestreaming': True,
                'outbound-call': True,
                'sip-outbound-call': False,
                'transcription': True,
                'recording': True,
                'flip': False
            },
            'user': {
                'hidden-from-recorder': False,
                'moderator': True,
                'name': user_name,
                'id': user_name,  # You can use a unique user id here
                'avatar': '',
                'email': ''
            }
        },
        'room': room
    }
    print('JaaS JWT payload:', payload)
    with open(PRIVATE_KEY_PATH, 'r') as f:
        private_key = f.read()
    token = jwt.encode(payload, private_key, algorithm='RS256', headers={'kid': KID})
    print('JaaS JWT token:', token)
    # Print decoded payload for debugging
    def b64url_decode(data):
        rem = len(data) % 4
        if rem > 0:
            data += '=' * (4 - rem)
        return base64.urlsafe_b64decode(data)
    try:
        parts = token.split('.')
        decoded_payload = json.loads(b64url_decode(parts[1]))
        print('Decoded JWT payload:', json.dumps(decoded_payload, indent=2))
    except Exception as e:
        print('Could not decode JWT:', e)
    return {'jwt': token} 