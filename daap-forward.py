 #!/usr/bin/env python
import os
import sys
import signal
from select import select
from subprocess import Popen
from threading import Thread

config = {
    'ssh-server-name':          'localhost',
    'ssh-username':             '',
    'daap-server-name':         'localhost',
    'remote-daap-port':         '3689',
    'local-daap-port':          '3689',
    'share-name':               'Remote iTunes Share'
}


def read_config(path):
    if not os.path.isfile(path):
        print >> sys.stderr, 'Missing config %s' % path
        return
    for line in open(path):
        line = line.strip().split(None, 1)
        if not line or line[0][:1] == '#':
            continue
        config[line[0]] = line[1]


def start_ssh(pids):
    user = config['ssh-username']
    if user:
        user += '@'
    c = Popen(['ssh', user + config['ssh-server-name'], '-g', '-N', '-L',
               '%s:%s:%s' % (config['local-daap-port'],
                             config['daap-server-name'],
                             config['remote-daap-port'])])
    pids.append(c.pid)
    c.wait()


def start_proxy(pids):
    c = Popen(['dns-sd', '-R', config['share-name'], '_daap._tcp.', 'local',
               config['local-daap-port']])
    pids.append(c.pid)
    c.wait()


def main():
    read_config(os.path.expanduser('~/.daapforward'))
    pids = []
    print 'Starting up...'
    print 'Connecting to %s via %s' % (
        config['daap-server-name'],
        config['ssh-server-name']
    )
    try:
        try:
            for task in start_ssh, start_proxy:
                t = Thread(target=task, args=(pids,))
                t.setDaemon(True)
                t.start()
            while 1:
                select([sys.stdin], [], [])
        except KeyboardInterrupt:
            pass
    finally:
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        print 'Shut down'


if __name__ == '__main__':
    main()
