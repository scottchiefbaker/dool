### Author: Dag Wieers <dag@wieers.com>

class dool_plugin(dool):
    def __init__(self):
        self.name = 'thermal'
        self.type = 'd'
        self.width = 3
        self.scale = 20

        selection = os.getenv('DOOL_THERMAL_ZONES')
        thermal_dir = '/sys/devices/virtual/thermal/'
        if os.path.exists(thermal_dir):
            zones = {}
            for zone in os.listdir(thermal_dir):
                match = re.fullmatch(r'thermal_zone([0-9]+)', zone)
                if match:
                    zones[int(match.group(1))] = zone

            selected_ids = set(zones)
            if selection:
                values = selection.split(',')
                if any(not re.fullmatch(r'[0-9]+', value) for value in values):
                    raise Exception('DOOL_THERMAL_ZONES needs comma-separated thermal zone IDs')
                selected_ids = {int(value) for value in values}
                missing_ids = selected_ids.difference(zones)
                if missing_ids:
                    missing = ', '.join(str(zone_id) for zone_id in sorted(missing_ids))
                    raise Exception('unknown thermal zone: ' + missing)

            zone_ids = sorted(selected_ids)
            self.vars = [zones[zone_id] for zone_id in zone_ids]
            self.nick = ['tz%d' % zone_id for zone_id in zone_ids]
            self.width = max([self.width] + [len(label) for label in self.nick])

        elif selection:
            raise Exception('DOOL_THERMAL_ZONES requires Linux sysfs thermal zones')

        elif os.path.exists('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'):
            self.vars = os.listdir('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/')
            self.nick = []
            for name in self.vars:
                self.nick.append(name.lower())

        elif os.path.exists('/proc/acpi/ibm/thermal'):
            self.namelist = ['cpu', 'pci', 'hdd', 'cpu', 'ba0', 'unk', 'ba1', 'unk']
            self.nick = []
            for line in dopen('/proc/acpi/ibm/thermal'):
                l = line.split()
                for i, name in enumerate(self.namelist):
                    if int(l[i+1]) > 0:
                        self.nick.append(name)
            self.vars = self.nick

        elif os.path.exists('/proc/acpi/thermal_zone/'):
            self.vars = os.listdir('/proc/acpi/thermal_zone/')
#           self.nick = [name.lower() for name in self.vars]
            self.nick = []
            for name in self.vars:
                self.nick.append(name.lower())

        else:
            raise Exception('Needs kernel thermal, ACPI or IBM-ACPI support')

    def check(self):
        if not os.path.exists('/proc/acpi/ibm/thermal') and \
           not os.path.exists('/proc/acpi/thermal_zone/') and \
           not os.path.exists('/sys/devices/virtual/thermal/') and \
           not os.path.exists('/sys/bus/acpi/devices/LNXTHERM:00/thermal_zone/'):
            raise Exception('Needs kernel thermal, ACPI or IBM-ACPI support')

    def extract(self):
        if os.path.exists('/sys/devices/virtual/thermal/'):
            for zone in self.vars:
                for line in dopen('/sys/devices/virtual/thermal/'+zone+'/temp').readlines():
                    l = line.split()
                    self.val[zone] = int(l[0])
        elif os.path.exists('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'):
            for zone in self.vars:
                if os.path.isdir('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'+zone) == False:
                    for line in dopen('/sys/bus/acpi/devices/LNXTHERM:01/thermal_zone/'+zone).readlines():
                        l = line.split()
                        if l[0].isdigit() == True:
                            self.val[zone] = int(l[0])
                        else:
                            self.val[zone] = 0
        elif os.path.exists('/proc/acpi/ibm/thermal'):
            for line in dopen('/proc/acpi/ibm/thermal'):
                l = line.split()
                for i, name in enumerate(self.namelist):
                    if int(l[i+1]) > 0:
                        self.val[name] = int(l[i+1])
        elif os.path.exists('/proc/acpi/thermal_zone/'):
            for zone in self.vars:
                for line in dopen('/proc/acpi/thermal_zone/'+zone+'/temperature').readlines():
                    l = line.split()
                    self.val[zone] = int(l[1])

# vim:ts=4:sw=4:et
