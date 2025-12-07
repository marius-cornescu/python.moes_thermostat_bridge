# TinyTuya ThermostatDevice Example
# -*- coding: utf-8 -*-
"""
 Example script using the community-contributed Python module for Tuya WiFi smart thermostats

 Author: uzlonewolf (https://github.com/uzlonewolf)
 For more information see https://github.com/jasonacox/tinytuya

"""
import logging

def execute_example_code(thermo, data, iteration: int, show_all_attribs: bool):
    if show_all_attribs:
        show_all_attribs = False
        logging.getLogger(__name__).debug(f'All attribs:{dict(thermo)}')
        logging.getLogger(__name__).debug('==============================')

        # if tstatdev.isSingleSetpoint():
        #     logging.getLogger(__name__).info('Single Setpoint (Mode is "cool" or "heat")')
        # else:
        #     logging.getLogger(__name__).info('Dual Setpoints (Mode is "auto")')

        logging.getLogger(__name__).debug(f'Temperature is in [{'°' + thermo.getCF().upper()}]')

        # hexadecimal dump of all sensors in a DPS:
        for s in thermo.sensorlists:
            logging.getLogger(__name__).debug( f'DPS {s.dps} = {str(s)}' )

        ## Base64 dump of all sensors in a DPS:
        # for s in tstatdev.sensorlists:
        #    logging.getLogger(__name__).info( 'DPS', s.dps, '=', s.b64() )

        ## display info for every sensor:
        # for s in tstatdev.sensors():
        #     ## logging.getLogger(__name__).info the DPS containing the sensor, the sensor ID, name, and temperature
        #     logging.getLogger(__name__).info(
        #         f'Sensor: DPS:{s.parent_sensorlist.dps} ID:{s.id} Name:"{s.name}" Temperature:{s.temperature}')
        #
        #     ## dump all data as a hexadecimal string
        #     logging.getLogger(__name__).info(str(s))

        logging.getLogger(__name__).info('DONE: show_all_attribs')


    if 'dps' in data and len(data['dps']) > 0:
        logging.getLogger(__name__).info(f'>> DPS:{data["dps"]}')
        # for c in data['changed']:
        #     logging.getLogger(__name__).info(f'Changed:{repr(c)} New Value:{getattr(tstatdev, c)}')
        #
        # if 'cooling_setpoint_f' in data['changed']:
        #     if tstatdev.mode != 'heat' and tstatdev.cooling_setpoint_f < 65:
        #         logging.getLogger(__name__).info('Cooling setpoint was set below 65, increasing to 72')
        #         tstatdev.setCoolSetpoint(72)
        #
        # if 'system' in data['changed'] and tstatdev.system == 'coolfanon':
        #     logging.getLogger(__name__).info('System now cooling to %s', tstatdev.cooling_setpoint_f)

        if iteration == 5:
            logging.getLogger(__name__).info('>> DPS >> setMode 40')
            thermo.setMode(40)

        if iteration == 10:
            logging.getLogger(__name__).info('>> DPS >> setMiddleSetpoint')
            thermo.setMiddleSetpoint(setpoint=10, cf='c')


        logging.getLogger(__name__).info('>> DONE: DPS')



    if 'changed_sensors' in data and len(data['changed_sensors']) > 0:
        for s in data['changed_sensors']:
            logging.getLogger(__name__).info(f'Sensor Changed! DPS:{s.parent_sensorlist.dps} ID:{s.id} Name:"{s.name}" Changed:{s.changed}')
            # logging.getLogger(__name__).info(repr(s))
            # logging.getLogger(__name__).info(vars(s))

            for changed in s.changed:
                logging.getLogger(__name__).info(f'Changed:{repr(changed)} New Value:{getattr(s, changed)}')

            if 'sensor_added' in s.changed:
                logging.getLogger(__name__).info('New sensor was added!')
                # logging.getLogger(__name__).info(repr(s.parent_sensorlist))
                # logging.getLogger(__name__).info(str(s))

            if 'sensor_added' in s.changed and s.id == '01234567':
                logging.getLogger(__name__).info(f'Changing data for sensor {s.id}')

                ## by default every change will be sent immediately.  if multiple values are to be changed, it is much faster
                ##  to call s.delayUpdates() first, make the changes, and then call s.sendUpdates() to send them
                s.delayUpdates()

                ## make some changes
                # s.setName( 'Bedroom Sensor 1' )
                s.setEnabled(True)
                # s.setEnabled( False )
                # s.setOccupied( True )
                s.setParticipation('wake', True)
                # s.setParticipation( 'sleep', True )
                # s.setParticipation( 0x0F )
                # s.setUnknown2( 0x0A )

                ## send the queued changes
                s.sendUpdates()

                show_all_attribs = True

            if 'name' in s.changed:
                logging.getLogger(__name__).info(f'Sensor was renamed!  New name:{s.name}')

        logging.getLogger(__name__).info('DONE: changed_sensors')


