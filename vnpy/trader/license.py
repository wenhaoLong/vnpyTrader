import os
import datetime
import uuid
import pickle
# 安装方式 pip install wmi
import wmi
# 安装方式 pip install rsa
import rsa
from rsa.key import PublicKey, PrivateKey
from rsa import common, transform, core
import sys
from pathlib import Path

"""license 认证模块：该模块通过RSA加解密机制来实现
    在实际使用中，应分为产生license的生成器（掌握在公司手里）,以及嵌入到客户程序中的认证程序
    生成器流程：
        （1）生成一对RSA公钥和私钥，其中私钥妥善保管（在一个版本内使用），公钥嵌入到客户程序中
        （2）当客户有需求时，向公司提供其MAC地址（可通过模块中的`get_mac_address()`方法得到）
        （3）公司填入相关信息（见`generate_license()`）发送给客户，客户将其放入客户程序中的指定文件夹中
    认证程序流程：
        （1）读取指定位置的license文件
        （2）使用提供的公钥进行解密
        （3）验证程序（`validate()`函数）检验相关数据项是否有效，若有效则开始启动客户程序，否则提前退出程序(调用`exit()`方法)
    一个license所有的数据项：
        - mac-address: 机器码，用于绑定只能单机使用
        - end-date: 到期时间，用以判定license的有效时间性
        - version: 版本号，不同的版本号可以绑定不同的公钥
        - …………
"""


def dump_object(obj, path):
    """保存对象"""
    with open(path, 'wb') as f:
        pickle.dump(obj, f)


def load_object(path):
    with open(path, 'rb') as f:
        obj = pickle.load(f)
    return obj


def get_mac_address():
    """得到本机的 MAC 地址"""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


def get_disk_serial_number():
    """得到硬盘序列号"""
    c = wmi.WMI()
    for physical_disk in c.Win32_DiskDrive():
        return physical_disk.SerialNumber
    return "error"


def get_cpu_serial_number():
    """获取cpu序列号"""
    c = wmi.WMI()
    for cpu in c.Win32_Processor():
        return cpu.ProcessorId.strip()
    return "error"


def get_board_serial_number():
    """获取主板序列号"""
    c = wmi.WMI()
    for board in c.Win32_BaseBoard():
        return board.SerialNumber
    return "error"


def generate_rsa_keypair(nbits: int):
    """产生公钥和私钥"""
    public_key, private_key = rsa.newkeys(nbits=nbits)
    return public_key, private_key


def __pad_for_encrypt(message: str, target_length: int):
    """填充加密内容"""
    max_length = target_length - 11
    message_length = len(message)

    if message_length > max_length:
        raise OverflowError("%i bytes needed for message, but there is only space for %i"
                            % (message_length, max_length))

    padding = b""
    padding_length = target_length - message_length - 3

    while len(padding) < padding_length:
        needed_bytes = padding_length - len(padding)
        new_padding = os.urandom(needed_bytes + 5)
        new_padding = new_padding.replace(b"\x00", b"")
        padding = padding + new_padding[:needed_bytes]

    assert len(padding) == padding_length

    return b"".join([b"\x00\x02", padding, b"\x00", message])


def rsa_encrypt(message, key):
    """加密方法"""
    # 判断密钥类型
    if isinstance(key, PublicKey):
        a = key.e
        b = key.n
    elif isinstance(key, PrivateKey):
        a = key.d
        b = key.n
    else:
        raise TypeError("'key' must be PublicKey or PrivateKey")

    key_length = common.byte_size(b)
    # 得到信息字节
    message_bytes = bytes(message, encoding='utf-8')
    padded = __pad_for_encrypt(message_bytes, key_length)
    num = transform.bytes2int(padded)
    decryto = core.encrypt_int(num, a, b)
    out = transform.int2bytes(decryto)
    return out


def rsa_decrypt(message: bytes, key):
    """解密方法"""
    # 判断密钥类型
    if isinstance(key, PublicKey):
        a = key.e
        b = key.n
    elif isinstance(key, PrivateKey):
        a = key.d
        b = key.n
    else:
        raise TypeError("'key' must be PublicKey or PrivateKey")

    num = transform.bytes2int(message)
    decryto = core.decrypt_int(num, a, b)
    out = transform.int2bytes(decryto)
    sep_idx = out.index(b"\x00", 2)
    out = out[sep_idx + 1:]
    return out.decode()


def generate_license(private_key: PrivateKey, mac_address: str, end_date: str):
    """产生license"""
    _license = {}
    # 校验mac地址是否合法
    if len(mac_address) != 17:
        raise Exception("The length of mac-address must be 17!")
    if len(mac_address.split(':')) != 6:
        raise Exception("Format of mac-address error!")
    # 转换结束时间
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # 组装license
    _license["mac-address"] = mac_address
    _license["end-date"] = end_date
    # 返回license
    return _license.__str__()


def validate():
    running_path = Path(sys.argv[0]).parent
    """验证license是否有效"""
    # 加载公钥
    public_key_path = running_path.joinpath("public_key")
    license_path = running_path.joinpath("license")
    # public_key = load_object(public_key_path)
    public_key = PublicKey(17678024172605641870484485379373765045154353775774647612063188585229377042449387375486683344973933059875226700350516337536356936243196745526448255027904184849233915420944451548362350752407846657656554293246961153871129151902497397800479624446244954509302356486864279611430616643015294416638205564080606278386365471770757979966031669714520698584786484426511523926864094110425950634625735584833490057200000532410250844093535446915739692372052660331972359594892813942138928241282568255208957631097239343373540927749529700542612843294526067453133166583624701869442393881939817345685457400771510940670953666919506783257891, 65537)
    # 加载license 文件
    with open(license_path, 'rb') as f:
        _license = f.read()
    # 解密license
    _license = rsa_decrypt(_license, public_key)
    # 转换license为字典
    _license = eval(_license)
    if not isinstance(_license, dict):
        raise TypeError("license type error!")
    # 验证数据项
    mac_address = _license["mac_address"]
    disk_serial_number = _license["disk_serial_number"]
    cpu_serial_number = _license["cpu_serial_number"]
    board_serial_number = _license["board_serial_number"]
    end_date = _license["end_date"]
    # 如果机器码与本机机器码不匹配
    if mac_address != get_mac_address():
        print("Mac-address not match!")
        return False
    # 如果硬盘序列号不匹配
    if disk_serial_number != get_disk_serial_number():
        print("disk serial number not match!")
        return False
    # 如果cpu序列号不匹配
    if cpu_serial_number != get_cpu_serial_number():
        print("cpu serial number not match!")
        return False
    # 如果主板序列号不匹配
    if board_serial_number != get_board_serial_number():
        print("board serial number not match!")
        return False
    # 如果到期日期大于今天
    # 采用本地时间容易绕过该项认证，可更改为联网认证
    if datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S') < datetime.datetime.now():
        print("license expire!")
        return False
    return True
