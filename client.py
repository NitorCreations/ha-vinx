import asyncio
from time import sleep

from custom_components.vinx.lw3 import LW3


async def main():
    lw3 = LW3('office-assistant.nitor.zone', 61075)
    await lw3.connect()

    device_info = {
        'product_name': str(await lw3.get_property('/.ProductName')),
        'serial_number': str(await lw3.get_property('/.SerialNumber')),
        'mac_address': str(await lw3.get_property('/.MacAddress')),
    }

    print(device_info)

    signal_present = await lw3.get_property('/MEDIA/VIDEO/I1.SignalPresent')
    print(signal_present.__dict__)

    video_channel_id = await lw3.get_property('/SYS/MB/PHY.VideoChannelId')
    print(video_channel_id.__dict__)

    print('sleeping 5 sec')
    sleep(5)

    print('changing to 5')
    video_channel_id = await lw3.set_property('/SYS/MB/PHY.VideoChannelId', '5')
    print(video_channel_id.__dict__)

    print('changing back to 2')
    video_channel_id = await lw3.set_property('/SYS/MB/PHY.VideoChannelId', '2')
    print(video_channel_id.__dict__)
    #try:
    #    await lw3.get_property('/Foo')
    #except ValueError as e:
    #    print('caught error', e)


asyncio.run(main())
