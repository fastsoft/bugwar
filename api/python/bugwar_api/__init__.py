
from datetime import datetime

class Singleton(object):
    salvo = None
singleton = Singleton()

# doctest and unittest integration

import unittest
import doctest

class TestResult(unittest.TestResult):
    def __init__(self, salvo = None, *args, **kws):
        super(TestResult, self).__init__(*args, **kws)
        self._salvo = salvo
    def addSuccess(self, test):
        self._salvo.success('%s' % test)
    def addFailure(self, test, err):
        self._salvo.failure('%s' % test, '%s' % (err,))
    def addError(self, test, err):
        self._salvo.error('%s' % test, '%s' % (err,))

def modules_test(battery_name = None, modules = None):

    salvo = Salvo(battery_name = battery_name)
    salvo.start()

    def importer():
        for module in modules:
            if not isinstance(module, basestring):
                yield module
            else:
                try:
                    yield __import__(module.strip(), fromlist = ['__file__'])
                except ImportError:
                    salvo.error('import %s' % module, 'failed to import %s' % module)

    modules = list(importer())

    suite = unittest.TestSuite()

    for module in modules:
        try:
            suite.addTest(doctest.DocTestSuite(module))
        except ValueError, x:
            salvo.error('doctest %s' % module.__name__, 'no tests in %s' % module.__name__)

    result = TestResult(salvo)
    suite.run(result)
    unittest.TextTestRunner()
    salvo.stop()


# assertion layer

def ASSERT(guard, name, message = None):
    return (failure, success)[guard](name, message)

def assert_eq(actual, oracle, name):
    if actual == oracle:
        success(name)
    else:
        result = failure(name)
        result.log('expected: %r' % oracle)
        result.log('actual: %r' % actual)

def test(function = None, name = None, raise_on_error = False):
    if function is None:
        return lambda function: test(function, name, raise_on_error)
    else:
        if name is None:
            name = function.func_name
        def decorated(*args, **kws):
            result = Result(salvo_id = singleton.salvo.id, name = name)
            result.start()
            try:
                return function(result, *args, **kws)
                result.stop()
            except Exception, exception:
                from traceback import format_exc
                result.error(exception)
                result.log(format_exc())
                if raise_on_error:
                    raise
        decorated()


# functional layer

def start(battery_name = None, owner_name = None):
    assert singleton.salvo is None, 'a test salvo %s has already been started' % singleton.salvo
    battery = Battery(name = battery_name)
    try:
        battery.load()
    except Exception:
        battery.save()
    salvo = Salvo(
        battery_id = battery.id,
        owner_name = owner_name,
    ).start().save()
    singleton.salvo = salvo
    return salvo

def stop():
    return singleton.salvo.stop()

def success(*args, **kws):
    return singleton.salvo.success(*args, **kws)
    
def failure(*args, **kws):
    return singleton.salvo.failure(*args, **kws)

def error(*args, **kws):
    return singleton.salvo.error(*args, **kws)

def measure(name, value, datetime = None):
    return singleton.salvo.measure(name, value, datetime = datetime)

def aggregate(message):
    r"""
        >>> list(aggregate("a\nb\nc\n")) == ["a\nb\nc"]
        True
        >>> list(aggregate("\n".join('x' * 1024 for n in range(3)))) == list('x' * 1024 for n in range(3))
        True
        >>> list(aggregate("\n".join('x' * 1025 for n in range(3)))) == list('x' * 1021 + '...' for n in range(3))
        True
    """
    messages = message.rstrip().split("\n")
    pool = []
    for message in messages:
        if len(message) > 1024:
            if pool:
                yield "\n".join(pool)
                pool = []
            yield message[:1021] + '...'
        else:
            aggregate = pool + [message]
            if len("\n".join(aggregate)) >= 1024:
                if pool:
                    yield "\n".join(pool)
                pool = [message]
            else:
                pool = aggregate
    if pool:
        yield "\n".join(pool)
        pool = []

def log(message, datetime = None):
    for message in aggregate(message):
        return singleton.salvo.log(message, datetime = datetime)

def warn(message, datetime = None):
    return singleton.salvo.warn(message, datetime = datetime)


# djata api

from djata_api import Model, Field, ForeignKey
url = 'http://bugwar.fastsoft.com/'

from itertools import count
next_creation_counter = count().next

class Timed(object):
    def save(self):
        if 'datetime' not in self or self['datetime'] is None:
            self['datetime'] = now()
        self['creation_counter'] = next_creation_counter()
        return super(Timed, self).save()

class Salvo(Model):

    id = Field()
    battery = ForeignKey('Battery')
    owner_name = Field()
    url = Field()
    revision = Field(int, null = True)
    start = Field()
    stop = Field()

    def __init__(self, **kws):
        url = kws.get('url', None)
        revision = kws.get('revision', None)
        if url is None or revision is None:
            import __main__
            file_name = getattr(__main__, '__file__', '<manual>')
            info = svn_info(file_name)
            if url is None:
                url = info.get('URL', None)
            if revision is None:
                revision = info.get('Revision', None)
        kws.update({
            'url': url,
            'revision': revision,
        })
        super(Salvo, self).__init__(**kws)

    def start(self, save = True):
        self['start'] = now()
        if save:
            self.save()
        return self

    def stop(self, save = True):
        self['stop'] = now()
        if save:
            self.save()
        return self

    def result(self, label = None, name = None, message = None, datetime = None, save = None):
        if save is None:
            save = True
        result = Result(
            salvo_id = self.id,
            label = label,
            name = name,
            message = message,
            datetime = datetime,
        )
        if save:
            result.save()
        print result.datetime, label.upper(), name, message
        return result

    def success(self, name, message = None, datetime = None, save = None):
        return self.result('pass', name, message, datetime, save)

    def failure(self, name, message = None, datetime = None, save = None):
        return self.result('fail', name, message, datetime, save)

    def error(self, name, message = None, datetime = None, save = None):
        return self.result('error', name, message, datetime, save)

    def warn(self, name, message = None, datetime = None, save = None):
        return self.result('warn', name, message, datetime, save)

    def log(self, message, datetime = None):
        log = Log(
            label = 'log',
            salvo_id = self.id,
            message = message,
            datetime = datetime,
        )
        log.save()
        print log.datetime, message
        return self

    def measure(self, name, value, datetime = None, save = None):
        if save is None:
            save = True
        measure = Measure(
            salvo_id = self.id,
            name = name,
            value = value,
            datetime = datetime,
        )
        if save:
            measure.save()
        print measure.datetime, 'measure'.upper(), value
        return measure

class Result(Timed, Model):
    id = Field()
    label = Field()
    salvo = ForeignKey('Salvo')
    name = Field()
    datetime = Field()
    message = Field()

    def start(self):
        self.label = 'warn'
        self.message = 'the test is in progress or did not complete.'
        self.save()

    def stop(self):
        self.datetime = now()
        self.save()

    def success(self, message = None, save = True):
        self.label = 'pass'
        self.message = message
        self.save()

    def failure(self, message = None):
        self.label = 'fail'
        self.message = message
        self.save()

    def error(self, message = None):
        self.label = 'error'
        self.message = message
        self.save()

    def log(self, message, datetime = None):
        log = Log(
            label = 'log',
            salvo_id = self.salvo.id,
            result_id = self.id,
            message = message,
            datetime = datetime,
        )
        log.save()
        return log

    def warn(self, message, datetime = None):
        log = Log(
            label = 'warn',
            salvo_id = self.salvo.id,
            result_id = self.id,
            message = message,
            datetime = datetime,
        )
        log.save()
        return self

class Measure(Timed, Model):
    _verbose_name = 'measurement'
    id = Field()
    salvo = ForeignKey('Salvo')
    datetime = Field()
    name = Field()
    value = Field()

    def log(self, message, datetime = None):
        log = Log(
            label = 'log',
            salvo_id = self.salvo.id,
            measure_id = self.id,
            message = message,
            datetime = datetime,
        )
        log.save()
        return self

class Log(Timed, Model):
    _verbose_name = 'event'
    salvo = ForeignKey('Salvo')
    result = ForeignKey('Result')
    measure = ForeignKey('Measure')
    datetime = Field()
    message = Field()
    label = Field()

class Battery(Model):
    _index = 'name'
    id = Field()
    name = Field()

# utilities

def now():
    return datetime.now()

def svn_info(file_name):
    import commands
    svn_info = commands.getoutput('svn info %s' % repr(file_name))
    return dict(
        line.split(": ", 1)
        for line in svn_info.split("\n")
        if ": " in line
    )

if __name__ == '__main__':
    from doctest import testmod
    testmod()
    """
#    s = Salvo.objects.get(106)
#    print s
#    print s.success('bugwar test')
        import random
        start('bugwar api')
        success('success')
        failure('failure')
        error('error')
        e = error('error with a log')
        e.log('error log thing')
        e.log('another error')
        e = error('error with a log')
        e.log('error log thing')
        e.log('another error')
        e.log('saved last')
        e.save()
        warn('warn')
        measure('measurement', random.randint(10, 100))
        measure('measurement2', random.randint(10, 100)).log("this is another random measurement")
        stop()
    """
