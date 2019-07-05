from flask import Blueprint, request, jsonify

from warden.model import obtener_session
from warden.model.WardenModel import WardenModel


from . import permisos

bp = Blueprint('warden', __name__, url_prefix='/warden/api/v2.0')

SYSTEM = 'warden-api'
PERMISSION_CREATE = 'urn:warden:permission:create'
PERMISSION_READ = 'urn:warden:permission:read'
PERMISSION_DELETE = 'urn:warden:permission:delete'
USER_PERMISSION_CREATE = 'urn:warden:user_permission:create'
USER_PERMISSION_READ = 'urn:warden:user_permission:read'
USER_PERMISSION_DELETE = 'urn:warden:user_permission:delete'

@bp.route('/autoregistrarpermisos', methods=['GET'])
def autoregistrar_permisos():
    try:
        warden_permissions = {
            'system' : SYSTEM,
            'permissions': [
                PERMISSION_CREATE,
                PERMISSION_READ,
                PERMISSION_DELETE,
                USER_PERMISSION_CREATE,
                USER_PERMISSION_READ,
                USER_PERMISSION_DELETE
            ]
        }
        with obtener_session() as session:
            datos = WardenModel.register_permissions(session,warden_permissions)
            session.commit()
            return jsonify({'status':200, 'data':datos})
    except Exception as e:
        return jsonify({'status':500, 'response': str(e)})

@bp.before_app_request
def antes_de_cada_requerimiento():
    pass

@bp.route('/registrar_permisos', methods=['POST'])
def registrar_permisos():
    """
    Registra en la db los permisos enviados desde un sistema
    """
    data = request.json
    assert 'system' in data
    assert 'permissions' in data
    with obtener_session() as session:
        r = WardenModel.register_permissions(session, data)
        session.commit()
        return (str(r), 200)

@bp.route('/permisos', methods=['GET'])
def obtener_permisos_disponibles():
    """
    Retorna una lista de todos los permisos disponibles registrados
    """
    with obtener_session() as session:
        _p = WardenModel.permissions(session)
        s = [{'permission':p.permission, 'system':p.system} for p in _p]
        return jsonify(s)

@bp.route('/usuarios/<uid>', methods=['GET'])
def obtener_permisos_usuario(uid=None):
    """
    Retorna la lista de permisos disponibles para ese usuario
    """
    assert uid is not None        
    with obtener_session() as session:
        permisos = WardenModel.permissions_by_uid(session,uid)
        perm = [{'permission':p.permission,'system':p.system} for p in permisos]
        return jsonify(perm)

@bp.route('/usuarios/<uid>', methods=['PUT'])
def actualizar_permisos_usuario(uid=None):
    """
    Actualiza los permisos recibidos por parametro para el uid
    """
    assert uid is not None
    data = request.json
    with obtener_session() as session:
        for p in data:
            if p['habilitado']:
                WardenModel.register_user_permissions(session,uid,[p['permiso']])
            else:
                WardenModel.delete_user_permissions(session,uid,[p['permiso']])
        session.commit()
        return ('ok',200)

@bp.route('/has_permissions', methods=['POST'])
def has_permissions(token=None):
    """
    Chequea que la el usuario identificado por el token tenga como mínimo los permisos pasados en el requerimineto:
    el formato de la consutla es:
    {
        'permissions': [
            perm1,
            perm2,
            perm3
        ]
    }
    
    formato de respuesta es:
    {
        status: number,
        description: string,
        result: boolean,
        granted: string[]
    }
    """
    assert token is not None
    
    uid = token['sub']
    perms = request.json
    if 'permissions' in perms:
        granted, permissions_granted = _chequear_permisos(uid, perms['permissions'])
        if granted:
            return {'status':200, 'description':'ok', 'result':granted, 'granted':list(permissions_granted)}
        else:
            return {'status':403, 'description':'forbidden', 'result':granted, 'granted':[]}
    return {'status':500, 'description':'Invalid', 'result':False, 'granted':[]}


def _chequear_permisos(uid, permisos=[]):
    from . import permisos
    granted, permissions_granted = permisos.chequear_permisos(uid, perms['permissions'], permissions)
    return (granted, permissions_granted)