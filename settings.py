import re


class Settings:
    modpack_name = ''
    modpack_url = ''
    # URL or other text
    donate_to = ''
    map_link = ''
    # Bot's token
    tg_token = ''
    # Each line of log file starts with this pattern
    datetime_prefix = '\[([0-2][0-9])\:([0-9]{2})\:([0-9]{2})\] '
    # Log location/filename
    log_file = '/home/minecraft/server/logs/latest.log'
    log_offset = '/home/minecraft/server/logs/latest.log.offset'
    # Local database
    database = './db.db'
    # TG Users:MC users
    mc_users = {
        'photopiter': 'spaut'
    }
    # Chats that cannot be subscribed
    banned_chats = {}
    # List of regexps for catching actions in log
    actions = {
        # [21:19:38] [Server thread/INFO] [net.minecraft.server.
        # management.PlayerList]:
        # spaut[/0.0.0.0:57630] logged in with entity id 476284 in
        # world(0) at (805.5899196278124, 66.0, 1520.1268665385317)
        'login': re.compile(datetime_prefix +
                            '.+: ([A-z0-9]*)?\[\/[0-9.]{4,15}\:[0-9]*\].+ in ([.+]*)'),
        # [18:30:07] [Server thread/INFO] [net.minecraft.network.
        # NetHandlerPlayServer]: spaut lost connection: Disconnected
        'logout': re.compile(datetime_prefix +
                             '.+: ([A-z0-9]*) lost connection'),
        # [17:05:03] [Server Shutdown Thread/INFO] [net.minecraft.server.
        # MinecraftServer]: Stopping server
        'server_stop': re.compile(datetime_prefix +
                                  '\[Server Shutdown Thread/INFO\].+ Stopping server'),
        # [10:02:02] [Server thread/INFO] [FML]: Loading dimension 0 (world)
        # (net.minecraft.server.dedicated.DedicatedServer@7facf5fd)
        'server_start': re.compile(datetime_prefix +
                                   '.+: Loading dimension 0 \(world\)?'),
        # [21:24:36] [Server thread/INFO] [net.minecraft.server.dedicated.
        # DedicatedServer]: spaut§r has made the advancement
        # §r§a[§r§aIsn't It Iron Pick§r§a]§r
        'advancement': re.compile(datetime_prefix +
                                  '.+: ([A-z0-9]*).+ has (made|reached) the (advancement|goal) §.§.?\[§.§.?(.*)§.§.?\]'),
        # spaut has reached the goal [Fizzing Electrodes]
        # [18:00:58] [Server thread/INFO] [net.minecraft.server.dedicated.
        # DedicatedServer]: <§2Iworb§r> §rхв§r
        # [18:01:02] [Server thread/INFO] [net.minecraft.server.dedicated.
        # DedicatedServer]: <spaut> §ro/§r
        'chat_message': re.compile(datetime_prefix +
                                   '.+: \<(§.)?([A-z0-9]*)(§.)?\> §.(.*)§.'),
        # [23:46:14] [Server thread/INFO] [tombmanygraves]:
        # [TombManyGraves]: Kapn614 died in dimension 0 at
        # BlockPos{x=1013, y=81, z=1540}. Their grave may be near!
        # [23:46:14] [Server thread/INFO] [net.minecraft.server.dedicated.
        # DedicatedServer]: Kapn614§r was slain by §rSpider§r
        'death': re.compile(datetime_prefix + '.+: ([A-z0-9]*) died?'),
    }
