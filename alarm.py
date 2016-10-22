#!/usr/bin/python

import yaml, time, os, sys, subprocess
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import SerialDevice
from me.maurer.alarmdecoder.zonemapper import ZoneMapper
from twilio.rest import TwilioRestClient
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def main():
    global deactivate

    # Number map of different Zones
    zm = ZoneMapper('./zone-map.yml')

    # used to toggle disarm message send
    deactivate = False

    # Load Account settings
    with open("./settings.yml") as filestream:
        try:
            settings = yaml.load(filestream)
        except yaml.YAMLError as exc:
            print(exc)



    class DisarmEventHandler(FileSystemEventHandler):
        def on_modified(self, event):
            global deactivate
            # Only deactivate when file matches
            if self.find_file(event.src_path) == settings["dir_watch_file"]:
                #Find last line in file
                line = subprocess.check_output(['tail', '-1', event.src_path])
                # if you find the passcode in the line
                if "Body="+settings["alarm_pass"] in line:
                    print("Disarming")
                    deactivate = True

        def find_file(self, file_path):
            pathArr = file_path.split("/")
            return pathArr[len(pathArr)-1]

            



    def handle_on_arm(device):
        send_sms_message("Alarm Armed")


    def handle_on_disarm(device):
        send_sms_message("Alarm Disarmed")



    def handle_on_fire(device, status):
        send_sms_message("Alarm is going off! FIRE - " + str(status))


    def handle_on_panic(device, status):
        send_sms_message("Alarm is going off! PANIC - " + str(status))



    def handle_on_alarm(device, zone):
        zone_name = zm.get_zone_name(int(zone))
        send_sms_message("Alarm is going off for the " + zone_name + "!")


    def handle_on_alarm_restored(device, zone):
        zone_name = zm.get_zone_name(int(zone))
        send_sms_message("Alarm is restored for the " + zone_name)



    def handle_on_zone_fault(device, zone):
        zone_name = zm.get_zone_name(zone)
        if not zm.is_zone_whitelist(zone):
            send_sms_message("Zone Fault - " + zone_name)


    def handle_zone_restore(device, zone):
        zone_name = zm.get_zone_name(zone)
        if not zm.is_zone_whitelist(zone):
            send_sms_message("Zone Restored - " + zone_name)



    def send_sms_message(msg):
        client = TwilioRestClient(settings["twilio_account_sid"], settings["twilio_auth_token"])
        for numb in settings["twilio_numbers_to_text"]:
            client.messages.create(to=numb, from_=settings["twilio_number_from"], body=msg)



    event_handler = DisarmEventHandler()
    observer = Observer()
    observer.schedule(event_handler, settings["dir_watch_path"], recursive=False)
    observer.start()



    try:
        # Retrieve the first USB device /dev/tty.usbserial-DJ009GBR
        serialDevice = SerialDevice(interface=settings["device"])
        device = AlarmDecoder(serialDevice)

        device.on_zone_fault += handle_on_zone_fault
        device.on_zone_restore += handle_zone_restore
        device.on_arm += handle_on_arm
        device.on_disarm += handle_on_disarm
        device.on_alarm += handle_on_alarm
        device.on_alarm_restored += handle_on_alarm_restored
        device.on_fire += handle_on_fire
        device.on_panic += handle_on_panic

        with device.open(baudrate=115200):
            while True:
                if deactivate:
                    deactivate = False
                    print "Deactivated!"
                    device.send(settings["alarm_pass"] + "1")

                time.sleep(1)


    except Exception, ex:
        print 'Exception:', ex


        




if __name__ == '__main__':
    main()
