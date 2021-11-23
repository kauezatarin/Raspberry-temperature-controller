# -*- coding: utf-8 -*-
import configparser as ConfigParser
import os

#CONFIGURACOES PRADRAO
fanPort = 7 #porta onde o rele esta conectado
minFanUpTime = 5 * 60 #tempo minimo que a fan deve ficar ligada em segundos
refreshRate = 3 #tempo de monitoramento da temperatura em segundos
maxTemp = 55.00 #temperatura em que a fan ira ligar
minTemp = 45.00 #temperatura minima em que a fan ira desligar
channel_id = -1 # id do canal thingspeak
write_key  = -1 # chave de escrita do canal
tskrefresh = 15 # tempo de atualização do thingspeak
isRelay = False # determina se o acionamento da fan será acionada utilizando reles
useSocCmd = False # determina se a temperatura sera obtida diretamente do SoC do raspberry pi, oferece uma maior precisao

def createConfig():
	
	config = ConfigParser.RawConfigParser(allow_no_value=True)
	
#	Cria o arquivo de configuração
	config.add_section('FAN')
	config.add_section('TSK')
	
	config.set('FAN', '#If fan is auto starting, reboot your system')
	config.set('FAN', '#to apply changes to the configuration file.')
	config.set('FAN', 'fanPort', '7')
	config.set('FAN', 'minFanUpTime', '300')
	config.set('FAN', 'refreshRate', '3')
	config.set('FAN', '#Turning tis option to "True" offers a better reading precision, but may not be compatible with all devices.')
	config.set('FAN', 'useSocCmd', 'False')
	config.set('FAN', 'maxTemp', '55.00')
	config.set('FAN', 'minTemp', '45.00')
	config.set('FAN', '#If you use an relay to activate your fan, turn tis option to "True".')
	config.set('FAN', 'isRelay', 'False')
	
	config.set('TSK', '#Put here your Thingspeak channel infos.')
	config.set('TSK', 'channel_id', '-1')
	config.set('TSK', 'write_key', '-1')
	config.set('TSK', 'tskrefresh', '15')
	
	filepath = "%s/fanConf.cfg" % (os.path.dirname(os.path.abspath(__file__)))
	
	with open(filepath, 'w') as configfile:
		config.write(configfile)
	
	return
	
def loadConfig():
#(fanPort,minFanUpTime,refreshRate,maxTemp,minTemp,channel_id,write_key,tskrefresh,isRelay,useSocCmd) = configs.loadConfig()

	global fanPort
	global minFanUpTime
	global refreshRate
	global maxTemp
	global minTemp
	global channel_id
	global write_key
	global tskrefresh
	global isRelay
	global useSocCmd
	
	try:
		filepath = "%s/fanConf.cfg" % (os.path.dirname(os.path.abspath(__file__)))
		
		config = ConfigParser.RawConfigParser(allow_no_value=True)
		config.read(filepath)
		
		fanPort = config.getint('FAN','fanPort')
		minFanUpTime = config.getint('FAN','minFanUpTime')
		refreshRate = config.getint('FAN','refreshRate')
		maxTemp = config.getfloat('FAN','maxTemp')
		minTemp = config.getfloat('FAN','minTemp')
		isRelay = config.getboolean('FAN','isRelay')
		useSocCmd = config.getboolean('FAN','useSocCmd')
		
		channel_id = config.getint('TSK','channel_id')
		write_key = config.get('TSK', 'write_key')
		tskrefresh = config.getint('TSK', 'tskrefresh')
	
	except:
		pass
	
	return (fanPort,minFanUpTime,refreshRate,maxTemp,minTemp,channel_id,write_key,tskrefresh,isRelay,useSocCmd)
	
def printConfigs():
	
	print(loadConfig())

	return