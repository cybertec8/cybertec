from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
ctf_admin_bp = Blueprint('ctf_admin', __name__, url_prefix='/ctf-admin')
participant_bp = Blueprint('participant', __name__, url_prefix='')
ctf_battle_bp = Blueprint('ctf_battle', __name__, url_prefix='/admin/ctf-battle')
battle_bp = Blueprint('battle', __name__, url_prefix='/ctf-battle')

from . import admin, ctf_admin, participant, ctf_battle
