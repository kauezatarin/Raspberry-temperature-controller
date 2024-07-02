#!/usr/bin python
# -*- coding: utf-8 -*-
# sudo nano /etc/rc.local --> sudo nohup python /home/pi/tempControl/fan.py -a &

import sys
import os
import sysv_ipc
import RPi.GPIO as GPIO
import signal
import time
import optparse
import psutil
import MemoryUtils as utils
import ConfigUtils as configs
import thingspeak
import datetime
from _version import __version__

# VARIAVEIS GLOBAIS
counter = 0 #contador auxiliar
shutdown = False #killswitch
channel = None
lastUpdate = datetime.datetime.now()
pwm = None
isPwmOn = False
# transistor => onValue = 1 and offValue = 0; relay=> offValue = 0 and offValue = 1;
onValue = 1
offValue = 0

# CONFIGURACOES
fanPort = None
minFanUpTime = None
refreshRate = None
maxTemp = None
minTemp  = None
channel_id = None # id do canal thingspeak
write_key  = None # chave de escrita do canal
tskrefresh = 15 # tempo de refresh do thingspeak em segundos
isRelay = False # determina se o acionamento da fan ser? acionada utilizando reles
useSocCmd = False # determina se a temperatura sera obtida diretamente do SoC do raspberry pi, oferece uma maior precisao
usePwm = True # determina se a velocidade da ventoinha deve ser controlada via PWM
fanSpeed = 100.00 # determina a velocidade da venotinha em %

# pega a temperatura da CPU
def getTemp():
	if(useSocCmd):
		temp = getTempSoc()
	else:
		file = open("/sys/class/thermal/thermal_zone0/temp","r")
		temp = (float(file.readline()))/1000	
		file.close()
	
	return temp

# pega a temperatura utilizando o comando Soc
def getTempSoc():
	stream = os.popen("vcgencmd measure_temp")
	tempText = stream.readlines()
	
	return float(tempText[0][5:-3])

# adiciona o comando 'fan' a linha de comando
def installFan():
	file = open("/usr/local/bin/fan","w")
	file.write("sudo python3 %s $1 $2" % (os.path.abspath(__file__))) 
	file.close()
	os.chmod("/usr/local/bin/fan", 0o777)

# instala a inicializa??o automatica do processo
def installAutoInit():
	with open("/etc/rc.local","r") as fin:
		with open("/etc/rc.local.TMP","w") as fout:
			for line in fin:
				if(line != "sudo nohup python3 -u %s -a &\n" % (os.path.abspath(__file__))):
					if (line == "exit 0\n" or line == "exit 0"):
						fout.write("sudo nohup python3 -u %s -a &\n\n" % (os.path.abspath(__file__)))
						
					fout.write(line)

	#remove the original version
	os.remove('/etc/rc.local')
	
	#rename the new version
	os.rename('/etc/rc.local.TMP', '/etc/rc.local')
	
	#add the needed permissions
	os.chmod("/etc/rc.local", 0o777)

# desinstala a inicializa??o automatica do processo
def uninstallAutoInit():
	secondLine = False

	with open("/etc/rc.local","r") as fin:
		with open("/etc/rc.local.TMP","w") as fout:
			for line in fin:
				if(line != "sudo nohup python3 -u %s -a &\n" % (os.path.abspath(__file__))):						
					fout.write(line)
				elif(secondLine == True):
					if(line != "\n"):
						fout.write(line)
				else:
					secondLine = True

	#remove the original version
	os.remove('/etc/rc.local')
	
	#rename the new version
	os.rename('/etc/rc.local.TMP', '/etc/rc.local')
	
	#add the needed permissions
	os.chmod("/etc/rc.local", 0o777)

# recebe o sinal de shutdown do sistema
def stop(sig, frame):
	global shutdown
	shutdown = True

# inicializa a GPIO
def setGPIO():
	global fanPort
	global pwm
	global usePwm

#	desliga o alarme da GPIO
	GPIO.setwarnings(False)
#	seta o tipo de numeracao dos pinos	
	GPIO.setmode(GPIO.BOARD)
#	Define os pinos dos leds como saida
	GPIO.setup(fanPort, GPIO.OUT)

	if usePwm:
		pwm = GPIO.PWM(fanPort, 20)
		pwm.start(0)

#envia os dados para o Thingspeak
def updateThingspeak():
	global channel
	global lastUpdate
	global fanPort
	global tskrefresh
	
	nowTemp = (datetime.datetime.now() - datetime.timedelta(seconds=tskrefresh))
	
	if(lastUpdate < nowTemp and channel != None):
	
		if(GPIO.input(fanPort)):
			fanStat = 0
		else:
			fanStat = 1
		
		try:
			response = channel.update({1:getTemp(), 2:psutil.cpu_percent(), 3:psutil.virtual_memory().percent, 4:fanStat})
			lastUpdate = datetime.datetime.now()
		except:
			pass

#reload the configurations
def reloadConfigs():
	global fanPort
	global minFanUpTime
	global refreshRate
	global maxTemp
	global minTemp
	global channel_id
	global write_key
	global tskrefresh
	global channel
	global alwaysOn
	global isRelay
	global onValue
	global offValue
	global useSocCmd
	global usePwm
	global fanSpeed
	global pwm
	
	lastFanPort = fanPort
	lasUsePwm = usePwm
	
	(fanPort,minFanUpTime,refreshRate,maxTemp,minTemp,channel_id,write_key,tskrefresh,alwaysOn,isRelay,useSocCmd,usePwm,fanSpeed) = configs.loadConfig()
	
	if(channel_id != -1):
		channel = thingspeak.Channel(id=channel_id,write_key=write_key)
	
	if(isRelay):
		onValue = 0
		offValue = 1
		usePwm = False
	else:
		onValue = 1
		offValue = 0
	
	GPIO.cleanup(lastFanPort)
	if lasUsePwm:
		pwm.stop()

	print(fanPort,minFanUpTime,refreshRate,maxTemp,minTemp,channel_id,write_key,tskrefresh,alwaysOn,isRelay,useSocCmd,usePwm,fanSpeed)
	setGPIO()

def setFanSpeed(speed:float):
	global pwm
	global isPwmOn

	if speed == 0:
		isPwmOn = False
	else:
		isPwmOn = True

	pwm.ChangeDutyCycle(speed)

def setFanOn():
	global usePwm
	global onValue
	global fanPort
	global fanSpeed

	if usePwm:
		setFanSpeed(fanSpeed)
	else:
		GPIO.output(fanPort, onValue)

def setFanOff():
	global usePwm
	global offValue
	global fanPort

	if usePwm:
		setFanSpeed(0)
	else:
		GPIO.output(fanPort, offValue)

def isFanOn():
	global usePwm
	global fanPort
	global isPwmOn
	global onValue

	if usePwm:
		return isPwmOn
	
	return GPIO.input(fanPort) == onValue

def main():
#	instacia das variaveis globais
	global counter
	global shutdown
	global fanPort
	global minFanUpTime
	global refreshRate
	global maxTemp
	global minTemp
	global channel_id
	global write_key
	global tskrefresh
	global lastUpdate
	global channel
	global alwaysOn
	global isRelay
	global onValue
	global offValue
	global useSocCmd
	global usePwm
	global pwm
	global fanSpeed

#	Carrega as configura??es	
	(fanPort,minFanUpTime,refreshRate,maxTemp,minTemp,channel_id,write_key,tskrefresh,alwaysOn,isRelay,useSocCmd,usePwm,fanSpeed) = configs.loadConfig()
	
	if(isRelay):
		onValue = 0
		offValue = 1
		usePwm = False # Desliga o PWM para evitar problemas
	else:
		onValue = 1
		offValue = 0
	
	if(channel_id != -1):
		channel = thingspeak.Channel(id=channel_id,write_key=write_key)
	
	parser = optparse.OptionParser()
	
	parser.add_option("-v", "--version", action="store_true", dest="version",
                  help="Show the software version.", default = False)
				  
	parser.add_option("-c", "--config", action="store_true", dest="config",
                  help="Generates a default config file. WARNING: this can overwrite existing settings file.", default = False)
	
	parser.add_option("--reloadConf", action="store_true", dest="reload",
                  help="Reloads the config file to apply changes.", default = False)
	
	group = optparse.OptionGroup(parser, "Controll Options")
	
	group.add_option("-f", "--force", type="string", nargs = 1, dest="force",
                  help="force the fan to be always ON/OFF", default = "null")
	
	group.add_option("-r", "--restore", action="store_true", dest="restore",
                  help="restore the fan to auto mode", default = False)
	
	parser.add_option_group(group)
	
	group = optparse.OptionGroup(parser, "Status Options")
	  
	group.add_option("-a", "--appear", action="store_true", dest="appear",
                  help="force run even if a process is already running", default=False)
	
	group.add_option("-s", "--status", action="store_true", dest="fanstatus",
                  help="show if the fan is ON/OFF", default=False)
				  
	group.add_option("-t", "--temp", action="store_true", dest="temp",
                  help="shows the current temperature", default=False)
	
	parser.add_option_group(group)
	
	group = optparse.OptionGroup(parser, "Installation Options")
				  
	group.add_option("--install", action="store_true", dest="install",
                  help="makes 'fan' command available to bash command line", default=False)
	
	group.add_option("--uninstall", action="store_true", dest="uninstall",
                  help="uninstall 'fan' command from bash command line", default=False)
				  
	group.add_option("--autoinit", type="string", nargs = 1, dest="autoinit",
                  help="sets the auto init true/false, if true the process will start at boot up", default = "null")
				  
	parser.add_option_group(group)
	
	group = optparse.OptionGroup(parser, "Dangerous Options","Use this options with caution.")
				  
	group.add_option("--clear", action="store_true", dest="clear",
                  help="free shared memory, this may cause some stability issues, try using '--restore' after using this option.", default = False)
				  
	parser.add_option_group(group)
				  
	(options, args) = parser.parse_args()
	
#	para o processo caso o computador comece a desligar
	signal.signal(signal.SIGTERM, stop)
	
	if(options.reload):
		
		try:
			configReload = sysv_ipc.SharedMemory(19021999) #procura a memoria compartilhada
			utils.write_to_memory(configReload,"reload")
			print("The configuration was reloaded.")

		except:
			print("Fail to reload the configuration.")
				
		sys.exit()
		
	elif(options.config):
		try:
			configs.createConfig()
			print('Config file created.')
		
		except:
			print('Fail to create the config file.')
			
		sys.exit()
		
	elif(options.version):
		print("Fan version: %s" % (__version__))
		sys.exit()
		
	elif(options.clear):
		try:
			setGPIO()
			fanForce = sysv_ipc.SharedMemory(22061995)
			sysv_ipc.remove_shared_memory(fanForce.id)
			print("Memory Cleared.")
		except:
			print("There was no memory to clear.")
		
		GPIO.cleanup(fanPort)
		if usePwm:
			pwm.stop()

		print("GPIO Cleared.")
			
		sys.exit()
	
	elif(options.install):		
		try:
			installFan()
			print("'fan' was installed to the command line.")
		except:
			print("Fail to install 'fan' to the command line.")
		
		sys.exit()
		
	elif(options.uninstall):		
		try:
			os.remove("/usr/local/bin/fan")
			print("'fan' was removed from command line.")
		except:
			print("Fail to remove 'fan' from command line.")
		
		sys.exit()
		
	elif(options.autoinit == "true"):
		try:
			installAutoInit()
			print("Autoinit set to True, restart your system apply changes.")
		except:
			print("Fail to set Autoinit to True.")
		
		sys.exit()

	elif(options.autoinit == "false"):
		try:
			uninstallAutoInit()
			print("Autoinit set to False")
		except:
			print("Fail to set Autoinit to False.")
		
		sys.exit()
			
	elif(options.autoinit != "null"):
		print("Invalid parameter.")
		print("")
		print("Usage: --autoinit [true/false]")
		sys.exit()
		
#	se receber o comando -a forca abrir uma instancia nova		
	elif (options.appear):
		setGPIO()
		setFanOff()
	
	elif(options.force == "on"):
		try:
			fanForce = sysv_ipc.SharedMemory(22061995) #procura a memoria compartilhada
			utils.write_to_memory(fanForce,"on")
			setGPIO()
			setFanOn()
			print("The Fan was forced to be on.")
		except:
			print("Fail forcing fan to be on.")
		
		sys.exit()
		
	elif(options.force == "off"):
		try:
			fanForce = sysv_ipc.SharedMemory(22061995) #procura a memoria compartilhada
			utils.write_to_memory(fanForce,"off")
			setGPIO()
			setFanOff()
			print("The Fan was forced to be off. WARNING: The fan will not auto turn on anymore.")
		except:
			print("Fail forcing fan to be off.")
		
		sys.exit()
	
	elif(options.force != "null"):
		print("Invalid parameter.")
		print("")
		print("Usage: --force [on/off]")
		sys.exit()
	
	elif(options.restore):

		try:
			fanForce = sysv_ipc.SharedMemory(22061995) #procura a memoria compartilhada
			utils.write_to_memory(fanForce,"default")
			print("The Fan was restored to auto-mode.")

		except:
			print("The Fan was not able to fully restore to auto-mode. System restart is recommended.")
		
		sys.exit()
		
	elif(options.fanstatus):
		setGPIO()
		
		if(isFanOn()):
			print("The fan is active.")
		else:
			print("The fan is inactive.")
		sys.exit()
	
	elif(options.temp):
		print ("Temperature: %0.2f 'C" % (getTemp()))
		sys.exit()
		
	else:
		parser.error("fan requires an argument.")
		quit()
	
	try:
		fanForce = sysv_ipc.SharedMemory(22061995,sysv_ipc.IPC_CREX) #cria memoria compartilhada
		configReload = sysv_ipc.SharedMemory(19021999,sysv_ipc.IPC_CREX) #cria memoria compartilhada
	except:
		fanForce = sysv_ipc.SharedMemory(22061995) #cria memoria compartilhada
		configReload = sysv_ipc.SharedMemory(19021999) #cria memoria compartilhada
		
	utils.write_to_memory(fanForce,"default")
	utils.write_to_memory(configReload,"default")
	
	try:
		while (shutdown == False):
#			descobre se a fan esta ligada
			isFanStatusOn = isFanOn()
#			se receber um comando de force via console para de rodar
			if(utils.read_from_memory(fanForce) == "default"):
				if (alwaysOn):
					if(not isFanStatusOn):
						setFanOn()

					updateThingspeak()
					time.sleep(refreshRate)
					counter=0

#				se a temperatura for maior ou igual a maxTemp graus liga a fan
				elif (getTemp() >= maxTemp):
					if(not isFanStatusOn):
#						liga a fan
						setFanOn()
#						envia o status para o thingspeak
						
						k=0
						
#						aguarda o tempo minimo de execucao da fan
						while(k < minFanUpTime and shutdown == False):	
#							se receber um comando de controle de fan sai da espera
							if(utils.read_from_memory(fanForce) == "default"):
#								envia o status para o thingspeak
								updateThingspeak()
								
								if(utils.read_from_memory(configReload) == "reload"):
									reloadConfigs()
									utils.write_to_memory(configReload,"default")
									
								time.sleep(1)
								k+=1
							else:
								break
						
						counter=0
					else:
						updateThingspeak()
						
						if(utils.read_from_memory(configReload) == "reload"):
									reloadConfigs()
									utils.write_to_memory(configReload,"default")
								
						time.sleep(refreshRate)#apos o tempo minimo ele aguarda o tempo de refresh hate definido
						counter=0
						
#				se estiver no limite da transicao aguarda 2x o refresh rate para desligar a fan, assim evitando liga e desliga de fan			
				elif (counter < 2):
					counter += 1
					time.sleep(refreshRate)
				
				elif (minTemp < getTemp()):
					counter = 0
					updateThingspeak()
					
					if(utils.read_from_memory(configReload) == "reload"):
									reloadConfigs()
									utils.write_to_memory(configReload,"default")
				
				else:
					if(isFanStatusOn):
						setFanOff()
						
					updateThingspeak()
					if(utils.read_from_memory(configReload) == "reload"):
									reloadConfigs()
									utils.write_to_memory(configReload,"default")
									
					time.sleep(refreshRate)
			else:
				updateThingspeak()
				if(utils.read_from_memory(configReload) == "reload"):
									reloadConfigs()
									utils.write_to_memory(configReload,"default")
				time.sleep(refreshRate)
				
	except KeyboardInterrupt:
		pass
	
	finally:
		GPIO.cleanup(fanPort)
		if usePwm:
			pwm.stop()

		sysv_ipc.remove_shared_memory(fanForce.id)
		sysv_ipc.remove_shared_memory(configReload.id)
		
#chama a funcao principal caso o scrips seja chamado via console
if __name__ == "__main__":

	if sys.version_info[0] < 3:
		print ("This program needs python 3.x or higher")
		sys.exit()
	
	user = os.getenv("SUDO_USER")
	
	if user is None:
		print ("This program needs 'sudo'")
		sys.exit()
	else:
		try:
			main()
		except Exception as e:
			print(e)
