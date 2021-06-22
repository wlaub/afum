import vlc


class AudioManager():
    def __init__(self):
        self.loaded = False
        self.path = ''
        self.sound = None
        self.position = 0
        self.play_obj = None

        self.cache = {}

        self.vlc = vlc.Instance()
        self.player = self.vlc.media_player_new()

        self.is_playing = False

    def set_pos(self, value):
        self.position = value
        self.player.set_time(value*1000)

    def get_pos(self):
        if not self.loaded: return 0
        if self.player.is_playing():
            return round(self.player.get_time()/1000)
        else:
            if self.is_playing and self.player.get_state() == vlc.State.Ended:
                print('Playback finished')
                self.player.set_media(self.sound)
                self.is_playing = False
                self.position = 0
            return self.position

        
    def stop(self):
        self.player.pause()
        self.is_playing = False

    def load(self, path):
        if self.path == path: return
        self.stop()
        self.path = path
        if path in self.cache.keys():
            self.sound = self.cache[path]
        else:
            self.sound = self.vlc.media_new(path)
            self.cache[path] = self.sound
        self.player.set_media(self.sound)
        self.loaded = True
        self.position = 0

    def clear(self):
        self.stop()
        self.loaded = False

    def play(self):
        if not self.loaded: return
        self.player.play() 
        self.set_pos(self.position)
        self.is_playing = True

    def toggle_play(self):
        if not self.loaded: return
        if self.player.is_playing():
            self.stop()
        else:
            self.play()


