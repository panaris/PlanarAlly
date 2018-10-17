from urllib.parse import unquote

from aiohttp_security import authorized_userid

from api.rooms import load_location
from app import sio, logger, app, state
from models import Location, Room, User


@sio.on('connect', namespace='/planarally')
async def connect(sid, environ):
    user = await authorized_userid(environ['aiohttp.request'])
    if user is None:
        await sio.emit("redirect", "/", room=sid, namespace='/planarally')
    else:
        ref = unquote(environ['HTTP_REFERER']).strip("/").split("/")
        room = Room.select().join(User).where(
            (Room.name == ref[-1]) & (User.name == ref[-2]))[0]
        if room.creator == user:
            location = Location.get(room=room, name=room.dm_location)
        else:
            location = Location.get(room=room, name=room.player_location)

        state.add_sid(sid, user, room, location)

        logger.info(f"User {user.name} connected with identifier {sid}")

        # TODO
        # assets = policy.user_map[username].asset_info

        sio.enter_room(sid, location.get_path(), namespace='/planarally')
        await sio.emit("Username.Set", user.name, room=sid, namespace='/planarally')
        await sio.emit("Room.Info.Set", {'name': room.name, 'creator': room.creator.name, 'invitationCode': str(room.invitation_code)}, room=sid, namespace='/planarally')
        # await sio.emit("Notes.Set", room.get_notes(username), room=sid, namespace='/planarally')
        # await sio.emit('Asset.List.Set', assets, room=sid, namespace='/planarally')
        await load_location(sid, location)


@sio.on('disconnect', namespace='/planarally')
async def test_disconnect(sid):
    if sid not in state.sid_map:
        return
    user = state.sid_map[sid]['user']

    logger.info(f'User {user.name} disconnected with identifier {sid}')
    await state.remove_sid(sid)
