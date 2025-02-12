#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import argparse
import ipaddress
from libnmap.parser import NmapParser


def err(s):
  print("[!] " + s, file=sys.stderr)
  sys.exit(1)

class c:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  DIM = '\033[2m'
  UNDERLINE = '\033[4m'

def removeColors(s):
  for colorName in dir(c):
    if not '_' in colorName:
      color = getattr(c, colorName)
      s = s.replace(color, '')
  return s


theList = []
portIgnoreList = []
verbose = 0
listThe = []
showTargets = []


def showThisTarget(t):
  if showTargets and len(showTargets) > 0:
    for target in showTargets:
      if t == target:
        return True
    return False
  return True 


def parseFile(filename):
  def isRange(maybeRange):
    if "-" in maybeRange:
      return True
    else:
      return False

  def portShouldBeIgnored(port):
    return portIgnoreList and port[0] in portIgnoreList

  def hasSeenPort(port):
    for entry in theList:
      if entry[0] == port:
        return True
    return False

  def appendAlreadySeenPort(port, newHost):
    for entry in theList:
      if entry[0] == port:
        for host in entry[1]:
          if host[0] == newHost.address:
            host[1].append(newHost)
            return
        entry[1].append((newHost.address, [newHost]))

  def addNewPort(port, host):
    newEntry = (port, [(host.address, [host])])
    theList.append(newEntry)

  nmap_report = NmapParser.parse_fromfile(filename)
  for host in nmap_report.hosts:
    if showThisTarget(host.address): 
      ports = host.get_open_ports()

      if ports:
        for port in ports:
          if not portShouldBeIgnored(port):
            if hasSeenPort(port):
              appendAlreadySeenPort(port, host)
            else:
              addNewPort(port, host)

  # command stuff
  def hasSeenHost(host):
    for entry in listThe:
      if entry[0] == host:
        return True
    return False
  
  def hostHasPort(host, p):
    for entry in listThe:
      if entry[0] == host:
        for port in entry[1]:
          if port == p:
            return True
    return False

  def appendPort(host, p):
    for entry in listThe:
      if entry[0] == host:
        entry[1].append(p)

  def appendHost(host):
    listThe.append((host,[]))

  for host in nmap_report.hosts:
    if showThisTarget(host.address): 
      ports = host.get_open_ports()
      if len(ports) > 0:
        for port in ports:
          if not hostHasPort(host.address, port):
            if not hasSeenHost(host.address):
              appendHost(host.address)
            appendPort(host.address, port)




def pprint_tree(node, file=None, _prefix="", _last=True, _first=False, something=False):
  if not node:
    return
  if (not args.targets_only) and (not args.command):
    if not node.value:
      node.value = ''

    printIt = False 
    if '\n' in node.value:
      if node.value[len(node.value) - 1] == '\n':
        node.value = node.value[:-1]
      lines = node.value.split('\n')
      new = ''
      for index, line in enumerate(lines):
        if index == 0:
          new += _prefix + c.DIM + "├─ " + c.ENDC + line + '\n'
        elif (index+1) < len(lines):
          new += _prefix + c.DIM + "├  " + c.ENDC + line + '\n'
        else:
          print(new, file=file, end='')
          new += _prefix + c.DIM + "├  " + c.ENDC + line + '\n'
          node.value = line
          printIt = True 

    if _first:
      print(_prefix, node.value, sep="", file=file)
    else:
      
      if not node.value or len(node.value) == 0:
        print(_prefix + c.DIM, "└──" if _last else "├──", '┐' + c.ENDC, sep="", file=file)
      else:

        if printIt:
          print(_prefix + c.DIM, "└  " if _last else "├  ", c.ENDC + node.value, sep="", file=file)
        else:
          print(_prefix + c.DIM, "└─ " if _last else "├─ ", c.ENDC + node.value, sep="", file=file)

      _prefix += "    " if _last else c.DIM + "│   " + c.ENDC

    for i, child in enumerate(node.children):
        _last = i == (len(node.children) - 1)
        if i == 0:
          something = True
        else:
          something = False
        pprint_tree(child, file, _prefix, _last, False, something)

    if _last and _first:
      pass
      #print('')



class Node:
    def __init__(self, value=None, children=None):
        if children is None:
            children = []
        self.value, self.children = value, children
'''
exampleTree = Node("Root", [
    Node("Node 1", [
        Node("Node 1.1", [
            Node("Node 1.1.1", [
                Node("Node 1.1.1.1"),
                Node("Node 1.1.1.2"),
            ]),
        ]),
        Node("Node 1.2"),
        Node("Node 1.3", [
            Node("Node 1.3.1")
        ]),
        Node("Node 1.4", [
            Node("Node 1.4.1"),
            Node("Node 1.4.2", [
                Node("Node 1.4.2.1"),
                Node("Node 1.4.2.2", [
                    Node("Node 1.4.2.2.1"),
                ]),
            ]),
        ]),
    ]),
    Node("Node 2", [
        Node("Node 2.1"),
        Node("Node 2.2"),
    ]),
    Node("Node 3"),
])
'''

def printArray(arr):
  def r(arr, tree=None):
    if not tree:
      tree = Node()


    if str(type(arr)).split("'")[1] == 'libnmap.objects.host.NmapHost':
      service = arr.get_service(portNumber, portProtocol)
      if service:
        for scriptResult in service.scripts_results:
          scriptName = scriptResult['id']
          scriptOutput = scriptResult['output']
          tree.children.append(Node(scriptName + ' :: ' + scriptOutput))
      return tree

    for a in arr:
      if isinstance(a, list) or isinstance(a, tuple): 
        sub = r(a, Node(str(type(a)).split("'")[1] + ' length: ' + str(len(a))))
        tree.children.append(sub)
      elif str(type(a)).split("'")[1] == 'libnmap.objects.host.NmapHost':
        sub = r(a, Node(str(type(a)).split("'")[1]))
        tree.children.append(sub)
      else:
       tree.children.append(Node(str(type(a)).split("'")[1] + ': ' + str(a)))

    return tree
  t = r(arr)
  pprint_tree(t, None, '', True, True, False)


     

tree = None
def printI(ind, string):
  if (not args.targets_only) and (not args.command):
    ind = ind - 1 
    o = tree
    for a in range(0,ind):
      o = o.children[len(o.children) - 1]
    o.children.append(Node(string))

def parsePorts(s):
  if not s:
    return None

  ports = []

  for spart in s:
    for part in spart.split(','):
      if part.isdigit():
        if part not in ports:
          ports.append(int(part))
      else:
        if '-' in part:
          ps = part.split('-')
          if len(ps) != 2:
            err('your port range is messed up! Just look at this: ' + str(s))
          ports = ports + range(int(ps[0]), int(ps[1]) + 1)

  return sorted(ports)

def parseTargets(s):
  if not s:
    return None

  targets = []

  for entry in s:
    if '-' in entry:
      err('your target specification is not supported. Only comma seperated entries and CIDR notation is allowed.' )

    parts = entry.split(',')

    for part in parts:
      if '/' in part:
        ips = ipaddress.IPv4Network(part, strict=False)
        for ip in ips:
          targets.append(str(ip))
      else:
        targets.append(part)

  return targets

def main():  
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--verbose", help="Increase verbosity - can be used twice", required=False, default=0, action='count')
  parser.add_argument("-t", "--targets", help="Only show specific targets", required=False, action='append')
  parser.add_argument("-p", "--ports", help="Only show specific ports", required=False, action='append')
  parser.add_argument("-ip", "--ignore-ports", help="silence a specific port (protocol agnostic) from output - can be used multiple times", required=False, action='append')

  maxDifferentResults = 3
  parser.add_argument("-m", "--max-different-results", help="maximum amount of different scan results to show (when multiple scan results have different opinions about the results. Default is " + str(maxDifferentResults) + ")", required=False, type=int)
  parser.add_argument("-to", "--targets-only", help="hide everything but targets", required=False, action='store_true', default=False)
  parser.add_argument("-ht", "--http-truncate-header", help="truncate HTTP headers. Comman separated", required=False)
  parser.add_argument("-c", "--command", help="print basic commands needed to rescan", required=False, action='store_true', default=False)
  parser.add_argument("-cf", "--command-flags", help=" nmap arguments to add to nmap commands. '@@' will be replaced by host address", required=False, action='store', type=str)
  parser.add_argument("files", metavar='<nmap XML file>', nargs='+', help='nmap XML file renerated with -oX or -oA of nmap')
  args = parser.parse_args()

  if args.ports and args.ignore_ports:
    err('can\'t both use -p and -ip pick one or the other!')

  if args.command_flags and not args.command:
    args.command = True

  showTargets = parseTargets(args.targets)
  showPorts = parsePorts(args.ports)
  portIgnoreList = parsePorts(args.ignore_ports)

  truncateHeaders = []

  if args.http_truncate_header:
    if ',' in args.http_truncate_header:
      truncateHeaders = args.http_truncate_header.split(',')
    else:
      truncateHeaders.append(args.http_truncate_header)

  if args.max_different_results:
      maxDifferentResults = args.max_different_results

  targets = []
  def addTarget(target):
    for t in targets:
      if targets == t:
        return
    targets.append(target)

  if args.targets_only or args.command:
    args.verbose = 1


  # parse
  for entry in args.files:
    try:
      parseFile(entry)
    except:
      print(entry + " could not be parsed. Skipped.", file=sys.stderr)
      pass

  # sort
  theList = sorted(theList, key=lambda tup: tup[0])
  listThe = sorted(listThe, key=lambda tup: tup[0])

  # print
  first = True
  for entry in theList:

    portNumber = entry[0][0]
    portProtocol = entry[0][1]

    if args.ports and portNumber not in showPorts:
      continue


    if not first:
      pprint_tree(tree, None, '', True, True)
    tree = Node(str(portNumber) + '/' + portProtocol, [])
    first = False

    if args.verbose > 0:
      for host in entry[1]:
        address = host[0]

        if len(host) >= 2:
          if host[1][0].hostnames:
            if len(host[1][0].hostnames) > 0:
              if args.verbose > 1:
                address = host[1][0].hostnames[0] + ' (' + address + ')'
              else:
                address = host[1][0].hostnames[0]

        addTarget(address)

        def addText(newText, texts):
          for text in texts:
            if text[1] == newText:
              text[0] += 1
              return
          texts.append([1, newText])

        serviceTexts = [] 
        bannerTexts = []
        for nmapResult in host[1]:
          service = nmapResult.get_service(portNumber, portProtocol)
          if not (not service.service and args.only_identified):


            if len(service.banner) < 1:
              addText(service.service, serviceTexts)
            else:
              addText(service.banner, bannerTexts)

        if args.verbose > 1:
          if len(bannerTexts) > 1:
            if len(bannerTexts) > maxDifferentResults:
              printI(1, address + c.WARNING + ' more than ' + str(maxDifferentResults) + ' inconsistent service detection results:' + c.ENDC)

              highestCount = 0
              theOnes = []
              for text in bannerTexts:
                textCount = text[0]
                textText = text[1]

                if textCount > highestCount:
                  theOnes = []
                  theOnes.append(textText)
                elif textCount == highestCount:
                  if len(theOnes) < maxDifferentResults:
                    theOnes.append(textText)

              for one in theOnes:
                t = text[1].replace("\n", c.ENDC + "\n" + c.WARNING) + c.ENDC
                printI(2, str(text[0]) + ' result(s): ' + t)

            else:
              printI(1, address + c.WARNING + ' inconsistent version scan results:' + c.ENDC)
              for text in bannerTexts:
                t = c.WARNING + text[1].replace("\n", c.ENDC + "\n" + c.WARNING) + c.ENDC
                printI(2, str(text[0]) + ' result(s): ' + t)
          else:
            if len(bannerTexts) == 1:
              if service.service:
                printI(1, address + ' ' + service.service + ' ' + bannerTexts[0][1])
              else:
                printI(1, address + ' ' + bannerTexts[0][1])
            else:
              if len(serviceTexts) > 1:

                if len(serviceTexts) > maxDifferentResults:
                  printI(1, address + c.WARNING + ' more than ' + str(maxDifferentResults) + ' inconsistent service detection results:' + c.ENDC)

                  highestCount = 0
                  theOnes = []
                  for text in serviceTexts:
                    textCount = text[0]
                    textText = text[1]

                    if textCount > highestCount:
                      theOnes = []
                      theOnes.append(textText)
                    elif textCount == highestCount:
                      if len(theOnes) < maxDifferentResults:
                        theOnes.append(textText)

                  for one in theOnes:
                    t = c.WARNING +text[1].replace("\n", c.ENDC + "\n" + c.WARNING) + c.ENDC
                    printI(2, str(text[0]) + ' result(s): ' + t)
                else:
                  printI(1, address + c.WARNING + ' inconsistent service detection:' + c.ENDC)
                  for text in serviceTexts:
                    t = c.WARNING + text[1].replace("\n", c.ENDC + "\n" + c.WARNING) + c.ENDC
                    printI(2, str(text[0]) + ' result(s): ' + t)
              else:
                if len(serviceTexts) == 1:
                  #printI(1, address + ' ' + serviceTexts[0][1])
                  t = serviceTexts[0][1]
                  if t == 'tcpwrapped':
                    printI(1, address + ' ' + c.DIM + t + c.ENDC)
                  else:
                    printI(1, address + ' ' + serviceTexts[0][1])
                else:
                  printI(1, address)
                            
        else:
          printI(1, address)


        def buildList(liist):
          def ensureEntry(scriptName, scriptOutput, liist):
            for entry in liist:
              entryName = entry[0]
              entryResultsList = entry[1]

              if entryName == scriptName:
                for result in entryResultsList:
                  resultCount = result[0]
                  resultOutput = result[1]

                  if resultOutput == scriptOutput:
                    # list already contains this result
                    resultCount += 1
                    return

                entryResultsList.append([1, scriptOutput])
                return

            liist.append([scriptName, [[1,scriptOutput]]])

          global host

          for nmapResult in host[1]:
            service = nmapResult.get_service(portNumber, portProtocol)
            if service:
              for scriptResult in service.scripts_results:
                scriptName = c.DIM + scriptResult['id'] + ':' + c.ENDC
                scriptOutput = scriptResult['output']

                truncated = c.DIM + '[..]' + c.ENDC
                def hideCerts(s):
                  start = '-----BEGIN CERTIFICATE-----'
                  end = '-----END CERTIFICATE-----'
                  if start in s and end in s:
                    pre = s.split(start)[0]
                    post = s.split(end)[1]

                    return pre + start + '\n' + truncated + '\n' + end + post
                  return s

                def hideHeader(s,cc):
                  n = ''
                  cc = cc + ': '

                  parts = s.split(cc)
                  n = n + parts[0]
                  stuff = None
                  for i in range(1, len(parts)):
                    lines = parts[i].split('\n')
                    
                    if cc == 'Set-Cookie: ':
                      cookie = lines[0]

                      if '=' in cookie:
                        cookie = cookie.split('=')
                        cookieName = cookie[0]
                        del cookie[0]
                        rest = '='.join(cookie)

                        if ';' in rest:
                          r = rest.split(';')
                          del r[0]
                          r = ';'.join(r)

                          stuff = True
                          lines[0] = cookieName + '=' + truncated + ';' + r
                      
                    if stuff:
                      n = n + cc + '\n'.join(lines)
                    else:
                      del lines[0]
                      n = n + cc + truncated + '\n' + '\n'.join(lines)

                  return n


                if args.verbose < 4:
                  global truncateHeaders
                  for header in truncateHeaders:
                    scriptOutput = hideHeader(scriptOutput, header)

                  scriptOutput = hideHeader(scriptOutput, 'Set-Cookie')
                  scriptOutput = hideHeader(scriptOutput, 'Date')
                  scriptOutput = hideHeader(scriptOutput, 'X-FB-Debug')
                  scriptOutput = hideCerts(scriptOutput)

                ensureEntry(scriptName, scriptOutput, liist)

        def printList(liist):
          for entry in liist:
            entryName = entry[0]
            entryResultsList = entry[1]
            

            if len(entryResultsList) > maxDifferentResults:

              printI(2, entryName + c.WARNING + ' more than ' + str(maxDifferentResults) + ' script scan results are inconsistent' + c.ENDC)

              highestCount = 0
              theOnes = []
              for result in entryResultsList:
                resultCount = result[0]
                resultOutput = result[1]
                resultOutput = removeColors(resultOutput)
                resultOutput = c.WARNING + resultOutput.replace("\n", c.ENDC + "\n" + c.WARNING) + c.ENDC

                if resultCount > highestCount:
                  highestCount = resultCount
                  theOnes = []
                  theOnes.append(resultOutput)
                elif resultCount == highestCount:
                  theOnes.append(resultOutput)

              if len(theOnes) > 1:
                printI(3, str(len(theOnes)) +' results were the most common:')

                for index, value in enumerate(theOnes):
                  if index >= maxDifferentResults:
                    break

                  printI(4, str(highestCount) + ' result(s): ' + value)
              
            elif len(entryResultsList) > 1:
              printI(2, entryName + ' ' + c.WARNING + 'inconsistent script scan results' + c.ENDC)
              for result in entryResultsList:
                resultCount = result[0]
                resultOutput = result[1]
                resultOutput = removeColors(resultOutput)
                resultOutput = resultOutput.replace("\n", c.ENDC + "\n" + c.WARNING) + c.ENDC
                printI(3, str(resultCount) + ' result(s): ' + resultOutput)

            elif len(entryResultsList) == 1:
              printI(2, entryName + ' ' + entryResultsList[0][1])

        if args.verbose > 2: 
          liist = []
          buildList(liist)
          printList(liist)


  pprint_tree(tree, None, '', True, True)

  if args.targets_only:
    for target in targets:
      print(target)

  if args.command:
    for entry in listThe:
      tcpList = []
      udpList = []

      for port in entry[1]:
        if port[1] == 'tcp':
          tcpList.append(port[0])
        if port[1] == 'udp':
          udpList.append(port[0])
      
      s = ''
      if len(tcpList) > 0:
        s += ' -sS'
      if len(udpList) > 0:
        s += ' -sU'

      s += ' -p'
      if len(tcpList) > 0:
        first = True
        for port in tcpList:
          if first:
            first = False
            s += 'T:'
          else:
            s += ','
          s += str(port)

      if len(udpList) > 0:
        if len(tcpList) > 0:
          s += ','
        first = True
        for port in udpList:
          if first:
            first = False
            s += 'U:'
          else:
            s += ','
          s += str(port)

      s = 'sudo nmap ' + entry[0] + s 
      if args.command_flags:
        s += ' ' + args.command_flags
        s = s.replace('@@', entry[0])

      print(s)
