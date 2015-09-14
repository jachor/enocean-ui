import logging
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File
from .radio import RADIO, Packet


class LastPackets(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.last = []
        RADIO.listeners.append(self._got_packet)

    def _got_packet(self, packet):
        self.last = [packet] + self.last[:9]

    def render_GET(self, request):
        data = []
        data.append('<html><body>')
        data.append('<p>Got {} packets.'.format(len(self.last)))
        data.append('<ul>')
        for p in self.last:
            data.append('<li>{}'.format(str(p)))
            data.append(' <a href="/radio/send?packet={}">Send</a>'.format(p.to_string()))
        data.append('</ul>')
        data.append('</body></html>')
        return ''.join(data)


class SendPacket(Resource):
    def render_POST(self, request):
        p = Packet.from_string(request.args['packet'][0])
        RADIO.send(p)
        return 'Sent ' + str(p)

    render_GET = render_POST


class RadioResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('last', LastPackets())
        self.putChild('send', SendPacket())


def start_web(port=8080):
    root = File('./enocean_site')
    root.putChild('radio', RadioResource())
    site = Site(root)
    reactor.listenTCP(port, site)
    logging.info('HTTP server running on port '+str(port))
    return site

