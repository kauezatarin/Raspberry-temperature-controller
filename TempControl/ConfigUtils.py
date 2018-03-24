# -*- coding: utf-8 -*-
import ConfigParser
import os

#CONFIGURACOES PRADRAO
fanPort = 7 #porta onde o rele esta conectado
minFanUpTime = 5 * 60 #tempo minimo que a fan deve ficar ligada em segundos
refreshRate = 3 #tempo de monitoramento da temperatura em segundos
maxTemp = 55.00 #temperatura em que a fan ira ligar
minTemp = 45.00 #temperatura minima em que a fan ira desligar

def createConfig():
	
	config = ConfigParser.RawConfigParser(allow_no_value=True)
	
#	Cria o arquivo de configuração
	config.add_section('FAN')
	
	config.set('FAN', '#If fan is auto starting, reboot your system')
	config.set('FAN', '#to apply changes to the configuration file.')
	config.set('FAN', 'fanPort', '7')
	config.set('FAN', 'minFanUpTime', '300')
	config.set('FAN', 'refreshRate', '3')
	config.set('FAN', 'maxTemp', '55.00')
	config.set('FAN', 'minTemp', '45.00')
	
	filepath = "%s/fanConf.cfg" % (os.path.dirname(os.path.abspath(__file__)))
	
	with open(filepath, 'wb') as configfile:
		config.write(configfile)
	
	return
	
def loadConfig():
#(fanPort,minFanUpTime,refreshRate,maxTemp,minTemp) = configs.loadConfig()

	global fanPort
	global minFanUpTime
	global refreshRate
	global maxTemp
	global minTemp
	
	try:
		filepath = "%s/fanConf.cfg" % (os.path.dirname(os.path.abspath(__file__)))
		
		config = ConfigParser.RawConfigParser(allow_no_value=True)
		config.read(filepath)
		
		fanPort = config.getint('FAN','fanPort')
		minFanUpTime = config.getint('FAN','minFanUpTime')
		refreshRate = config.getint('FAN','refreshRate')
		maxTemp = config.getfloat('FAN','maxTemp')
		minTemp = config.getfloat('FAN','minTemp')
	
	except:
		pass
	
	return (fanPort,minFanUpTime,refreshRate,maxTemp,minTemp)
	
def printConfigs():
	
	print(loadConfig())

	return