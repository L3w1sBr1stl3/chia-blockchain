from typing import Any, Dict

constants: Dict[str, Any] = {
    "NUMBER_OF_HEADS": 3,  # The number of tips each full node keeps track of and propagates
    "DIFFICULTY_STARTING": 5000,  # These are in units of 2^32
    "DIFFICULTY_FACTOR": 3,  # The next difficulty is truncated to range [prev / FACTOR, prev * FACTOR]
    "IPS_FACTOR": 3,  # The next ips is truncated to range [prev / FACTOR, prev * FACTOR]
    # These 3 constants must be changed at the same time
    "DIFFICULTY_EPOCH": 128,  # The number of blocks per epoch
    "DIFFICULTY_WARP_FACTOR": 4,  # DELAY divides EPOCH in order to warp efficiently.
    "DIFFICULTY_DELAY": 32,  # EPOCH / WARP_FACTOR
    "DISCRIMINANT_SIZE_BITS": 1024,
    "BLOCK_TIME_TARGET": 300,  # The target number of seconds per block
    # The number of seconds that that the VDF must be run for, at a minimum
    "MIN_BLOCK_TIME": 30,
    # For the first epoch, since we have no previous blocks, we can't estimate vdf iterations per second
    "VDF_IPS_STARTING": 5000,
    "MAX_FUTURE_TIME": 7200,  # The next block can have a timestamp of at most these many seconds more
    "NUMBER_OF_TIMESTAMPS": 11,  # Than the average of the last NUMBEBR_OF_TIMESTAMPS blocks
    # If an unfinished block is more than these many seconds slower than the best unfinished block,
    # don't propagate it.
    "PROPAGATION_THRESHOLD": 300,
    # If the expected time is more than these seconds, slightly delay the propagation of the unfinished
    # block, to allow better leaders to be released first. This is a slow block.
    "PROPAGATION_DELAY_THRESHOLD": 1500,
    # Hardcoded genesis block, generated using tests/block_tools.py
    # Replace this any time the above constants change.
    "GENESIS_BLOCK": b"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x15N3\xd3\xf9H\xc2K\x96\xfe\xf2f\xa2\xbf\x87\x0e\x0f,\xd0\xd4\x0f6s\xb1\".\\\xf5\x8a\xb4\x03\x84\x8e\xf9\xbb\xa1\xca\xdef3:\xe4?\x0c\xe5\xc6\x12\x80\x17\xd2\xcc\xd7\xb4m\x94\xb7V\x959\xed4\x89\x04b\x08\x07^\xca`\x8f#%\xe9\x9c\x9d\x86y\x10\x96W\x9d\xce\xc1\x15r\x97\x91U\n\x11<\xdf\xb2\xfc\xfb<\x13\x00\x00\x00\x98\x97N\xe3py\xb5*\xe8\xbe_\xa5\xa5mq\xceY\x08$;\xe1\xef;:\xc0\x93\x84\xa6(`\xe7\xf1\x0b\xb6\x08\xb4\xa1\xc7\x03\xe5v\xb9)\xd2\xc9|\t\xcc\xb3\xd4\x05\xd9-\xa2;\xeb\xdd!\xd1\\Oh<\x01+\x9e\xbfK\xe3y\xd8\xd0T\xac\xb52+Zj+)\xad\xabIg\x82\x998\xe5\x86\xa3[\xd1\xc1\xe9\x9dD\xbb\xe2IN\x01\xdc\x1e\xcc\t\x1c\xa7\xe4\xb92\x98^\xd5\xd6\xce\xe1Z\xcd\x9e\xee\xba\x9f,\x94B?}\xf7\xeb\x8f,\xbds\xc4g\x02\"}\x88\x17.\xf7\xd3\x89\x15Vi\xbe2\xdct\xc4\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x02M\xf9\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1c#\xc2\xe9\x12\xd5I\xc1v\x07H\xa1\x90\xe7\xcaE\xfb\xe1d\xbd\x05=\x95\x14\xd15O\xb6\xed;\x00\xa4\xba!\xb99\xab\x89\xae\xa5\x96e\xf9\xd2D\x1c\xa8\xd9H\xb3\x15*\xa8\xdc\xc5\x89\xf9q\xc2J9\x01F\xd6\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xeb\x1e*\xda3k\x83\x83\xa6\xc9a\x83O\xfcM\x14\xd5E\x81Ob\x7fxW`A?\x06t\x8a\xf0\xf4n\xde\x9e\x9eHP\xd9\xd3rL\xebe-\xab\x96H\xdd\xeb\x8e\xea-\xeccL+\x1fF\xa7L\xdfy/\x03\x00\x00\x03\xa6\x00>\x93\x89\x7f\tiBhT\xa0\x90\x81\x93y\xb3\xe8#\xdb#\xfe(t\xc3\xd4b\x80\x0b\xceE\xd1r\xcc\xaag\x97\"\xfd\xcc\x99\xbbr\xea\x95\x9c\xb1\x16\x05K\xf0\x98\xd8j\x06P\xa2m\xc8\x8a\x1a\xe6\xf8\xed \xbb\xff\xd9\xf7*\xf9m\x16\xf1\x80j\xa2\xe9\xcb&S\x0e\x95\xeb\xe4W\xa6\xb0\x14\xd1Q\x9b\xc9vs\x07\x90.\x82#\xc5\\I\x0f\xfe\xd5%h\xf8{KsC\xa7\xb5T\xe2\x0fud7y\x8a\x01dK\x0e\x0b\x95\x13\xd3\x00\x00\x00\x00\x00\x00\x0c\xa5\x00\x03$Gm\xc3\x01\xcbm\x19N(P\xf3\xa5T\x87G\xae\x97\xde\x9f[\x86\x9c\x9d\xd2\x1b\x91\x9a{%\xb1\xf4c\xd4\x03\x84\"\xd8?\x96\xa6\xa5\x94\x1cYg\xcfb(\xf2\x94V\x8b\x14\x84\x86NR\x1d\'\xcd\xe8{\xff\xff\xc6\x00\x82\x8b]\'\x19)\x05\xad\xb7k\x90\x07u\xae\xe2\xbc\xbf$H\xcf5l\xf4M\xca\xc6\x8bW\xcc\xf2\xbd>\xaa\n\x02\x07\x13\xe9\xb5p-\xbc\x8c\xbb\xa8\x91\xc8\xbe\xfc\x01n\xdb\xb9W\x98\x1f\xce\xd0!\x1c\r\x00C\x08\xbeo0\x83\x00h\x0fQ\xe6\x15T\xde\xcc\x7f\xf9uhV\xff\x1ds\x98\x86\x95\x17\xc6\x921\xbcu\xf1~\xa2\x00KV\xd8\xf9\xfa\xe0~\xd9\xfb\x8e\xc4}d\x1b\xfc<#}f\x1ej\xdbr\xa1\xc8%\x13\xea\xff\xc0\x08A\x86\xb41MA{\x8d\xed\xdb7\x96\xc59\x8c>\xc0\xcc6\xba\xa5Im\xae\xe1k\xfeJX\xfcer^\x8b\x87\xe4\x1f\x1dz\xcc\x9aI\x12\xf8d,\xb3\xa0\xaab\xcaI8L\xb2E^\xb8U\xbe\xcb\x8b\x00\x00\x00\x00\x00\x00Cm\x00\x18\xeb\xb7d\xad`)\xbf\xb931rL`rm\x14\xe1C\x0e\x06.\xee_%\xaa\x87O$\x0e\xa7\xd3\x93\xd3\x91\xcd>\x9d\xba\xcb\x17Gxb\xcb:\xae\xba\x01\x8a\xac\x92\xef?P!(\xff\xde\xc3\xed\x14\xf96\x00\t\xe0\x10J\xb2\x83\x1f4s+\x8f\"iD|\x89\xd1\xd85\xc6\r\x98\xdeq\x9a&e\t-\x13\xd1JNT\xccr\x19\xd8\x1dm\x91\x11\xaf\xb2\xbak\xf0\x02\xe6\r<\xdc+i;\x8ek\xa5|\xc0F4`Q\x00\\\x83#?\xe7\x87\x7fzV\xe6\xc6\x88/\xaaz\xa9C\xbd@q\x84H-\xa3\xeai\x16\'\x87\xfbt2\xc5-\x12\xa0\x18\x8a\xa9\x9e\xe6\x93\xb6\x95\x01k\x94}%\xad\x12\xfb\x88\xb2\xa4e\xc8rZ\x0c\x02B|^\x00J\xb7\xcf\xe6v\x16pjv\xd6\xc3y\xc2\x84W\x979&\xdf\xf2\t\xd8\xc3\xb7D\xb5\xa0\xf2\x92\x109\xfb?U\xbd\x0f\\\x10\xe1c\xba\xa4\xa1f9\x85\xb9\xb9\x13\x88Bk\xc6\xf7\x8fXn> \xa5\xf0\x1b\xd0\x83\x00\x00\x00\x00\x00\x01\xf9\xb0\x00K\xda\x15\x12\x84\xa4\x99\x88\xa4,\xb6\xba$\xaaH\xee\x8cq\xfd\xde\xf1\t\xac\x81\'\xb8\r\x90\x96\xa3\x10\xefx\xae\x19s\xd9\xad\xdc\x10\xb34\x1d\x16i\x8bO\x8bv\x86\x98VjUt8\x1e`\xb91.I\x07\xda\xff\xed\xe6\x9f[\xe2\x16\x0c\xe9\xb7\xbc\x95\x916\x96\xd5=Z:\xe6\x80\x0b\x903\xd8%\xa8ApE\xc7\xaa\x0f\xde\xc5\xe0\xf0\x82\xf47\xc4\xc9\x9a\xff\x9aAB\xf5\x07\x0cX\xa3\xe3\x89\xc8\'\xc3\xfd\xc9\xd4\x93\xa9\xacD\xe5\x00\x06\x97\x1a\xf8\xa4\xd4\xac\x8b\t\xad\x0b\xb7.\xb4\xd3P\xc3;\x8b!\xcb\xbaY\xc6\xa7\xcd\xbc\xd3\x1b\x00\x87E\x9e>\xa6$\x00\xb4l\xfa\xdf\xaf\x03_\xb9\xfd\xb8\xf4\xae\x91y\x01K9\xb7\xc8t\x97\t\xdb\xc4k\xda\x9e\xff\xfc\xf3\xbbs\x10\xd7\'\xc9\xaa\xa3cq\x0f\x95\xb4\xc1\x83\xb7\x85\xe9(\xac\x83BDl\x05\xeeX\xb0\x87\xd4\xcd\x1f\xcc\x03`\x8d\x9cg\n\x8c\x15\x95\xc6:\x8e\x97\xe5\xc8\xeeO\x01\x93\xa6\x8e\xdbk\xef\x1ex\x8b\x12\xa5\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\xa7\xb0\x1a\xba$sST\x96\xa9[\xc1\xb2\x08\xbe5\xb41\x89\x8f\x19<\x18\x1db\x01!wG\x82\xc2\xb8\x0f:%R\xd3K\x08\xb4,\x81\xd1\nZx\xdeB\xd2\xa0\n\xac9>\x18\xf9\xf2e;\xe0\x06\x8eh6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\x88\x00\x00\x00\x00\x00\x02M\xf9\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00^0\x8dx\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa7\xb0\x1a\xba$sST\x96\xa9[\xc1\xb2\x08\xbe5\xb41\x89\x8f\x19<\x18\x1db\x01!wG\x82\xc2\xb8\x99V\x94\x94i&:\x91\xfacm_63F\xe2\xd9\x89!\x9e%\xfbT\x9b\xc2\xe6\xcd\xf1\xbc\x13J\xa3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00X(\x82&\xee\xb9\x0e,\xf3\x9cJ`\xa5\x96\x99\x95\x02\x15wo\xb3d!\x9e\xd1\xf8\"y\xf8\x16\xcc\x9an\xf4}\xc4hUg\xd9\xee\x93-\x7f\x8a`\x81\x15\t)\'D\x95\xfb\xa2\xf6\x137\xe4\xe8\x1b\xcf\x89\x8fW\x02U>\xa0\xbb\x1c\xbew\xa0\xbe\xf2\x0716%.\x17\xf3\xbfm\xe7e\x88\xc0\xed\xbfE\xa6H\x99S\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8b)\xaa\x96x8\xd76J\xa6\x8b[\x98\t\xe0\\\xe3^7qD\x8c\xf5q\x08\xf2\xa2\xc9\xb03mv\x00\x00\x0e\x8dJQ\x00\x00M\xd3\xe2\xd6,\xa9\xef/#O\xcbJ\x96\xbf\xba\xaf\xa4G\xc0\xe6\xe5\x90\xad\x0c\xab\xfb\xc5\x9cz\x9e\xec\xb7h:\xb2\x13\xf7\xc9\x9e\xb8C\xe6,\xef\xbd\x85\x80C\x0c\x8a\x9e=\xf2\x19|s\xd2\xe2\xca\xe56\xcc\xb0\x04\xa0\x1ae\x17\x99\xddh\xfd\xc3\xb6)\x14\x8d\xcb\x03\xe0\x9d\xfa\x0e\xb5\xa9\xc5d\x82;\x87\xad\xda\x8dA\xa1+T\x0f\x010\xf6\xf5`\x04\xcd+ta\xa4\xf0\x19\xc7[\xb7\xeb8\xe35\x9c\xb0\xff\x85\xe3\x87\xac\xb0\x0e,\x8b)\xaa\x96x8\xd76J\xa6\x8b[\x98\t\xe0\\\xe3^7qD\x8c\xf5q\x08\xf2\xa2\xc9\xb03mv\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00_\xec\xebf\xff\xc8o8\xd9Rxlmily\xc2\xdb\xc29\xddN\x91\xb4g)\xd7:\'\xfbW\xe9\x00\x00\x00\x00\x00\x00\x00\x00",  # noqa: E501

    # Target tx count per sec
    "TX_PER_SEC": 20,
    # Size of mempool = 10x the size of block
    "MEMPOOL_BLOCK_BUFFER": 10,
}
