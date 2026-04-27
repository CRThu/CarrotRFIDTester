from crft.parsers.base_parser import BaseParser, ParsedField, ParsedFrame


# Mifare Classic 指令码
_MIFARE_CMDS = {
    0x30: ("READ",          "Read Block"),
    0xA0: ("WRITE",         "Write Block (Mifare Ultralight)"),
    0xA2: ("WRITE",         "Write Block (NTAG)"),
    0xA4: ("WRITE",         "Write Value Block"),
    0x50: ("HALT",          "Halt"),
    0x60: ("AUTH_A",        "Authenticate with Key A"),
    0x61: ("AUTH_B",        "Authenticate with Key B"),
    0xC0: ("DECREMENT",     "Decrement Value Block"),
    0xC1: ("INCREMENT",     "Increment Value Block"),
    0xC2: ("RESTORE",       "Restore Value Block"),
    0xB0: ("TRANSFER",      "Transfer Value Block"),
}

# 访问位含义（部分）
_ACCESS_MAP = {
    0b000: "Always",
    0b010: "Key B only",
    0b100: "Never",
    0b110: "Key A or B",
}


class MifareClassicParser(BaseParser):
    """
    Mifare Classic 卡片指令解析器。

    解析对象是经由 PN532 InDataExchange 之后剥离 PN532 封装的原始 APDU 层数据。
    目前实现：READ / AUTH_A / AUTH_B / HALT 指令。
    """

    def can_parse(self, data: bytes) -> bool:
        return len(data) >= 1 and data[0] in _MIFARE_CMDS

    def parse(self, data: bytes) -> ParsedFrame:
        if not data:
            return ParsedFrame(raw=data, label="Mifare Classic (Empty)", is_valid=False)

        cmd_byte = data[0]
        short_name, cmd_desc = _MIFARE_CMDS.get(cmd_byte, ("UNKNOWN", f"Unknown Command 0x{cmd_byte:02X}"))

        fields: list[ParsedField] = []

        cmd_field = ParsedField(
            name="COMMAND",
            raw=bytes([cmd_byte]),
            value=cmd_byte,
            description=f"{short_name} — {cmd_desc}",
        )
        fields.append(cmd_field)

        # READ 指令: CMD(1) + BLOCK_NO(1)
        if cmd_byte == 0x30:
            if len(data) >= 2:
                blk = data[1]
                fields.append(ParsedField("Block Number", bytes([blk]), blk, f"Block {blk} (Sector {blk // 4})"))
            if len(data) > 2:
                fields.append(ParsedField("CRC", data[2:4], int.from_bytes(data[2:4], "little"), "ISO14443A CRC-A"))

        # AUTH 指令: CMD(1) + BLOCK_NO(1) + KEY(6) + UID(4)
        elif cmd_byte in (0x60, 0x61):
            key_type = "Key A" if cmd_byte == 0x60 else "Key B"
            if len(data) >= 2:
                blk = data[1]
                fields.append(ParsedField("Block Number", bytes([blk]), blk, f"Block {blk} (Sector {blk // 4})"))
            if len(data) >= 8:
                key = data[2:8]
                fields.append(ParsedField(key_type, key, int.from_bytes(key, "big"), "6-byte Authentication Key"))
            if len(data) >= 12:
                uid = data[8:12]
                fields.append(ParsedField("UID", uid, int.from_bytes(uid, "big"), "Card UID (4 bytes)"))

        # HALT 指令: CMD(1) + 0x00 + CRC(2)
        elif cmd_byte == 0x50:
            if len(data) >= 2:
                fields.append(ParsedField("Reserved", bytes([data[1]]), data[1], "Must be 0x00"))
            if len(data) >= 4:
                fields.append(ParsedField("CRC", data[2:4], int.from_bytes(data[2:4], "little"), "ISO14443A CRC-A"))

        # 其余指令：通用载荷
        else:
            if len(data) > 1:
                payload = data[1:]
                fields.append(ParsedField("Payload", payload, payload[0], f"{len(payload)} bytes"))

        return ParsedFrame(raw=data, label=f"Mifare Classic — {short_name}", fields=fields)
