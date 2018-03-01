import json
import time
from flask import Blueprint, request, session
from flask_jwt_extended import jwt_required
from flask_socketio import emit, send, join_room, leave_room
from .. import x_socketio
import eventlet

from lib.managers.SchemaManager import SchemaManager
from lib.utils.RequestHelpers import extractRepeatingParameterBlocksFromRequest, extractRepeatingParameterFromRequest, responseHandler
from lib.crossDomain import crossdomain
from lib.utils.RequestHelpers import makeResponse
from lib.exceptions.SettingsValidationError import SettingsValidationError

@x_socketio.on('connect')
def test_connect():
    print "Connected"

@x_socketio.on('disconnect')
def test_disconnect():
    print "Disconnected"

@x_socketio.on("send_user_id")
def new_user(data):
    emit('entered_response', {'data': 'new room!'})

@x_socketio.on("start_upload_process")
def start_upload():
    print "Started Upload Process"

def pass_message(target, data):
    u_thread = eventlet.spawn(emit_message, target, data)
    u_res = u_thread.wait()
    return True

def emit_message(target, data):
    x_socketio.emit(target, data)
    return True
