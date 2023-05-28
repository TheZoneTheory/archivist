import pickle


__template = {
    'default_fandom': '',
    'restrict_explicit': True,
    'restrict_mature': False,
    'promo_channels': [],
    'auto_embed_links': True
}
settings = pickle.load(open("server_settings.pickle", 'rb'))


def setting(guild_id: int, key=None, value=None):
    # check if settings object has guild_id key
    # - if doesn't, create object from template
    server = settings.get(guild_id, None)
    if server is None:
        server = __template.copy()
        settings[guild_id] = server

    # check if key is none
    # - if true, return settings[guild_id]
    if key is None:
        return server

    # check if value is none
    # - if value exists, overwrite value at key
    if value is None:
        return server.get(key, __template.get(key, None))
    else:
        print(f'SERVER: {guild_id}\nKEY: {key}\nVALUE: {value}')
        server[key] = value
        # pickle time
        pickle.dump(settings, open("server_settings.pickle", 'wb'))


def reset_server(guild_id):
    try:
        del settings[guild_id]
        pickle.dump(settings, open("server_settings.pickle", 'wb'))
    except KeyError:
        pass
