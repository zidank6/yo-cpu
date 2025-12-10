# yo / gurt assembler
# brandon gaona and zidan kazi
# i pledge my honor that i have abided by the stevens honor system.

import os
import sys

# opcode dictionary
opcodes = {
    "add": 0,   # 00
    "sub": 1,   # 01
    "load": 2,  # 10
    "store": 3  # 11
}

# register mapping
regs = {
    "r0": 0,
    "r1": 1,
    "r2": 2,
    "r3": 3
}


def clean():
    # remove old memory image files if they exist
    for name in ("instruction_mem.hex", "data_mem.hex"):
        try:
            os.remove(name)
            print("removed old", name)
        except FileNotFoundError:
            pass


def read_source(path):
    # read the assembly source file and return its lines
    try:
        with open(path, "r") as f:
            return f.readlines()
    except FileNotFoundError:
        print("file not found", path)
        sys.exit(1)


def parse_sections(lines):
    # split file into .text and .data sections
    in_text = False
    in_data = False
    text_lines = []
    data_values = []

    for raw in lines:
        line = raw.strip()

        # skip blank lines and pure comment lines
        if not line or line.startswith(";"):
            continue

        if line.lower() == ".text":
            in_text = True
            in_data = False
            continue

        if line.lower() == ".data":
            in_text = False
            in_data = True
            continue

        if in_text:
            text_lines.append(raw)

        elif in_data:
            # strip comment after data value if present
            data_part = raw.split(";", 1)[0].strip()
            if data_part:
                try:
                    val = int(data_part, 0)
                except ValueError:
                    print("invalid data value:", data_part)
                    sys.exit(1)

                if val < 0 or val > 255:
                    print("data value out of 8-bit range (0–255):", val)
                    sys.exit(1)

                data_values.append(val)

    return text_lines, data_values


def assemble_instruction(line):
    # convert one gurt instruction into an 8-bit machine code number
    if ";" in line:
        line = line.split(";", 1)[0]
    line = line.strip()
    if not line:
        return None

    parts = line.split()
    mnemonic = parts[0].lower()

    if mnemonic not in opcodes:
        print("unknown instruction:", line)
        sys.exit(1)

    opcode = opcodes[mnemonic]
    if mnemonic in ("add", "sub"):
        if len(parts) != 4:
            print("wrong operand count in:", line)
            sys.exit(1)

        rd = parts[1].lower()
        rs = parts[2].lower()
        rt = parts[3].lower()

        if rd not in regs or rs not in regs or rt not in regs:
            print("invalid register in:", line)
            sys.exit(1)

        return (
            (opcode << 6) |
            (regs[rd] << 4) |
            (regs[rs] << 2) |
            regs[rt]
        )

    if mnemonic == "load":
        if len(parts) != 4:
            print("wrong operand count in:", line)
            sys.exit(1)

        rd = parts[1].lower()
        rb = parts[2].lower()
        imm_str = parts[3]

        if rd not in regs or rb not in regs:
            print("invalid register in:", line)
            sys.exit(1)

        try:
            imm = int(imm_str, 0)
        except ValueError:
            print("invalid immediate in:", line)
            sys.exit(1)

        if imm < 0 or imm > 3:
            print("immediate out of 2-bit range (0–3):", imm)
            sys.exit(1)

        return (
            (opcode << 6) |
            (regs[rd] << 4) |
            (regs[rb] << 2) |
            imm
        )

    if mnemonic == "store":
        if len(parts) != 4:
            print("wrong operand count in:", line)
            sys.exit(1)

        rs = parts[1].lower()
        rb = parts[2].lower()
        imm_str = parts[3]

        if rs not in regs or rb not in regs:
            print("invalid register in:", line)
            sys.exit(1)

        try:
            imm = int(imm_str, 0)
        except ValueError:
            print("invalid immediate in:", line)
            sys.exit(1)

        if imm < 0 or imm > 3:
            print("immediate out of 2-bit range (0–3):", imm)
            sys.exit(1)

        return (
            (opcode << 6) |
            (regs[rs] << 4) |
            (regs[rb] << 2) |
            imm
        )

    print("unsupported instruction:", line)
    sys.exit(1)


def assemble_instructions(text_lines):
    words = []
    for l in text_lines:
        code = assemble_instruction(l)
        if code is not None:
            words.append(code & 0xff)
    return words


def write_mem_image(filename, words, per_row=16):
    # write an 8-bit logisim-compatible memory image file
    with open(filename, "w") as f:
        f.write("v3.0 hex words addressed\n")

        if not words:
            words = [0]

        padded = list(words)
        while len(padded) % per_row != 0:
            padded.append(0)

        addr = 0
        index = 0

        while index < len(padded):
            row = padded[index:index + per_row]
            f.write("{:02x}: ".format(addr))
            for w in row:
                f.write("{:02x} ".format(w & 0xff))
            f.write("\n")
            index += per_row
            addr += per_row


def main():
    if len(sys.argv) != 2:
        print("usage: python3 assembler.py yo.gurt")
        sys.exit(1)

    src = sys.argv[1]

    clean()
    lines = read_source(src)
    text_lines, data_values = parse_sections(lines)

    instr_words = assemble_instructions(text_lines)

    write_mem_image("instruction_mem.hex", instr_words)
    write_mem_image("data_mem.hex", data_values)

    print("assembled", src, "-> instruction_mem.hex, data_mem.hex")


if __name__ == "__main__":
    main()
