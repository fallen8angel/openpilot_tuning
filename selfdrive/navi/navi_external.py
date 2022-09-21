#!/usr/bin/env python3
import cereal.messaging as messaging
from common.params import Params

import zmq

# OPKR, this is for getting navi data from external device.
# 20Hz
class ENavi():
  def __init__(self):
    self.navi_selection = int(Params().get("OPKRNaviSelect", encoding="utf8"))
    self.spd_limit = 0
    self.safety_distance = 0
    self.sign_type = 0
    self.turn_info = 0
    self.turn_distance = 0

    self.ip_add = ""
    self.ip_bind = False
    self.ip_check_timer = 0
  
    self.check_connection = False
    self.check_timer = 0

  def bind_ip(self):
    if not self.ip_bind:
      self.ip_check_timer += 1
      if self.ip_check_timer > 25:
        self.ip_check_timer = 0
        self.ip_add = Params().get("ExternalDeviceIPNow", encoding="utf8")
        if self.ip_add is not None:
          self.ip_bind = True

  def navi_data(self):
    if self.ip_bind:
      self.spd_limit = 0
      self.safety_distance = 0
      self.sign_type = 0
      self.turn_info = 0
      self.turn_distance = 0

      context = zmq.Context()
      socket = context.socket(zmq.SUB)
      try:
        socket.connect("tcp://" + str(self.ip_add) + ":5555")
      except:
        socket.connect("tcp://127.0.0.1:5555")
        pass
      socket.subscribe("")

      message = str(socket.recv(), 'utf-8')

      for line in message.split('\n'):
        if "opkrspdlimit" in line:
          arr = line.split('opkrspdlimit: ')
          self.spd_limit = arr[1]
          self.check_connection = True
        else:
          self.check_timer += 1
          if self.check_timer > 25:
            self.check_timer = 0
            self.check_connection = False
        if "opkrspddist" in line:
          arr = line.split('opkrspddist: ')
          self.safety_distance = arr[1]
        if "opkrsigntype" in line:
          arr = line.split('opkrsigntype: ')
          self.sign_type = arr[1]
        if "opkrturninfo" in line:
          arr = line.split('opkrturninfo: ')
          self.turn_info = arr[1]
        if "opkrdistancetoturn" in line:
          arr = line.split('opkrdistancetoturn: ')
          self.turn_distance = arr[1]

  def publish(self, pm):
    if self.navi_selection != 3:
      return

    navi_msg = messaging.new_message('liveENaviData')
    navi_msg.liveENaviData.speedLimit = int(self.spd_limit)
    navi_msg.liveENaviData.safetyDistance = float(self.safety_distance)
    navi_msg.liveENaviData.safetySign = int(self.sign_type)
    navi_msg.liveENaviData.turnInfo = int(self.turn_info)
    navi_msg.liveENaviData.distanceToTurn = float(self.turn_distance)
    navi_msg.liveENaviData.connectionAlive = bool(self.check_connection)
    pm.send('liveENaviData', navi_msg)

def navid_thread(pm=None):
  navid = ENavi()

  if pm is None:
    pm = messaging.PubMaster(['liveENaviData'])

  while True:
    navid.bind_ip()
    navid.navi_data()
    navid.publish(pm)


def main(pm=None):
  navid_thread(pm)


if __name__ == "__main__":
  main()
