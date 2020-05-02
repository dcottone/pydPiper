#!/usr/bin/python.pydPiper
# coding: UTF-8

# pydPiper service to display music data to LCD and OLED character displays
# Written by: Ron Ritchey

from __future__ import unicode_literals
import json, threading, logging, Queue, time, sys, getopt, moment, signal, commands, os, copy, datetime, math, requests
import pages
import displays
import sources
import pydPiper_config_dual
import pause

#try:
#    import pyowm
#except ImportError:
#    pass


exitapp = [ False ]

class music_controller(threading.Thread):
    # Receives updates from music services
    # Determines what page to displays
    # Sends relevant updates to display_controller

    # musicdata variables.
    # Includes all from musicdata class plus environmentals
    musicdata_init = {
        'state':u"stop",
        'musicdatasource':u"",
        'actPlayer':u"",
        'artist':u"",
        'title':u"",
        'album':u"",
        'uri':u"",
        'current':-1,
        'elapsed':-1,
        'remaining':u"",
        'duration':-1,
        'length':-1,
        'position':u"",
        'elapsed_formatted':u"",
        'volume':-1,
        'repeat': 0,
        'single': 0,
        'random': 0,
        'channels':0,
        'bitdepth':u"",
        'bitrate':u"",
        'samplerate':u"",
        'type':u"",
        'tracktype':u"",
        'repeat_onoff': u"Off",
        'single_onoff': u"Off",
        'random_onoff': u"Off",
        'playlist_display':u"",
        'playlist_position':-1,
        'playlist_count':-1,
        'playlist_length':-1,
        'current_tempc':0,
        'current_tempf':0,
        'disk_avail':0,
        'disk_availp':0,
        'current_time':u"",
        'utc':moment.utcnow(),
        'localtime':moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE),
        'current_time_sec':u"",
        'current_time_formatted':u"",
        'time_formatted':u"",
        'current_ip':u"",
        'outside_conditions':'No data',
        'outside_temp_min':0,
        'outside_temp_max':0,
        'outside_temp_formatted':'',
        'system_temp_formatted':''
    }


    def __init__(self, servicelist, display_controller, showupdates=False):
        threading.Thread.__init__(self)

        self.daemon = True
        self.musicqueue = Queue.Queue()
        self.image = None
        self.showupdates = showupdates
        self.display_controller = display_controller

        self.musicdata = copy.deepcopy(self.musicdata_init)
        self.musicdata_prev = copy.deepcopy(self.musicdata)
        self.servicelist = servicelist
        self.services = { }

        # Attempt to initialize services
        self.initservices()

        # Lock used to prevent simultaneous update of the musicdata dictionary
        self.musicdata_lock = threading.Lock()


    def initservices(self):

        # Make sure that if rune is selected that is is the only service that is selected
        if u"rune" in self.servicelist and len(self.servicelist) > 1:
            logging.critical(u"Rune service can only be used alone")
            raise RuntimeError(u"Rune service can only be used alone")
        if u"volumio" in self.servicelist and len(self.servicelist) > 1:
            logging.critical(u"Volumio service can only be used alone")
            raise RuntimeError(u"Volumio service can only be used alone")

        musicservice = None
        for s in self.servicelist:
            s = s.lower()
            try:
                if s == u"mpd" :
                    musicservice = sources.musicdata_mpd.musicdata_mpd(self.musicqueue, pydPiper_config_dual.MPD_SERVER, pydPiper_config_dual.MPD_PORT, pydPiper_config_dual.MPD_PASSWORD)
                elif s == u"moode":
                    musicservice = sources.musicdata_moode.musicdata_moode(self.musicqueue, pydPiper_config_dual.MPD_SERVER, pydPiper_config_dual.MPD_PORT, pydPiper_config_dual.MPD_PASSWORD)
                elif s == u"spop":
                    musicservice = sources.musicdata_spop.musicdata_spop(self.musicqueue, pydPiper_config_dual.SPOP_SERVER, pydPiper_config_dual.SPOP_PORT, pydPiper_config_dual.SPOP_PASSWORD)
                elif s == u"lms":
                    musicservice = sources.musicdata_lms.musicdata_lms(self.musicqueue, pydPiper_config_dual.LMS_SERVER, pydPiper_config_dual.LMS_PORT, pydPiper_config_dual.LMS_USER, pydPiper_config_dual.LMS_PASSWORD, pydPiper_config.LMS_PLAYER)
                elif s == u"rune":
                    musicservice = sources.musicdata_rune.musicdata_rune(self.musicqueue, pydPiper_config_dual.RUNE_SERVER, pydPiper_config_dual.RUNE_PORT, pydPiper_config_dual.RUNE_PASSWORD)
                elif s == u"volumio":
                    musicservice = sources.musicdata_volumio2.musicdata_volumio2(self.musicqueue, pydPiper_config_dual.VOLUMIO_SERVER, pydPiper_config_dual.VOLUMIO_PORT, exitapp )
                else:
                    logging.debug(u"Unsupported music service {0} requested".format(s))
                    continue
            except NameError:
                # Missing dependency for requested servicelist
                logging.warning(u"Request for {0} failed due to missing dependencies".format(s))
                pass
            if musicservice != None:
                self.services[s] = musicservice

        if len(self.services) == 0:
            logging.critical(u"No music services succeeded in initializing")
            raise RuntimeError(u"No music services succeeded in initializing")

    def launch_update_thread(self, func):
        sv_t = threading.Thread(target=func)
        sv_t.daemon = True
        sv_t.start()

    def run(self):

        logging.debug(u"Music Controller Starting")

        self.launch_update_thread(self.updatesystemvars)
        self.launch_update_thread(self.updateconditions)
        self.launch_update_thread(self.updateforecast)

        timesongstarted = 0


        # Inform the system that we are starting up
        with self.musicdata_lock:
            self.musicdata_prev[u'state'] = ''
            self.musicdata[u'state'] = 'starting'
        self.starttime = time.time()

        lastupdate = 0 # Initialize variable to be used to force updates every second regardless of the receipt of a source update
        while not exitapp[0]:

            updates = { }

            # Check if we are starting up.  If yes, update pages to display any start message.
            if self.starttime + pydPiper_config_dual.STARTUP_MSG_DURATION > time.time():
                time.sleep(pydPiper_config_dual.STARTUP_MSG_DURATION)
                with self.musicdata_lock:
                    self.musicdata['state'] = 'stop'
                continue

            # Attempt to get an update from the queue
            try:
                updates = self.musicqueue.get_nowait()
                self.musicqueue.task_done()
            except Queue.Empty:
                pass

            # Get current time
            try:
                utc = moment.utcnow()
                localtime = moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE)
                current_time_ampm = moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE).strftime(u"%p").strip().decode()
                if pydPiper_config_dual.TIME24HOUR == True:
                    current_time = moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE).strftime(u"%H:%M").strip().decode()
                    current_time_sec = moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE).strftime(u"%H:%M:%S").strip().decode()
                else:
                    current_time = moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE).strftime(u"%-I:%M %p").strip().decode()
                    current_time_sec = moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE).strftime(u"%-I:%M:%S %p").strip().decode()
            except ValueError:
                # Don't know why but on exit, the moment code is occasionally throwing a ValueError
                current_time = u"00:00"
                current_time_sec = u"00:00:00"
                current_time_ampm = u''
                utc = None
                localtime = None

            with self.musicdata_lock:
                # Update musicdata based upon received message
                for item, value in updates.iteritems():
                    self.musicdata[item] = value

                # Update song timing variables
                if u'elapsed' in updates:
                    self.musicdata[u'elapsed'] = self.musicdata[u'current'] = updates[u'elapsed']
                    timesongstarted = time.time() - self.musicdata[u'elapsed']

                if self.musicdata[u'state'] == u'play':
                    if u'elapsed' not in updates:
                        if timesongstarted > 0:
                            self.musicdata[u'elapsed'] = int(time.time() - timesongstarted)
                        else:
                            # We got here without timesongstarted being set which is a problem...
                            logging.debug(u"Trying to update current song position with an uninitialized start time")

                # If the value of current has changed then update the other related timing variables
                if self.musicdata[u'elapsed'] != self.musicdata_prev[u'elapsed']:
                    if self.musicdata[u'length'] > 0:
                        timepos = time.strftime("%-M:%S", time.gmtime(self.musicdata[u'elapsed'])) + "/" + time.strftime("%-M:%S", time.gmtime(self.musicdata[u'length']))
                        remaining = time.strftime("%-M:%S", time.gmtime(self.musicdata[u'length'] - self.musicdata[u'elapsed'] ) )

                    else:
                        timepos = time.strftime("%-M:%S", time.gmtime(self.musicdata[u'elapsed']))
                        remaining = timepos

                    self.musicdata[u'remaining'] = remaining.decode()
                    self.musicdata[u'elapsed_formatted'] = self.musicdata[u'position'] = timepos.decode()

                # Update onoff variables (random, single, repeat)
                self.musicdata[u'random_onoff'] = u"On" if self.musicdata[u'random'] else u"Off"
                self.musicdata[u'single_onoff'] = u"On" if self.musicdata[u'single'] else u"Off"
                self.musicdata[u'repeat_onoff'] = u"On" if self.musicdata[u'repeat'] else u"Off"

                # update time variables
                self.musicdata[u'utc'] = utc
                self.musicdata[u'localtime'] = localtime
                self.musicdata[u'time'] = current_time
                self.musicdata[u'time_ampm'] = current_time_ampm
                # note: 'time_formatted' is computed during page processing as it needs the value of the strftime key contained on the line being displayed

                # For backwards compatibility
                self.musicdata[u'current_time'] = current_time
                self.musicdata[u'current_time_sec'] = current_time


            # If anything has changed, update pages ### probably unnecessary to check this now that time is being updated in this section
            if self.musicdata != self.musicdata_prev or lastupdate < time.time():

                # Set lastupdate time to 1 second in the future
                lastupdate = time.time()+1

                self.musicdata[u'time_formatted'] = moment.utcnow().timezone(pydPiper_config_dual.TIMEZONE).strftime('%H:%M').strip().decode()
                # To support previous key used for this purpose
                self.musicdata[u'current_time_formatted'] = self.musicdata[u'time_formatted']

                # Update display controller
                # The primary call to this routine is in main but this call is needed to catch variable changes before musicdata_prev is updated.
                for displayIndex in len(self.display_controller):
                    self.display_controller[displayIndex].next()
                # self.display_controller.next()

                # Print the current contents of musicdata if showupdates is True
                if self.showupdates:

                    # Check to see if a variable has changed (except time variables)
                    shouldshowupdate = False
                    for item, value in self.musicdata.iteritems():
                        try:
                            if item in ['utc', 'localtime', 'time', 'time_ampm', 'current_time', 'current_time_sec']:
                                continue
                            if self.musicdata_prev[item] != value:
                                shouldshowupdate = True
                                break
                        except KeyError:
                            shouldshowupdate = True
                            break


                    if shouldshowupdate:
                        ctime = localtime.strftime("%-I:%M:%S %p").strip()
                        print u"Status at time {0}".format(ctime)

                        with self.musicdata_lock:
                            for item,value in self.musicdata.iteritems():
                                try:
                                    print u"    [{0}]={1} {2}".format(item,repr(value), type(value))
                                except:
                                    print u"err"
                                    print u"[{0}] =".format(item)
                                    print type(value)
                                    print repr(value)
                            print u"\n"

                # Update musicdata_prev
                with self.musicdata_lock:
                    for item, value in self.musicdata.iteritems():
                        try:
                            if self.musicdata_prev[item] != value:
                                self.musicdata_prev[item] = value
                        except KeyError:
                            self.musicdata_prev[item] = value

            # Update display data every 1/4 second
            time.sleep(.25)

    def checkweatherconfiguration(self):
        if not pydPiper_config_dual.WEATHER_SERVICE:
            logging.debug('Weather service not enabled')
            return False

        if pydPiper_config_dual.WEATHER_SERVICE not in ['wunderground', 'accuweather']:
            logging.warning('{0} is not a valid weather service'.format(pydPiper_config_dual.WEATHER_SERVICE))
            return False

        if not pydPiper_config_dual.WEATHER_API:
            logging.warning('Weather service requires an API key.  Weather services will not be available until one is provided')
            return False

        if not pydPiper_config_dual.WEATHER_LOCATION:
            logging.warning('Weather service requires that a location be specified.  Weather services will not be available until one is provided')
            return False
        return True

    def checkaccuweatherreturn(self, status_code):
        if status_code == 400:
            logging.warning('Request had bad syntax or the parameters supplied were invalid.  Request was [{0}]'.format(querystr))
        elif status_code == 401:
            logging.warning('Unauthorized. API authorization failed.  API key is [{0}]'.format(pydPiper_config_dual.WEATHER_API))
        elif status_code == 403:
            logging.warning('Unauthorized. You do not have permission to access this endpoint')
        elif status_code == 404:
            logging.warning('Server has not found a route matching the given URI.  Request was [{0}]'.format(querystr))
        elif status_code == 500:
            logging.warning('Server encountered an unexpected condition which prevented it from fulfilling the request.  Request was [{0}]'.format(querystr))
        elif status_code == 200:
            return True
        else:
            logging.warning('An unexpected return value was provide.  Value was [{0}]. Request was [{1}]'.format(status_code,querystr))
        return False


    def updateforecast(self):
        if not self.checkweatherconfiguration():
            return

        logging.debug('Initializing weather forecast update process.  Forecasts will update every 12 hours at noon and midnight')

        while not exitapp[0]:
            updateFlag = False

            logging.debug('Requesting weather forecast from {0}'.format(pydPiper_config_dual.WEATHER_SERVICE))
            if pydPiper_config_dual.WEATHER_SERVICE == 'accuweather':
                querystr = 'http://dataservice.accuweather.com/forecasts/v1/daily/1day/' + pydPiper_config_dual.WEATHER_LOCATION
                r = requests.get(querystr, { 'apikey': pydPiper_config_dual.WEATHER_API,  })

                if self.checkaccuweatherreturn(r.status_code):
                    try:
                        res = r.json()
                        todaysForecast = res['DailyForecasts'][0]

                        temp_max_f = todaysForecast['Temperature']['Maximum']['Value'] if todaysForecast['Temperature']['Maximum']['Unit'] == 'F' else round((todaysForecast['Temperature']['Maximum']['Value']*1.8)+32,1)
                        temp_min_f = todaysForecast['Temperature']['Minimum']['Value'] if todaysForecast['Temperature']['Minimum']['Unit'] == 'F' else round((todaysForecast['Temperature']['Minimum']['Value']*1.8)+32,1)
                        outside_temp_max = temp_max_f if pydPiper_config_dual.TEMPERATURE.lower() == 'fahrenheit' else round((temp_max_f-32)*0.55555556,1)
                        outside_temp_min = temp_min_f if pydPiper_config_dual.TEMPERATURE.lower() == 'fahrenheit' else round((temp_min_f-32)*0.55555556,1)
                        outside_temp_max_formatted = u"{0}°{1}".format(int(outside_temp_max),{'fahrenheit':'F', 'celsius': 'C'}.get(pydPiper_config_dual.TEMPERATURE.lower()))
                        outside_temp_min_formatted = u"{0}°{1}".format(int(outside_temp_min),{'fahrenheit':'F', 'celsius': 'C'}.get(pydPiper_config_dual.TEMPERATURE.lower()))
                        outside_conditions = todaysForecast['Day']['IconPhrase']
                        updateFlag = True
                    except (KeyError, IndexError, ValueError):
                        logging.warning('AccuWeather provided a response in an unexpected format.  Received [{0}]'.format(res))

            if updateFlag:
                logging.debug('Forecast calls for a high of {0}, a low of {1}.  Condition is {2}'.format(outside_temp_max_formatted, outside_temp_min_formatted, outside_conditions))
                with self.musicdata_lock:
                    self.musicdata[u'outside_temp_max'] = outside_temp_max
                    self.musicdata[u'outside_temp_min'] = outside_temp_min
                    self.musicdata[u'outside_temp_max_formatted'] = outside_temp_max_formatted
                    self.musicdata[u'outside_temp_min_formatted'] = outside_temp_min_formatted
                    self.musicdata[u'outside_conditions'] = outside_conditions

            # Sleep until next update which occurs every half day
            pause.sleepUntil(time.time()+pause.nextHalfday(60), exitapp)


    def updateconditions(self):
        if not self.checkweatherconfiguration():
            return

        logging.debug('Initializing weather current conditions update process.  Current conditions will update every hour')

        while not exitapp[0]:
            updateFlag = False
            # If using accuweather, sample current condition date every hour
            if pydPiper_config_dual.WEATHER_SERVICE == 'accuweather':
                logging.debug('Requesting current conditions from {0}'.format(pydPiper_config_dual.WEATHER_SERVICE))
                querystr = 'http://dataservice.accuweather.com/currentconditions/v1/' + pydPiper_config_dual.WEATHER_LOCATION
                r = requests.get(querystr, { 'apikey': pydPiper_config_dual.WEATHER_API })

                if self.checkaccuweatherreturn(r.status_code):
                    try:
                        res = r.json()
                        current_observation = res[0]

                        temp = current_observation['Temperature']['Imperial']['Value'] if pydPiper_config_dual.TEMPERATURE.lower() == 'fahrenheit' else current_observation['Temperature']['Metric']['Value']
                        temp_formatted = u"{0}°{1}".format(int(temp),{'fahrenheit':'F', 'celsius': 'C'}.get(pydPiper_config_dual.TEMPERATURE.lower()))
                        updateFlag = True
                    except (KeyError, IndexError, ValueError):
                        logging.warning('AccuWeather provided a response in an unexpected format.  Received [{0}]'.format(res))

                    if updateFlag:
                        logging.debug('Current Temperature is {0}'.format(temp_formatted))
                        with self.musicdata_lock:
                            self.musicdata[u'outside_temp'] = temp
                            self.musicdata[u'outside_temp_formatted'] = temp_formatted

            # If using Weather Undergroun, sample current and forecast condition date every hour
            elif pydPiper_config_dual.WEATHER_SERVICE == 'wunderground':
                querystr = 'http://api.wunderground.com/api/' + pydPiper_config_dual.WEATHER_API + '/geolookup/conditions/forecast/q/' + pydPiper_config_dual.WEATHER_LOCATION + '.json'
                r = requests.get(querystr)

                if self.checkaccuweatherreturn(r.status_code):
                    try:
                        res = r.json()
                        if 'error' in res['response']:
                            logging.warning('Error occured retrieving forecast from Weather Underground.  Problem type was [{0}]:[{1}]'.format(res['response']['error']['type'],res['response']['error']['description']))
                        else:
                            todaysForecast = res['forecast']['simpleforecast']['forecastday'][0]
                            currentObservation = res['current_observation']

                            temp = currentObservation['temp_f'] if pydPiper_config_dual.TEMPERATURE.lower() == 'fahrenheit' else currentObservation['temp_c']
                            temp_formatted = u"{0}°{1}".format(int(temp),{'fahrenheit':'F', 'celsius': 'C'}.get(pydPiper_config_dual.TEMPERATURE.lower()))

                            temp_max_f = round(float(todaysForecast['high']['fahrenheit']),1)
                            temp_min_f = round(float(todaysForecast['low']['fahrenheit']),1)
                            temp_max_c = round(float(todaysForecast['high']['celsius']),1)
                            temp_min_c = round(float(todaysForecast['low']['celsius']),1)
                            outside_temp_max = temp_max_f if pydPiper_config_dual.TEMPERATURE.lower() == 'fahrenheit' else temp_max_c
                            outside_temp_min = temp_min_f if pydPiper_config_dual.TEMPERATURE.lower() == 'fahrenheit' else temp_min_c
                            outside_temp_max_formatted = u"{0}°{1}".format(int(outside_temp_max),{'fahrenheit':'F', 'celsius': 'C'}.get(pydPiper_config_dual.TEMPERATURE.lower()))
                            outside_temp_min_formatted = u"{0}°{1}".format(int(outside_temp_min),{'fahrenheit':'F', 'celsius': 'C'}.get(pydPiper_config_dual.TEMPERATURE.lower()))
                            outside_conditions = currentObservation['weather']
                            updateFlag = True
                    except (KeyError, IndexError, ValueError):
                        logging.warning('Weather Underground provided a response in an unexpected format.  Received [{0}]'.format(res))

                    if updateFlag:
                        logging.debug('Current Temperature is {0}'.format(temp_formatted))
                        with self.musicdata_lock:
                            self.musicdata[u'outside_temp'] = temp
                            self.musicdata[u'outside_temp_formatted'] = temp_formatted
                            self.musicdata[u'outside_temp_max'] = outside_temp_max
                            self.musicdata[u'outside_temp_min'] = outside_temp_min
                            self.musicdata[u'outside_temp_max_formatted'] = outside_temp_max_formatted
                            self.musicdata[u'outside_temp_min_formatted'] = outside_temp_min_formatted
                            self.musicdata[u'outside_conditions'] = outside_conditions

            # Sleep until next update which occurs every hour
            pause.sleepUntil(time.time()+pause.nextHour(60), exitapp)

    def updatesystemvars(self):
        logging.debug('Initializing current system status update process.  System status will update every five minutes')

        while not exitapp[0]:

            current_ip = commands.getoutput(u"ip -4 route get 1 | head -1 | cut -d' ' -f8 | tr -d '\n'").strip()

            try:
                with open(u"/sys/class/thermal/thermal_zone0/temp") as file:
                    system_tempc = int(file.read())

                # Convert value to float and correct decimal place
                system_tempc = round(float(system_tempc) / 1000,1)

                # convert to fahrenheit
                system_tempf = round(system_tempc*9/5+32,1)

            except AttributeError:
                system_tempc = 0.0
                system_tempf = 0.0

            try:
                if pydPiper_config_dual.TEMPERATURE.lower() == u'celsius':
                    system_temp = system_tempc
                    system_temp_formatted = u"{0}°c".format(int(system_temp))
                else:
                    system_temp = system_tempf
                    system_temp_formatted = u"{0}°f".format(int(system_temp))
            except:
                system_temp = system_tempf
                system_temp_formatted = u"{0}°f".format(int(system_temp))

            try:
                # Check if running on OSX.  If yes, adjust df command
                with os.popen(u'cat /etc/os-release') as p:
                    releaseName = p.readline()


                if sys.platform == u"darwin":
                    with os.popen(u"df /") as p:
                        p = os.popen(u"df /")
                        line = p.readline()
                        line = p.readline()

                    va = line.split()
                    line = "{0} {1}".format(va[3], va[4])

                    va = line.split()
                    avail = int(va[3])
                    usedp = int(va[4][:-1]) # Remove trailing % and convert to int
                    used = int(va[2])
                    availp = 100-usedp

                elif releaseName[6:12] == 'Alpine':
                    with os.popen(u"df /") as p:
                        p = os.popen(u"df -B 1 /")
                        line = p.readline()
                        line = p.readline()
                        line = p.readline()

                        va = line.split()
                        avail = int(va[2])
                        usedp = int(va[3][:-1]) # Remove trailing % and convert to int
                        used = int(va[1])
                        availp = 100-usedp
                else:
                    # assume running on Raspberry linux
                    with os.popen(u"df -B 1 /") as p:
                        line = p.readline()
                        line = p.readline().strip()

                    va = line.split()
                    avail = int(va[3])
                    usedp = int(va[4][:-1]) # Remove trailing % and convert to int
                    used = int(va[2])
                    availp = 100-usedp

            except AttributeError:
                avail = 0
                availp = 0
                usedp = 0
                used = 0

            logging.debug('System status: Temp {0}, Disk space remaining {1}%, IP address {2}'.format(system_temp_formatted, availp, current_ip.decode()))
            with self.musicdata_lock:
                self.musicdata[u'system_temp'] = system_temp
                self.musicdata[u'system_temp_formatted'] = system_temp_formatted

                self.musicdata[u'system_tempc'] = system_tempc
                self.musicdata[u'system_tempf'] = system_tempf

                # For backward compatibility
                self.musicdata[u'current_tempc'] = self.musicdata[u'system_tempc']
                self.musicdata[u'current_tempf'] = self.musicdata[u'system_tempf']

                self.musicdata[u'disk_avail'] = avail
                self.musicdata[u'disk_availp'] = availp
                self.musicdata[u'disk_used'] = used
                self.musicdata[u'disk_usedp'] = usedp


                self.musicdata[u'ip'] = current_ip.decode()

                # For backwards compatibility
                self.musicdata[u'current_ip'] = current_ip.decode()

            # Sleep until next update which occurs every minutes
            pause.sleepUntil(time.time()+300, exitapp)

def sigterm_handler(_signo, _stack_frame):
        sys.exit(0)

if __name__ == u'__main__':
    import math
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Changing the system encoding should no longer be needed
#    if sys.stdout.encoding != u'UTF-8':
#            sys.stdout = codecs.getwriter(u'utf-8')(sys.stdout, u'strict')

    logging.basicConfig(format=u'%(asctime)s:%(levelname)s:%(message)s', filename=pydPiper_config_dual.LOGFILE, level=pydPiper_config_dual.LOGLEVEL)
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.getLogger(u'socketIO-client').setLevel(logging.WARNING)

    # Move unhandled exception messages to log file
    def handleuncaughtexceptions(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.error(u"Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        try:
            if len(mc.musicdata) > 0:
                logging.error(u"Player status at exception")
                logging.error(unicode(mc.musicdata))
        except NameError:
            # If this gets called before the music controller is instantiated, ignore it
            pass

        sys.__excepthook__(exc_type, exc_value, exc_traceback)


    sys.excepthook = handleuncaughtexceptions

    # Suppress MPD libraries INFO messages
    loggingMPD = logging.getLogger(u"mpd")
    loggingMPD.setLevel( logging.WARN )
    loggingPIL = logging.getLogger(u'PIL')
    loggingPIL.setLevel( logging.WARN )

    try:
        opts, args = getopt.getopt(sys.argv[1:],u"d:",[u"driver=",u"devicetype=",u"width=",u"height=","rs=","e=","d4=","d5=","d6=","d7=","i2caddress=","i2cport=", "spidevice=", "spiport=", "gpioDC=", "gpioRST=" ,u"wapi=", u"wlocale=", u"timezone=", u"temperature=", u"lms",u"mpd",u"spop",u"rune",u"volumio",u"pages=", u"lmsplayer=", u"showupdates"])
    except getopt.GetoptError:
        print u'pydPiper.py -d <driver> --devicetype <devicetype (for LUMA devices)> --width <width in pixels> --height <height in pixels> --rs <rs> --e <e> --d4 <d4> --d5 <d5> --d6 <d6> --d7 <d7> --i2caddress <i2c address> --i2cport <i2c port> --spidevice <spi dev> --spiport <spi port> --gpioDC <spi gpio DC> --gpioRST <spi gpio RST> --wapi <weather underground api key> --wlocale <weather location> --timezone <timezone> --temperature <fahrenheit or celsius> --mpd --spop --lms --rune --volumio --pages <pagefile> --lmsplayer <mac address of lms player> --showupdates'
        sys.exit(2)

    services_list = [ ]
    driver_1 = ''
    driver_2 = ''
    devicetype_1 = ''
    devicetype_2 = ''
    showupdates = False
    pagefile_1 = 'pages.py'
    pagefile_2 = 'pages.py'

    pin_rs_1 = pydPiper_config_dual.DISPLAY_1_PIN_RS
    pin_e_1 = pydPiper_config_dual.DISPLAY_1_PIN_E
    [pin_d4_1, pin_d5_1, pin_d6_1, pin_d7_1] = pydPiper_config_dual.DISPLAY_1_PINS_DATA
    rows_1 = pydPiper_config_dual.DISPLAY_1_HEIGHT
    cols_1 = pydPiper_config_dual.DISPLAY_1_WIDTH
    i2c_address_1 = pydPiper_config_dual.DISPLAY_1_I2C_ADDRESS
    i2c_port_1 = pydPiper_config_dual.DISPLAY_1_I2C_PORT
    spi_device_1 = pydPiper_config_dual.DISPLAY_1_SPI_DEVICE
    spi_port_1 = pydPiper_config_dual.DISPLAY_1_SPI_PORT
    gpio_DC_1 = pydPiper_config_dual.DISPLAY_1_GPIO_DC
    gpio_RST_1 = pydPiper_config_dual.DISPLAY_1_GPIO_RST
    enable_1 = pydPiper_config_dual.DISPLAY_1_ENABLE_DURATION
    driver_1 = pydPiper_config_dual.DISPLAY_1_DRIVER
    pagefile_1 = pydPiper_config_dual.PAGEFILE_1

    pin_rs_2 = pydPiper_config_dual.DISPLAY_2_PIN_RS
    pin_e_2 = pydPiper_config_dual.DISPLAY_2_PIN_E
    [pin_d4_2, pin_d5_2, pin_d6_2, pin_d7_2] = pydPiper_config_dual.DISPLAY_2_PINS_DATA
    rows_2 = pydPiper_config_dual.DISPLAY_2_HEIGHT
    cols_2 = pydPiper_config_dual.DISPLAY_2_WIDTH
    i2c_address_2 = pydPiper_config_dual.DISPLAY_2_I2C_ADDRESS
    i2c_port_2 = pydPiper_config_dual.DISPLAY_2_I2C_PORT
    spi_device_2 = pydPiper_config_dual.DISPLAY_2_SPI_DEVICE
    spi_port_2 = pydPiper_config_dual.DISPLAY_2_SPI_PORT
    gpio_DC_2 = pydPiper_config_dual.DISPLAY_2_GPIO_DC
    gpio_RST_2 = pydPiper_config_dual.DISPLAY_2_GPIO_RST
    enable_2 = pydPiper_config_dual.DISPLAY_2_ENABLE_DURATION
    driver_2 = pydPiper_config_dual.DISPLAY_2_DRIVER
    pagefile_2 = pydPiper_config_dual.PAGEFILE_2

    services_list.append(pydPiper_config_dual.MUSIC_SERVICE)


    for opt, arg in opts:
        if opt == u'-h':
            print u'pydPiper.py -d_1 <driver> --devicetype_1 <devicetype e.g. ssd1306, sh1106> --width_1 <width in pixels> --height_1 <height in pixels> --rs_1 <rs> --e_1 <e> --d4_1 <d4> --d5_1 <d5> --d6_1 <d6> --d7_1 <d7> --i2caddress_1 <i2c address> --i2cport_1 <i2c port> --spidevice_1 <spi dev> --spiport_1 <spi port> --gpioDC_1 <spi gpio DC> --gpioRST_1 <spi gpio RST> --enable_1 <enable duration> -d_2 <driver> --devicetype_2 <devicetype e.g. ssd1306, sh1106> --width_2 <width in pixels> --height_2 <height in pixels> --rs_2 <rs> --e_2 <e> --d4_2 <d4> --d5_2 <d5> --d6_2 <d6> --d7_2 <d7> --i2caddress_2 <i2c address> --i2cport_2 <i2c port> --spidevice_2 <spi dev> --spiport_2 <spi port> --gpioDC_2 <spi gpio DC> --gpioRST_2 <spi gpio RST> --enable_2 <enable duration> --wapi <weather underground api key> --wlocale <weather location> --timezone <timezone> --temperature <fahrenheit or celsius> --mpd --spop --lms --rune --volumio --pages_1 <pagefile> --pages_2 <pagefile> --lmsplayer <mac address of lms player> --showupdates'
            sys.exit()
        elif opt in (u"-d_1", u"--driver_1"):
            driver_1 = arg
        elif opt in (u"--devicetype_1"):
            devicetype_1 = arg
        elif opt in ("--rs_1"):
            pin_rs_1  = int(arg)
        elif opt in ("--e_1"):
            pin_e_1  = int(arg)
        elif opt in ("--d4_1"):
            pin_d4_1  = int(arg)
        elif opt in ("--d5_1"):
            pin_d5_1  = int(arg)
        elif opt in ("--d6_1"):
            pin_d6_1  = int(arg)
        elif opt in ("--d7_1"):
            pin_d7_1  = int(arg)
        elif opt in ("--i2caddress_1"):
            i2c_address_1 = int(arg,0)
        elif opt in ("--i2cport_1"):
            i2c_port_1 = int(arg,0)
        elif opt in ("--spidevice_1"):
            spi_device_1 = int(arg,0)
        elif opt in ("--spiport_1"):
            spi_port_1 = int(arg,0)
        elif opt in ("--gpioDC_1"):
            gpio_DC_1 = int(arg,0)
        elif opt in ("--gpioRST_1"):
            gpio_RST_1 = int(arg,0)
        elif opt in ("--width_1"):
            cols_1 = int(arg,0)
        elif opt in ("--height_1"):
            rows_1 = int(arg,0)
        elif opt in ("--enable_1"):
            enable_1 = int(arg)
        elif opt in (u"-d_2", u"--driver_2"):
            driver_2 = arg
        elif opt in (u"--devicetype_2"):
            devicetype_2 = arg
        elif opt in ("--rs_2"):
            pin_rs_2  = int(arg)
        elif opt in ("--e_2"):
            pin_e_2  = int(arg)
        elif opt in ("--d4_2"):
            pin_d4_2  = int(arg)
        elif opt in ("--d5_2"):
            pin_d5_2  = int(arg)
        elif opt in ("--d6_2"):
            pin_d6_2  = int(arg)
        elif opt in ("--d7_2"):
            pin_d7_2  = int(arg)
        elif opt in ("--i2caddress_2"):
            i2c_address_2 = int(arg,0)
        elif opt in ("--i2cport_2"):
            i2c_port_2 = int(arg,0)
        elif opt in ("--spidevice_2"):
            spi_device_2 = int(arg,0)
        elif opt in ("--spiport_2"):
            spi_port_2 = int(arg,0)
        elif opt in ("--gpioDC_2"):
            gpio_DC_2 = int(arg,0)
        elif opt in ("--gpioRST_2"):
            gpio_RST_2 = int(arg,0)
        elif opt in ("--width_2"):
            cols_2 = int(arg,0)
        elif opt in ("--height_2"):
            rows_2 = int(arg,0)
        elif opt in ("--enable_2"):
            enable_2 = int(arg)
        elif opt in (u"--wapi"):
            pydPiper_config_dual.WUNDER_API = arg
        elif opt in (u"--wlocale"):
            pydPiper_config_dual.WUNDER_LOCATION = arg
        elif opt in (u"--timezone"):
            pydPiper_config_dual.TIMEZONE = arg
        elif opt in (u"--temperature"):
            pydPiper_config_dual.TEMPERATURE = arg
        elif opt in (u"--mpd"):
            services_list.append(u'mpd')
        elif opt in (u"--spop"):
            services_list.append(u'spop')
        elif opt in (u"--lms"):
            services_list.append(u'lms')
        elif opt in (u"--lmsplayer"):
            pydPiper_config_dual.LMS_PLAYER = arg
        elif opt in (u"--rune"):
            services_list.append(u'rune')
        elif opt in (u"--volumio"):
            services_list.append(u'volumio')
        elif opt in (u"--pages_1"):
            pagefile_1 = arg
        elif opt in (u"--pages_2"):
            pagefile_2 = arg
            # print u"Loading {0} as page file".format(arg)
            # If page file provided, try to load provided file on top of default pages file
            # try:
            #     newpages = imp.load_source(u'pages', arg)
            #     if validpages(newpages):
            #         pages = newpages
            #     else:
            #         print u"Invalid page file provided.  Using default pages."
            # except IOError:
            #     # Page file not found
            #     print u"Page file {0} not found.  Using default pages".format(arg)

        elif opt in (u"--showupdates"):
            showupdates = True

    pydPiper_config_dual.DISPLAY_1_SIZE = (cols_1, rows_1)
    pydPiper_config_dual.DISPLAY_2_SIZE = (cols_2, rows_2)

    pins_data_1 = [pin_d4_1, pin_d5_1, pin_d6_1, pin_d7_1]
    pins_data_2 = [pin_d4_2, pin_d5_2, pin_d6_2, pin_d7_2]

    if len(services_list) == 0:
        logging.critical(u"Must have at least one music service to monitor")
        sys.exit()

    logging.info(u'pydPiper starting')

    dq = Queue.Queue()



    # Choose display

    if not driver_1:
        try:
            driver_1 = pydPiper_config_dual.DISPLAY_1_DRIVER
        except:
            driver_1 = u''

    if not devicetype_1:
        try:
            devicetype_1 = pydPiper_config_dual.DISPLAY_1_DEVICETYPE
        except:
            devicetype_1 = u''

    if not driver_2:
        try:
            driver_2 = pydPiper_config_dual.DISPLAY_2_DRIVER
        except:
            driver_2 = u''

    if not devicetype_2:
        try:
            devicetype_2 = pydPiper_config_dual.DISPLAY_2_DEVICETYPE
        except:
            devicetype_2 = u''


    if driver_1 == u"winstar_weg":
        lcd_1 = displays.winstar_weg.winstar_weg(rows_1, cols_1, pin_rs_1, pin_e_1, pins_data_1, enable_1)
    elif driver_1 == u"hd44780":
        lcd_1 = displays.hd44780.hd44780(rows_1, cols_1, pin_rs_1, pin_e_1, pins_data_1, enable_1)
    elif driver_1 == u"hd44780_i2c":
        lcd_1 = displays.hd44780_i2c.hd44780_i2c(rows_1, cols_1, i2c_address_1, i2c_port_1, enable_1)
    elif driver_1 == u"hd44780_mcp23008":
        lcd_1 = displays.hd44780_i2c.hd44780_mcp23008(rows_1, cols_1, i2c_address_1, i2c_port_1, enable_1)
    elif driver_1 == u"ssd1306_i2c":
        lcd_1 = displays.ssd1306_i2c.ssd1306_i2c(rows_1, cols_1, i2c_address_1, i2c_port_1)
    elif driver_1 == u"luma_i2c":
        lcd_1 = displays.luma_i2c.luma_i2c(rows_1, cols_1, i2c_address_1, i2c_port_1, devicetype_1)
    elif driver_1 == u"luma_spi":
        lcd_1 = displays.luma_spi.luma_spi(rows_1, cols_1, spi_device_1, spi_port_1, gpio_DC_1, gpio_RST_1, devicetype_1)
    elif driver_1 == u"lcd_curses":
        lcd_1 = displays.lcd_curses.lcd_curses(rows_1, cols_1)
    else:
        logging.critical(u"No valid display 1 found")
        sys.exit()

    if driver_2 == u"winstar_weg":
        lcd_2 = displays.winstar_weg.winstar_weg(rows_2, cols_2, pin_rs_2, pin_e_2, pins_data_2, enable_2)
    elif driver_2 == u"hd44780":
        lcd_2 = displays.hd44780.hd44780(rows_2, cols_2, pin_rs_2, pin_e_2, pins_data_2, enable_2)
    elif driver_2 == u"hd44780_i2c":
        lcd_2 = displays.hd44780_i2c.hd44780_i2c(rows_2, cols_2, i2c_address_2, i2c_port_2, enable_2)
    elif driver_2 == u"hd44780_mcp23008":
        lcd_2 = displays.hd44780_i2c.hd44780_mcp23008(rows_2, cols_2, i2c_address_2, i2c_port_2, enable_2)
    elif driver_2 == u"ssd1306_i2c":
        lcd_2 = displays.ssd1306_i2c.ssd1306_i2c(rows_2, cols_2, i2c_address_2, i2c_port_2)
    elif driver_2 == u"luma_i2c":
        lcd_2 = displays.luma_i2c.luma_i2c(rows_2, cols_2, i2c_address_2, i2c_port_2, devicetype_2)
    elif driver_2 == u"luma_spi":
        lcd_2 = displays.luma_spi.luma_spi(rows_2, cols_2, spi_device_2, spi_port_2, gpio_DC_2, gpio_RST_2, devicetype_2)
    elif driver_2 == u"lcd_curses":
        lcd_2 = displays.lcd_curses.lcd_curses(rows_2, cols_2)
    else:
        logging.critical(u"No valid display 2 found")
        sys.exit()

    lcd_1.clear()
    lcd_1.clear()

    logging.debug('Loading display controller')
    dc_1 = displays.display.display_controller(pydPiper_config_dual.DISPLAY_1_SIZE)
    dc_2 = displays.display.display_controller(pydPiper_config_dual.DISPLAY_2_SIZE)

    logging.debug('Loading music controller')
    mc_1 = music_controller(services_list, [dc_1,dc_2], showupdates)
    #mc_2 = music_controller(services_list, dc_2, showupdates)
    time.sleep(2)
    mc_1.start()
    #mc_2.start()
    dc_1.load(pagefile_1, mc_1.musicdata,mc_1.musicdata_prev )
    dc_2.load(pagefile_2, mc_1.musicdata,mc_1.musicdata_prev )

    try:
        while True:
            # Get next image and send it to the display every .1 seconds
            with mc_1.musicdata_lock:
                img_1 = dc_1.next()
          #  with mc_2.musicdata_lock:
                img_2 = dc_2.next()
#            displays.graphics.update(img)
            lcd_1.update(img_1)
            lcd_2.update(img_2)
            time.sleep(pydPiper_config_dual.ANIMATION_SMOOTHING_1)


    except KeyboardInterrupt:
        pass

    finally:
        print u"Shutting down threads"
        exitapp[0] = True
        try:
            lcd_1.clear()
            lcd_2.clear()
            time.sleep(3)
            lcd_1.cleanup()
            lcd_2.cleanup()
        except:
            pass
        mc_1.join()
#        mc_2.join()
        logging.info(u"Exiting...")
