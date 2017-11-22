class Subscriber:
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def update(self, message):
        # start new Thread in here to handle any task
        print('\n\n {} got message "{}"'.format(self.name, message))
        pass
        
class Publisher:
    def __init__(self, channels, *args, **kwargs):
        # maps channel names to subscribers
        # str -> dict
        super().__init__(*args, **kwargs)
        self.channels = { channel : dict()
                          for channel in channels }
                          
    def get_subscribers(self, channel):
        return self.channels[channel]

    def get_channels(self):
        return self.channels
                
    def register(self, channel, subscriber):
        self.get_subscribers(channel)[subscriber] = subscriber.update

    def unregister(self, channel, subscriber):
        del self.get_subscribers(channel)[subscriber]

    def dispatch(self, channel, message):
        for subscriber, callback in self.get_subscribers(channel).items():
            callback(message)

